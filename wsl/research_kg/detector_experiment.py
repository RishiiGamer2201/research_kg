"""
Contamination detector experiment (self-healing KB, first result).

Signal: an entity's description should be semantically consistent with its own graph
neighbourhood. We encode both with BGE-M3 and score cosine similarity. A low score flags the
description as inconsistent with the structure, i.e. likely contaminated. Training-free.

Evaluation is a controlled-injection benchmark on STRUCTURE-RICH entities (>= MIN_DEG edges) that
have a real description:
  - clean  (label 0): the entity's real description vs its own structure.
  - injected (label 1): a DIFFERENT random entity's real description vs this entity's structure
    (a wrong-entity fabrication, guaranteed inconsistent, needs no generation).
Plus a REAL-contamination subset: the actual Llama-fabricated descriptions that happen to have
>= 2 edges, as an in-the-wild anchor.

Reports separation, ROC-AUC, and precision/recall/F1 at the best-F1 threshold.
"""
import os, json, random, math
from collections import defaultdict
import torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

_ROOT = os.environ.get('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
P = os.path.join(_ROOT, 'DBP5L/processed')
MODEL = 'BAAI/bge-m3'
MIN_DEG = 3
N_CONTROLLED = 200
random.seed(0)

cur = json.load(open(f'{P}/entity_descriptions.json', encoding='utf-8'))
bak = json.load(open(f'{P}/entity_descriptions_backup.json', encoding='utf-8'))
ent = json.load(open(f'{P}/entities.json', encoding='utf-8'))
id2name = {int(k): v.get('name', '') for k, v in ent.items()}
lang = {int(k): v.get('lang', 'en') for k, v in ent.items()}
rel = {}
if os.path.exists(f'{P}/relation_names.json'):
    rel = {int(k): v for k, v in json.load(open(f'{P}/relation_names.json')).items()}

# structure from ALL splits (detection is not the KGC task, so using all known edges is fair)
out_edges = defaultdict(list)
deg = defaultdict(int)
for sp in ['train', 'valid', 'test']:
    for line in open(f'{P}/{sp}.json'):
        ex = json.loads(line)
        h, r, t = ex['h'], ex['r'], ex['t']
        out_edges[h].append((r, t)); deg[h] += 1; deg[t] += 1

def serialize_structure(eid):
    parts = []
    by_rel = defaultdict(list)
    for r, t in out_edges.get(eid, [])[:12]:
        by_rel[rel.get(r, f'relation {r}')].append(id2name.get(t, ''))
    for rname, tails in list(by_rel.items())[:6]:
        parts.append(f"{rname}: {', '.join(x for x in tails[:4] if x)}")
    return id2name.get(eid, '') + ' | ' + ' | '.join(parts) if parts else id2name.get(eid, '')

def ascii_frac(s):
    L = [c for c in s if c.isalpha()]
    return sum(c.isascii() for c in L) / len(L) if L else 0.0

# structure-rich entities with a real (not name-only, not contaminated) description
rich = [int(k) for k, v in cur.items()
        if deg[int(k)] >= MIN_DEG and v == bak.get(k) and len(v) > len(id2name.get(int(k), '')) + 10]
random.shuffle(rich)
rich = rich[:N_CONTROLLED]

# real in-the-wild contamination that has >=2 edges (EL/JA English prose that changed)
real_contam = [int(k) for k, v in cur.items()
               if lang[int(k)] in ('el', 'ja') and v != bak.get(k) and '|' not in v
               and len(v) >= 60 and ascii_frac(v) > 0.85 and deg[int(k)] >= 2]
random.shuffle(real_contam)
real_contam = real_contam[:40]

# build (text, structure, label, tag) rows
rows = []
donors = list(rich)
for i, e in enumerate(rich):
    struct = serialize_structure(e)
    rows.append((cur[str(e)], struct, 0, 'clean'))                       # real desc vs own structure
    donor = donors[(i + 7) % len(donors)]
    while donor == e:
        donor = random.choice(donors)
    rows.append((cur[str(donor)], struct, 1, 'injected'))                # wrong-entity desc vs structure
for e in real_contam:
    rows.append((cur[str(e)], serialize_structure(e), 1, 'real_contam')) # actual Llama fabrication

print(f'controlled entities: {len(rich)} | real-contamination anchor: {len(real_contam)} | rows: {len(rows)}')

# encode with BGE-M3
device = 'cuda' if torch.cuda.is_available() else 'cpu'
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModel.from_pretrained(MODEL, torch_dtype=torch.bfloat16).to(device).eval()

@torch.no_grad()
def embed(texts, bs=64, ml=160):
    vecs = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i+bs], max_length=ml, padding='max_length', truncation=True, return_tensors='pt').to(device)
        out = model(**enc).last_hidden_state.float()
        m = enc['attention_mask'].unsqueeze(-1).float()
        pooled = (out * m).sum(1) / m.sum(1).clamp(min=1e-6)
        vecs.append(F.normalize(pooled, dim=-1).cpu())
    return torch.cat(vecs)

desc_emb = embed([r[0] for r in rows])
struct_emb = embed([r[1] for r in rows])
scores = (desc_emb * struct_emb).sum(1).tolist()   # cosine consistency; low = inconsistent

def stats(sel):
    s = [scores[i] for i in sel]
    return (sum(s)/len(s), min(s), max(s)) if s else (0, 0, 0)

clean_idx = [i for i, r in enumerate(rows) if r[3] == 'clean']
inj_idx   = [i for i, r in enumerate(rows) if r[3] == 'injected']
rc_idx    = [i for i, r in enumerate(rows) if r[3] == 'real_contam']
print(f"consistency (mean): clean={stats(clean_idx)[0]:.3f}  injected={stats(inj_idx)[0]:.3f}  real_contam={stats(rc_idx)[0]:.3f}")

# controlled benchmark: clean (0) vs injected (1). Flag = score below threshold.
labels = [rows[i][2] for i in clean_idx + inj_idx]
sc = [scores[i] for i in clean_idx + inj_idx]

# ROC-AUC (probability a contaminated row scores lower than a clean row)
pos = [sc[i] for i in range(len(sc)) if labels[i] == 1]
neg = [sc[i] for i in range(len(sc)) if labels[i] == 0]
auc = sum((p < n) + 0.5*(p == n) for p in pos for n in neg) / (len(pos)*len(neg))

best = None
for thr in sorted(set(sc)):
    tp = sum(1 for i in range(len(sc)) if sc[i] < thr and labels[i] == 1)
    fp = sum(1 for i in range(len(sc)) if sc[i] < thr and labels[i] == 0)
    fn = sum(1 for i in range(len(sc)) if sc[i] >= thr and labels[i] == 1)
    prec = tp/(tp+fp) if tp+fp else 0
    rec = tp/(tp+fn) if tp+fn else 0
    f1 = 2*prec*rec/(prec+rec) if prec+rec else 0
    if best is None or f1 > best[0]:
        best = (f1, thr, prec, rec)
f1, thr, prec, rec = best
print(f"\nCONTROLLED BENCHMARK (clean vs wrong-entity injection), n={len(sc)}")
print(f"  ROC-AUC = {auc:.3f}")
print(f"  best-F1 threshold = {thr:.3f} -> precision {prec:.3f}, recall {rec:.3f}, F1 {f1:.3f}")

# how would that threshold catch the REAL in-the-wild contamination?
if rc_idx:
    caught = sum(1 for i in rc_idx if scores[i] < thr)
    print(f"  real in-the-wild contamination flagged at that threshold: {caught}/{len(rc_idx)} ({caught/len(rc_idx)*100:.0f}%)")

json.dump({'auc': auc, 'threshold': thr, 'precision': prec, 'recall': rec, 'f1': f1,
           'mean_clean': stats(clean_idx)[0], 'mean_injected': stats(inj_idx)[0],
           'mean_real_contam': stats(rc_idx)[0], 'n_controlled': len(rich), 'n_real_contam': len(rc_idx)},
          open(os.path.join(_ROOT, 'logs/detector_result.json'), 'w'), indent=2)
print('\nsaved logs/detector_result.json')

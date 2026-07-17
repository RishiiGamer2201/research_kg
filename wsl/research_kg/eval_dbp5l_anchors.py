"""
eval_dbp5l_anchors.py — Anchor-aware eval for the CRR+XL checkpoints (W2 / Gate G1).

The XL models were TRAINED with anchor-augmented queries:
    q = normalize( (encode(query) + encode(anchor)) / 2 )
but the standard eval_dbp5l.py scores the BARE query. That train/eval mismatch may be the real
cause of the reported 3.17% collapse (same bug class as run v2). This script evaluates WITH matched
anchors to decide Gate G1:
  * anchor recovers perf  -> the -68% was a mismatch artifact; negative result dies/softens.
  * still collapses       -> negative result is real and now defensible.

Anchor sourcing mirrors PreTokenizedDataset._pick_anchor in train_dbp5l_lora.py:
  cands = anchors_by_rel[str(r)]  (built from TRAIN triples: {'h','t','lang'})
  if XL and query lang != 'en': prefer EN candidates, then same-lang
  drop candidates whose head == query head
  anchor text = description of candidate tail(s)
We average the embeddings of up to K sampled anchors (K defaults to 4 = training n_anchors) to
reduce the single-sample noise; --anchor-mode none reproduces the bare-query control (~3.17%).

Usage (run when GPU is free):
  python3 eval_dbp5l_anchors.py --checkpoint .../crr_xl/best_model.pt --anchor-mode meanK --k 4
  python3 eval_dbp5l_anchors.py --checkpoint .../crr_xl/best_model.pt --anchor-mode none   # control
"""
import os, json, argparse, logging, random
from collections import defaultdict
import torch
import torch.nn.functional as F

from eval_dbp5l import (BGE_M3_LoRA_KGC, load_checkpoint, encode_entities,
                        compute_filtered_metrics, PROCESSED)
from transformers import AutoTokenizer

logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)
IND = os.path.join(os.environ.get('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg')), 'DBP5L/ind')
LANGS = ['en', 'fr', 'es', 'ja', 'el']


def build_anchor_text_fn(anchors_by_rel, entity_texts, use_xl, k, rng):
    """Return f(h, r, lang) -> list of up to k anchor texts, mirroring training _pick_anchor."""
    def pick(h, r, lang):
        cands = anchors_by_rel.get(str(r), [])
        if use_xl and lang != 'en':
            cands = [c for c in cands if c.get('lang') == 'en'] + \
                    [c for c in cands if c.get('lang') == lang]
        cands = [c for c in cands if c.get('h') != h]
        if not cands:
            return []
        sample = cands if len(cands) <= k else rng.sample(cands, k)
        return [entity_texts[c['t']] for c in sample if c['t'] in entity_texts]
    return pick


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--anchor-mode', choices=['none', 'meanK'], default='meanK')
    ap.add_argument('--k', type=int, default=4)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model, model_name, lora_rank, ml = load_checkpoint(args.checkpoint)
    model = model.to(device).eval()
    tok = AutoTokenizer.from_pretrained('BAAI/bge-m3')
    logger.info(f'anchor-mode={args.anchor_mode} k={args.k} max_length={ml}')

    # data
    entity_texts = {int(k): v for k, v in json.load(open(f'{PROCESSED}/entity_descriptions.json', encoding='utf-8')).items()}
    ent_json = json.load(open(f'{PROCESSED}/entities.json'))
    entity_lang = {int(k): v.get('lang', 'en') for k, v in ent_json.items()}
    relation_names = json.load(open(f'{PROCESSED}/relation_names.json'))
    anchors_by_rel = json.load(open(f'{PROCESSED}/anchors_by_rel.json'))
    test = [json.loads(l) for l in open(f'{PROCESSED}/test.json')]
    logger.info(f'{len(test)} test triples')

    all_ids = sorted(entity_texts.keys())
    eid_to_idx = {e: i for i, e in enumerate(all_ids)}

    # filter map incl. support triples (same logic as eval_dbp5l.py)
    fm = defaultdict(set)
    for path in ['train.json', 'valid.json', 'test.json']:
        for line in open(f'{PROCESSED}/{path}'):
            ex = json.loads(line); fm[(ex['h'], ex['r'])].add(ex['t'])
    offset = 0
    for lang in LANGS:
        up = f'{IND}/{lang}/entity_uris.txt'; sp = f'{IND}/{lang}/support.txt'
        if not os.path.exists(up):
            continue
        n = sum(1 for _ in open(up))
        if os.path.exists(sp):
            for line in open(sp):
                p = line.split()
                if len(p) >= 3:
                    fm[(offset + int(p[0]), int(p[1]))].add(offset + int(p[2]))
        offset += n

    # candidate embeddings (BARE — anchors only augment the query side)
    all_emb = encode_entities(model, tok, entity_texts, all_ids, max_length=ml, device=device).to(device)
    lang_ids = defaultdict(list); lang_idx = defaultdict(list)
    for i, e in enumerate(all_ids):
        lang_ids[entity_lang.get(e, 'en')].append(e); lang_idx[entity_lang.get(e, 'en')].append(i)
    lang_emb = {l: all_emb[torch.tensor(ix)] for l, ix in lang_idx.items()}
    lang_lidx = {l: {e: j for j, e in enumerate(lang_ids[l])} for l in lang_ids}

    pick = build_anchor_text_fn(anchors_by_rel, entity_texts, use_xl=True, k=args.k, rng=rng)

    def enc_text(texts):
        e = tok(texts, max_length=ml, padding='max_length', truncation=True, return_tensors='pt').to(device)
        return model.encode(e['input_ids'], e['attention_mask'])

    wl = defaultdict(lambda: {'mrr': [], 'h1': [], 'h3': [], 'h10': []})
    wl_all = {'mrr': [], 'h1': [], 'h3': [], 'h10': []}
    model.eval()
    with torch.no_grad():
        for n, ex in enumerate(test):
            h, r, t = ex['h'], ex['r'], ex['t']; lang = ex.get('lang', 'en')
            if t not in eid_to_idx or t not in lang_lidx.get(lang, {}):
                continue
            qtext = f"{entity_texts.get(h, f'entity_{h}')} [SEP] {relation_names.get(str(r), f'relation {r}')}"
            q = enc_text([qtext])  # (1,D)
            if args.anchor_mode == 'meanK':
                atexts = pick(h, r, lang)
                if atexts:
                    a = enc_text(atexts).mean(0, keepdim=True)  # (1,D)
                    q = F.normalize((q + a) / 2.0, dim=-1)
            l_embs = lang_emb[lang]
            sims = torch.matmul(q, l_embs.T).squeeze(0)
            ti = lang_lidx[lang][t]
            filt = [lang_lidx[lang][ft] for ft in fm.get((h, r), set())
                    if ft in lang_lidx.get(lang, {}) and ft != t]
            m = compute_filtered_metrics(sims.cpu(), ti, filt + [ti])
            for kk in ['mrr', 'h1', 'h3', 'h10']:
                wl_all[kk].append(m[kk]); wl[lang][kk].append(m[kk])
            if (n + 1) % 5000 == 0:
                logger.info(f'  {n+1}/{len(test)} | running WL-MRR {sum(wl_all["mrr"])/len(wl_all["mrr"])*100:.2f}%')

    def fmt(d):
        nn = len(d['mrr'])
        return f"MRR={sum(d['mrr'])/nn*100:.2f}% H@1={sum(d['h1'])/nn*100:.2f}% H@10={sum(d['h10'])/nn*100:.2f}% (n={nn})" if nn else 'N/A'
    print('\n' + '=' * 60)
    print(f'ANCHOR-AWARE EVAL | {os.path.basename(os.path.dirname(args.checkpoint))} | mode={args.anchor_mode} k={args.k}')
    print('=' * 60)
    print('WITHIN-LANGUAGE:', fmt(wl_all))
    for l in LANGS:
        print(f'  {l.upper()}: {fmt(wl[l])}')


if __name__ == '__main__':
    main()

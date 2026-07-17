"""
eval_dbp5l.py — Full Inductive Evaluation on DBP-5L-Ind
=========================================================
Computes FILTERED MRR, H@1, H@3, H@10 for a trained BGE-M3+LoRA checkpoint.

Inductive evaluation protocol:
  1. Encode ALL candidate entities (train + test) using their text descriptions
  2. For each test triple (h, r, t):
     - Query embedding = encode(h_description)
     - Score = cosine_similarity(query, all_candidate_embeddings)
     - Rank the correct tail entity among ALL candidates
     - Apply filtering: remove other true tails of (h, r) from ranking
  3. Report: MRR, H@1, H@3, H@10 — overall AND per-language

Usage:
    source ~/research_kg/RAA-KGC/SimKGC/venv/bin/activate

    # Evaluate a specific checkpoint:
    python3 eval_dbp5l.py --checkpoint ~/research_kg/DBP5L/checkpoints/bgem3_lora_*/best_model.pt

    # Evaluate latest checkpoint automatically:
    python3 eval_dbp5l.py --latest

    # Per-language breakdown:
    python3 eval_dbp5l.py --latest --per-language
"""

import os
import json
import glob
import argparse
import logging
from collections import defaultdict

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer, AutoModel
import torch.nn as nn

logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# RESEARCH_KG_ROOT lets a clean clone point at data elsewhere without editing source; default = old behavior.
_ROOT = os.environ.get('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
PROCESSED = os.path.join(_ROOT, 'DBP5L/processed')
CHECKPOINT_DIR = os.path.join(_ROOT, 'DBP5L/checkpoints')
CACHE_DIR = os.path.join(_ROOT, 'DBP5L/token_cache')
DESC_PATH_OVERRIDE = None  # set by --desc-path for description ablations


# ─── LoRA Layer (must match train_dbp5l_lora.py exactly) ─────────────────────
class LoRALinear(nn.Module):
    def __init__(self, linear: nn.Linear, rank: int = 8, alpha: float = 16.0):
        super().__init__()
        self.linear = linear
        self.linear.weight.requires_grad_(False)
        if self.linear.bias is not None:
            self.linear.bias.requires_grad_(False)
        in_f, out_f = linear.in_features, linear.out_features
        self.lora_A = nn.Parameter(torch.randn(rank, in_f) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(out_f, rank))
        self.scale = alpha / rank

    def forward(self, x):
        dtype = x.dtype
        x32 = x.float()
        base = self.linear(x)
        lora = F.linear(F.linear(x32, self.lora_A), self.lora_B) * self.scale
        return base + lora.to(dtype)


def inject_lora(model, rank=8, alpha=16.0, target_modules=('query', 'value')):
    replaced = 0
    for name, module in model.named_modules():
        for child_name, child in module.named_children():
            if isinstance(child, nn.Linear):
                if any(t in child_name for t in target_modules):
                    setattr(module, child_name, LoRALinear(child, rank=rank, alpha=alpha))
                    replaced += 1
    return replaced


# ─── Model (must match train_dbp5l_lora.py exactly) ──────────────────────────
class BGE_M3_LoRA_KGC(nn.Module):
    def __init__(self, model_name, lora_rank=8, lora_alpha=16.0,
                 lora_targets=('query', 'value'), temperature=0.05):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name, torch_dtype=torch.bfloat16)
        for p in self.encoder.parameters():
            p.requires_grad_(False)
        inject_lora(self.encoder, rank=lora_rank, alpha=lora_alpha, target_modules=lora_targets)
        self.temperature = nn.Parameter(torch.tensor(temperature))

    def encode(self, input_ids, attention_mask):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        h = out.last_hidden_state.float()
        mask = attention_mask.unsqueeze(-1).float()
        pooled = (h * mask).sum(1) / mask.sum(1).clamp(min=1e-6)
        return F.normalize(pooled, dim=-1)


# ─── Evaluation ───────────────────────────────────────────────────────────────
def load_checkpoint(checkpoint_path):
    """Load model from a saved checkpoint."""
    logger.info(f'Loading checkpoint: {checkpoint_path}')
    ckpt = torch.load(checkpoint_path, map_location='cpu')
    args = ckpt.get('args', {})

    model_name = args.get('model_name', 'BAAI/bge-m3')
    lora_rank = args.get('lora_rank', 8)
    max_length = args.get('max_length', 96)  # read from saved training args

    model = BGE_M3_LoRA_KGC(model_name, lora_rank=lora_rank, lora_alpha=lora_rank * 2)
    model.load_state_dict(ckpt['model_state_dict'])
    logger.info(f'Loaded epoch {ckpt.get("epoch", "?")} | valid acc@1 at save: {ckpt.get("valid_acc1", "?"):.2f}%')
    logger.info(f'Checkpoint training args: max_length={max_length} | lora_rank={lora_rank}')
    return model, model_name, lora_rank, max_length


def encode_entities(model, tokenizer, entity_texts, entity_ids,
                    max_length=96, batch_size=256, device='cuda'):
    """Encode all entities into embeddings. Returns (n_entities, d) tensor."""
    logger.info(f'Encoding {len(entity_ids)} entities (batch {batch_size})...')

    # Cache path for embeddings
    cache_key = f'entity_embeddings_{len(entity_ids)}.pt'
    cache_path = os.path.join(CACHE_DIR, cache_key)

    texts = [entity_texts.get(eid, f'entity_{eid}') for eid in entity_ids]

    # Tokenize
    all_ids, all_masks = [], []
    for i in range(0, len(texts), 512):
        batch = texts[i:i+512]
        enc = tokenizer(batch, max_length=max_length, padding='max_length',
                        truncation=True, return_tensors='pt')
        all_ids.append(enc['input_ids'])
        all_masks.append(enc['attention_mask'])
    all_ids = torch.cat(all_ids)
    all_masks = torch.cat(all_masks)

    # Encode in batches
    model.eval()
    embeddings = []
    ds = TensorDataset(all_ids, all_masks)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0)

    with torch.no_grad():
        for i, (ids, mask) in enumerate(loader):
            ids, mask = ids.to(device), mask.to(device)
            emb = model.encode(ids, mask)
            embeddings.append(emb.cpu())
            if (i + 1) % 10 == 0:
                logger.info(f'  Encoded {min((i+1)*batch_size, len(texts))}/{len(texts)} entities')

    embeddings = torch.cat(embeddings, dim=0)  # (N, D)
    logger.info(f'Entity embeddings: {embeddings.shape} | dtype: {embeddings.dtype}')
    return embeddings


def compute_filtered_metrics(scores, true_tail_idx, filter_indices):
    """
    Filtered ranking: remove other true tails from the ranking before computing rank.
    scores: (N_candidates,) — similarity scores
    true_tail_idx: int — index of the correct tail in scores
    filter_indices: list[int] — indices of ALL true tails (including the current one)
    """
    true_score = scores[true_tail_idx].item()

    # Set scores of other true tails to -inf (filtered MRR)
    scores_filtered = scores.clone()
    for idx in filter_indices:
        if idx != true_tail_idx:
            scores_filtered[idx] = -float('inf')

    # Rank of the true tail (1-indexed)
    rank = (scores_filtered > true_score).sum().item() + 1

    return {
        'rank': rank,
        'mrr': 1.0 / rank,
        'h1':  1 if rank <= 1 else 0,
        'h3':  1 if rank <= 3 else 0,
        'h10': 1 if rank <= 10 else 0,
    }


def evaluate(checkpoint_path, per_language=True, max_length=None, zero_shot=False, dump_ranks=None):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f'Device: {device}')

    if zero_shot:
        logger.info('ZERO-SHOT MODE: Loading raw BGE-M3 without LoRA (no checkpoint)')
        model_name = 'BAAI/bge-m3'
        # Use a plain BGE-M3 without any LoRA layers for zero-shot baseline
        from transformers import AutoModel
        class PlainBGE(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder = AutoModel.from_pretrained(model_name, torch_dtype=torch.bfloat16)
            def encode(self, input_ids, attention_mask):
                out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                h = out.last_hidden_state.float()
                mask = attention_mask.unsqueeze(-1).float()
                pooled = (h * mask).sum(1) / mask.sum(1).clamp(min=1e-6)
                return F.normalize(pooled, dim=-1)
        model = PlainBGE().to(device)
        ckpt_name = 'zero_shot_bgem3'
        if max_length is None:
            max_length = 96
    else:
        model, model_name, lora_rank, ckpt_max_length = load_checkpoint(checkpoint_path)
        model = model.to(device)
        ckpt_name = os.path.basename(os.path.dirname(checkpoint_path))
        if max_length is None:
            max_length = ckpt_max_length  # auto-use training max_length
            logger.info(f'Auto-detected max_length={max_length} from checkpoint')
        elif max_length != ckpt_max_length:
            logger.warning(f'CLI --max-length={max_length} overrides checkpoint max_length={ckpt_max_length}')
    logger.info(f'Evaluating with max_length={max_length}')
    # Use the checkpoint's own encoder tokenizer (BGE-M3, mBERT, XLM-R, ...) — not hardcoded.
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    logger.info(f'Tokenizer: {model_name}')

    # Load rich entity descriptions (override path via --desc-path for ablations)
    desc_path = DESC_PATH_OVERRIDE or f'{PROCESSED}/entity_descriptions.json'
    if os.path.exists(desc_path):
        logger.info(f'Loading entity descriptions from {desc_path}')
        with open(desc_path, encoding='utf-8') as f:
            desc_data = json.load(f)
        entity_texts = {int(k): v for k, v in desc_data.items()}
        logger.info(f'  Loaded {len(entity_texts)} descriptions')
    else:
        logger.info('WARNING: entity_descriptions.json not found! Run build_entity_descriptions.py first.')
        with open(f'{PROCESSED}/entities.json') as f:
            raw_ents = json.load(f)
        entity_texts = {
            int(k): (f"{v['name']}: {v['description']}"
                     if v.get('description') and v['description'] != v['name']
                     else v.get('name', ''))
            for k, v in raw_ents.items()
        }
    entity_lang = {int(k): v.get('lang', 'en') for k, v in
                   json.load(open(f'{PROCESSED}/entities.json')).items()}

    # Load relation names
    rel_names_path = f'{PROCESSED}/relation_names.json'
    if os.path.exists(rel_names_path):
        with open(rel_names_path) as f:
            relation_names = json.load(f)
        logger.info(f'Loaded {len(relation_names)} relation names')
    else:
        logger.info('WARNING: relation_names.json missing — queries will lack relation context')
        relation_names = {}

    # Load test triples
    logger.info('Loading test triples...')
    test_examples = []
    with open(f'{PROCESSED}/test.json') as f:
        for line in f:
            test_examples.append(json.loads(line))
    logger.info(f'  {len(test_examples)} test triples')

    # Build candidate entity list (ALL entities — inductive eval)
    all_entity_ids = sorted(entity_texts.keys())
    eid_to_idx = {eid: i for i, eid in enumerate(all_entity_ids)}

    # Build filter map: (h, r) -> set of true tails (for filtered eval)
    logger.info('Building filter map...')
    filter_map = defaultdict(set)
    for path in [f'{PROCESSED}/train.json', f'{PROCESSED}/valid.json', f'{PROCESSED}/test.json']:
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                ex = json.loads(line)
                filter_map[(ex['h'], ex['r'])].add(ex['t'])

    # Also filter SUPPORT triples: they are known-true facts about the test entities
    # (held out as the inference/support graph, not in test.json). Standard filtered
    # setting requires removing ALL known true tails, including these. Support edges use
    # per-language local IDs; convert to the same global IDs preprocess assigned
    # (global_id = lang_offset + local_id, langs ordered en,fr,es,ja,el).
    IND = os.path.join(_ROOT, 'DBP5L/ind')
    LANGS = ['en', 'fr', 'es', 'ja', 'el']
    n_support_filtered = 0
    if os.path.isdir(IND):
        offset = 0
        for lang in LANGS:
            uri_path = f'{IND}/{lang}/entity_uris.txt'
            sup_path = f'{IND}/{lang}/support.txt'
            if not os.path.exists(uri_path):
                continue
            n_ent = sum(1 for _ in open(uri_path))
            if os.path.exists(sup_path):
                with open(sup_path) as f:
                    for line in f:
                        p = line.split()
                        if len(p) < 3:
                            continue
                        h = offset + int(p[0]); r = int(p[1]); t = offset + int(p[2])
                        filter_map[(h, r)].add(t)
                        n_support_filtered += 1
            offset += n_ent
        logger.info(f'  Added {n_support_filtered} support triples to filter map')
    else:
        logger.warning(f'  Support dir {IND} not found — support triples NOT filtered')

    # Encode all entities
    all_embeddings = encode_entities(
        model, tokenizer, entity_texts, all_entity_ids,
        max_length=max_length, device=device
    )
    all_embeddings = all_embeddings.to(device)  # (N, D) float32

    # Build per-language entity index for within-language eval
    lang_entity_ids = defaultdict(list)   # lang -> [global_entity_id, ...]
    lang_entity_idx = defaultdict(list)   # lang -> [idx_in_all_entity_ids, ...]
    for i, eid in enumerate(all_entity_ids):
        lang = entity_lang.get(eid, 'en')
        lang_entity_ids[lang].append(eid)
        lang_entity_idx[lang].append(i)

    # Pre-extract per-language embedding blocks
    lang_embeddings = {}    # lang -> (N_lang, D) tensor on GPU
    lang_eid_to_lidx = {}  # lang -> {global_eid: local_idx}
    for lang, idxs in lang_entity_idx.items():
        t_idxs = torch.tensor(idxs, dtype=torch.long)
        lang_embeddings[lang] = all_embeddings[t_idxs]  # (N_lang, D)
        lang_eid_to_lidx[lang] = {eid: li for li, eid in enumerate(lang_entity_ids[lang])}
    logger.info(f'Per-language candidate counts: { {l: len(v) for l, v in lang_entity_ids.items()} }')

    # Evaluate — both cross-lingual (all 56K) and within-language
    logger.info(f'Evaluating {len(test_examples)} test triples...')
    # Cross-lingual (all candidates)
    results_by_lang = defaultdict(lambda: {'mrr': [], 'h1': [], 'h3': [], 'h10': []})
    overall = {'mrr': [], 'h1': [], 'h3': [], 'h10': []}
    # Within-language (same-language candidates only — standard multilingual KGC protocol)
    wl_results_by_lang = defaultdict(lambda: {'mrr': [], 'h1': [], 'h3': [], 'h10': []})
    wl_overall = {'mrr': [], 'h1': [], 'h3': [], 'h10': []}
    rank_rows = [] if dump_ranks else None   # per-triple within-language RR for significance tests

    EVAL_BS = 512  # queries per batch

    model.eval()
    with torch.no_grad():
        for i in range(0, len(test_examples), EVAL_BS):
            batch = test_examples[i:i+EVAL_BS]

            # Encode query: head [SEP] relation (SimKGC-style — relation anchors the search)
            head_texts = []
            for ex in batch:
                h_text = entity_texts.get(ex['h'], f"entity_{ex['h']}")
                r_text = relation_names.get(str(ex['r']), f"relation {ex['r']}")
                head_texts.append(f"{h_text} [SEP] {r_text}")
            enc = tokenizer(head_texts, max_length=max_length, padding='max_length',
                            truncation=True, return_tensors='pt').to(device)
            q_embs = model.encode(enc['input_ids'], enc['attention_mask'])  # (B, D)

            # Score against ALL entities (cross-lingual eval)
            sim_all = torch.matmul(q_embs, all_embeddings.T)  # (B, N_all)

            for j, ex in enumerate(batch):
                h, r, t = ex['h'], ex['r'], ex['t']
                lang = ex.get('lang', 'en')

                if t not in eid_to_idx:
                    continue
                true_idx = eid_to_idx[t]
                filter_tails = [eid_to_idx[ft] for ft in filter_map.get((h, r), set())
                                if ft in eid_to_idx and ft != t]

                # ── Cross-lingual eval (all 56K candidates) ──
                metrics = compute_filtered_metrics(sim_all[j].cpu(), true_idx, filter_tails + [true_idx])
                for k in ['mrr', 'h1', 'h3', 'h10']:
                    overall[k].append(metrics[k])
                    results_by_lang[lang][k].append(metrics[k])

                # ── Within-language eval (same-language candidates only) ──
                if lang in lang_embeddings and t in lang_eid_to_lidx.get(lang, {}):
                    l_embs = lang_embeddings[lang]  # (N_lang, D)
                    sim_lang = torch.matmul(q_embs[j].unsqueeze(0), l_embs.T).squeeze(0)  # (N_lang,)
                    true_lidx = lang_eid_to_lidx[lang][t]
                    wl_filter = [lang_eid_to_lidx[lang][ft] for ft in filter_map.get((h, r), set())
                                 if ft in lang_eid_to_lidx.get(lang, {}) and ft != t]
                    wl_metrics = compute_filtered_metrics(sim_lang.cpu(), true_lidx, wl_filter + [true_lidx])
                    for k in ['mrr', 'h1', 'h3', 'h10']:
                        wl_overall[k].append(wl_metrics[k])
                        wl_results_by_lang[lang][k].append(wl_metrics[k])
                    if rank_rows is not None:
                        rank_rows.append({'h': h, 'r': r, 't': t, 'lang': lang,
                                          'rank': wl_metrics['rank'], 'rr': wl_metrics['mrr']})

            if (i // EVAL_BS + 1) % 5 == 0:
                n_done = min(i + EVAL_BS, len(test_examples))
                curr_mrr = sum(overall['mrr']) / len(overall['mrr'])
                logger.info(f'  Evaluated {n_done}/{len(test_examples)} | running MRR: {curr_mrr:.4f}')

    # Print results
    def fmt(d):
        n = len(d['mrr'])
        if n == 0:
            return '   N/A'
        return (f"MRR={sum(d['mrr'])/n*100:.2f}% "
                f"H@1={sum(d['h1'])/n*100:.2f}% "
                f"H@3={sum(d['h3'])/n*100:.2f}% "
                f"H@10={sum(d['h10'])/n*100:.2f}%  (n={n})")

    print('\n' + '='*70)
    print(f'CHECKPOINT: {ckpt_name}')
    print('='*70)
    print('\n[CROSS-LINGUAL EVAL] Rank against all 56K entities:')
    print(f'  OVERALL: {fmt(overall)}')
    if per_language:
        for lang in ['en', 'fr', 'es', 'ja', 'el']:
            print(f'  {lang.upper():3s}: {fmt(results_by_lang[lang])}')

    print('\n[WITHIN-LANGUAGE EVAL] Rank against same-language entities only (standard ML-KGC):')
    print(f'  OVERALL: {fmt(wl_overall)}')
    if per_language:
        for lang in ['en', 'fr', 'es', 'ja', 'el']:
            d = wl_results_by_lang[lang]
            n_cands = len(lang_entity_ids.get(lang, []))
            print(f'  {lang.upper():3s} ({n_cands:,} cands): {fmt(d)}')

    # Save results to JSON alongside checkpoint (or to a dedicated dir for zero-shot)
    if checkpoint_path is not None:
        results_path = os.path.join(os.path.dirname(checkpoint_path), 'eval_results.json')
    else:
        zs_dir = os.path.join(CHECKPOINT_DIR, 'zero_shot_bgem3')
        os.makedirs(zs_dir, exist_ok=True)
        results_path = os.path.join(zs_dir, 'eval_results.json')
    save_data = {
        'checkpoint': checkpoint_path,
        'cross_lingual': {
            'overall': {k: sum(v)/len(v)*100 if v else 0 for k, v in overall.items()},
            'per_language': {
                lang: {k: sum(v)/len(v)*100 if v else 0 for k, v in d.items()}
                for lang, d in results_by_lang.items()
            }
        },
        'within_language': {
            'overall': {k: sum(v)/len(v)*100 if v else 0 for k, v in wl_overall.items()},
            'per_language': {
                lang: {k: sum(v)/len(v)*100 if v else 0 for k, v in d.items()}
                for lang, d in wl_results_by_lang.items()
            }
        }
    }

    with open(results_path, 'w') as f:
        json.dump(save_data, f, indent=2)
    logger.info(f'Results saved to: {results_path}')

    if rank_rows is not None:
        with open(dump_ranks, 'w') as f:
            json.dump(rank_rows, f)
        logger.info(f'Per-triple within-language ranks ({len(rank_rows)}) dumped to: {dump_ranks}')

    return save_data


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint', default=None,
                   help='Path to best_model.pt checkpoint file')
    p.add_argument('--latest', action='store_true',
                   help='Auto-find the most recent best_model.pt')
    p.add_argument('--zero-shot', action='store_true',
                   help='Evaluate raw BGE-M3 without any fine-tuning (zero-shot baseline)')
    p.add_argument('--per-language', action='store_true', default=True,
                   help='Show per-language breakdown (default: True)')
    p.add_argument('--max-length', type=int, default=None,
                   help='Tokenization max_length. If not set, auto-read from checkpoint training args.')
    p.add_argument('--dump-ranks', default=None,
                   help='If set, write per-triple within-language ranks to this JSON path (for '
                        'paired bootstrap significance testing).')
    p.add_argument('--desc-path', default=None,
                   help='Override the entity descriptions file (for description ablations, '
                        'e.g. the no-LLM-backfill variant).')
    args = p.parse_args()
    if args.desc_path:
        DESC_PATH_OVERRIDE = args.desc_path

    if args.zero_shot:
        checkpoint = None
    elif args.latest or args.checkpoint is None:
        pattern = os.path.join(CHECKPOINT_DIR, '*', 'best_model.pt')
        candidates = glob.glob(pattern)
        if not candidates:
            print(f'No checkpoints found in {CHECKPOINT_DIR}')
            exit(1)
        checkpoint = max(candidates, key=os.path.getmtime)
        logger.info(f'Auto-selected latest checkpoint: {checkpoint}')
    else:
        checkpoint = args.checkpoint

    evaluate(checkpoint, per_language=args.per_language,
             max_length=args.max_length, zero_shot=args.zero_shot, dump_ranks=args.dump_ranks)

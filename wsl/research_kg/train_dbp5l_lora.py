"""
train_dbp5l_lora.py — BGE-M3 + LoRA Multilingual Inductive KGC Trainer
=======================================================================
LoRA replaces full fine-tuning — only trains ~4M params instead of 568M.

Memory breakdown with LoRA (rank=8):
  BGE-M3 frozen weights (bf16):    1.14 GB
  LoRA trainable params (~4M fp32): 0.016 GB  
  Adam state for LoRA only:         0.032 GB
  Activations (batch 128, seq 96):  ~2-3 GB
  Total:                           ~4-5 GB  ← fits easily in 16 GB

This enables batch 128+ and ~0.5-1.0 steps/s → 5 epochs in ~3-6 hours.

Usage:
    source ~/research_kg/RAA-KGC/SimKGC/venv/bin/activate

    # Row 1: BGE-M3 + LoRA baseline (InfoNCE)
    python3 train_dbp5l_lora.py

    # Row 3: + CRR loss
    python3 train_dbp5l_lora.py --use-crr 1

    # Row 5: + CRR + cross-lingual anchors
    python3 train_dbp5l_lora.py --use-crr 1 --n-anchors 3 --use-cross-lingual-anchors 1
"""

import os
import json
import math
import time
import random
import argparse
import logging
from datetime import datetime

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from torch.optim import AdamW

import run_manifest as rm  # P0.2 immutable run manifests

logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# RESEARCH_KG_ROOT lets a clean clone point at data elsewhere without editing source; default = old behavior.
_ROOT = os.environ.get('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
PROCESSED = os.path.join(_ROOT, 'DBP5L/processed')
CHECKPOINT_DIR = os.path.join(_ROOT, 'DBP5L/checkpoints')
CACHE_DIR = os.path.join(_ROOT, 'DBP5L/token_cache')


# ─── LoRA Layer (manual, no peft dependency) ─────────────────────────────────
class LoRALinear(nn.Module):
    """
    Wraps a frozen nn.Linear with a low-rank LoRA adapter.
    W_new = W_frozen + (B @ A) * scale
    Only A and B are trained: params = rank*(in+out) vs in*out for full fine-tuning.
    """
    def __init__(self, linear: nn.Linear, rank: int = 8, alpha: float = 16.0):
        super().__init__()
        self.linear = linear
        self.linear.weight.requires_grad_(False)
        if self.linear.bias is not None:
            self.linear.bias.requires_grad_(False)

        in_f, out_f = linear.in_features, linear.out_features
        # A: (rank, in_f), B: (out_f, rank) — both in float32 for stable training
        self.lora_A = nn.Parameter(torch.randn(rank, in_f) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(out_f, rank))
        self.scale = alpha / rank

    def forward(self, x):
        # Cast x to float32 for LoRA computation, then cast result back
        dtype = x.dtype
        x32 = x.float()
        base = self.linear(x)  # uses frozen bfloat16 weights
        lora = F.linear(F.linear(x32, self.lora_A), self.lora_B) * self.scale
        return base + lora.to(dtype)


def inject_lora(model, rank=8, alpha=16.0, target_modules=('query', 'value')):
    """Replace target linear layers with LoRA-wrapped versions."""
    replaced = 0
    for name, module in model.named_modules():
        for child_name, child in module.named_children():
            if isinstance(child, nn.Linear):
                if any(t in child_name for t in target_modules):
                    setattr(module, child_name, LoRALinear(child, rank=rank, alpha=alpha))
                    replaced += 1
    return replaced


# ─── CRR Loss ─────────────────────────────────────────────────────────────────
def crr_loss(pos_logits, all_logits, rho=0.1, tau=0.1):
    """CRR Loss (KGCRR AAAI 2025).
    Works with non-square all_logits (B, B+K) when hard negatives are appended.
    pos_logits: (B,)  — scores of true (q_i, t_i) pairs (diagonal of in-batch block)
    all_logits: (B, B+K)  — in-batch block (B,B) + hard-neg block (B,K)
    """
    diff = all_logits - pos_logits.unsqueeze(1)          # (B, B+K)
    B = pos_logits.size(0)
    # Mask ONLY the diagonal of the in-batch block (true positives)
    eye = torch.zeros(B, all_logits.size(1), dtype=torch.bool, device=all_logits.device)
    eye[:, :B] = torch.eye(B, dtype=torch.bool, device=all_logits.device)
    diff.masked_fill_(eye, -1e4)
    # Clamp exponent to prevent exp() overflow → NaN after many epochs
    exponent = ((rho - diff) / tau).clamp(-80.0, 80.0)
    H = 1.0 / (1.0 + torch.exp(exponent))
    return torch.log(1.0 + H.sum(dim=-1)).mean()


# ─── Hard Negative Mining ─────────────────────────────────────────────────────
@torch.no_grad()
def build_entity_cache(model, tokenizer, entity_texts, all_entity_ids,
                        max_length, device, batch_size=512):
    """Encode all entities; return (N,D) CPU float32 tensor + eid→idx map."""
    logger.info(f'  [HN] Building entity cache for {len(all_entity_ids)} entities...')
    t0 = time.time()
    model.eval()
    texts = [entity_texts.get(eid, f'entity_{eid}') for eid in all_entity_ids]
    embeddings = []
    for i in range(0, len(texts), batch_size):
        enc = tokenizer(texts[i:i+batch_size], max_length=max_length,
                        padding='max_length', truncation=True, return_tensors='pt')
        ids  = enc['input_ids'].to(device)
        mask = enc['attention_mask'].to(device)
        emb  = model.encode(ids, mask)     # (b, D) float32 normalised
        embeddings.append(emb.cpu())
    entity_cache = torch.cat(embeddings, dim=0)  # (N, D)
    eid_to_idx   = {eid: i for i, eid in enumerate(all_entity_ids)}
    model.train()
    logger.info(f'  [HN] Cache built in {(time.time()-t0)/60:.1f} min | shape {entity_cache.shape}')
    return entity_cache, eid_to_idx


def get_hard_negatives(q_embs_detached, t_eids, entity_cache_gpu,
                        eid_to_idx, k=7):
    """Return (B, k, D) hard-negative embeddings from the entity cache."""
    sims = torch.matmul(q_embs_detached, entity_cache_gpu.T)  # (B, N)
    # Mask true targets so they can’t be chosen as hard negatives
    for i, eid in enumerate(t_eids):
        idx = eid_to_idx.get(int(eid), None)
        if idx is not None:
            sims[i, idx] = -1e9
    _, top_idx = sims.topk(k, dim=1)          # (B, k)
    return entity_cache_gpu[top_idx]           # (B, k, D)


# ─── Pre-tokenized Dataset ────────────────────────────────────────────────────
class PreTokenizedDataset(Dataset):
    def __init__(self, examples, entity_texts, anchors_by_rel, relation_names,
                 tokenizer, max_length, n_anchors=0,
                 use_cross_lingual_anchors=False, cache_path=None):

        self.n_anchors = n_anchors
        self.anchors_by_rel = anchors_by_rel
        self.use_xl = use_cross_lingual_anchors

        logger.info(f'  Building {len(examples)} example texts...')
        q_texts, t_texts, a_texts = [], [], []
        self.has_anchor = []
        self.t_eids = []   # tail entity IDs for hard-negative exclusion

        for ex in examples:
            h, r, t = ex['h'], ex['r'], ex['t']
            lang = ex.get('lang', 'en')
            rel_name = relation_names.get(str(r), relation_names.get(r, f'relation {r}'))
            head_text = entity_texts.get(h, f'entity_{h}')
            q_texts.append(f'{head_text} [SEP] {rel_name}')
            t_texts.append(entity_texts.get(t, f'entity_{t}'))
            self.t_eids.append(t)   # store tail entity ID for hard-neg lookup
            anch = self._pick_anchor(h, r, lang, entity_texts) if n_anchors > 0 else None
            if anch:
                a_texts.append(anch)
                self.has_anchor.append(True)
            else:
                a_texts.append(q_texts[-1])
                self.has_anchor.append(False)

        self.q_ids, self.q_mask = self._tok(tokenizer, q_texts, max_length, cache_path, 'q')
        self.t_ids, self.t_mask = self._tok(tokenizer, t_texts, max_length, cache_path, 't')
        if n_anchors > 0:
            self.a_ids, self.a_mask = self._tok(tokenizer, a_texts, max_length, cache_path, 'a')
        else:
            self.a_ids = self.a_mask = None
        self.has_anchor_t = torch.tensor(self.has_anchor)

    def _pick_anchor(self, head_id, rel, lang, entity_texts):
        cands = self.anchors_by_rel.get(str(rel), [])
        if self.use_xl and lang != 'en':
            cands = [c for c in cands if c.get('lang') == 'en'] + \
                    [c for c in cands if c.get('lang') == lang]
        cands = [c for c in cands if c.get('h') != head_id]
        if not cands:
            return None
        return entity_texts.get(random.choice(cands)['t'])

    def _tok(self, tokenizer, texts, max_length, cache_path, suffix):
        if cache_path:
            fi, fm = f'{cache_path}_{suffix}_ids.pt', f'{cache_path}_{suffix}_mask.pt'
            if os.path.exists(fi):
                logger.info(f'    Cache hit: {os.path.basename(fi)}')
                return torch.load(fi), torch.load(fm)
        all_ids, all_masks = [], []
        for i in range(0, len(texts), 512):
            enc = tokenizer(texts[i:i+512], max_length=max_length, padding='max_length',
                            truncation=True, return_tensors='pt')
            all_ids.append(enc['input_ids'])
            all_masks.append(enc['attention_mask'])
            if (i // 512) % 20 == 0:
                logger.info(f'    Tokenized {min(i+512, len(texts))}/{len(texts)}')
        ids, mask = torch.cat(all_ids), torch.cat(all_masks)
        if cache_path:
            torch.save(ids, f'{cache_path}_{suffix}_ids.pt')
            torch.save(mask, f'{cache_path}_{suffix}_mask.pt')
        return ids, mask

    def __len__(self): return self.q_ids.size(0)

    def __getitem__(self, idx):
        item = {'q_ids': self.q_ids[idx], 'q_mask': self.q_mask[idx],
                't_ids': self.t_ids[idx], 't_mask': self.t_mask[idx],
                't_eid': self.t_eids[idx]}   # needed for hard-negative exclusion
        if self.a_ids is not None:
            item['a_ids'] = self.a_ids[idx]
            item['a_mask'] = self.a_mask[idx]
        return item


# ─── Model ────────────────────────────────────────────────────────────────────
class BGE_M3_LoRA_KGC(nn.Module):
    def __init__(self, model_name, lora_rank=8, lora_alpha=16.0,
                 lora_targets=('query', 'value'), temperature=0.05):
        super().__init__()
        # Load frozen in bfloat16 — weights stay frozen, only LoRA adapters train
        logger.info(f'Loading {model_name} in bfloat16 (frozen)...')
        self.encoder = AutoModel.from_pretrained(model_name, torch_dtype=torch.bfloat16)

        # Freeze ALL parameters first
        for p in self.encoder.parameters():
            p.requires_grad_(False)

        # Inject LoRA into attention query + value projections
        n = inject_lora(self.encoder, rank=lora_rank, alpha=lora_alpha,
                        target_modules=lora_targets)
        logger.info(f'Injected LoRA into {n} linear layers (rank={lora_rank}, alpha={lora_alpha})')

        # Temperature is trainable in float32
        self.temperature = nn.Parameter(torch.tensor(temperature))

        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        logger.info(f'Total params: {total/1e6:.1f}M | Trainable (LoRA): {trainable/1e6:.2f}M ({trainable/total*100:.1f}%)')

    def encode(self, input_ids, attention_mask):
        # Run frozen backbone without storing activations (saves ~10 GB at batch 128)
        # LoRA adapters compute their own residual inside LoRALinear.forward()
        # and ARE differentiable because they're called inside the encoder's forward pass.
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)
        h = out.last_hidden_state.float()  # bfloat16 → float32 for stable pooling
        mask = attention_mask.unsqueeze(-1).float()
        pooled = (h * mask).sum(1) / mask.sum(1).clamp(min=1e-6)
        return F.normalize(pooled, dim=-1)

    def forward(self, q_ids, q_mask, t_ids, t_mask, a_ids=None, a_mask=None):
        q = self.encode(q_ids, q_mask)
        t = self.encode(t_ids, t_mask)
        if a_ids is not None:
            a = self.encode(a_ids, a_mask)
            q = F.normalize((q + a) / 2.0, dim=-1)
        return torch.matmul(q, t.T) / self.temperature.exp()


# ─── Training ─────────────────────────────────────────────────────────────────
def train(args):
    # Reproducibility
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    if args.resume:
        # Resume in-place: reuse the checkpoint's own run directory so all artifacts stay together
        run_dir = os.path.dirname(os.path.abspath(args.resume))
        run_name = os.path.basename(run_dir)
        logger.info(f'RESUMING from {args.resume} (run dir {run_dir})')
    else:
        run_name = f"bgem3_lora_dbp5l_{datetime.now().strftime('%Y%m%d_%H%M')}"
        if args.use_crr:                    run_name += '_crr'
        if args.use_cross_lingual_anchors:  run_name += '_xl'
        if args.global_neg:                 run_name += '_globalneg'
        elif args.hard_neg_k > 0:           run_name += f'_hn{args.hard_neg_k}'
        if args.curriculum:                 run_name += '_curr'
        if args.lora_rank != 8:             run_name += f'_r{args.lora_rank}'
        if args.seed != 42:                 run_name += f'_s{args.seed}'
        run_dir = os.path.join(CHECKPOINT_DIR, run_name)
    os.makedirs(run_dir, exist_ok=True)

    logger.info(f'Run: {run_name} | Seed: {args.seed}')
    logger.info(f'LoRA rank={args.lora_rank} | CRR={args.use_crr} | XL={args.use_cross_lingual_anchors} | HardNeg K={args.hard_neg_k}')

    # Load support data
    # Load rich entity descriptions (KG neighbor-based, built by build_entity_descriptions.py).
    # --desc-path overrides for ablations (e.g. the clean no-back-fill variant).
    desc_path = args.desc_path or f'{PROCESSED}/entity_descriptions.json'
    logger.info(f'Entity descriptions: {desc_path}')
    if os.path.exists(desc_path):
        logger.info('Loading KG neighbor-based entity descriptions...')
        with open(desc_path, encoding='utf-8') as f:
            desc_data = json.load(f)
        entity_texts = {int(k): v for k, v in desc_data.items()}
        logger.info(f'  Loaded {len(entity_texts)} entity descriptions')
    else:
        logger.info('entity_descriptions.json not found — falling back to entities.json name field')
        logger.info('Run build_entity_descriptions.py first for best results!')
        with open(f'{PROCESSED}/entities.json') as f:
            raw_ents = json.load(f)
        entity_texts = {
            int(k): (f"{v['name']}: {v['description']}"
                     if v.get('description') and v['description'] != v['name']
                     else v.get('name', ''))
            for k, v in raw_ents.items()
        }
    # Load relation names for query construction (SimKGC-style: head [SEP] relation)
    rel_names_path = f'{PROCESSED}/relation_names.json'
    if os.path.exists(rel_names_path):
        with open(rel_names_path) as f:
            relation_names = json.load(f)
        logger.info(f'Loaded {len(relation_names)} relation names')
    else:
        logger.info('WARNING: relation_names.json not found — run build_relation_names.py!')
        relation_names = {}

    with open(f'{PROCESSED}/anchors_by_rel.json') as f:
        anchors_by_rel = json.load(f)
    logger.info(f'Loaded {len(entity_texts)} entities, {len(anchors_by_rel)} relation anchor groups')

    # ── P0.2: pin this run to immutable code/data/env state ───────────────────
    # Resume reuses an existing run dir (and its manifest); only fresh runs create one.
    if not args.resume:
        rm.start_run(
            run_dir, kind='train',
            inputs={
                'train_split': f'{PROCESSED}/train.json',
                'valid_split': f'{PROCESSED}/valid.json',
                'descriptions': desc_path,
                'relation_names': rel_names_path,
                'anchors_by_rel': f'{PROCESSED}/anchors_by_rel.json',
            },
            seed=args.seed, model_name=args.model_name,
            extra={'args': vars(args), 'run_name': run_name, 'max_length': args.max_length},
        )
        logger.info(f'  Wrote run manifest: {run_dir}/manifest.json')

    # Model
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = BGE_M3_LoRA_KGC(
        args.model_name, lora_rank=args.lora_rank, lora_alpha=args.lora_rank * 2,
        temperature=args.temperature
    )
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    if device.type == 'cuda':
        used = torch.cuda.memory_allocated() / 1e9
        free = torch.cuda.mem_get_info()[0] / 1e9
        logger.info(f'GPU: {torch.cuda.get_device_name(0)} | VRAM used after model load: {used:.2f} GB | free: {free:.1f} GB')

    # Datasets
    def load_exs(path):
        return [json.loads(l) for l in open(path)]

    # Token cache MUST be keyed by encoder AND by the descriptions file: different tokenizers
    # (BGE-M3 SentencePiece vs mBERT/XLM-R WordPiece) produce incompatible ids, and different
    # description sources produce different text. Without these tags a run would silently reuse a
    # stale cache (mBERT would index out of its vocab; a no-back-fill run would load the old
    # back-filled text).
    model_tag = args.model_name.replace('/', '_')
    desc_tag = os.path.splitext(os.path.basename(desc_path))[0]
    cache_tag = f'{model_tag}_{desc_tag}'

    logger.info('Pre-tokenizing training set...')
    train_ds = PreTokenizedDataset(
        load_exs(f'{PROCESSED}/train.json'), entity_texts, anchors_by_rel, relation_names,
        tokenizer, args.max_length, n_anchors=args.n_anchors,
        use_cross_lingual_anchors=bool(args.use_cross_lingual_anchors),
        cache_path=os.path.join(CACHE_DIR, f'train_{cache_tag}_ml{args.max_length}_na{args.n_anchors}_xl{args.use_cross_lingual_anchors}_v2')
    )
    logger.info('Pre-tokenizing validation set...')
    valid_ds = PreTokenizedDataset(
        load_exs(f'{PROCESSED}/valid.json'), entity_texts, anchors_by_rel, relation_names,
        tokenizer, args.max_length, n_anchors=0,
        cache_path=os.path.join(CACHE_DIR, f'valid_{cache_tag}_ml{args.max_length}_v2')
    )

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=0, pin_memory=True)
    valid_loader = DataLoader(valid_ds, batch_size=args.batch_size * 2,
                              shuffle=False, num_workers=0, pin_memory=True)

    # Only optimize LoRA parameters + temperature
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = AdamW(trainable_params, lr=args.lr, weight_decay=0.01)
    total_steps = (len(train_loader) * args.epochs) // args.grad_accum
    scheduler = get_linear_schedule_with_warmup(
        optimizer, max(1, int(0.06 * total_steps)), total_steps)
    ce_loss = nn.CrossEntropyLoss()

    logger.info(f'Training: {len(train_ds)} examples | {total_steps} opt steps | {args.epochs} epochs')
    logger.info(f'Batch={args.batch_size} | GradAccum={args.grad_accum} | Effective batch={args.batch_size*args.grad_accum}')

    best_acc1 = 0.0
    results = []
    entity_cache     = None   # (N, D) CPU tensor — populated after ep hard_neg_start_epoch
    entity_cache_gpu = None   # same but on GPU for fast matmul
    eid_to_idx       = None
    # Sorted entity IDs needed for cache building
    all_entity_ids = sorted(entity_texts.keys())

    # ── Resume: restore model / optimizer / scheduler / RNG / progress ───────────
    start_epoch = 0
    if args.resume:
        ck = torch.load(args.resume, map_location=device)
        model.load_state_dict(ck['model_state_dict'])
        if 'optimizer_state_dict' in ck:
            optimizer.load_state_dict(ck['optimizer_state_dict'])
            scheduler.load_state_dict(ck['scheduler_state_dict'])
            best_acc1 = ck.get('best_acc1', 0.0)
            results = ck.get('results', [])
            if ck.get('rng_python') is not None: random.setstate(ck['rng_python'])
            if ck.get('rng_torch') is not None:  torch.set_rng_state(ck['rng_torch'].cpu())
            if ck.get('rng_cuda') is not None and torch.cuda.is_available():
                torch.cuda.set_rng_state_all([s.cpu() for s in ck['rng_cuda']])
            start_epoch = ck.get('epoch', 0)   # number of completed epochs
            logger.info(f'Resumed at epoch {start_epoch}/{args.epochs} | best acc@1 so far {best_acc1:.2f}%')
            # Rebuild the hard-negative entity cache if the next epoch needs it
            if args.hard_neg_k > 0 and start_epoch >= args.hard_neg_start_epoch:
                entity_cache, eid_to_idx = build_entity_cache(
                    model, tokenizer, entity_texts, all_entity_ids, args.max_length, device, batch_size=512)
                entity_cache_gpu = entity_cache.to(device)
        else:
            logger.warning('Resume checkpoint has no optimizer state (old best_model.pt format); '
                           'loaded weights only, restarting epoch count at 0.')

    for epoch in range(start_epoch, args.epochs):
        model.train()
        ep_loss, c1, c3, n = 0.0, 0, 0, 0
        t0 = time.time()
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader):
            q_ids  = batch['q_ids'].to(device, non_blocking=True)
            q_mask = batch['q_mask'].to(device, non_blocking=True)
            t_ids  = batch['t_ids'].to(device, non_blocking=True)
            t_mask = batch['t_mask'].to(device, non_blocking=True)
            t_eids = batch['t_eid'].tolist()   # list of int entity IDs
            a_ids  = batch.get('a_ids', None)
            a_mask = batch.get('a_mask', None)
            if a_ids is not None and args.n_anchors > 0:
                a_ids  = a_ids.to(device, non_blocking=True)
                a_mask = a_mask.to(device, non_blocking=True)
            else:
                a_ids = a_mask = None

            # ── Hard Negative / Global Negative Augmentation ───────────────
            if entity_cache_gpu is not None and args.global_neg:
                # ---- Option 1: Full Global Negative Loss ----
                # Score each query against ALL 56K entity embeddings (SimKGC-style)
                q_embs = model.encode(q_ids, q_mask)  # (B, D)
                if a_ids is not None:
                    a_embs = model.encode(a_ids, a_mask)
                    q_embs = F.normalize((q_embs + a_embs) / 2.0, dim=-1)
                temp = model.temperature.exp()
                logits = torch.matmul(q_embs, entity_cache_gpu.T) / temp  # (B, N)
                # True target global indices
                labels = torch.tensor(
                    [eid_to_idx.get(int(eid), 0) for eid in t_eids],
                    device=device, dtype=torch.long
                )
                if args.use_crr:
                    pos_logits = logits[torch.arange(logits.size(0), device=device), labels]
                    loss = crr_loss(pos_logits, logits, args.crr_rho, args.crr_tau)
                else:
                    loss = ce_loss(logits, labels)

            elif entity_cache_gpu is not None and args.hard_neg_k > 0:
                # ---- Original: In-batch + K hard negatives ----
                # Curriculum: ramp hard_neg_k from 1 → target over curriculum_step epochs
                if args.curriculum and entity_cache_gpu is not None:
                    epochs_with_hn = (epoch + 1) - args.hard_neg_start_epoch
                    current_k = min(args.hard_neg_k,
                                    max(1, epochs_with_hn // max(1, args.curriculum_step)))
                else:
                    current_k = args.hard_neg_k

                q_embs = model.encode(q_ids, q_mask)
                t_embs = model.encode(t_ids, t_mask)
                if a_ids is not None:
                    a_embs = model.encode(a_ids, a_mask)
                    q_embs = F.normalize((q_embs + a_embs) / 2.0, dim=-1)

                with torch.no_grad():
                    hn_embs = get_hard_negatives(
                        q_embs.detach(), t_eids,
                        entity_cache_gpu, eid_to_idx, k=current_k
                    )  # (B, K, D)

                temp = model.temperature.exp()
                logits_ib = torch.matmul(q_embs, t_embs.T) / temp  # (B, B)
                logits_hn = torch.einsum('bd,bkd->bk', q_embs, hn_embs) / temp
                logits = torch.cat([logits_ib, logits_hn], dim=1)   # (B, B+K)
                labels = torch.arange(logits.size(0), device=device)

                if args.use_crr:
                    pos_logits = logits[:, :logits.size(0)].diagonal()
                    loss = crr_loss(pos_logits, logits, args.crr_rho, args.crr_tau)
                else:
                    loss = ce_loss(logits, labels)

            else:
                # ---- Fallback: standard in-batch negatives ----
                logits = model(q_ids, q_mask, t_ids, t_mask, a_ids, a_mask)  # (B, B)
                labels = torch.arange(logits.size(0), device=device)
                if args.use_crr:
                    pos_logits = logits[:, :logits.size(0)].diagonal()
                    loss = crr_loss(pos_logits, logits, args.crr_rho, args.crr_tau)
                else:
                    loss = ce_loss(logits, labels)

            (loss / args.grad_accum).backward()

            # NaN guard — skip optimizer step if loss exploded
            if torch.isnan(loss):
                logger.warning(f'  NaN loss at step {step+1} — skipping grad step')
                optimizer.zero_grad()
                continue

            if (step + 1) % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            ep_loss += loss.item()
            p1 = logits.argmax(dim=1)
            p3 = logits.topk(min(3, logits.size(1)), dim=1).indices
            c1 += (p1 == labels).sum().item()
            c3 += sum(labels[i].item() in p3[i] for i in range(len(labels)))
            n  += labels.size(0)

            if (step + 1) % 50 == 0:
                elapsed = time.time() - t0
                rate = (step + 1) / elapsed
                steps_left = (len(train_loader) - step - 1) + len(train_loader) * (args.epochs - epoch - 1)
                eta_h = steps_left / rate / 3600
                vram_used = torch.cuda.memory_allocated() / 1e9 if device.type == 'cuda' else 0
                logger.info(
                    f'Ep {epoch+1}/{args.epochs} step {step+1}/{len(train_loader)} | '
                    f'loss {ep_loss/(step+1):.4f} | acc@1 {c1/n*100:.1f}% acc@3 {c3/n*100:.1f}% | '
                    f'{rate:.2f} steps/s | ETA {eta_h:.1f}h | VRAM {vram_used:.1f}GB'
                )

        # Validation
        model.eval()
        vl, vc1, vc3, vn = 0.0, 0, 0, 0
        with torch.no_grad():
            for batch in valid_loader:
                q_ids  = batch['q_ids'].to(device, non_blocking=True)
                q_mask = batch['q_mask'].to(device, non_blocking=True)
                t_ids  = batch['t_ids'].to(device, non_blocking=True)
                t_mask = batch['t_mask'].to(device, non_blocking=True)
                logits = model(q_ids, q_mask, t_ids, t_mask)
                labels = torch.arange(logits.size(0), device=device)
                vl += ce_loss(logits, labels).item()
                p1 = logits.argmax(1)
                p3 = logits.topk(min(3, logits.size(1)), 1).indices
                vc1 += (p1 == labels).sum().item()
                vc3 += sum(labels[i].item() in p3[i] for i in range(len(labels)))
                vn  += labels.size(0)

        va1 = vc1 / max(vn, 1) * 100
        va3 = vc3 / max(vn, 1) * 100
        ep_min = (time.time() - t0) / 60
        logger.info(
            f'=== Ep {epoch+1}/{args.epochs} | valid acc@1 {va1:.2f}% acc@3 {va3:.2f}% | '
            f'loss {vl/len(valid_loader):.4f} | time {ep_min:.1f}min ==='
        )

        results.append({'epoch': epoch+1, 'valid_acc1': va1, 'valid_acc3': va3})
        with open(f'{run_dir}/results.json', 'w') as f:
            json.dump(results, f, indent=2)

        if va1 > best_acc1:
            best_acc1 = va1
            torch.save({'epoch': epoch+1, 'model_state_dict': model.state_dict(),
                        'valid_acc1': va1, 'args': vars(args)},
                       f'{run_dir}/best_model.pt')
            logger.info(f'  ✓ New best acc@1={va1:.2f}% — saved')

        # ── Full-state resume checkpoint (rolling, overwritten each epoch) ────────
        # Lets a killed run resume from the last completed epoch instead of epoch 0.
        torch.save({
            'epoch': epoch + 1,                       # number of completed epochs
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'best_acc1': best_acc1,
            'results': results,
            'args': vars(args),
            'rng_python': random.getstate(),
            'rng_torch': torch.get_rng_state(),
            'rng_cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        }, f'{run_dir}/last_checkpoint.pt')

        # ── Build / refresh entity cache for next epoch’s hard negatives ──────
        if args.hard_neg_k > 0 and (epoch + 1) >= args.hard_neg_start_epoch:
            entity_cache, eid_to_idx = build_entity_cache(
                model, tokenizer, entity_texts, all_entity_ids,
                args.max_length, device, batch_size=512)
            entity_cache_gpu = entity_cache.to(device)
            logger.info(f'  [HN] Cache on GPU ({entity_cache_gpu.element_size()*entity_cache_gpu.nelement()/1e6:.0f} MB)')

    logger.info(f'Done. Best valid acc@1: {best_acc1:.2f}%  Checkpoints: {run_dir}')

    # ── P0.2: finalize manifest (status=complete) with headline metric + ckpt hash ──
    if rm.load_manifest(run_dir) is not None:
        rm.finish_run(run_dir, status='complete',
                      metrics={'best_valid_acc1': best_acc1, 'epochs_run': len(results)},
                      checkpoint_path=f'{run_dir}/best_model.pt')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model-name', default='BAAI/bge-m3')
    p.add_argument('--desc-path', default=None,
                   help='Override entity descriptions file (e.g. the clean no-back-fill variant). '
                        'The token cache is keyed by this file, so different descriptions do not collide.')
    p.add_argument('--resume', default=None,
                   help='Path to a last_checkpoint.pt to resume from (restores model, optimizer, '
                        'scheduler, RNG, epoch). Resumes in the checkpoint\'s own run directory. '
                        'Pass the SAME training flags as the original run.')
    p.add_argument('--epochs', type=int, default=10)
    p.add_argument('--batch-size', type=int, default=32,
                   help='32 keeps activations ~2.5GB; use grad-accum for effective large batch')
    p.add_argument('--grad-accum', type=int, default=8,
                   help='Effective batch = batch_size * grad_accum. Default: 32*8=256')
    p.add_argument('--lr', type=float, default=5e-4,
                   help='LoRA uses higher LR than full fine-tuning (1e-3 to 5e-4 typical)')
    p.add_argument('--max-length', type=int, default=96)
    p.add_argument('--lora-rank', type=int, default=8,
                   help='LoRA rank. 8=~4M params (fast), 16=~8M (better quality)')
    p.add_argument('--temperature', type=float, default=0.05)
    p.add_argument('--n-anchors', type=int, default=0)
    p.add_argument('--use-crr', type=int, default=0)
    p.add_argument('--crr-rho', type=float, default=0.1)
    p.add_argument('--crr-tau', type=float, default=0.1)
    p.add_argument('--use-cross-lingual-anchors', type=int, default=0)
    # Hard negative mining
    p.add_argument('--hard-neg-k', type=int, default=0,
                   help='Number of hard negatives per sample. 0=disabled, 7=recommended')
    p.add_argument('--hard-neg-start-epoch', type=int, default=5,
                   help='Start building entity cache (and using hard negatives) from this epoch. '
                        'Early epochs train on random negatives to warm up the encoder first.')
    # Global negative loss (Option 1)
    p.add_argument('--global-neg', action='store_true',
                   help='Score each query against ALL 56K entities (SimKGC-style). '
                        'Requires --hard-neg-start-epoch to build cache first. '
                        'Overrides --hard-neg-k when cache is available.')
    # Curriculum learning (Option 4)
    p.add_argument('--curriculum', action='store_true',
                   help='Ramp hard_neg_k from 1 to target over curriculum_step epochs.')
    p.add_argument('--curriculum-step', type=int, default=3,
                   help='Increase hard_neg_k by 1 every N epochs during curriculum phase.')
    p.add_argument('--seed', type=int, default=42,
                   help='Random seed for reproducibility. Use different seeds for multi-seed runs.')
    args = p.parse_args()
    train(args)

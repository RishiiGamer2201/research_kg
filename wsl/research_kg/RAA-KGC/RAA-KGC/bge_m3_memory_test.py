"""
BGE-M3 Memory & Feasibility Test for RTX 5070 Ti 16 GB
=======================================================
Run from inside the SimKGC venv:

    cd ~/research_kg/RAA-KGC/RAA-KGC
    source ~/research_kg/RAA-KGC/SimKGC/venv/bin/activate
    pip install sentence-transformers          # one-time
    python bge_m3_memory_test.py

What this script checks:
  1. BGE-M3 loads in bf16 on GPU (shared tower, 1 copy only)
  2. Achievable batch size before OOM (bi-encoder pass = query + candidate)
  3. Memory headroom after forward pass (needed for CRR loss + gradient accum)
  4. Speed estimate (samples / second)
  5. Whether gradient checkpointing is needed
"""

import torch
import gc
import time

# ── helpers ──────────────────────────────────────────────────────────────────

def free_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def gpu_mem_used_gb():
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.memory_allocated() / 1e9

def gpu_mem_reserved_gb():
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.memory_reserved() / 1e9

# ── Step 0: basic GPU check ───────────────────────────────────────────────────

print("=" * 60)
print("STEP 0 — GPU check")
print("=" * 60)

if not torch.cuda.is_available():
    print("  CUDA not available — CPU-only run (useful for import test only)")
    DEVICE = "cpu"
    DTYPE  = torch.float32
else:
    DEVICE = "cuda:0"
    props  = torch.cuda.get_device_properties(0)
    total_gb = props.total_memory / 1e9
    print(f"  GPU : {props.name}")
    print(f"  VRAM: {total_gb:.1f} GB")
    # bf16 supported on Ampere (sm_80+) and Blackwell (sm_90, sm_120)
    DTYPE = torch.bfloat16 if props.major >= 8 else torch.float16
    print(f"  dtype: {DTYPE} (bf16 on Ampere/Blackwell, else fp16)")

print()

# ── Step 1: load BGE-M3 (dense-only, shared tower) ───────────────────────────

print("=" * 60)
print("STEP 1 — Load BGE-M3 (this downloads ~2 GB first time)")
print("=" * 60)

try:
    from transformers import AutoTokenizer, AutoModel
    MODEL_NAME = "BAAI/bge-m3"

    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model     = AutoModel.from_pretrained(MODEL_NAME, torch_dtype=DTYPE)
    model     = model.to(DEVICE)
    model.eval()
    t1 = time.time()

    param_m = sum(p.numel() for p in model.parameters()) / 1e6
    mem_after_load = gpu_mem_used_gb()
    print(f"  Loaded in {t1-t0:.1f}s")
    print(f"  Parameters : {param_m:.0f} M")
    print(f"  GPU memory after load: {mem_after_load:.2f} GB")
    print()

except Exception as e:
    print(f"  FAILED to load model: {e}")
    raise

# ── Step 2: batch size sweep ─────────────────────────────────────────────────
# In the bi-encoder we do TWO forward passes per step:
#   g(query) and g(candidate).  Both use the same (shared) encoder.
# We simulate this by encoding [batch_size queries] then [batch_size candidates].

print("=" * 60)
print("STEP 2 — Batch size sweep (query + candidate forward pass, no grads)")
print("=" * 60)

# Fake but realistic text lengths
QUERY_TEXT     = "Paris [SEP] capital of [SEP] This is a description of Paris, the capital city of France."
CANDIDATE_TEXT = "France [SEP] France is a country in Western Europe, known for its culture and history."

def encode_batch(texts, batch_size, with_grad=False):
    """One forward pass over a list of texts."""
    enc = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )
    enc = {k: v.to(DEVICE) for k, v in enc.items()}
    ctx = torch.enable_grad() if with_grad else torch.no_grad()
    with ctx:
        out = model(**enc)
    # mean pool
    emb = out.last_hidden_state[:, 0]   # CLS token (BGE-M3 convention)
    return emb

max_ok_bs = 0
print(f"  {'Batch':>8}  {'Query(GB)':>10}  {'+ Cand(GB)':>11}  {'Status':>8}")
print(f"  {'-'*8}  {'-'*10}  {'-'*11}  {'-'*8}")

for bs in [8, 16, 32, 64, 128, 256]:
    free_memory()
    queries    = [QUERY_TEXT]     * bs
    candidates = [CANDIDATE_TEXT] * bs
    try:
        q_emb  = encode_batch(queries, bs)
        mem_q  = gpu_mem_used_gb()
        c_emb  = encode_batch(candidates, bs)
        mem_qc = gpu_mem_used_gb()
        # cosine sim (like bi-encoder scoring)
        scores = torch.nn.functional.cosine_similarity(q_emb, c_emb, dim=-1)
        print(f"  {bs:>8}  {mem_q:>10.2f}  {mem_qc:>11.2f}  {'   OK':>8}")
        max_ok_bs = bs
    except torch.cuda.OutOfMemoryError:
        print(f"  {bs:>8}  {'OOM':>10}  {'OOM':>11}  {'  OOM':>8}")
        break
    except Exception as ex:
        print(f"  {bs:>8}  {'ERR':>10}  {'ERR':>11}  {str(ex)[:8]:>8}")
        break

print(f"\n  Largest clean batch (no grad): {max_ok_bs}")
print()

# ── Step 3: with gradient (training mode) ────────────────────────────────────

print("=" * 60)
print("STEP 3 — Training mode sweep (with_grad=True, no grad-checkpoint)")
print("=" * 60)

model.train()
max_ok_train_bs = 0

print(f"  {'Batch':>8}  {'Fwd+Bwd(GB)':>12}  {'Status':>8}")
print(f"  {'-'*8}  {'-'*12}  {'-'*8}")

for bs in [8, 16, 32, 64]:
    free_memory()
    queries    = [QUERY_TEXT]     * bs
    candidates = [CANDIDATE_TEXT] * bs
    try:
        q_emb = encode_batch(queries,    bs, with_grad=True)
        c_emb = encode_batch(candidates, bs, with_grad=True)
        # fake CRR-style loss
        scores  = torch.nn.functional.cosine_similarity(q_emb, c_emb, dim=-1)
        loss    = -scores.mean()            # stand-in for CRR
        loss.backward()
        mem_bwd = gpu_mem_used_gb()
        print(f"  {bs:>8}  {mem_bwd:>12.2f}  {'   OK':>8}")
        max_ok_train_bs = bs
        # zero grads
        model.zero_grad()
    except torch.cuda.OutOfMemoryError:
        print(f"  {bs:>8}  {'OOM':>12}  {'  OOM':>8}")
        break
    except Exception as ex:
        print(f"  {bs:>8}  {'ERR':>12}  {str(ex)[:8]:>8}")
        break

print(f"\n  Largest clean training batch (no grad-ckpt): {max_ok_train_bs}")
print()

# ── Step 4: gradient checkpointing ───────────────────────────────────────────

print("=" * 60)
print("STEP 4 — Gradient checkpointing (recompute activations to save VRAM)")
print("=" * 60)

# Enable gradient checkpointing on the encoder
try:
    model.encoder.gradient_checkpointing_enable()
    gc_enabled = True
    print("  gradient_checkpointing_enable() -> OK")
except AttributeError:
    # Fallback for models that expose it at the top level
    try:
        model.gradient_checkpointing_enable()
        gc_enabled = True
        print("  model.gradient_checkpointing_enable() -> OK")
    except Exception:
        gc_enabled = False
        print("  gradient checkpointing not available on this model variant")

max_ok_gc_bs = 0

if gc_enabled:
    print(f"\n  {'Batch':>8}  {'Fwd+Bwd(GB)':>12}  {'Status':>8}")
    print(f"  {'-'*8}  {'-'*12}  {'-'*8}")

    for bs in [8, 16, 32, 64, 128]:
        free_memory()
        queries    = [QUERY_TEXT]     * bs
        candidates = [CANDIDATE_TEXT] * bs
        try:
            q_emb = encode_batch(queries,    bs, with_grad=True)
            c_emb = encode_batch(candidates, bs, with_grad=True)
            scores = torch.nn.functional.cosine_similarity(q_emb, c_emb, dim=-1)
            loss   = -scores.mean()
            loss.backward()
            mem_gc = gpu_mem_used_gb()
            print(f"  {bs:>8}  {mem_gc:>12.2f}  {'   OK':>8}")
            max_ok_gc_bs = bs
            model.zero_grad()
        except torch.cuda.OutOfMemoryError:
            print(f"  {bs:>8}  {'OOM':>12}  {'  OOM':>8}")
            break
        except Exception as ex:
            print(f"  {bs:>8}  {'ERR':>12}  {str(ex)[:8]:>8}")
            break

    print(f"\n  Largest clean training batch (WITH grad-ckpt): {max_ok_gc_bs}")
print()

# ── Step 5: speed estimate ────────────────────────────────────────────────────

print("=" * 60)
print("STEP 5 — Speed estimate (inference, max clean batch)")
print("=" * 60)

model.eval()
bs_speed = max(max_ok_bs, 8)
texts    = [QUERY_TEXT] * bs_speed

# warm-up
_ = encode_batch(texts, bs_speed)
if DEVICE != "cpu":
    torch.cuda.synchronize()

N_ITERS = 20
t0 = time.time()
for _ in range(N_ITERS):
    _ = encode_batch(texts, bs_speed)
if DEVICE != "cpu":
    torch.cuda.synchronize()
t1 = time.time()

total_samples = bs_speed * N_ITERS
sps = total_samples / (t1 - t0)
print(f"  Batch size : {bs_speed}")
print(f"  Throughput : {sps:.0f} samples/sec")
print(f"  Seconds/batch : {(t1-t0)/N_ITERS:.3f}s")
print()

# ── Summary ───────────────────────────────────────────────────────────────────

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Model loaded    : BAAI/bge-m3  ({param_m:.0f}M params, {DTYPE})")
print(f"  Load memory     : {mem_after_load:.2f} GB")
print(f"  Max inference batch  : {max_ok_bs}")
print(f"  Max train batch (no grad-ckpt): {max_ok_train_bs}")
if gc_enabled:
    print(f"  Max train batch (WITH grad-ckpt): {max_ok_gc_bs}")

print()
print("VERDICT")
print("-------")
effective_bs = max_ok_gc_bs if gc_enabled and max_ok_gc_bs > 0 else max_ok_train_bs
if effective_bs >= 32:
    print(f"  GREEN  — batch {effective_bs} is workable for contrastive KGC.")
    print("           Use gradient accumulation to reach an effective batch of 256+.")
elif effective_bs >= 16:
    print(f"  YELLOW — batch {effective_bs} is tight. Use gradient accumulation x8 or more.")
    print("           Consider LoRA instead of full fine-tune to free VRAM.")
elif effective_bs > 0:
    print(f"  RED    — batch {effective_bs} is too small for stable contrastive training.")
    print("           Switch to mE5-base (278M) as primary; keep BGE-M3 for ablation.")
else:
    print("  RED    — training did not fit at all. Use mE5-base as primary.")

print()
print("Next steps after this script:")
print("  1. If GREEN/YELLOW -> proceed with BGE-M3 swap into RAA-KGC.")
print("  2. If RED          -> run with --pretrained-model intfloat/multilingual-e5-base instead.")
print("  3. In either case  -> start DBP-5L data download in parallel.")

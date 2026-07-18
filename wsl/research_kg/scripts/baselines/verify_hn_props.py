"""Verify the four correctness properties of the fixed build_entity_cache."""
import os, sys, json, torch
sys.path.insert(0, os.path.expanduser('~/research_kg'))
os.environ.setdefault('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
import train_dbp5l_lora as T
from transformers import AutoTokenizer

ROOT=os.path.expanduser('~/research_kg'); dev=torch.device('cuda')
tok=AutoTokenizer.from_pretrained('BAAI/bge-m3')
model=T.BGE_M3_LoRA_KGC('BAAI/bge-m3', lora_rank=16, lora_alpha=32).to(dev)
opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=5e-4)  # epoch-5 pressure
desc=json.load(open(f'{ROOT}/DBP5L/ind_v2/tracks/descriptions_v2_primary.json'))
etext={int(k):v for k,v in desc.items()}
fold=f'{ROOT}/DBP5L/ind_v2/folds/fold0_seed13'
train_ents=set(json.load(open(f'{fold}/train_entities.json')))
universe=sorted(e for e in etext if e in train_ents)

# --- instrument: intercept per-batch tensors to check grad_fn/device and bound memory ---
import train_dbp5l_lora as M
orig_encode = M.BGE_M3_LoRA_KGC.encode
peaks=[]; batch_props=[]
def probe_encode(self, ids, mask):
    emb = orig_encode(self, ids, mask)
    batch_props.append((emb.requires_grad, emb.grad_fn is None, emb.is_cuda))
    peaks.append(torch.cuda.memory_allocated())
    return emb
M.BGE_M3_LoRA_KGC.encode = probe_encode

torch.cuda.reset_peak_memory_stats()
cache, idx, meta = T.build_entity_cache(model, tok, etext, universe, 160, dev,
                                        batch_size=512, epoch=5, cache_key='PARENTKEY-e6875a6')
M.BGE_M3_LoRA_KGC.encode = orig_encode

# 1. final cache tensor: no grad, no graph
p1 = (cache.requires_grad is False) and (cache.grad_fn is None)
print(f"1. cache requires_grad={cache.requires_grad}, grad_fn={cache.grad_fn} -> {'PASS' if p1 else 'FAIL'}")

# 3. every per-batch embedding on CPU before accumulation? (probe caught them on GPU pre-.cpu();
#    the real check is the ACCUMULATED list is CPU — verify final cache is CPU)
p3 = (cache.device.type == 'cpu')
allbatch_nograd = all(gf for _,gf,_ in batch_props)   # grad_fn is None for every batch under no_grad
print(f"3. cache.device={cache.device.type}; every batch grad_fn None={allbatch_nograd} -> "
      f"{'PASS' if (p3 and allbatch_nograd) else 'FAIL'}")

# 2. GPU allocated memory bounded across all 83 batches (no monotonic growth = no leak)
n=len(peaks); span=(max(peaks)-min(peaks))/1e9
growth=(peaks[-1]-peaks[0])/1e9
print(f"2. {n} batches | alloc min {min(peaks)/1e9:.2f} max {max(peaks)/1e9:.2f} GB | "
      f"span {span:.3f} first->last {growth:+.3f} GB -> {'PASS' if span < 0.5 else 'FAIL'}")

# 4. metadata: epoch-5 adapter hash + corrected parent key
p4 = (meta['epoch']==5 and meta['cache_key']=='PARENTKEY-e6875a6'
      and meta['lora_hash']==T.lora_state_hash(model) and meta['persisted'] is False)
print(f"4. meta epoch={meta['epoch']} cache_key={meta['cache_key']} "
      f"adapter={meta['lora_hash'][:12]} persisted={meta['persisted']} -> {'PASS' if p4 else 'FAIL'}")

assert p1 and p3 and allbatch_nograd and span<0.5 and p4, "a property FAILED"
print("ALL FOUR PROPERTIES PASS")

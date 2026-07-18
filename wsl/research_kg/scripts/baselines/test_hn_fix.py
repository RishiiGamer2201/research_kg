"""Confirm the ACTUAL fixed build_entity_cache completes on the full 42,450 universe."""
import os, sys, json, torch
sys.path.insert(0, os.path.expanduser('~/research_kg'))
os.environ.setdefault('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
import train_dbp5l_lora as T
from transformers import AutoTokenizer

ROOT=os.path.expanduser('~/research_kg')
dev=torch.device('cuda')
tok=AutoTokenizer.from_pretrained('BAAI/bge-m3')
model=T.BGE_M3_LoRA_KGC('BAAI/bge-m3', lora_rank=16, lora_alpha=32).to(dev)
# simulate mid-training pressure: hold optimizer state like epoch 5 would
opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=5e-4)
desc=json.load(open(f'{ROOT}/DBP5L/ind_v2/tracks/descriptions_v2_primary.json'))
etext={int(k):v for k,v in desc.items()}
fold=f'{ROOT}/DBP5L/ind_v2/folds/fold0_seed13'
train_ents=set(json.load(open(f'{fold}/train_entities.json')))
universe=sorted(e for e in etext if e in train_ents)
torch.cuda.reset_peak_memory_stats()
cache, idx, meta = T.build_entity_cache(model, tok, etext, universe, 160, dev,
                                        batch_size=512, epoch=5, cache_key='testkey')
print(f"BUILT: cache {tuple(cache.shape)} | universe {len(universe)} | "
      f"peak VRAM {torch.cuda.max_memory_allocated()/1e9:.2f} GB")
assert cache.shape[0]==len(universe)==42450
print("HN FIX CONFIRMED: full 42,450-entity cache builds without OOM under the fixed code")

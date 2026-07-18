"""Prove the no_grad fix: grad-ON cache build leaks activation memory; grad-OFF is flat."""
import os, sys, torch, time
sys.path.insert(0, os.path.expanduser('~/research_kg'))
os.environ.setdefault('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
import train_dbp5l_lora as T
from transformers import AutoTokenizer

dev = torch.device('cuda')
tok = AutoTokenizer.from_pretrained('BAAI/bge-m3')
model = T.BGE_M3_LoRA_KGC('BAAI/bge-m3', lora_rank=16, lora_alpha=32).to(dev).eval()
texts = {i: f"entity number {i} with some descriptive text about it" for i in range(4000)}
ids = list(texts)

def peak_build(use_nograd):
    torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
    embs=[]
    ctx = torch.no_grad() if use_nograd else torch.enable_grad()
    with ctx:
        for i in range(0, len(ids), 512):
            enc = tok([texts[e] for e in ids[i:i+512]], max_length=160,
                      padding='max_length', truncation=True, return_tensors='pt')
            emb = model.encode(enc['input_ids'].to(dev), enc['attention_mask'].to(dev))
            embs.append(emb.cpu())
    return torch.cuda.max_memory_allocated()/1e9

# old behavior (grad tracked, model.eval only) vs fix (no_grad)
p_grad = peak_build(False)
p_nograd = peak_build(True)
print(f"peak VRAM  grad-ON (old, leaky): {p_grad:.2f} GB")
print(f"peak VRAM  no_grad  (fixed):     {p_nograd:.2f} GB")
print(f"reduction: {p_grad/p_nograd:.1f}x")
assert p_nograd < p_grad * 0.5, "no_grad must roughly halve+ peak memory"
print("HN OOM FIX CONFIRMED: no_grad removes the activation-graph accumulation")

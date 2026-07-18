import os, sys, torch
sys.path.insert(0, os.path.expanduser('~/research_kg'))
os.environ.setdefault('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
import train_dbp5l_lora as T

class Tiny(torch.nn.Module):
    def __init__(s):
        super().__init__()
        s.frozen = torch.nn.Linear(4, 4); s.frozen.weight.requires_grad_(False)
        s.lora = torch.nn.Linear(4, 4)          # trainable = "adapter"
m = Tiny()

h0 = T.lora_state_hash(m)
meta = {'epoch': 3, 'lora_hash': h0}
T.assert_hn_cache_fresh(meta, m, 3)             # matching -> must pass
print("PASS matching adapter accepted")

# frozen-only change must NOT change the hash (base revision is not the identifier)
with torch.no_grad(): m.frozen.weight += 1.0
T.assert_hn_cache_fresh(meta, m, 3)
print("PASS frozen-base change ignored (hash tracks adapter only)")

# adapter change MUST be rejected — this is the stale-cache failure mode
with torch.no_grad(): m.lora.weight += 0.001
try:
    T.assert_hn_cache_fresh(meta, m, 4)
    print("FAIL stale adapter accepted"); sys.exit(1)
except RuntimeError as e:
    assert 'HN cache rejected' in str(e)
    print("PASS stale adapter rejected:", str(e)[:80])
print("hn freshness self-check OK")

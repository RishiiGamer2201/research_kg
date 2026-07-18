"""HN cache freshness: requires BOTH the exact adapter hash AND the parent immutable key."""
import os, sys, torch
sys.path.insert(0, os.path.expanduser('~/research_kg'))
os.environ.setdefault('RESEARCH_KG_ROOT', os.path.expanduser('~/research_kg'))
import train_dbp5l_lora as T

class Tiny(torch.nn.Module):
    def __init__(s):
        super().__init__()
        s.frozen = torch.nn.Linear(4, 4); s.frozen.weight.requires_grad_(False)
        s.lora = torch.nn.Linear(4, 4)
m = Tiny()
KEY = "parentkey-aaaa1111"

meta = {'epoch': 3, 'lora_hash': T.lora_state_hash(m), 'cache_key': KEY}
T.assert_hn_cache_fresh(meta, m, 3, KEY)
print("PASS 1 matching adapter + matching parent key accepted")

# UNIT property of the hash function only: it must not see frozen weights.
h_before = T.lora_state_hash(m)
with torch.no_grad(): m.frozen.weight += 1.0
assert T.lora_state_hash(m) == h_before, "adapter hash must ignore frozen weights"
print("PASS 2 lora_state_hash isolates the adapter (unit property)")

# ...but the FULL assertion must still reject a base-model change, via the parent key,
# because a base/tokenizer revision change changes the parent key.
try:
    T.assert_hn_cache_fresh(meta, m, 3, "parentkey-DIFFERENT")
    print("FAIL 3 base/config change accepted"); sys.exit(1)
except RuntimeError as e:
    assert 'parent key' in str(e), e
    print("PASS 3 base/config change rejected via parent key")

# adapter drift under the same parent key must be rejected
with torch.no_grad(): m.lora.weight += 0.001
try:
    T.assert_hn_cache_fresh(meta, m, 4, KEY)
    print("FAIL 4 stale adapter accepted"); sys.exit(1)
except RuntimeError as e:
    assert 'adapter' in str(e), e
    print("PASS 4 stale adapter rejected under matching parent key")

# parent key alone must not rescue a stale adapter, and vice versa (both required)
try:
    T.assert_hn_cache_fresh({'epoch': 3, 'lora_hash': 'deadbeef', 'cache_key': KEY}, m, 3, KEY)
    print("FAIL 5"); sys.exit(1)
except RuntimeError:
    print("PASS 5 both identities are required")
print("hn freshness self-check OK")

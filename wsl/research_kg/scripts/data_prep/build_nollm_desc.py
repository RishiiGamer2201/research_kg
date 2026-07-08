"""
Build entity_descriptions_nollm.json for the W4.3 ablation.
Intervention: for EL and JA entities whose current description is ENGLISH prose that was
back-filled after the pre-LLM backup (i.e. LLM-generated OR English-Wikipedia-fallback, the two
sources we cannot verify per-entity and which the audit showed are heavily hallucinated for
transliterated names), revert to the pre-LLM value (name-only). Keeps native-language Wikipedia
abstracts and KG-neighbor descriptions untouched. Measures whether the risky English back-fill
for the two low-resource languages helps or hurts.
"""
import json, os
P = os.path.expanduser('~/research_kg/DBP5L/processed')
cur = json.load(open(P + '/entity_descriptions.json', encoding='utf-8'))
bak = json.load(open(P + '/entity_descriptions_backup.json', encoding='utf-8'))
ent = json.load(open(P + '/entities.json', encoding='utf-8'))

def ascii_frac(s):
    L = [c for c in s if c.isalpha()]
    return sum(c.isascii() for c in L) / len(L) if L else 0.0

out = dict(cur)
reverted = {'el': 0, 'ja': 0}
for k, v in cur.items():
    lang = ent.get(k, {}).get('lang', '?')
    if lang in ('el', 'ja') and v != bak.get(k) and '|' not in v and len(v) >= 60 and ascii_frac(v) > 0.85:
        out[k] = bak.get(k, ent.get(k, {}).get('name', v))  # revert to pre-back-fill (name-only)
        reverted[lang] += 1

json.dump(out, open(P + '/entity_descriptions_nollm.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('reverted English back-fill for EL/JA:', reverted, 'total', sum(reverted.values()))
print('wrote entity_descriptions_nollm.json (', len(out), 'entities )')

import json

with open('/home/admin_wsl/research_kg/DBP5L/processed/entity_descriptions.json') as f:
    desc = json.load(f)
with open('/home/admin_wsl/research_kg/DBP5L/processed/entities.json') as f:
    ents = json.load(f)

short = {k: v for k, v in desc.items() if len(v) < 120 and '|' not in v}
kg_nb = {k: v for k, v in desc.items() if '|' in v}
wiki  = {k: v for k, v in desc.items() if len(v) >= 120 and '|' not in v}

print(f'Total entities:                         {len(desc):,}')
print(f'Wikipedia abstract (>=120 chars):       {len(wiki):,}')
print(f'KG-neighbor (has | pipe):               {len(kg_nb):,}')
print(f'Short/name-only (<120 chars, no pipe):  {len(short):,}')

# Per-language breakdown
from collections import Counter
lang_wiki  = Counter()
lang_kg    = Counter()
lang_short = Counter()
for k, v in desc.items():
    lang = ents.get(k, {}).get('lang', '?')
    if len(v) >= 120 and '|' not in v:
        lang_wiki[lang] += 1
    elif '|' in v:
        lang_kg[lang] += 1
    else:
        lang_short[lang] += 1

print('\nPer-language breakdown:')
print(f"{'Lang':>5} | {'Wikipedia':>10} | {'KG-neighbor':>12} | {'Name-only':>10}")
print('-' * 45)
for lang in ['en', 'fr', 'es', 'ja', 'el']:
    print(f"{lang:>5} | {lang_wiki[lang]:>10,} | {lang_kg[lang]:>12,} | {lang_short[lang]:>10,}")

print('\nSample name-only entities:')
for k, v in list(short.items())[:8]:
    lang = ents.get(k, {}).get('lang', '?')
    name = ents.get(k, {}).get('name', '?')
    print(f'  [{lang}] {name[:60]}')

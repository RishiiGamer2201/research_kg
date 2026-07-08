"""
W4.1 — JA error analysis (CPU only).
Hypothesis: ml=160 helped JA/EL most because their enriched descriptions are LONG (esp. JA:
CJK tokenizes into many subwords) and were being truncated at ml=96/128. Tests coverage +
token-length + truncation rate per language over the TEST (unseen) entities.
"""
import os, json
from collections import defaultdict
from transformers import AutoTokenizer

PROC = os.path.expanduser('~/research_kg/DBP5L/processed')
LANGS = ['en', 'fr', 'es', 'ja', 'el']

ent = json.load(open(f'{PROC}/entities.json'))
entity_lang = {int(k): v.get('lang', 'en') for k, v in ent.items()}
entity_name = {int(k): v.get('name', '') for k, v in ent.items()}
desc = {int(k): v for k, v in json.load(open(f'{PROC}/entity_descriptions.json', encoding='utf-8')).items()}

# test (unseen) entities per language: heads + tails appearing in test.json
test_entities = defaultdict(set)
for line in open(f'{PROC}/test.json'):
    ex = json.loads(line)
    test_entities[ex.get('lang', 'en')].add(ex['h'])
    test_entities[ex.get('lang', 'en')].add(ex['t'])

tok = AutoTokenizer.from_pretrained('BAAI/bge-m3')

print(f"{'Lang':>4} | {'#testEnt':>8} | {'%rich':>6} | {'%nameOnly':>9} | {'medTok':>6} | {'meanTok':>7} | {'%>96':>6} | {'%>128':>6} | {'%>160':>6}")
print('-' * 90)
rows = {}
for lang in LANGS:
    ents = sorted(test_entities[lang])
    n = len(ents)
    rich = name_only = 0
    toks = []
    for e in ents:
        d = desc.get(e, entity_name.get(e, ''))
        nm = entity_name.get(e, '')
        # "rich" = has KG-neighbor structure or is materially longer than the bare name
        if ('|' in d) or (len(d) > len(nm) + 15):
            rich += 1
        else:
            name_only += 1
        toks.append(len(tok(d, add_special_tokens=True)['input_ids']))
    toks.sort()
    med = toks[len(toks)//2] if toks else 0
    mean = sum(toks)/len(toks) if toks else 0
    p96 = sum(t > 96 for t in toks)/n*100
    p128 = sum(t > 128 for t in toks)/n*100
    p160 = sum(t > 160 for t in toks)/n*100
    rows[lang] = dict(n=n, rich=rich/n*100, name=name_only/n*100, med=med, mean=mean, p96=p96, p128=p128, p160=p160)
    print(f"{lang.upper():>4} | {n:>8} | {rich/n*100:>5.1f}% | {name_only/n*100:>8.1f}% | {med:>6} | {mean:>7.1f} | {p96:>5.1f}% | {p128:>5.1f}% | {p160:>5.1f}%")

print()
print("Read: %>96 = fraction of test-entity descriptions truncated at eval ml=96 (info lost).")
print("If JA has high %>128 but strong ml160 gains, truncation (not coverage) explains its weakness.")

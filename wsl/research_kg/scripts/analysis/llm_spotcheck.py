import json, os, random
P = os.path.expanduser('~/research_kg/DBP5L/processed')
cur = json.load(open(P + '/entity_descriptions.json', encoding='utf-8'))
bak = json.load(open(P + '/entity_descriptions_backup.json', encoding='utf-8'))
ent = json.load(open(P + '/entities.json', encoding='utf-8'))

def ascii_frac(s):
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(c.isascii() for c in letters) / len(letters)

# LLM-generated (per generate_llm_descriptions.py + llm_descriptions.log):
#  - only EL and JA entities (146 + 897 = 1043 attempted, 1042 succeeded)
#  - written in ENGLISH (Latin script) regardless of entity language
#  - 2-sentence prose, no '|', >= 60 chars
#  - description changed vs the pre-LLM backup
cand = []
for k, v in cur.items():
    lang = ent.get(k, {}).get('lang', '?')
    if lang in ('el', 'ja') and v != bak.get(k) and '|' not in v and len(v) >= 60 and ascii_frac(v) > 0.85:
        cand.append(k)

from collections import Counter
print('LLM-generated candidates (English prose, EL/JA, changed):', len(cand))
print('by language:', dict(Counter(ent.get(k, {}).get('lang') for k in cand)))
lens = sorted(len(cur[k]) for k in cand)
print('char length: min %d median %d max %d' % (lens[0], lens[len(lens)//2], lens[-1]))

random.seed(7)
sample = random.sample(cand, 50)
out = []
for k in sample:
    info = ent.get(k, {})
    out.append({'id': k, 'name': info.get('name', ''), 'lang': info.get('lang', '?'),
                'uri': info.get('uri', ''), 'desc': cur[k]})
json.dump(out, open(os.path.expanduser('~/research_kg/logs/llm_spotcheck_sample.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('wrote 50-sample to logs/llm_spotcheck_sample.json')

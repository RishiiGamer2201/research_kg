import os, json
IND = os.path.expanduser('~/research_kg/DBP5L/ind')
PROC = os.path.expanduser('~/research_kg/DBP5L/processed')
LANGS = ['en','fr','es','ja','el']

# lang offsets: replicate preprocess logic (global_id = offset + local_id, ordered by entity_uris line count)
offsets = {}
off = 0
for l in LANGS:
    n = sum(1 for _ in open(f'{IND}/{l}/entity_uris.txt'))
    offsets[l] = off
    off += n

total_support = 0
per_lang = {}
support_by_hr = {}  # (h_global, r) -> set(t_global)
for l in LANGS:
    f = f'{IND}/{l}/support.txt'
    cnt = 0
    for line in open(f):
        p = line.split()
        if len(p) < 3: continue
        h = offsets[l] + int(p[0]); r = int(p[1]); t = offsets[l] + int(p[2])
        support_by_hr.setdefault((h, r), set()).add(t)
        cnt += 1
    per_lang[l] = cnt
    total_support += cnt

print('offsets:', offsets)
print('support per lang:', per_lang, '| total:', total_support)

# How many test queries share an (h,r) with a support triple whose tail != gold?
test = [json.loads(x) for x in open(f'{PROC}/test.json')]
print('test triples:', len(test))
affected = 0
extra_filters = 0
for ex in test:
    key = (ex['h'], ex['r'])
    if key in support_by_hr:
        others = support_by_hr[key] - {ex['t']}
        if others:
            affected += 1
            extra_filters += len(others)
print(f'test queries with an extra support-tail to filter: {affected} ({affected/len(test)*100:.2f}%)')
print(f'total extra filtered tails: {extra_filters}')

# Does current filter_map already include some of these via train/valid/test? Check overlap.
fm = {}
for path in ['train.json','valid.json','test.json']:
    for x in open(f'{PROC}/{path}'):
        ex = json.loads(x); fm.setdefault((ex['h'],ex['r']), set()).add(ex['t'])
already = 0
new = 0
for (h,r), tails in support_by_hr.items():
    cur = fm.get((h,r), set())
    for t in tails:
        if t in cur: already += 1
        else: new += 1
print(f'support tails already in filter_map: {already} | genuinely new: {new}')

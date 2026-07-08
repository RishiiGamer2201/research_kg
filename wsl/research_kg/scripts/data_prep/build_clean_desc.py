"""
Build entity_descriptions_clean.json for the option-b clean retrain.
For the 2,359 EL/JA entities whose descriptions were unverifiable English back-fill (LLM or
English-Wikipedia-fallback), try one native-language Wikipedia REST summary; if that fails (as
it likely will, since these already failed native fetch once), fall back to the bare name.
Everything else (KG-neighbors, native-language Wikipedia abstracts) is untouched.
"""
import json, os, time, urllib.request, urllib.parse
P = os.path.expanduser('~/research_kg/DBP5L/processed')
cur = json.load(open(P + '/entity_descriptions.json', encoding='utf-8'))
bak = json.load(open(P + '/entity_descriptions_backup.json', encoding='utf-8'))
ent = json.load(open(P + '/entities.json', encoding='utf-8'))
WIKI = 'https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}'

def ascii_frac(s):
    L = [c for c in s if c.isalpha()]
    return sum(c.isascii() for c in L) / len(L) if L else 0.0

def native_summary(name, lang, timeout=4):
    title = urllib.parse.quote(name.replace(' ', '_'))
    url = WIKI.format(lang=lang, title=title)
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'KGC-Research/1.0 (academic; contact@research.org)'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
            ex = (d.get('extract') or '').strip()
            # accept only a real native-language summary (not a disambiguation stub)
            if len(ex) >= 60 and d.get('type', 'standard') == 'standard':
                return ex
    except Exception:
        pass
    return None

targets = [k for k, v in cur.items()
           if ent.get(k, {}).get('lang') in ('el', 'ja') and v != bak.get(k)
           and '|' not in v and len(v) >= 60 and ascii_frac(v) > 0.85]
print('entities to re-source:', len(targets))

out = dict(cur)
recovered = names = 0
t0 = time.time()
for i, k in enumerate(targets):
    info = ent.get(k, {})
    name = info.get('name', '')
    lang = info.get('lang')
    s = native_summary(name, lang)
    if s:
        out[k] = s; recovered += 1
    else:
        out[k] = bak.get(k, name); names += 1  # bare native name
    if (i + 1) % 200 == 0:
        print('  %d/%d | recovered %d | names %d | %.0fs' % (i + 1, len(targets), recovered, names, time.time() - t0))

json.dump(out, open(P + '/entity_descriptions_clean.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('DONE: recovered native %d, fell back to name %d, total %d' % (recovered, names, len(targets)))
print('wrote entity_descriptions_clean.json')

import os, re

def parse(logpath):
    if not os.path.exists(logpath):
        return None
    t = open(logpath, encoding='utf-8', errors='replace').read()
    out = {}
    for sec in ['CROSS-LINGUAL', 'WITHIN-LANGUAGE']:
        block = t[t.find('[' + sec):] if ('[' + sec) in t else t[t.find(sec):]
        m = re.search(r'OVERALL: MRR=([\d.]+)% H@1=([\d.]+)% H@3=([\d.]+)% H@10=([\d.]+)%', block)
        if m:
            out[sec] = dict(MRR=float(m.group(1)), H1=float(m.group(2)), H3=float(m.group(3)), H10=float(m.group(4)))
        lang_block = block[:block.find('WITHIN-LANGUAGE')] if sec == 'CROSS-LINGUAL' else block
        for lang in ['EN', 'FR', 'ES', 'JA', 'EL']:
            lm = re.search(r'\n  ' + lang + r'[ (:].*?MRR=([\d.]+)%.*?H@1=([\d.]+)%.*?H@10=([\d.]+)%', lang_block)
            if lm:
                out.setdefault(sec + '_lang', {})[lang] = (float(lm.group(1)), float(lm.group(2)), float(lm.group(3)))
    return out

runs = [
    ('zero-shot', 'final_zeroshot'), ('Row3-HN', 'final_Row3HN_ml96_r8'),
    ('A', 'final_A_ml128_r8'), ('B', 'final_B_ml128_r16'),
    ('E-ref', 'final_E_ml160_r16'), ('F', 'final_F_ml128_r16_40ep'),
    ('seed42', 'eval_seed42_ml160'), ('seed123', 'eval_seed123_ml160'), ('seed777', 'eval_seed777_ml160'),
]
L = os.path.expanduser('~/research_kg/logs/')
print('OVERALL (cross-lingual vs within-language):')
for name, stem in runs:
    r = parse(L + stem + '.log')
    if not r:
        print('  %-9s MISSING' % name); continue
    cl = r.get('CROSS-LINGUAL', {}); wl = r.get('WITHIN-LANGUAGE', {})
    print('  %-9s | XL MRR=%5.2f H@1=%5.2f H@10=%5.2f | WL MRR=%5.2f H@1=%5.2f H@10=%5.2f' % (
        name, cl.get('MRR', 0), cl.get('H1', 0), cl.get('H10', 0),
        wl.get('MRR', 0), wl.get('H1', 0), wl.get('H10', 0)))

print('\nE-ref cross-lingual per-language (MRR, H@1, H@10):')
r = parse(L + 'final_E_ml160_r16.log')
for lang in ['FR', 'ES', 'EN', 'EL', 'JA']:
    v = r.get('CROSS-LINGUAL_lang', {}).get(lang)
    if v:
        print('  %s: MRR=%.2f H@1=%.2f H@10=%.2f' % (lang, v[0], v[1], v[2]))

# seed cross-lingual overall for mean/std
import statistics as st
xls = []
for stem in ['eval_seed42_ml160', 'eval_seed123_ml160', 'eval_seed777_ml160']:
    r = parse(L + stem + '.log')
    if r and 'CROSS-LINGUAL' in r:
        xls.append(r['CROSS-LINGUAL']['MRR'])
if len(xls) == 3:
    print('\nseed cross-lingual MRR:', xls, 'mean=%.2f std=%.2f' % (st.mean(xls), st.stdev(xls)))

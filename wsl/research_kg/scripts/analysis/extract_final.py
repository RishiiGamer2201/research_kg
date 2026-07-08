import re, os, glob
LOGDIR = os.path.expanduser('~/research_kg/logs')
order = ['final_zeroshot','final_Row3HN_ml96_r8','final_A_ml128_r8','final_B_ml128_r16','final_E_ml160_r16','final_F_ml128_r16_40ep']
for name in order:
    f = f'{LOGDIR}/{name}.log'
    if not os.path.exists(f):
        print(f'{name}: MISSING'); continue
    txt = open(f, encoding='utf-8', errors='replace').read()
    ml = re.search(r'Evaluating with max_length=(\d+)', txt)
    sup = re.search(r'Added (\d+) support triples', txt)
    # within-language block
    m = re.search(r'\[WITHIN-LANGUAGE EVAL\].*?OVERALL: (MRR=[\d.]+% H@1=[\d.]+% H@3=[\d.]+% H@10=[\d.]+%)', txt, re.S)
    print(f'### {name}  (ml={ml.group(1) if ml else "?"}, support_filter={"Y:"+sup.group(1) if sup else "N"})')
    if m: print('   WL OVERALL:', m.group(1))
    for lang in ['EN','FR','ES','JA','EL']:
        lm = re.search(rf'\n  {lang}\s*\([\d,]+ cands\): (MRR=[\d.]+%[^\n]*)', txt)
        if lm: print(f'   {lang}: {lm.group(1)}')
    print()

import json, os, numpy as np
ROOT=os.path.expanduser('~/research_kg')
D=f'{ROOT}/DBP5L/ind_v2/audits/eval/B0-FOLD0-SEED42'
SHA='c99a7b6ce90e0b143a47492cc773b3923c725af2050715a84feaead4dd9fe8f4'
VIEW_HASH={'natural':'d1afcf20'}  # frozen primary; assert natural only (masked/missing differ by design)
e2c={int(k):v for k,v in json.load(open(f'{ROOT}/DBP5L/ind_v2/concepts/entity2concept.json')).items()}
LANGS=['en','fr','es','ja','el']
def qent(r): return int(r['h']) if r['direction']=='tail' else int(r['t'])

ec=json.load(open(f'{D}/evaluated_checkpoint.json'))
assert ec['selected_checkpoint_sha256']==SHA and ec['selection_epoch']==27, 'evaluated_checkpoint SHA/epoch mismatch'
assert ec['selected_checkpoint'].endswith('best_model.pt')
views={}
for v in ('natural','masked','missing'):
    s=json.load(open(f'{D}/view_{v}.json'))
    # ASSERTIONS: checkpoint SHA + rank_dump filename + (natural) view_hash
    assert s['checkpoint'].endswith('best_model.pt'), f'{v}: unexpected ckpt path'
    assert s['rank_dump'].endswith(f'ranks_{v}.json'), f'{v}: rank_dump not ranks_{v}.json'
    if v in VIEW_HASH: assert s['view_hash'].startswith(VIEW_HASH[v]), f'{v}: view_hash mismatch'
    rows=json.load(open(s['rank_dump']))
    assert len(rows)==73880, f'{v}: expected 73880 rows got {len(rows)}'
    views[v]=rows
print('ASSERTIONS PASS: ckpt SHA c99a7b6c, rank_dump filenames, natural view_hash d1afcf20, 73880 rows x3')

def mrr(rows): return 100*np.mean([r['rr'] for r in rows]) if rows else float('nan')
def cci(rows,n_boot=2000,seed=20260719):
    by={}
    for r in rows:
        c=e2c.get(qent(r))
        if c is not None: by.setdefault(c,[]).append(r['rr'])
    if not by: return (float('nan'),float('nan'),0)
    cs=sorted(by); sums=np.array([sum(by[c]) for c in cs]); cnts=np.array([len(by[c]) for c in cs])
    rng=np.random.default_rng(seed); n=len(cs); idx=rng.integers(0,n,(n_boot,n))
    b=100*sums[idx].sum(1)/cnts[idx].sum(1)
    return (float(np.percentile(b,2.5)),float(np.percentile(b,97.5)),len(cs))

def row(rows):
    comb=mrr(rows); tail=mrr([r for r in rows if r['direction']=='tail']); head=mrr([r for r in rows if r['direction']=='head'])
    ment=mrr([r for r in rows if r['mentioned']]); ur=[r for r in rows if not r['mentioned']]
    unm=mrr(ur); lo,hi,nc=cci(ur)
    return comb,tail,head,ment,unm,lo,hi,len(rows),nc

out=[]
out.append('| Lang | Comb | Tail | Head | Ment | Unm | Unm 95% CI | nQ | nConc | Masked | Missing |')
out.append('|---|---|---|---|---|---|---|---|---|---|---|')
nat=views['natural']; msk=views['masked']; mis=views['missing']
for L in LANGS+['ALL']:
    nr = nat if L=='ALL' else [r for r in nat if r['lang']==L]
    mkr = msk if L=='ALL' else [r for r in msk if r['lang']==L]
    msr = mis if L=='ALL' else [r for r in mis if r['lang']==L]
    c,t,h,m,u,lo,hi,nq,nc=row(nr)
    out.append(f'| {L.upper()} | {c:.2f} | {t:.2f} | {h:.2f} | {m:.2f} | **{u:.2f}** | [{lo:.2f}, {hi:.2f}] | {nq:,} | {nc:,} | {mrr(mkr):.2f} | {mrr(msr):.2f} |')
print('\n'.join(out))
# direction-split unmentioned natural
print('\nDIRSPLIT (natural, ALL):')
for dr in ('tail','head'):
    ur=[r for r in nat if r['direction']==dr and not r['mentioned']]
    lo,hi,nc=cci(ur)
    print(f'  {dr}: unm={mrr(ur):.2f} CI[{lo:.2f},{hi:.2f}] n={len(ur)} conc={nc}')
open(f'{D}/perlang_tables.md','w').write('\n'.join(out))
print('\nwrote perlang_tables.md')

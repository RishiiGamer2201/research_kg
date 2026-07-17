"""
Paired bootstrap significance test between two models' per-triple within-language ranks
(dumped by eval_dbp5l.py --dump-ranks). Tests whether model A's MRR exceeds model B's.

  python3 bootstrap_sig.py --a ranks_full.json --b ranks_row3hn.json --iters 10000

Both files must come from the SAME test set (they do — test.json order is fixed), so rows align
by (h, r, t, lang). Reports MRR_A, MRR_B, mean paired delta, 95% CI, and a two-sided p-value
(fraction of resamples where the delta crosses 0).
"""
import argparse, json, random


def load(path):
    rows = json.load(open(path))
    return {(x['h'], x['r'], x['t'], x['lang']): x['rr'] for x in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True, help='model A rank dump (e.g. full model)')
    ap.add_argument('--b', required=True, help='model B rank dump (baseline)')
    ap.add_argument('--iters', type=int, default=10000)
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    A, B = load(args.a), load(args.b)
    keys = sorted(set(A) & set(B))
    n = len(keys)
    if n == 0:
        raise SystemExit('No overlapping test triples — are both dumps from the same eval set?')
    a = [A[k] for k in keys]
    b = [B[k] for k in keys]
    mrr_a = sum(a) / n
    mrr_b = sum(b) / n
    diff = [a[i] - b[i] for i in range(n)]
    obs = mrr_a - mrr_b

    deltas = []
    ge0 = 0
    for _ in range(args.iters):
        s = 0.0
        for _ in range(n):
            s += diff[rng.randrange(n)]
        d = s / n
        deltas.append(d)
        if d <= 0:
            ge0 += 1
    deltas.sort()
    lo = deltas[int(0.025 * args.iters)]
    hi = deltas[int(0.975 * args.iters)]
    # two-sided p: fraction of resamples on the opposite side of 0 from the observed effect
    p = 2.0 * (ge0 / args.iters if obs > 0 else (args.iters - ge0) / args.iters)
    p = min(1.0, p)

    print(f'n paired triples : {n}')
    print(f'MRR A            : {mrr_a*100:.2f}%')
    print(f'MRR B            : {mrr_b*100:.2f}%')
    print(f'observed delta   : {obs*100:+.2f} MRR points')
    print(f'95% bootstrap CI : [{lo*100:+.2f}, {hi*100:+.2f}]')
    print(f'two-sided p      : {p:.4g}')
    print(f'significant @0.05: {"YES" if (lo > 0 or hi < 0) else "no"}')

    # Wilcoxon signed-rank (the test the AAAI checklist names). scipy if present, else
    # normal-approximation fallback (fine at n ~ 50K).
    try:
        from scipy.stats import wilcoxon
        stat, wp = wilcoxon(a, b, zero_method='wilcox', alternative='two-sided')
        print(f'Wilcoxon signed-rank: statistic={stat:.4g}, two-sided p={wp:.4g} (scipy)')
    except ImportError:
        import math
        pairs = [(abs(d), 1 if d > 0 else -1) for d in diff if d != 0]
        nn = len(pairs)
        if nn == 0:
            print('Wilcoxon: all paired differences are zero')
            return
        pairs.sort(key=lambda x: x[0])
        # average ranks for ties
        ranks = [0.0] * nn
        i = 0
        while i < nn:
            j = i
            while j + 1 < nn and pairs[j + 1][0] == pairs[i][0]:
                j += 1
            r = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[k] = r
            i = j + 1
        w_plus = sum(r for r, (_, s) in zip(ranks, pairs) if s > 0)
        mu = nn * (nn + 1) / 4
        sigma = math.sqrt(nn * (nn + 1) * (2 * nn + 1) / 24)
        z = (w_plus - mu) / sigma
        wp = math.erfc(abs(z) / math.sqrt(2))
        print(f'Wilcoxon signed-rank (normal approx): z={z:.3f}, two-sided p={wp:.4g}, n_nonzero={nn}')


if __name__ == '__main__':
    main()

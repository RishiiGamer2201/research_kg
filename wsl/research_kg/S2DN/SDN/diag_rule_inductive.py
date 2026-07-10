"""Does rule support TRANSFER to unseen entities (the inductive split)?

Rules are relation-level and entity-independent, so they should transfer to the inductive
test graph where a GNN's learned entity structure does not. This is the core reason to
expect a rule term to help an INDUCTIVE model, and it is the claim RuleTrust rests on.

Setup (no GNN, no subgraph extraction, pure graph ops):
  - mine rules on the TRAINING graph            (data/<ds>/train.txt)
  - apply them to the INDUCTIVE support graph   (data/<ds>_ind/train.txt)
  - score real inductive test triples           (data/<ds>_ind/test.txt)
    against corrupted-tail negatives drawn from the inductive entity set

Reports coverage, discrimination (AUC), and rule-only MRR/Hits. Relations are mapped by
NAME through the training relation2id, matching how test_ranking.py reuses saved_relation2id.

Read-only.
"""
import argparse
import os
import random
from collections import defaultdict

from utils.rule_miner import mine_rules

MAIN_DIR = "/home/admin_wsl/research_kg/S2DN/SDN"


def read_triples(path):
    out = []
    with open(path) as f:
        for line in f:
            p = line.strip().split()
            if len(p) == 3:
                out.append((p[0], p[1], p[2]))
    return out


def build_literal_adj(triples, relation2id):
    """out[(rel_id, inverted)][src] = set(dst)"""
    out = defaultdict(lambda: defaultdict(set))
    for h, r, t in triples:
        if r not in relation2id:
            continue
        rid = relation2id[r]
        out[(rid, False)][h].add(t)
        out[(rid, True)][t].add(h)
    return out


def rule_score(h, rid, t, out, rule_index):
    """max confidence over rules for rid whose body path connects h -> t."""
    best = 0.0
    for body, conf in rule_index.get(rid, ()):
        if conf <= best:
            continue
        if len(body) == 1:
            if t in out.get(body[0], {}).get(h, ()):
                best = conf
        else:
            mids = out.get(body[0], {}).get(h, ())
            l2 = out.get(body[1], {})
            for z in mids:
                if t in l2.get(z, ()):
                    best = conf
                    break
    return best


def auc(scores, labels):
    pairs = sorted(zip(scores, labels))
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    pos = [ranks[k] for k in range(n) if pairs[k][1] == 1]
    npos, nneg = len(pos), n - len(pos)
    if npos == 0 or nneg == 0:
        return float("nan")
    return (sum(pos) - npos * (npos + 1) / 2.0) / (npos * nneg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="fb237_v1")
    ap.add_argument("--conf-threshold", type=float, default=0.1)
    ap.add_argument("--min-support", type=int, default=2)
    ap.add_argument("--negatives", type=int, default=50, help="corrupted tails per test triple")
    ap.add_argument("--no-inverse", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)

    train_path = os.path.join(MAIN_DIR, f"data/{args.dataset}/train.txt")
    ind_sup_path = os.path.join(MAIN_DIR, f"data/{args.dataset}_ind/train.txt")
    ind_test_path = os.path.join(MAIN_DIR, f"data/{args.dataset}_ind/test.txt")

    train_triples = read_triples(train_path)
    rels = []
    for _, r, _ in train_triples:
        if r not in rels:
            rels.append(r)
    relation2id = {r: i for i, r in enumerate(rels)}

    rules = mine_rules(train_path, relation2id, min_support=args.min_support,
                       conf_threshold=args.conf_threshold, max_len=2,
                       use_inverse=not args.no_inverse)
    rule_index = {}
    for r in rules:
        body = tuple((int(a), bool(b)) for a, b in r["body"])
        rule_index.setdefault(int(r["head"]), []).append((body, float(r["confidence"])))
    for k in rule_index:
        rule_index[k].sort(key=lambda x: -x[1])  # high confidence first, enables early exit
    print(f"{args.dataset}: mined {len(rules)} rules on the TRAIN graph "
          f"({len(rule_index)}/{len(relation2id)} head relations)")

    ind_support = read_triples(ind_sup_path)
    ind_test = read_triples(ind_test_path)
    out = build_literal_adj(ind_support, relation2id)
    entities = sorted({e for h, _, t in ind_support for e in (h, t)})
    known = {(h, relation2id[r], t) for h, r, t in ind_support if r in relation2id}
    print(f"inductive support graph: {len(ind_support)} triples, {len(entities)} entities")
    print(f"inductive test triples : {len(ind_test)}")

    scores, labels = [], []
    pos_cov = neg_cov = npos = nneg = 0
    ranks = []

    for h, r, t in ind_test:
        if r not in relation2id:
            continue
        rid = relation2id[r]
        sp = rule_score(h, rid, t, out, rule_index)
        scores.append(sp); labels.append(1); npos += 1
        pos_cov += sp > 0

        neg_scores = []
        for _ in range(args.negatives):
            tc = random.choice(entities)
            if tc == t or (h, rid, tc) in known:
                continue
            sn = rule_score(h, rid, tc, out, rule_index)
            neg_scores.append(sn)
            scores.append(sn); labels.append(0); nneg += 1
            neg_cov += sn > 0

        # rule-only rank of the true tail among candidates (ties -> average rank)
        better = sum(1 for s in neg_scores if s > sp)
        tied = sum(1 for s in neg_scores if s == sp)
        ranks.append(better + 1 + tied / 2.0)

    mrr = sum(1.0 / r for r in ranks) / max(len(ranks), 1)
    h10 = sum(1 for r in ranks if r <= 10) / max(len(ranks), 1)
    h1 = sum(1 for r in ranks if r <= 1) / max(len(ranks), 1)

    print(f"\n=== inductive target-pair rule support ({npos} pos, {nneg} neg) ===")
    print(f"  positives with rule support : {pos_cov}/{npos} ({100.0*pos_cov/max(npos,1):.1f}%)")
    print(f"  negatives with rule support : {neg_cov}/{nneg} ({100.0*neg_cov/max(nneg,1):.1f}%)")
    print(f"\n=== discrimination on UNSEEN entities ===")
    print(f"  AUC, rule score alone : {auc(scores, labels):.4f}  (0.5 = chance)")
    print(f"  rule-only MRR         : {mrr:.4f}")
    print(f"  rule-only Hits@1      : {h1:.4f}")
    print(f"  rule-only Hits@10     : {h10:.4f}")
    print(f"\n  (S2DN GNN on this split: MRR 53.13, Hits@1 44.63, Hits@10 67.80)")
    print("  Note: rule-only ranks against random negatives, so these are NOT directly")
    print("  comparable to the paper's filtered ranking. Read them as transfer evidence.")


if __name__ == "__main__":
    main()

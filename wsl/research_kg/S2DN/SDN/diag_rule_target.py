"""Does rule support carry predictive signal for the TARGET triple?

The adjacency-level diagnostic showed rule support covers ~0.02% of N x N node pairs,
far too sparse to steer Structure Refining. But rules speak about the pair that actually
matters: the target triple's (head, tail). GraIL enclosing subgraphs are built around
that pair, and the target edge itself is removed, so there is no leakage.

This measures, on real positive and negative examples:
  1. coverage: fraction of examples where a rule for the query relation connects head->tail
  2. discrimination: does rule support separate positives from negatives?
  3. standalone AUC of the rule score, and its correlation with the trained GNN score

If discrimination is at chance, rules carry no complementary signal and RuleTrust should be
abandoned regardless of where the prior is injected. If it is above chance, the rule score
belongs on the final logit (a decision per example), not smeared across the adjacency.

Read-only. Does not train.
"""
import argparse
import os

import torch
import dgl
from torch.utils.data import DataLoader

from subgraph_extraction.datasets import SubgraphDataset
from utils.graph_utils import collate_dgl, move_batch_to_device_dgl
from utils.rule_miner import mine_rules
from utils.rule_features import rules_to_index, build_rule_boost

MAIN_DIR = "/home/admin_wsl/research_kg/S2DN/SDN"


def auc(scores, labels):
    """Rank-based AUC; ties get average rank."""
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


def target_scores(model, graphs, rel_labels, rule_index):
    """rule support on (head, tail) for each subgraph, plus the GNN's own logit."""
    rule_s, gnn_s = [], []
    for graph, rl in zip(graphs, rel_labels):
        boost = build_rule_boost(graph, rl, rule_index)
        h = (graph.ndata["id"] == 1).nonzero().squeeze(1)
        t = (graph.ndata["id"] == 2).nonzero().squeeze(1)
        if h.numel() == 0 or t.numel() == 0:
            rule_s.append(0.0)
        else:
            rule_s.append(float(boost[h[0], t[0]].item()))
    return rule_s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--conf-threshold", type=float, default=0.1)
    ap.add_argument("--min-support", type=int, default=2)
    ap.add_argument("--n-batches", type=int, default=25)
    ap.add_argument("--no-inverse", action="store_true")
    args = ap.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    ckpt = os.path.join(MAIN_DIR, f"experiments/{args.experiment}/best_graph_classifier.pth")
    model = torch.load(ckpt, map_location=device, weights_only=False)
    model.eval()
    p = model.params
    p.device = device
    p.use_rule_trust = False  # measure the UNMODIFIED gnn score

    db_path = os.path.join(MAIN_DIR, f"data/{args.dataset}/subgraphs_en_True_neg_1_hop_3")
    file_paths = {
        "train": os.path.join(MAIN_DIR, f"data/{args.dataset}/train.txt"),
        "valid": os.path.join(MAIN_DIR, f"data/{args.dataset}/valid.txt"),
    }
    ds = SubgraphDataset(
        db_path, "train_pos", "train_neg", file_paths,
        add_traspose_rels=p.add_traspose_rels,
        num_neg_samples_per_link=p.num_neg_samples_per_link,
        use_kge_embeddings=False, dataset=args.dataset,
        kge_model=p.kge_model, file_name="train",
    )
    relation2id = {rel: idx for idx, rel in ds.id2relation.items()}
    rules = mine_rules(file_paths["train"], relation2id,
                       min_support=args.min_support, conf_threshold=args.conf_threshold,
                       max_len=2, use_inverse=not args.no_inverse)
    rule_index = rules_to_index(rules, args.conf_threshold)
    print(f"{args.dataset}: {len(rules)} rules over {len(rule_index)}/{len(relation2id)} head relations")

    loader = DataLoader(ds, batch_size=16, shuffle=False, num_workers=0, collate_fn=collate_dgl)

    rs, gs, ys = [], [], []
    with torch.no_grad():
        for bi, batch in enumerate(loader):
            if bi >= args.n_batches:
                break
            (dp, _tp, dn, _tn) = move_batch_to_device_dgl(batch, device)
            for data, label in ((dp, 1), (dn, 0)):
                g, rl = data
                out, _ = model(g_and(g, rl))
                gs.extend(out.squeeze(-1).float().cpu().tolist())
                rl_list = rl.detach().cpu().tolist()
                rs.extend(target_scores(model, dgl.unbatch(g), rl_list, rule_index))
                ys.extend([label] * len(rl_list))

    n = len(ys)
    npos = sum(ys)
    cov_pos = sum(1 for r, y in zip(rs, ys) if y == 1 and r > 0)
    cov_neg = sum(1 for r, y in zip(rs, ys) if y == 0 and r > 0)
    mp = [r for r, y in zip(rs, ys) if y == 1]
    mn = [r for r, y in zip(rs, ys) if y == 0]

    print(f"\n=== target-pair rule support over {n} examples ({npos} pos, {n - npos} neg) ===")
    print(f"  positives with rule support : {cov_pos}/{npos} ({100.0 * cov_pos / max(npos,1):.1f}%)")
    print(f"  negatives with rule support : {cov_neg}/{n - npos} ({100.0 * cov_neg / max(n - npos,1):.1f}%)")
    print(f"  mean rule score  pos={sum(mp)/max(len(mp),1):.4f}   neg={sum(mn)/max(len(mn),1):.4f}")

    print(f"\n=== discrimination ===")
    print(f"  AUC, rule score alone : {auc(rs, ys):.4f}   (0.5 = chance)")
    print(f"  AUC, trained GNN alone: {auc(gs, ys):.4f}")
    comb = [g + 2.0 * r for g, r in zip(gs, rs)]
    print(f"  AUC, gnn + 2.0 * rule : {auc(comb, ys):.4f}")

    ra = auc(rs, ys)
    if ra != ra or abs(ra - 0.5) < 0.02:
        print("\nVERDICT: rule support does NOT separate positives from negatives.")
        print("No injection point will help. RuleTrust as conceived should be abandoned.")
    else:
        print("\nVERDICT: rule support carries signal on the target pair.")
        print("Inject it at the SCORE (one decision per example), not across the N x N adjacency.")


def g_and(g, rl):
    return (g, rl)


if __name__ == "__main__":
    main()

"""RuleTrust readiness report for a dataset + trained checkpoint.

Answers, with measurements rather than assumptions:
  1. Is the attention scale saturated? (how much of the [0.01,0.99] band is graded)
  2. Do mined rules cover the subgraphs at all? (rule-supported pair fraction)
  3. Is there HEADROOM? (are rule-supported pairs already at the 0.99 ceiling)
  4. Does the prior change the refined adjacency and the model output?

Usage: python diag_ruletrust_report.py --dataset fb237_v1 --experiment sdn_fb_v1_paper_gpu

Read-only w.r.t. experiments. May create data/<dataset>/ruletrust_rules.json.
"""
import argparse
import os

os.environ.setdefault("RULETRUST_DEBUG", "0")

import torch
import dgl
from torch.utils.data import DataLoader

from subgraph_extraction.datasets import SubgraphDataset
from utils.graph_utils import collate_dgl, move_batch_to_device_dgl
from utils.rule_miner import mine_rules
from utils.rule_features import rules_to_index, build_rule_boost

MAIN_DIR = "/home/admin_wsl/research_kg/S2DN/SDN"
SEED = 12345


def pct(x, n):
    return f"{100.0 * x / max(n, 1):.2f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--rule-weight", type=float, default=0.5)
    ap.add_argument("--conf-threshold", type=float, default=0.1)
    ap.add_argument("--min-support", type=int, default=2)
    ap.add_argument("--n-subgraphs", type=int, default=40)
    ap.add_argument("--max-len", type=int, default=2)
    ap.add_argument("--no-inverse", action="store_true", help="forward-only literals (old miner)")
    args = ap.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    ckpt = os.path.join(MAIN_DIR, f"experiments/{args.experiment}/best_graph_classifier.pth")
    model = torch.load(ckpt, map_location=device, weights_only=False)
    model.eval()
    p = model.params
    p.device = device

    print(f"=== {args.dataset} / {args.experiment} ===")
    for k in ("metric_type", "graph_type", "num_pers", "emb_dim", "top_k"):
        print(f"  {k}: {getattr(p, k, '<unset>')}")

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

    # CRITICAL: mine with the dataset's own relation2id so rule relation ids align with
    # graph.edata['type']. An ad-hoc ordering would silently target the wrong relations.
    relation2id = {rel: idx for idx, rel in ds.id2relation.items()}
    rules = mine_rules(file_paths["train"], relation2id,
                       min_support=args.min_support, conf_threshold=args.conf_threshold,
                       max_len=args.max_len, use_inverse=not args.no_inverse)
    rule_index = rules_to_index(rules, args.conf_threshold)
    model.rule_index = rule_index
    hi = sum(1 for r in rules if r["confidence"] >= 0.5)
    print(f"\nrules: {len(rules)} over {len(rule_index)}/{len(relation2id)} head relations, "
          f"{hi} with conf>=0.5")
    if not rules:
        print("FAIL: no rules. RuleTrust has nothing to inject on this dataset.")
        return

    loader = DataLoader(ds, batch_size=8, shuffle=False, num_workers=0, collate_fn=collate_dgl)

    tot = sup = head = graded = ceil_ = 0
    seen = 0
    with torch.no_grad():
        for batch in loader:
            (data_pos, _a, _b, _c) = move_batch_to_device_dgl(batch, device)
            g, rel_labels = data_pos
            g.ndata["h"], _ = model.gnn(g)
            gsl = model.gsl
            for graph, rl in zip(dgl.unbatch(g), rel_labels.detach().cpu().tolist()):
                ctx = graph.ndata["h"]
                if gsl.feature_denoise:
                    ctx = gsl.mask_feature(ctx)
                att = 0
                for i in range(len(gsl.linear_sims)):
                    fc = torch.relu(gsl.linear_sims[i](ctx))
                    att = att + torch.matmul(fc, fc.transpose(-1, -2))
                att = att / len(gsl.linear_sims)
                pclamp = torch.clamp(att, 0.01, 0.99)
                boost = build_rule_boost(graph, rl, rule_index)

                n = att.numel()
                tot += n
                graded += int(((att > 0.01) & (att < 0.99)).sum())
                ceil_ += int((att >= 0.99).sum())
                s = boost > 0
                sup += int(s.sum())
                head += int((s & (pclamp < 0.99)).sum())
                seen += 1
                if seen >= args.n_subgraphs:
                    break
            if seen >= args.n_subgraphs:
                break

    print(f"\n=== over {seen} subgraphs, {tot} node-pair entries ===")
    print(f"  attention in graded band (0.01,0.99) : {pct(graded, tot)}")
    print(f"  attention at 0.99 ceiling            : {pct(ceil_, tot)}")
    print(f"  rule-supported pairs                 : {sup} ({pct(sup, tot)})")
    print(f"  rule-supported WITH headroom (p<.99) : {head} ({pct(head, sup)} of supported)")

    # end-to-end: does the output change?
    batch = next(iter(loader))

    def fwd(use, w):
        model.params.use_rule_trust = use
        model.gsl.use_rule_trust = use
        model.gsl.rule_weight = w
        torch.manual_seed(SEED)
        (dp, _x, _y, _z) = move_batch_to_device_dgl(batch, device)
        with torch.no_grad():
            out, _ = model(dp)
        return out.detach().float().cpu()

    off = fwd(False, 0.0)
    on = fwd(True, args.rule_weight)
    d = (on - off).abs()
    print(f"\n=== end-to-end output delta (rule_weight={args.rule_weight}, seed fixed) ===")
    print(f"  logits changed: {int((d > 0).sum())}/{d.numel()}   max|d|={d.max():.6f}  mean|d|={d.mean():.6f}")

    zero = (fwd(True, 0.0) - off).abs().max().item()
    print(f"  baseline-equivalence check (rule_weight=0 must be 0.0): {zero:.6f}")

    if head == 0:
        print("\nVERDICT: FAIL. Rule-supported pairs are already at the ceiling. Boosting them")
        print("cannot change the graph. The prior is redundant with the neural attention.")
    elif d.max().item() == 0.0:
        print("\nVERDICT: FAIL. Headroom exists but output did not change.")
    else:
        print("\nVERDICT: PASS. Rules cover the graph, have headroom, and change the output.")


if __name__ == "__main__":
    main()

"""Diagnostic: measure the real distribution of GraphLearner attention values.

Purpose: RuleTrust injects a prior into `attention` before `build_prob_neighbourhood`
clamps it to [0.01, 0.99]. If attention is already saturated above 0.99, then neither a
centered nor a boost-only additive prior can change the sampled adjacency, and any
ablation would be a false negative.

This measures, on the TRAINED baseline checkpoint and REAL WN18RR_v1 subgraphs, what
fraction of attention entries land below 0.01, inside (0.01, 0.99), or above 0.99.

Read-only. Does not train. Does not modify any experiment artifact.
"""
import os
import torch
from torch.utils.data import DataLoader

from subgraph_extraction.datasets import SubgraphDataset
from utils.graph_utils import collate_dgl, move_batch_to_device_dgl
import dgl

MAIN_DIR = "/home/admin_wsl/research_kg/S2DN/SDN"
CKPT = os.path.join(MAIN_DIR, "experiments/sdn_wn_v1_gpu/best_graph_classifier.pth")
DATASET = "WN18RR_v1"
N_SUBGRAPHS = 40


def pct(x):
    return f"{100.0 * x:.2f}%"


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = torch.load(CKPT, map_location=device, weights_only=False)
    model.eval()
    p = model.params
    p.device = device

    print("=== model config ===")
    for k in ("metric_type", "graph_type", "num_pers", "emb_dim", "top_k", "feature_denoise"):
        print(f"  {k}: {getattr(p, k, '<unset>')}")

    db_path = os.path.join(MAIN_DIR, f"data/{DATASET}/subgraphs_en_True_neg_1_hop_3")
    file_paths = {
        "train": os.path.join(MAIN_DIR, f"data/{DATASET}/train.txt"),
        "valid": os.path.join(MAIN_DIR, f"data/{DATASET}/valid.txt"),
    }
    ds = SubgraphDataset(
        db_path, "train_pos", "train_neg", file_paths,
        add_traspose_rels=p.add_traspose_rels,
        num_neg_samples_per_link=p.num_neg_samples_per_link,
        use_kge_embeddings=False, dataset=DATASET,
        kge_model=p.kge_model, file_name="train",
    )
    loader = DataLoader(ds, batch_size=8, shuffle=False, num_workers=0, collate_fn=collate_dgl)

    gsl = model.gsl
    all_vals = []
    seen = 0

    with torch.no_grad():
        for batch in loader:
            (data_pos, _t_pos, _data_neg, _t_neg) = move_batch_to_device_dgl(batch, device)
            g, rel_labels = data_pos
            g.ndata["h"], _ = model.gnn(g)

            for graph in dgl.unbatch(g):
                ctx = graph.ndata["h"]
                if gsl.feature_denoise:
                    ctx = gsl.mask_feature(ctx)

                # replicate learn_adj's metric_type == 'attention' branch exactly
                attention = 0
                for i in range(len(gsl.linear_sims)):
                    fc = torch.relu(gsl.linear_sims[i](ctx))
                    attention = attention + torch.matmul(fc, fc.transpose(-1, -2))
                attention = attention / len(gsl.linear_sims)

                all_vals.append(attention.flatten().float().cpu())
                seen += 1
                if seen >= N_SUBGRAPHS:
                    break
            if seen >= N_SUBGRAPHS:
                break

    v = torch.cat(all_vals)
    n = v.numel()
    below = (v <= 0.01).sum().item() / n
    inside = ((v > 0.01) & (v < 0.99)).sum().item() / n
    above = (v >= 0.99).sum().item() / n

    print(f"\n=== attention distribution over {seen} real subgraphs, {n} entries ===")
    qs = torch.tensor([0.0, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0])
    for q, val in zip(qs.tolist(), torch.quantile(v, qs).tolist()):
        print(f"  q{q:<5} = {val:.4f}")
    print(f"  mean  = {v.mean():.4f}   std = {v.std():.4f}")

    print("\n=== behaviour under build_prob_neighbourhood's clamp(0.01, 0.99) ===")
    print(f"  clamped to floor 0.01 : {pct(below)}")
    print(f"  IN the graded band    : {pct(inside)}   <-- only here can an additive prior act")
    print(f"  clamped to ceil 0.99  : {pct(above)}")

    if inside < 0.05:
        print("\nVERDICT: attention is saturated. An additive prior (centered OR boost-only)")
        print("cannot move the adjacency. The prior must act BEFORE/INSTEAD OF this scale,")
        print("e.g. squash attention to a bounded score, or down-weight unsupported pairs.")
    else:
        print(f"\nVERDICT: {pct(inside)} of entries are in the graded band, so a boost-only")
        print("prior applied after the clamp CAN move the adjacency. Boost-only fix is valid.")


if __name__ == "__main__":
    main()

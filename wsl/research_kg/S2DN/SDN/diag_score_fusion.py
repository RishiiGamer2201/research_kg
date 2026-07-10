"""Verify the score-level RuleTrust fusion before any training run.

Checks, in order:
  1. baseline preserved: use_rule_trust=False output is unchanged by the new code path
  2. zero-init: with rule_scale=0 the fused output equals baseline exactly
  3. gradient: rule_scale receives a non-zero gradient (the symbolic term is connected)
  4. effect: with rule_scale != 0 the output moves, and moves UP on rule-supported examples

Any failure here means a training run would be wasted.
"""
import os
import torch
import dgl
from torch.utils.data import DataLoader

from subgraph_extraction.datasets import SubgraphDataset
from utils.graph_utils import collate_dgl, move_batch_to_device_dgl
from utils.rule_miner import mine_rules
from utils.rule_features import rules_to_index, build_rule_target_score

MAIN_DIR = "/home/admin_wsl/research_kg/S2DN/SDN"
DATASET = "fb237_v1"
CKPT = os.path.join(MAIN_DIR, "experiments/sdn_fb_v1_paper_gpu/best_graph_classifier.pth")
SEED = 7


def fwd(model, batch, device):
    torch.manual_seed(SEED)
    (dp, _a, _b, _c) = move_batch_to_device_dgl(batch, device)
    return model(dp)


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = torch.load(CKPT, map_location=device, weights_only=False)
    model.eval()
    p = model.params
    p.device = device

    file_paths = {
        "train": os.path.join(MAIN_DIR, f"data/{DATASET}/train.txt"),
        "valid": os.path.join(MAIN_DIR, f"data/{DATASET}/valid.txt"),
    }
    ds = SubgraphDataset(
        os.path.join(MAIN_DIR, f"data/{DATASET}/subgraphs_en_True_neg_1_hop_3"),
        "train_pos", "train_neg", file_paths,
        add_traspose_rels=p.add_traspose_rels,
        num_neg_samples_per_link=p.num_neg_samples_per_link,
        use_kge_embeddings=False, dataset=DATASET, kge_model=p.kge_model, file_name="train",
    )
    relation2id = {rel: idx for idx, rel in ds.id2relation.items()}
    rules = mine_rules(file_paths["train"], relation2id, min_support=2, conf_threshold=0.1)
    model.rule_index = rules_to_index(rules, 0.1)
    model.rule_mode = "score"
    if not hasattr(model, "rule_scale"):
        model.rule_scale = torch.nn.Parameter(torch.zeros(1, device=device))
    model.rule_scale.data.zero_()

    batch = next(iter(DataLoader(ds, batch_size=16, shuffle=False, num_workers=0, collate_fn=collate_dgl)))

    # 1 + 2: baseline vs zero-init fusion
    p.use_rule_trust = False
    with torch.no_grad():
        base, _ = fwd(model, batch, device)
    p.use_rule_trust = True
    with torch.no_grad():
        zero_init, _ = fwd(model, batch, device)
    d0 = (zero_init - base).abs().max().item()
    print(f"[1+2] zero-init fusion vs baseline: max|delta| = {d0:.8f}  "
          f"{'PASS' if d0 < 1e-5 else 'FAIL'}")

    # 3: gradient reaches rule_scale
    model.rule_scale.grad = None
    out, _ = fwd(model, batch, device)
    out.sum().backward()
    g = model.rule_scale.grad
    gval = float(g.abs().sum()) if g is not None else 0.0
    print(f"[3] rule_scale.grad = {None if g is None else float(g)}  "
          f"{'PASS' if gval > 0 else 'FAIL (symbolic term is disconnected)'}")

    # 4: nonzero weight moves the output, and lifts rule-supported examples
    model.rule_scale.data.fill_(1.0)
    with torch.no_grad():
        boosted, _ = fwd(model, batch, device)
    delta = (boosted - base).squeeze(-1)

    # recompute which examples actually have rule support
    (dp, _a, _b, _c) = move_batch_to_device_dgl(batch, device)
    g_b, rl = dp
    g_b.ndata["h"], _ = model.gnn(g_b)
    supp = []
    for graph, r in zip(dgl.unbatch(g_b), rl.detach().cpu().tolist()):
        h = (graph.ndata["id"] == 1).nonzero().squeeze(1)
        t = (graph.ndata["id"] == 2).nonzero().squeeze(1)
        hi = int(h[0]) if h.numel() else None
        ti = int(t[0]) if t.numel() else None
        supp.append(float(build_rule_target_score(graph, r, model.rule_index, hi, ti)))
    supp = torch.tensor(supp, device=delta.device)

    n_sup = int((supp > 0).sum())
    moved = int((delta.abs() > 1e-6).sum())
    print(f"[4] rule-supported examples: {n_sup}/{len(supp)}; outputs moved: {moved}")
    if n_sup:
        lifted = int(((supp > 0) & (delta > 0)).sum())
        print(f"    supported examples lifted upward: {lifted}/{n_sup} "
              f"{'PASS' if lifted == n_sup else 'FAIL'}")
        unsup_moved = int(((supp == 0) & (delta.abs() > 1e-6)).sum())
        print(f"    unsupported examples moved: {unsup_moved} "
              f"{'PASS (must be 0)' if unsup_moved == 0 else 'FAIL'}")
    else:
        print("    no rule-supported examples in this batch; rerun with a larger batch")


if __name__ == "__main__":
    main()

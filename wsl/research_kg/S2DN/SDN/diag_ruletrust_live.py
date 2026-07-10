"""Liveness proof for the RuleTrust prior.

A smoke test proves the code executes. This proves the prior has an EFFECT:
  1. deterministic: how many refined-adjacency probabilities change when the boost is applied
  2. end-to-end: whether the model's output logits change, with sampling noise held fixed

If `prob-changed` is 0, or the logit delta is 0, the prior is inert and any ablation from
that configuration is a false negative. Run this before spending GPU on a full ablation.

Read-only. Does not train. Does not write to any experiment directory.
"""
import os
os.environ.setdefault("RULETRUST_DEBUG", "6")

import torch
from torch.utils.data import DataLoader

from subgraph_extraction.datasets import SubgraphDataset
from utils.graph_utils import collate_dgl, move_batch_to_device_dgl
from utils.rule_features import load_rule_index
from model.dgl.layers import GraphLearner

MAIN_DIR = "/home/admin_wsl/research_kg/S2DN/SDN"
CKPT = os.path.join(MAIN_DIR, "experiments/sdn_wn_v1_gpu/best_graph_classifier.pth")
DATASET = "WN18RR_v1"
RULES = os.path.join(MAIN_DIR, f"data/{DATASET}/ruletrust_rules.json")
SEED = 12345


def forward_once(model, batch, device, use_rule_trust, rule_weight):
    model.params.use_rule_trust = use_rule_trust
    model.gsl.use_rule_trust = use_rule_trust
    model.gsl.rule_weight = rule_weight
    torch.manual_seed(SEED)  # hold RelaxedBernoulli sampling noise fixed across conditions
    (data_pos, _tp, _dn, _tn) = move_batch_to_device_dgl(batch, device)
    with torch.no_grad():
        out, _kl = model(data_pos)
    return out.detach().float().cpu()


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = torch.load(CKPT, map_location=device, weights_only=False)
    model.eval()
    p = model.params
    p.device = device
    p.rule_conf_threshold = getattr(p, "rule_conf_threshold", 0.1)

    rule_index = load_rule_index(RULES, p.rule_conf_threshold)
    model.rule_index = rule_index
    n_rules = sum(len(v) for v in rule_index.values())
    print(f"rules loaded: {n_rules} over {len(rule_index)} head relations "
          f"(conf_threshold={p.rule_conf_threshold})")
    if n_rules == 0:
        print("FAIL: no rules loaded; nothing to inject.")
        return

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
    batch = next(iter(DataLoader(ds, batch_size=8, shuffle=False, num_workers=0, collate_fn=collate_dgl)))

    print("\n=== per-subgraph effect of the boost (deterministic, pre-sampling) ===")
    GraphLearner._rule_debug_left = int(os.environ["RULETRUST_DEBUG"])
    out_on = forward_once(model, batch, device, True, rule_weight=0.5)

    GraphLearner._rule_debug_left = 0  # silence during the baseline pass
    out_off = forward_once(model, batch, device, False, rule_weight=0.5)

    delta = (out_on - out_off).abs()
    print("\n=== end-to-end effect on model output (same seed, so noise is held fixed) ===")
    print(f"  logits changed : {int((delta > 0).sum())}/{delta.numel()}")
    print(f"  max |delta|    : {delta.max().item():.6f}")
    print(f"  mean |delta|   : {delta.mean().item():.6f}")

    print("\n=== rule_weight sweep (mean |delta| vs baseline) ===")
    for w in (0.0, 0.1, 0.25, 0.5, 1.0):
        o = forward_once(model, batch, device, True, rule_weight=w)
        d = (o - out_off).abs().mean().item()
        print(f"  rule_weight={w:<5} mean|delta|={d:.6f}")

    if delta.max().item() == 0.0:
        print("\nVERDICT: FAIL. Prior does not change the output. Do not run an ablation.")
    else:
        print("\nVERDICT: PASS. The prior is live and changes the refined graph and the output.")
        print("rule_weight=0.0 must give delta 0.0 (that is the baseline-equivalence check).")


if __name__ == "__main__":
    main()

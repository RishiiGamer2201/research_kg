import json
from collections import defaultdict

import torch


def load_rule_index(cache_path, conf_threshold=0.0):
    if not cache_path:
        return {}
    with open(cache_path) as f:
        payload = json.load(f)

    rule_index = defaultdict(list)
    for rule in payload.get("rules", []):
        confidence = float(rule["confidence"])
        if confidence < conf_threshold:
            continue
        r1, r2 = rule["body"]
        rule_index[int(rule["head"])].append((int(r1), int(r2), confidence))
    return dict(rule_index)


def build_rule_boost(graph, target_rel, rule_index):
    """Dense (N, N) boost-only rule support for one enclosing subgraph.

    entry[i, j] = max confidence over mined rules (r1, r2) -> target_rel such that a
    typed length-2 path i --r1--> m --r2--> j exists in this subgraph. 0.0 when no rule
    supports the pair.

    Boost-only by construction: unsupported pairs get exactly 0.0 and are never penalised.
    An earlier version centred this at 0.5 and returned (conf - 0.5), which pushed pairs
    supported by sub-0.5-confidence rules BELOW unsupported pairs. That was a sign error.

    Fully vectorised: composes per-relation adjacencies with matmul instead of looping
    over edges in Python. The previous implementation did triple-nested Python loops with
    per-element GPU scalar writes and .tolist() host syncs on every forward pass.
    """
    num_nodes = graph.number_of_nodes()
    device = graph.device
    boost = torch.zeros((num_nodes, num_nodes), device=device)

    rules = rule_index.get(int(target_rel), ())
    if not rules or graph.number_of_edges() == 0:
        return boost

    src_nodes, dst_nodes = graph.edges()
    rel_types = graph.edata["type"]

    needed = set()
    for r1, r2, _ in rules:
        needed.add(r1)
        needed.add(r2)

    # one dense typed adjacency per relation that appears in a rule body
    adj = {}
    for rel in needed:
        mask = rel_types == rel
        a = torch.zeros((num_nodes, num_nodes), device=device)
        # empty mask yields an empty index assignment, which is a no-op
        a[src_nodes[mask], dst_nodes[mask]] = 1.0
        adj[rel] = a

    for r1, r2, confidence in rules:
        reach = adj[r1] @ adj[r2]  # >0 exactly where a typed length-2 path exists
        support = (reach > 0).to(boost.dtype) * float(confidence)
        boost = torch.maximum(boost, support)

    return boost

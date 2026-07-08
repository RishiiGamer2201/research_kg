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


def build_rule_prior(graph, target_rel, rule_index, default_prior=0.5):
    num_nodes = graph.number_of_nodes()
    device = graph.device
    prior = torch.full((num_nodes, num_nodes), float(default_prior), device=device)
    rules = rule_index.get(int(target_rel), ())
    if not rules or graph.number_of_edges() == 0:
        return prior

    src_nodes, dst_nodes = graph.edges()
    rel_types = graph.edata["type"].tolist()
    out_edges = defaultdict(lambda: defaultdict(list))
    for src, dst, rel in zip(src_nodes.tolist(), dst_nodes.tolist(), rel_types):
        out_edges[int(rel)][int(src)].append(int(dst))

    for r1, r2, confidence in rules:
        for src, mids in out_edges.get(r1, {}).items():
            for mid in mids:
                for dst in out_edges.get(r2, {}).get(mid, ()):
                    if confidence > prior[src, dst]:
                        prior[src, dst] = confidence

    return prior

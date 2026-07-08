import json
import os
from collections import defaultdict


def _read_triples(train_path, relation2id):
    triples = []
    with open(train_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 3:
                continue
            head, rel, tail = parts
            if rel in relation2id:
                triples.append((head, relation2id[rel], tail))
    return triples


def mine_length2_rules(train_path, relation2id, min_support=2, conf_threshold=0.1):
    triples = _read_triples(train_path, relation2id)
    rel_edges = defaultdict(set)
    out_by_rel = defaultdict(lambda: defaultdict(set))

    for head, rel, tail in triples:
        rel_edges[rel].add((head, tail))
        out_by_rel[rel][head].add(tail)

    body_pairs = {}
    for r1 in relation2id.values():
        for r2 in relation2id.values():
            pairs = set()
            for head, mids in out_by_rel[r1].items():
                for mid in mids:
                    for tail in out_by_rel[r2].get(mid, ()):
                        pairs.add((head, tail))
            if pairs:
                body_pairs[(r1, r2)] = pairs

    rules = []
    for (r1, r2), pairs in body_pairs.items():
        body_count = len(pairs)
        for target_rel, target_edges in rel_edges.items():
            support = len(pairs & target_edges)
            if support < min_support:
                continue
            confidence = support / body_count
            if confidence >= conf_threshold:
                rules.append({
                    "body": [int(r1), int(r2)],
                    "head": int(target_rel),
                    "support": int(support),
                    "body_count": int(body_count),
                    "confidence": float(confidence),
                })

    rules.sort(key=lambda rule: (-rule["confidence"], -rule["support"], rule["head"], rule["body"]))
    return rules


def default_rule_cache_path(main_dir, dataset):
    return os.path.join(main_dir, "data", dataset, "ruletrust_rules.json")


def ensure_rule_cache(params, relation2id):
    cache_path = params.rule_cache or default_rule_cache_path(params.main_dir, params.dataset)
    if os.path.exists(cache_path):
        return cache_path

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    rules = mine_length2_rules(
        params.file_paths["train"],
        relation2id,
        min_support=params.rule_min_support,
        conf_threshold=params.rule_conf_threshold,
    )
    payload = {
        "dataset": params.dataset,
        "train_file": params.file_paths["train"],
        "min_support": params.rule_min_support,
        "conf_threshold": params.rule_conf_threshold,
        "relation2id": relation2id,
        "rules": rules,
    }
    with open(cache_path, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return cache_path

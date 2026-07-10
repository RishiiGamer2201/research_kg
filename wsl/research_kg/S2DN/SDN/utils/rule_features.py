import json

import torch


def rules_to_index(rules, conf_threshold=0.0):
    """rule_index[head_rel] = [ (body_literals, confidence), ... ]

    body_literals is a tuple of (relation_id, inverted) pairs, length 1 or 2.
    """
    index = {}
    for rule in rules:
        confidence = float(rule["confidence"])
        if confidence < conf_threshold:
            continue
        body = tuple((int(r), bool(i)) for r, i in rule["body"])
        index.setdefault(int(rule["head"]), []).append((body, confidence))
    # highest confidence first: build_rule_target_score early-exits on this ordering
    for head in index:
        index[head].sort(key=lambda x: -x[1])
    return index


def load_rule_index(cache_path, conf_threshold=0.0):
    if not cache_path:
        return {}
    with open(cache_path) as f:
        payload = json.load(f)
    if payload.get("version") != 2:
        raise ValueError(
            f"{cache_path} is a v1 rule cache (forward-only, no inverse literals). "
            "Delete it and let ensure_rule_cache remine, or point --rule-cache at a v2 file."
        )
    return rules_to_index(payload.get("rules", []), conf_threshold)


def _literal_adjacency(num_nodes, src, dst, rel_types, relation, inverted, dtype, device):
    mask = rel_types == relation
    a = torch.zeros((num_nodes, num_nodes), dtype=dtype, device=device)
    # an empty mask yields an empty index assignment, which is a no-op
    if inverted:
        a[dst[mask], src[mask]] = 1.0
    else:
        a[src[mask], dst[mask]] = 1.0
    return a


def build_rule_target_score(graph, target_rel, rule_index, head_idx, tail_idx):
    """Max rule confidence supporting the single target pair (head_idx -> tail_idx).

    This is the signal that matters. Measured on fb237_v1: it fires on 36.1% of inductive
    test positives and 0.1% of negatives, and its AUC barely moves from train (0.690) to
    unseen entities (0.680) because rules are entity-independent. A dense N x N prior, by
    contrast, touches only 0.02% of node pairs and cannot steer Structure Refining.

    Only needs one row and one column, so it avoids the full N x N matmul.
    Returns a 0-dim tensor so autograd can flow to a learnable trust weight.
    """
    device = graph.device
    dtype = torch.float32
    best = torch.zeros((), dtype=dtype, device=device)

    rules = rule_index.get(int(target_rel), ())
    if not rules or graph.number_of_edges() == 0:
        return best
    if head_idx is None or tail_idx is None or int(head_idx) == int(tail_idx):
        return best

    src_nodes, dst_nodes = graph.edges()
    rel_types = graph.edata["type"]

    def successors(node, lit):
        """nodes y with node --lit--> y"""
        rel, inv = lit
        if inv:
            return src_nodes[(rel_types == rel) & (dst_nodes == node)]
        return dst_nodes[(rel_types == rel) & (src_nodes == node)]

    def predecessors(node, lit):
        """nodes x with x --lit--> node"""
        rel, inv = lit
        if inv:
            return dst_nodes[(rel_types == rel) & (src_nodes == node)]
        return src_nodes[(rel_types == rel) & (dst_nodes == node)]

    # Edge-list based, not dense: a dense N x N adjacency per literal would allocate
    # hundreds of MB per batch on FB15k-237 subgraphs just to read one row and column.
    succ_cache, pred_cache = {}, {}
    best_val = 0.0
    for body, confidence in rules:
        if confidence <= best_val:
            continue  # rules are confidence-sorted; nothing better remains
        if len(body) == 1:
            if body[0] not in succ_cache:
                succ_cache[body[0]] = successors(head_idx, body[0])
            hit = bool((succ_cache[body[0]] == tail_idx).any())
        else:
            if body[0] not in succ_cache:
                succ_cache[body[0]] = successors(head_idx, body[0])
            if body[1] not in pred_cache:
                pred_cache[body[1]] = predecessors(tail_idx, body[1])
            mids_from_head = succ_cache[body[0]]
            mids_to_tail = pred_cache[body[1]]
            if mids_from_head.numel() == 0 or mids_to_tail.numel() == 0:
                hit = False
            else:
                hit = bool(torch.isin(mids_from_head, mids_to_tail).any())
        if hit:
            best_val = confidence

    return torch.full((), float(best_val), dtype=dtype, device=device)


def build_rule_boost(graph, target_rel, rule_index):
    """Dense (N, N) boost-only rule support for one enclosing subgraph.

    entry[i, j] = max confidence over mined rules whose body path connects i to j in this
    subgraph. 0.0 when no rule supports the pair.

    Boost-only by construction: unsupported pairs get exactly 0.0 and are never penalised.
    An earlier version centred this at 0.5 and returned (conf - 0.5), which pushed pairs
    supported by sub-0.5-confidence rules BELOW unsupported pairs. That was a sign error;
    measured on WN18RR_v1, every mined rule had confidence below 0.5.

    Fully vectorised: composes typed literal adjacencies with matmul rather than looping
    over edges in Python.
    """
    num_nodes = graph.number_of_nodes()
    device = graph.device
    dtype = torch.float32
    boost = torch.zeros((num_nodes, num_nodes), dtype=dtype, device=device)

    rules = rule_index.get(int(target_rel), ())
    if not rules or graph.number_of_edges() == 0:
        return boost

    src_nodes, dst_nodes = graph.edges()
    rel_types = graph.edata["type"]

    needed = set()
    for body, _ in rules:
        needed.update(body)

    adj = {
        lit: _literal_adjacency(num_nodes, src_nodes, dst_nodes, rel_types,
                                lit[0], lit[1], dtype, device)
        for lit in needed
    }

    eye = torch.eye(num_nodes, dtype=torch.bool, device=device)
    for body, confidence in rules:
        if len(body) == 1:
            reach = adj[body[0]]
        else:
            reach = adj[body[0]] @ adj[body[1]]
        support = (reach > 0) & ~eye  # mining excluded self-pairs; mirror that here
        boost = torch.maximum(boost, support.to(dtype) * float(confidence))

    return boost

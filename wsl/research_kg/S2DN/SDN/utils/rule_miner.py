"""Rule mining for RuleTrust.

Rule language (AnyBURL-inspired, kept in Python to avoid a Java dependency):
  length 1:  (x, l1, y)                -> (x, target, y)
  length 2:  (x, l1, z) & (z, l2, y)   -> (x, target, y)
where each literal l = (relation, inverted). An inverted literal traverses an edge
backwards, so `(x, r^-1, y)` means the triple `(y, r, x)` exists.

Why inverses and length-1 matter: the original miner only matched forward r1 then
forward r2 paths, with no inverse traversal. Measured on fb237_v1, that produced 98
rules covering 0.01 percent of enclosing-subgraph node pairs, far too sparse for the
Structure Refining prior to have any effect. Enclosing subgraphs are directed, so
requiring two forward hops almost never matches.

Rule dict format (v2):
  {"body": [[rel, inv], ...], "head": rel, "support": int, "body_count": int,
   "confidence": float}
"""
import json
import os
import hashlib
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


def _literal_adjacency(triples, relation2id, use_inverse):
    """out[(rel, inv)][src] = set(dst). inv=True traverses the edge backwards."""
    out = defaultdict(lambda: defaultdict(set))
    for head, rel, tail in triples:
        out[(rel, False)][head].add(tail)
        if use_inverse:
            out[(rel, True)][tail].add(head)
    return out


def _pairs_of(literal_out):
    return {(h, t) for h, tails in literal_out.items() for t in tails if h != t}


def _compose(out_l1, out_l2):
    pairs = set()
    for src, mids in out_l1.items():
        for mid in mids:
            for dst in out_l2.get(mid, ()):
                if src != dst:
                    pairs.add((src, dst))
    return pairs


def _score_body(pairs, pair2rels, min_support, conf_threshold, body, rules, skip_identity_head=None):
    body_count = len(pairs)
    if body_count < min_support:
        return
    counts = defaultdict(int)
    for pair in pairs:
        for rel in pair2rels.get(pair, ()):
            counts[rel] += 1
    for target_rel, support in counts.items():
        if support < min_support:
            continue
        if skip_identity_head is not None and target_rel == skip_identity_head:
            continue  # body literal IS the head relation, forward: a trivial identity rule
        confidence = support / body_count
        if confidence < conf_threshold:
            continue
        rules.append({
            "body": [[int(r), bool(i)] for r, i in body],
            "head": int(target_rel),
            "support": int(support),
            "body_count": int(body_count),
            "confidence": float(confidence),
        })


def mine_rules(train_path, relation2id, min_support=2, conf_threshold=0.1,
               max_len=2, use_inverse=True):
    triples = _read_triples(train_path, relation2id)

    rel_edges = defaultdict(set)
    pair2rels = defaultdict(set)
    for head, rel, tail in triples:
        rel_edges[rel].add((head, tail))
        pair2rels[(head, tail)].add(rel)

    out = _literal_adjacency(triples, relation2id, use_inverse)
    literals = [lit for lit in out if len(out[lit]) > 0]

    rules = []

    # length-1 bodies
    lit_pairs = {}
    for lit in literals:
        pairs = _pairs_of(out[lit])
        if len(pairs) < min_support:
            continue
        lit_pairs[lit] = pairs
        rel, inv = lit
        # a forward literal equal to the head relation is the identity rule; skip that head only
        _score_body(pairs, pair2rels, min_support, conf_threshold, [lit], rules,
                    skip_identity_head=(rel if not inv else None))

    # length-2 bodies
    if max_len >= 2:
        for l1 in lit_pairs:
            for l2 in lit_pairs:
                pairs = _compose(out[l1], out[l2])
                _score_body(pairs, pair2rels, min_support, conf_threshold, [l1, l2], rules)

    rules.sort(key=lambda r: (-r["confidence"], -r["support"], r["head"], len(r["body"])))
    return rules


# Backwards-compatible alias for the old forward-only length-2 miner.
def mine_length2_rules(train_path, relation2id, min_support=2, conf_threshold=0.1):
    return mine_rules(train_path, relation2id, min_support=min_support,
                      conf_threshold=conf_threshold, max_len=2, use_inverse=False)


def rule_signature(dataset, train_file, min_support, conf_threshold, max_len,
                   use_inverse, relation2id, target_policy):
    """P0.4: a cache key over everything that changes the mined rules — dataset/fold,
    train file, mining params, the relation map, and the target-edge policy. Two runs
    with different settings get different signatures, so a stale cache is never reused."""
    blob = json.dumps({
        "dataset": dataset, "train_file": train_file,
        "min_support": min_support, "conf_threshold": conf_threshold,
        "max_len": max_len, "use_inverse": use_inverse,
        "relation2id": relation2id, "target_policy": target_policy,
    }, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def default_rule_cache_path(main_dir, dataset, sig=None):
    # v2: rule format carries an inverse flag. The signature suffix keys the cache to the
    # exact mining settings + relation map + target policy so different runs never collide.
    name = f"ruletrust_rules_v2_{sig}.json" if sig else "ruletrust_rules_v2.json"
    return os.path.join(main_dir, "data", dataset, name)


def ensure_rule_cache(params, relation2id):
    min_support = params.rule_min_support
    conf_threshold = params.rule_conf_threshold
    max_len = getattr(params, "rule_max_len", 2)
    use_inverse = getattr(params, "rule_use_inverse", True)
    # target-edge policy: the query's own edge must be excluded when rules score it.
    # Removal happens in the RuleTrust scorer (P2.6); recorded here so caches invalidate
    # if the policy changes. Default 'none' = global train-graph mining (current behaviour).
    target_policy = getattr(params, "rule_target_policy", "none")
    train_file = params.file_paths["train"]
    sig = rule_signature(params.dataset, train_file, min_support, conf_threshold,
                         max_len, use_inverse, relation2id, target_policy)
    cache_path = params.rule_cache or default_rule_cache_path(params.main_dir, params.dataset, sig)

    if os.path.exists(cache_path):
        try:
            payload = json.load(open(cache_path))
            if payload.get("signature") == sig:
                return cache_path
            # signature mismatch -> settings/relation-map/train changed: reject stale, re-mine.
        except Exception:
            pass  # unreadable cache -> re-mine

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    rules = mine_rules(
        train_file, relation2id,
        min_support=min_support, conf_threshold=conf_threshold,
        max_len=max_len, use_inverse=use_inverse,
    )
    payload = {
        "version": 2,
        "signature": sig,
        "dataset": params.dataset,
        "train_file": train_file,
        "min_support": min_support,
        "conf_threshold": conf_threshold,
        "max_len": max_len,
        "use_inverse": use_inverse,
        "target_policy": target_policy,
        "relation2id": relation2id,
        "rules": rules,
    }
    with open(cache_path, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return cache_path


def _selfcheck():
    """P0.4 runnable check: stale rule caches are rejected on any setting change."""
    import tempfile, shutil
    from types import SimpleNamespace
    d = tempfile.mkdtemp(prefix="rulecache_test_")
    try:
        train = os.path.join(d, "train.txt")
        with open(train, "w") as f:
            f.write("a born_in b\nb located_in c\na born_in c\n")
        rel2id = {"born_in": 0, "located_in": 1}
        def mk(**kw):
            base = dict(main_dir=d, dataset="toy", rule_cache=None,
                        file_paths={"train": train}, rule_min_support=1,
                        rule_conf_threshold=0.0, rule_max_len=2, rule_use_inverse=True)
            base.update(kw)
            return SimpleNamespace(**base)

        p1 = ensure_rule_cache(mk(), rel2id)
        s1 = json.load(open(p1))["signature"]
        # unchanged settings -> same cache path reused
        assert ensure_rule_cache(mk(), rel2id) == p1

        # change a mining param -> different signature + path (old cache NOT reused)
        p2 = ensure_rule_cache(mk(rule_min_support=2), rel2id)
        assert p2 != p1, "min_support change must produce a new cache"

        # change the relation map -> different signature
        p3 = ensure_rule_cache(mk(), {"born_in": 5, "located_in": 6})
        assert p3 != p1, "relation-map change must produce a new cache"

        # corrupt signature in a cache -> rejected and re-mined
        payload = json.load(open(p1)); payload["signature"] = "deadbeef"; payload["rules"] = []
        json.dump(payload, open(p1, "w"))
        ensure_rule_cache(mk(), rel2id)
        assert json.load(open(p1))["signature"] == s1, "stale/corrupt cache must be rebuilt"
        print("rule_miner cache self-check OK (stale caches rejected)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    _selfcheck()

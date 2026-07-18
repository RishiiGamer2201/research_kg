"""Immutable run manifests (Phase 0 / P0.2).

Every train/eval run writes a manifest.json that pins the exact code, inputs,
environment, and evaluator state so no two runs are ever compared by accident.

Rules:
- SHA-256 every input artifact (split, descriptions, relation map, candidates, filter, checkpoint).
- Atomic write; refuse to overwrite an existing *complete/valid* manifest in the same run dir.
- status in {running, complete, failed, invalidated}; carry parent_run_id / invalidates_run_id.

Design note: kept dependency-free (stdlib only) so it imports in any of the divergent venvs.
Self-check: `python3 run_manifest.py` (asserts a one-byte input change flips the manifest hash).
"""
import os, sys, json, time, uuid, socket, hashlib, subprocess, tempfile, platform

MANIFEST_NAME = "manifest.json"


# ── hashing ─────────────────────────────────────────────────────────────────
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    """Content hash of a file, or None if it does not exist."""
    if not path or not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj) -> str:
    """Order-independent hash of a JSON-able object (sorted keys, compact)."""
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def hash_inputs(paths: dict) -> dict:
    """Map {logical_name: filepath} -> {logical_name: sha256|None}."""
    return {k: sha256_file(v) for k, v in paths.items()}


# Bump when the negative-sampling POLICY changes semantics (not just its parameters).
# v1 = negatives drawn from every entity (LEAKY for inductive claims, see ledger R-038)
# v2 = negatives restricted to the fold's training entities
NEGATIVE_POLICY_VERSION = "negpol-v2-train-only"


def token_cache_key(*, model_name, desc_path, fold, candidate_universe, filter_hash,
                    negative_policy=NEGATIVE_POLICY_VERSION, hard_neg_k=None, max_length=None,
                    reciprocal=None, extra=None):
    """Complete cache key for tokenized/negative caches.

    Must pin EVERYTHING that changes what a cached tensor means: encoder, description-view
    CONTENT, fold, the training-candidate universe (negative pool) content, the complete
    known-fact filter, the negative-sampling policy version, K, sequence length and whether
    reciprocal examples are included. Model/fold/view alone is insufficient — two runs with
    different negative pools or filters would otherwise share a cache.

    `candidate_universe`: list/iterable of entity ids OR a path to a persisted id list.
    Returns a short hex digest suitable for embedding in a filename.
    """
    if isinstance(candidate_universe, (str, bytes, os.PathLike)) and os.path.exists(candidate_universe):
        cand_hash = sha256_file(candidate_universe)
    elif candidate_universe is None:
        cand_hash = None
    else:
        cand_hash = sha256_json(sorted(int(x) for x in candidate_universe))
    payload = {
        "model_name": model_name,
        "desc_hash": sha256_file(desc_path) if desc_path else None,
        "fold": (os.path.basename(str(fold).rstrip("/")) if fold else None),
        "candidate_universe_hash": cand_hash,
        "filter_hash": filter_hash,
        "negative_policy": negative_policy,
        "hard_neg_k": hard_neg_k,
        "max_length": max_length,
        "reciprocal": reciprocal,
        "extra": extra or {},
    }
    return sha256_json(payload)[:16], payload


# ── environment / provenance ──────────────────────────────────────────────────
def _git(args, cwd):
    try:
        return subprocess.check_output(["git", "-C", cwd] + args,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def _repo_dir():
    # module may be imported via a symlink; resolve to the real repo path.
    return os.path.dirname(os.path.realpath(__file__))


def collect_env(seed=None) -> dict:
    repo = _repo_dir()
    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "git_commit": _git(["rev-parse", "HEAD"], repo),
        "git_dirty": bool(_git(["status", "--porcelain"], repo)),
        "command": " ".join([os.path.basename(sys.executable)] + sys.argv),
        "seed": seed,
        "gpu": None,
        "torch": None, "transformers": None, "peft": None,
        "model_revision": None, "tokenizer_revision": None,
    }
    try:
        import torch
        env["torch"] = torch.__version__
        env["cuda"] = getattr(torch.version, "cuda", None)
        if torch.cuda.is_available():
            env["gpu"] = torch.cuda.get_device_name(0)
    except Exception:
        pass
    for mod in ("transformers", "peft"):
        try:
            env[mod] = __import__(mod).__version__
        except Exception:
            pass
    return env


def model_snapshot_revision(model_name):
    """Best-effort HF cache commit hash for a model; None if unavailable/unpinned."""
    try:
        from huggingface_hub import scan_cache_dir
        for repo in scan_cache_dir().repos:
            if repo.repo_id == model_name:
                revs = sorted(repo.revisions, key=lambda r: r.last_modified, reverse=True)
                return revs[0].commit_hash if revs else None
    except Exception:
        return None
    return None


# ── read / write ──────────────────────────────────────────────────────────────
def _atomic_write(path, obj):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
        os.replace(tmp, path)  # atomic on POSIX and Windows
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def load_manifest(run_dir):
    p = os.path.join(run_dir, MANIFEST_NAME)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def start_run(run_dir, kind, inputs, *, seed=None, model_name=None,
              parent_run_id=None, invalidates_run_id=None, extra=None):
    """Create run_dir manifest with status=running. Refuse to clobber a live/complete one.

    kind: 'train' | 'eval' | 'detector' | ...
    inputs: {logical_name: filepath} of every artifact whose bytes must pin the run.
    Returns the manifest dict (also written to disk).
    """
    os.makedirs(run_dir, exist_ok=True)
    existing = load_manifest(run_dir)
    if existing and existing.get("status") in ("running", "complete"):
        raise FileExistsError(
            f"{run_dir} already has a {existing['status']} manifest "
            f"(run_id={existing.get('run_id')}); refusing to overwrite. "
            f"Use a new run dir or set status=invalidated first.")
    env = collect_env(seed=seed)
    if model_name:
        env["model_name"] = model_name
        env["model_revision"] = model_snapshot_revision(model_name)
        env["tokenizer_revision"] = env["model_revision"]
    manifest = {
        "run_id": f"{time.strftime('%Y%m%d_%H%M%S', time.gmtime())}_{uuid.uuid4().hex[:8]}",
        "kind": kind,
        "status": "running",
        "parent_run_id": parent_run_id,
        "invalidates_run_id": invalidates_run_id,
        "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "end_utc": None,
        "env": env,
        "input_hashes": hash_inputs(inputs),
        "input_paths": inputs,
        "metrics": None,
        "extra": extra or {},
    }
    _atomic_write(os.path.join(run_dir, MANIFEST_NAME), manifest)
    return manifest


def finish_run(run_dir, status="complete", metrics=None, checkpoint_path=None, extra=None):
    """Mark a run complete/failed and attach metrics + checkpoint hash."""
    m = load_manifest(run_dir)
    if m is None:
        raise FileNotFoundError(f"no manifest in {run_dir}")
    m["status"] = status
    m["end_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if metrics is not None:
        m["metrics"] = metrics
    if checkpoint_path:
        m.setdefault("input_hashes", {})["checkpoint"] = sha256_file(checkpoint_path)
    if extra:
        m["extra"].update(extra)
    _atomic_write(os.path.join(run_dir, MANIFEST_NAME), m)
    return m


# ── self-check ────────────────────────────────────────────────────────────────
def _selfcheck():
    import shutil
    d = tempfile.mkdtemp(prefix="manifest_test_")
    try:
        f = os.path.join(d, "split.txt")
        with open(f, "w") as fh:
            fh.write("a b c\n")
        rd = os.path.join(d, "run1")
        m1 = start_run(rd, "train", {"split": f}, seed=42, model_name=None)
        assert m1["status"] == "running"
        h1 = m1["input_hashes"]["split"]

        # refuse to overwrite a running/complete manifest
        try:
            start_run(rd, "train", {"split": f})
            raise AssertionError("expected FileExistsError on re-start")
        except FileExistsError:
            pass

        finish_run(rd, "complete", metrics={"mrr": 12.3})
        assert load_manifest(rd)["status"] == "complete"
        assert load_manifest(rd)["metrics"]["mrr"] == 12.3

        # one-byte input change must flip the hash in a fresh run dir
        with open(f, "a") as fh:
            fh.write("d\n")
        rd2 = os.path.join(d, "run2")
        m2 = start_run(rd2, "train", {"split": f})
        assert m2["input_hashes"]["split"] != h1, "hash must change when input bytes change"

        # missing input hashes to None (not a crash)
        rd3 = os.path.join(d, "run3")
        m3 = start_run(rd3, "eval", {"ghost": os.path.join(d, "nope.json")})
        assert m3["input_hashes"]["ghost"] is None

        # ── token_cache_key: every pinned component must change the key ──────────
        desc = os.path.join(d, "desc.json")
        with open(desc, "w") as fh:
            fh.write('{"1":"a"}')
        base = dict(model_name="BAAI/bge-m3", desc_path=desc, fold="/x/fold0_seed13",
                    candidate_universe=[1, 2, 3], filter_hash="fh1",
                    hard_neg_k=7, max_length=160, reciprocal=True)
        k0, _ = token_cache_key(**base)
        for field, newval in [("model_name", "bert-base"), ("fold", "/x/fold1_seed42"),
                              ("candidate_universe", [1, 2, 3, 4]), ("filter_hash", "fh2"),
                              ("negative_policy", "negpol-v1-all-entities"),
                              ("hard_neg_k", 3), ("max_length", 96), ("reciprocal", False)]:
            kv = dict(base); kv[field] = newval
            assert token_cache_key(**kv)[0] != k0, f"cache key ignores {field}"
        # description CONTENT change must change the key too
        with open(desc, "w") as fh:
            fh.write('{"1":"b"}')
        assert token_cache_key(**base)[0] != k0, "cache key ignores description content"
        # candidate universe accepted as a persisted file, order-independent
        cu = os.path.join(d, "cands.json")
        json.dump([3, 1, 2], open(cu, "w"))
        kf, _ = token_cache_key(**{**base, "candidate_universe": cu})
        assert isinstance(kf, str) and len(kf) == 16

        # git commit captured (repo is a git tree)
        assert m1["env"]["git_commit"], "expected a git commit hash"
        print("run_manifest self-check OK  (git_commit=%s dirty=%s)"
              % (m1["env"]["git_commit"][:8], m1["env"]["git_dirty"]))
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    _selfcheck()

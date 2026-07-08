# WSL Snapshot

This folder preserves the important WSL-side research workspace from:

`/home/admin_wsl/research_kg`

It is intentionally a curated snapshot, not a raw 1:1 copy. The original WSL workspace contains
large virtual environments, checkpoints, token caches, generated subgraph databases, and model
artifacts that are not suitable for GitHub.

Included:

- `research_kg/S2DN/`: S2DN reproduction code, compatibility patches, runner scripts, and logs.
- `research_kg/logs/s2dn_reproduction/`: S2DN reproduction environment report and WN18RR results.
- `research_kg/scripts/`: WSL helper scripts.
- `research_kg/DBP5L/`: DBP-5L scripts, configs, processed JSON/TXT artifacts needed to understand
  the earlier multilingual/self-healing work.
- `research_kg/RAA-KGC/`, `SimKGC_original/`, `ALIGNKGC/`, `KEnS/`, `CBLiP/`, `WN18RR/`: legacy
  scripts/configs and lightweight text artifacts preserved for continuity.

Excluded:

- Python virtual environments.
- model checkpoints and binary weights.
- generated token caches.
- generated LMDB/subgraph caches.
- very large training artifacts that can be regenerated.

The active S2DN reproduction plan is documented in:

`docs/pivot/IMPLEMENTATION_PLAN_S2DN_LADDER.md`

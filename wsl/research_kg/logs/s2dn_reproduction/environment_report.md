# S2DN Environment Report

Generated: 2026-07-07T21:39:06

## Status

- WSL GPU/NVML is working after `wsl --shutdown` restart.
- PyTorch in `venv_s2dn` sees CUDA, but the installed DGL 2.1 wheel is CPU-only.
- PyTorch 2.1.0 warns that RTX 5070 Ti `sm_120` is unsupported, so this env is for CPU correctness smoke tests.
- Tiny CPU smoke training completed for `WN18RR_v1` with `--max_links 20 --num_epochs 1`.

## Versions

- `wsl_user`: `admin_wsl`
- `python`: `Python 3.10.20`
- `torch`: `2.1.0+cu121 12.1 True`
- `dgl`: `2.1.0`
- `lmdb`: `2.2.1`
- `networkx`: `3.4.2`
- `numpy`: `1.26.4`
- `s2dn_commit`: `605809ae8fc6bba8d99f3ebc1346a7f41ab4c77f`
- `grail_commit`: `2a3dffa719518e7e6250e355a2fb37cd932de91e`

## NVIDIA-SMI

```text
Tue Jul  7 21:39:06 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 610.53                 KMD Version: 610.74        CUDA UMD Version: 13.3     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 5070 Ti     On  |   00000000:02:00.0 Off |                  N/A |
|  0%   39C    P8              8W /  300W |       0MiB /  16303MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|  No running processes found                                                             |
+-----------------------------------------------------------------------------------------+
```

## Compatibility Patches Applied To WSL S2DN Copy

- `subgraph_extraction/graph_sampler.py`: cast LMDB `map_size` to int.
- `subgraph_extraction/graph_sampler.py`: add 1 GB minimum LMDB map size.
- `subgraph_extraction/graph_sampler.py`: close LMDB writer env after subgraph generation.
- `subgraph_extraction/graph_sampler.py`: treat `--num_workers 0` as one worker for smoke tests.
- `subgraph_extraction/datasets.py`: use `max_dbs=6` for LMDB reader.
- `subgraph_extraction/datasets.py`: cache LMDB read env per path so train/valid can share it.

## Next Gate

Run official WN18RR_v1 reproduction only after deciding whether to use CPU fallback or to build/install a CUDA-enabled DGL stack compatible with Blackwell.

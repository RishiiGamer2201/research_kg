#!/usr/bin/env bash
set -euo pipefail

source /home/admin_wsl/research_kg/S2DN/venv_s2dn/bin/activate

echo "== NVIDIA =="
nvidia-smi || true

echo "== Python packages =="
python - <<'PY'
import torch
import dgl
import lmdb
import networkx
import numpy

print("torch", torch.__version__, "cuda", torch.version.cuda, "cuda_available", torch.cuda.is_available())
print("dgl", dgl.__version__)
print("lmdb", lmdb.__version__)
print("networkx", networkx.__version__)
print("numpy", numpy.__version__)

graph = dgl.graph(([0, 1], [1, 2]))
print("dgl_cpu_graph", graph)
try:
    print("dgl_cuda_graph", graph.to("cuda"))
except Exception as exc:
    print("dgl_cuda_graph_error", type(exc).__name__, str(exc).splitlines()[0])
PY

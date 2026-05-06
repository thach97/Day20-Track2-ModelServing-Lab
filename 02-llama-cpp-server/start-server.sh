#!/usr/bin/env bash
# Launch llama-server (via llama-cpp-python) reading models/active.json.
# Linux + macOS. Windows users: see start-server.ps1.
set -euo pipefail

cd "$(dirname "$0")/.."

MODEL=$(python -c 'import json; print(json.load(open("models/active.json"))["primary_model"])')
THREADS=$(python -c 'import json; hw=json.load(open("hardware.json")); print(hw["cpu"].get("cores_physical") or 4)')
GPU_LAYERS="${LAB_N_GPU_LAYERS:-99}"
PARALLEL="${LAB_PARALLEL:-4}"
CTX="${LAB_N_CTX:-2048}"

echo "==> Starting llama-server"
echo "    model     : $MODEL"
echo "    threads   : $THREADS"
echo "    gpu_layers: $GPU_LAYERS"
echo "    parallel  : $PARALLEL"
echo "    ctx       : $CTX"
echo "    listening : http://0.0.0.0:8080"
echo

exec python 02-llama-cpp-server/server.py \
    --model "$MODEL" \
    --host 0.0.0.0 --port 8080 \
    --n_threads "$THREADS" \
    --n_gpu_layers "$GPU_LAYERS" \
    --n_ctx "$CTX" \
    --workers 1

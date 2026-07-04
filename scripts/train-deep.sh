#!/usr/bin/env bash
# Offline hard-processing: train the learned tier (1D-CNN + AE + contrastive) -> ONNX. Needs torch.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv-pipeline/bin/python}"; [ -x "$PY" ] || PY=".venv-pipeline/Scripts/python.exe"
PYTHONUTF8=1 "$PY" -c "from flowdnalab.deep.train import train_all; print(train_all('models/deep'))"

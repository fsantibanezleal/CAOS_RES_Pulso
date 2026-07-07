#!/usr/bin/env bash
# Create BOTH venvs + install per-lane requirements + the editable package. Idempotent. No global installs.
#   .venv-pipeline = heavy OFFLINE lane (data-pipeline/requirements.txt) + dev + editable pkg  (local-only)
#   .venv          = runtime/live-thin lane (requirements.txt)                                  (what ships)
# Dormant lanes are skipped gracefully. Re-runnable.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"

mkvenv() { [ -d "$1" ] || "$PY" -m venv "$1"; }
venvpy() { local p="$1/bin/python"; [ -x "$p" ] || p="$1/Scripts/python.exe"; echo "$p"; }

echo "[setup] .venv-pipeline (offline lane)…"
mkvenv .venv-pipeline
VP="$(venvpy .venv-pipeline)"
"$VP" -m pip install --upgrade pip -q
"$VP" -m pip install -q -r data-pipeline/requirements.txt -r requirements-dev.txt
"$VP" -m pip install -q -e .
# pygeotypes (private CAOS_GeoTypes until the PyPI release): sibling checkout, editable
GEO="$(cd .. && pwd)/CAOS_GeoTypes"
if [ -d "$GEO" ]; then "$VP" -m pip install -q -e "$GEO[fast,attr]"
else echo "[setup] WARNING: CAOS_GeoTypes not found next to this repo - clone it and re-run (pygeotypes is required)"; fi
echo "[setup] .venv-pipeline ready."

echo "[setup] .venv (runtime/live-thin lane)…"
mkvenv .venv
VR="$(venvpy .venv)"
"$VR" -m pip install --upgrade pip -q
"$VR" -m pip install -q -r requirements.txt
GEO="$(cd .. && pwd)/CAOS_GeoTypes"
[ -d "$GEO" ] && "$VR" -m pip install -q -e "$GEO"
echo "[setup] .venv ready."

# GPU training lane (.venv-train): torch cu124 for the learned tier (P2). ISOLATED from .venv-pipeline
# (which stays CPU for the deterministic offline bake + open-DARTS). Opt-in via PULSO_TRAIN=1 (only on a
# CUDA machine); skipped by default so a CPU-only checkout still sets up.
if [ "${PULSO_TRAIN:-}" = "1" ]; then
  echo "[setup] .venv-train (GPU training lane, torch cu124)…"
  mkvenv .venv-train
  VT="$(venvpy .venv-train)"
  "$VT" -m pip install --upgrade pip -q
  "$VT" -m pip install -q torch --index-url https://download.pytorch.org/whl/cu124
  "$VT" -m pip install -q -r data-pipeline/requirements-train.txt
  [ -d "$GEO" ] && "$VT" -m pip install -q -e "$GEO[fast,attr]"
  "$VT" -m pip install -q -e .
  echo "[setup] .venv-train ready. Verify: .venv-train/Scripts/python.exe scripts/gpu_smoke.py"
fi

echo "[setup] done. Next:  ./scripts/precompute.sh   then   ./scripts/dev.sh"

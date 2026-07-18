# Guide — the GPU training lane (`.venv-train`)

Pulso's learned tier (the 1D-CNN / autoencoder / contrastive / patch-transformer models of the method
ladder, phase P2) is trained on the GPU in a dedicated **isolated** environment, then exported to ONNX
for live in-browser inference. The GPU is only for TRAINING; the deployed site never needs it.

## Why a separate venv

Three isolated lanes, never global:

| venv | torch | purpose |
|---|---|---|
| `.venv-pipeline` | CPU (`+cpu`) | the deterministic offline bake + open-DARTS (DFN flow sim). Stays CPU so the bake is reproducible and open-DARTS is happy. |
| `.venv` | (none) | the runtime/live-thin lane (what ships). |
| `.venv-train` | **CUDA (cu124)** | the GPU training of the learned tier only. |

Mixing CUDA torch into `.venv-pipeline` would make the offline bake non-deterministic across machines
and pull a 2.5 GB wheel into the lane that only needs numpy/scipy. So training gets its own env.

## Create it

Verified on: NVIDIA RTX 4070 Laptop (8 GB), driver 560.94, CUDA 12.4 wheels.

```powershell
# opt-in flag (only on a CUDA machine):
./scripts/setup.ps1 -Train
```
```bash
PULSO_TRAIN=1 ./scripts/setup.sh
```

or by hand:

```bash
python -m venv .venv-train
.venv-train/Scripts/python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu124
.venv-train/Scripts/python.exe -m pip install -r data-pipeline/requirements-train.txt
.venv-train/Scripts/python.exe -m pip install -e .          # the pulso pipeline package (for datasets)
```

`torch` is installed from the CUDA index (the wheel URL is platform-specific, so it is not pinned in
`requirements-train.txt`); the exporter + data deps (`onnx`, `onnxscript`, `scikit-learn`, `pandas`,
`pyarrow`) install from PyPI. `.venv-train` is gitignored; only `requirements-train.txt` + the setup
scripts are committed.

## Verify

```bash
.venv-train/Scripts/python.exe scripts/gpu_smoke.py
```

Asserts `torch.cuda.is_available()`, prints the device, and runs a tiny 1D-conv forward + backward on
the GPU (the shape of the learned tier's `batch x 1 x length` curve inputs). Exits non-zero if the GPU
is not usable, so setup/CI fails loudly instead of silently training on the CPU.

## Training + export (phase P2)

`data-pipeline/flowdnalab/deep/train.py` runs under `.venv-train` with `device='cuda'`, trains each
model on the curve corpus (our simulated ensembles + the 4TU corpus), and exports self-contained ONNX
(opset 18, weights embedded, parity-checked < 1e-4) to `models/deep/`. The browser loads those via
onnxruntime-web (WASM); torch is never shipped. See `docs/frameworks/torch`.

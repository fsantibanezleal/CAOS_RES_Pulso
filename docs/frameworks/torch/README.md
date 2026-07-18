# PyTorch — the learned tier (offline hard-processing)

**What / why.** The deep-learning tier of the method ladder is trained with **PyTorch** in the offline
`.venv-pipeline` (the hard-processing lane) and exported to ONNX for live in-browser inference. This
is the PINN-Lab pattern: heavy training offline, tiny models shipped, live inference in the browser.
Three models on the GeoType curves:

| Model | Architecture | What it gives | Live viz |
|---|---|---|---|
| `GeoTypeCNN` | 1D-CNN (dilated Conv1d ×3 + global average pool + head) | class probabilities per GeoType — a fast learned accelerator of the DTW k-medoids assignment | class-probability bars |
| `CurveAutoencoder` | conv encoder → latent (8-D) → conv-transpose decoder | a latent embedding of behaviour + a reconstruction-error anomaly / OOD score | latent-space scatter + anomaly read-out |
| `ContrastiveEncoder` | conv encoder + projection, triplet loss | an L2-normalized embedding where same-GeoType curves are close | embedding scatter + nearest-neighbour retrieval |

**Install.** `pip install --index-url https://download.pytorch.org/whl/cpu torch` (CPU wheel;
`.venv-pipeline` only — torch is never shipped to the browser). Pinned in
`data-pipeline/requirements.txt` (torch 2.12.1). Also `onnx`, `onnxscript` (the torch≥2.9 exporter),
`onnxruntime` (parity check).

**How FlowDNA uses it.** `data-pipeline/flowdnalab/deep/`:
- `datasets.py` builds a labeled training set from discrete Warren-Root/homogeneous behaviour
  archetypes (genuinely separable GeoTypes) → DTW k-medoids labels.
- `models.py` the three architectures + thin export wrappers (softmax for the CNN; latent +
  reconstruction-error for the AE).
- `train.py` trains each, exports to ONNX (opset 18), **verifies ONNX-vs-torch parity < 1e-4**, and
  writes `models/deep/*.onnx` + `reference.json` (medoids + calibration + embedding/latent clouds).
- Run: `scripts/train-deep.ps1` (or `.sh`).

**Honest metrics** (`models/deep/manifest.json`): CNN held-out accuracy ~0.85, AE reconstruction
MSE ~0.48, contrastive retrieval@1 ~0.91. The CNN accuracy is bounded by the k-medoids label
fuzziness (it reproduces the DTW assignment, not a hidden ground truth).

**Gotchas.**
- **Single-file ONNX, not external data.** torch's exporter can emit weights to a `.onnx.data`
  sidecar; onnxruntime-web cannot resolve that from a URL. `_export` re-saves with
  `save_as_external_data=False` so the browser gets a self-contained `.onnx`.
- On Windows, set `PYTHONUTF8=1` when exporting (the exporter prints a ✅ the cp1252 console can't
  encode).
- The models take a fixed input length (the preprocessing `n_points`); the browser must preprocess a
  curve identically (resample → Bourdet derivative → z-score), which the TS engine mirrors.

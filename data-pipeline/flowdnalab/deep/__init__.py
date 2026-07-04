"""The LEARNED tier (deep models) — the offline hard-processing lane.

torch models trained on the GeoType curves, exported to ONNX for live onnxruntime-web inference in
the browser (the PINN-Lab pattern). NEVER imported by the live Python lane (torch is heavy/native);
the browser runs the exported .onnx, not this code. Trained in `.venv-pipeline` only.

- `models.py`  — the torch architectures (1D-CNN classifier, conv autoencoder, contrastive encoder).
- `datasets.py`— build a labeled training set (curves + GeoType labels) from a study ensemble.
- `train.py`   — train + export ONNX (opset 18) + verify ONNX-vs-torch parity + write a metrics manifest.
"""

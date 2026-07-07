# 04 · Learned tier (P2d)

**What this group answers.** Beyond the classical / SOTA-clustering / conformal tools, can learned neural
models read a pressure transient, and do they run genuinely LIVE in the browser? This group trains four
SOTA architectures on the GPU (torch, `.venv-train` cu124), exports each to ONNX with parity < 1e-4, and
runs them live via onnxruntime-web on the tuned curve. No server, no replay: real in-browser inference.

## The four models

| Model | Role | Architecture | Source |
|---|---|---|---|
| **InceptionTime** | GeoType classifier | multi-scale Inception modules + residual shortcuts, global average pool | Ismail Fawaz et al. 2020 |
| **PatchTST-lite** | GeoType classifier | patchify the series, linear patch embed + positional, Transformer encoder | Nie et al. 2023 |
| **deep conv-AE** | anomaly / OOD | 3 stride-2 conv blocks -> latent -> 3 deconv blocks; reconstruction error | (autoencoder) |
| **TS2Vec-style** | retrieval | dilated-conv residual encoder, contrastive (NT-Xent over two masked views) | Yue et al. 2022 |

The two classifiers are deliberately a **CNN vs. transformer** pair on the same task, so the Live lab shows
where each is stronger. The autoencoder's reconstruction error is an honest out-of-distribution signal (a
curve unlike the training catalogue reconstructs poorly). The TS2Vec-style encoder gives an embedding for
nearest-neighbour retrieval against the baked training cloud.

## Training + export discipline

- **GPU training** in `.venv-train` (torch 2.6 cu124, RTX 4070). Each model moves to CUDA, trains
  full-batch with Adam + a cosine LR schedule, then moves to CPU for export.
- **ONNX export** at opset 18 with a dynamic batch axis, re-saved self-contained (weights embedded, no
  `.onnx.data` sidecar, which onnxruntime-web cannot resolve from a URL).
- **Parity gate**: every export asserts `max|torch - onnxruntime| < 1e-4` on a sample before it is
  committed. A model that does not round-trip is never shipped.
- **TS2Vec contrastive**: two augmented views per curve (random contiguous masking), NT-Xent instance
  contrast (each sample's two views are positives, all other samples are negatives). At inference the
  encoder is a deterministic dilated-conv forward, so it exports and runs live cleanly.

## Committed artifacts

`models/deep/` (copied to `frontend/public/models/`): `geotype_incep.onnx`, `geotype_patchtst.onnx`,
`curve_ae.onnx`, `curve_embed.onnx`, plus `reference.json` (the training-set embedding + latent clouds,
the medoids, the class-conditional conformal calibration, preprocessing spec, and honest held-out
metrics) and `manifest.json`. The browser loads these once and runs all four live.

## Where it runs

The App **Live lab** (synthetic source): the `InceptionTime`, `PatchTST`, `Autoencoder`, and `Contrastive`
tools, each running live via onnxruntime-web on the tuned curve, showing class probabilities (with the
held-out accuracy), the latent point + reconstruction anomaly, or the nearest-neighbour retrieval. Tune a
slider and every model re-infers in the browser.

## References

- H. Ismail Fawaz et al. *InceptionTime: Finding AlexNet for Time Series Classification.* Data Mining and
  Knowledge Discovery 34, 2020.
- Y. Nie, N. H. Nguyen, P. Sinthong, J. Kalagnanam. *A Time Series is Worth 64 Words: Long-term
  Forecasting with Transformers (PatchTST).* ICLR 2023.
- Z. Yue et al. *TS2Vec: Towards Universal Representation of Time Series.* AAAI 2022.
- T. Chen et al. *A Simple Framework for Contrastive Learning of Visual Representations (SimCLR / NT-Xent).*
  ICML 2020.

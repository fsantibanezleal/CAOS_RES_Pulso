# Methods

The **method ladder**: the family of techniques Pulso runs on a pressure-transient ensemble, from the
reference catalogue to the SOTA alternatives it is honestly measured against. The ladder is grouped by
what each method operates on (a distance, a representation, a physical diagnostic, a learned embedding, or
an assignment). Each group has a deep note here; each concrete engine has a [framework card](frameworks.md).

The point is not to crown one clustering. It is to show, on the same data, *where the DTW k-medoids
catalogue earns its cost and where a cheaper method would agree*, reported as real numbers (silhouette,
Adjusted Rand Index), never asserted.

- [01 · Distances & clustering (P2a)](methods/01_clustering-ladder.md): the reference DTW k-medoids vs
  soft-DTW k-means, k-Shape, hierarchical, spectral, HDBSCAN, and Euclidean/correlation baselines.
- [02 · Representations (P2b)](methods/02_representations.md): MDS (have) plus UMAP, t-SNE, functional PCA
  eigen-shapes, and the catch22 feature signature, all aligned to the committed members.
- [03 · Diagnostics (P2c)](methods/03_diagnostics.md): live flow-regime auto-detection + marking,
  Warren-Root and Theis fits that recover the parameters from the curve, and the p'' curvature.
- [04 · Learned tier (P2d)](methods/04_learned-tier.md): InceptionTime + PatchTST-lite classifiers, a deep
  conv-AE (OOD), and a TS2Vec-style contrastive encoder, GPU-trained and exported to ONNX (parity < 1e-4),
  run live via onnxruntime-web.

*(Final group: attribution & assignment (ROM sweep, Mondrian conformal). Authored as it ships.)*

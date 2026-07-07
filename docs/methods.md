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

*(Later groups: representations (MDS/UMAP/t-SNE/fPCA/catch22), diagnostics (regime detection, Warren-Root
/ Theis fits), the learned tier (InceptionTime/conv-AE/TS2Vec/PatchTST, GPU to ONNX), and attribution &
assignment (ROM sweep, Mondrian conformal). Authored per unit as each group ships.)*

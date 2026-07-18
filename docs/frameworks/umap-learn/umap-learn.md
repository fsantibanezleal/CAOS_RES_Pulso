# Framework card: `umap-learn`

## What & why

`umap-learn` (BSD-3, [lmcinnes/umap](https://github.com/lmcinnes/umap)) provides UMAP (Uniform Manifold
Approximation and Projection; McInnes, Healy & Melville, arXiv:1802.03426, 2018), the manifold-learning
layout in Pulso's P2b representations group. UMAP builds a fuzzy topological representation of the data
and optimises a low-dimensional layout that preserves both local neighbourhoods and, better than t-SNE,
the global arrangement of clusters.

In Pulso it lays out the committed member curves in 2D so the scatter viz can switch from the DTW-MDS
embedding to a UMAP embedding and reveal structure the linear MDS may compress. It was chosen over a
hand-rolled projection because UMAP's cross-entropy manifold optimisation is a specific, cited algorithm;
the deep-work rule prescribes the maintained reference implementation, not a substitute.

## Install (exact, verified)

Pinned in `data-pipeline/requirements.txt`:

```
umap-learn>=0.5.0     # UMAP manifold layout (McInnes 2018); offline representation
```

Pure-Python (numba-accelerated); installs cleanly into `.venv-pipeline` with no C toolchain. offline-only
(the layout is baked into the `representations` block), so it never touches the live lane or Pyodide.

## Usage

```python
import umap
reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=seed)
xy = reducer.fit_transform(X)     # (n, 2), one row per committed member
```

Pulso clamps `n_neighbors` to `min(15, n-1)` so small committed sets do not error.

## Applying it here

Called from `flowdnalab/methods/representations.py::compute_representations` on the committed member
curves (the same rows as the CONTRACT-3 `members` block), so the 2D layout aligns element-for-element
with the curves and the MDS scatter. Result lands in `representations.umap2d` (contract `pulso.study/v2`);
the App **Representations** tab reads it and lets the user switch layouts. If `umap-learn` is absent at
bake time the field is `null` and the viz falls back to MDS/t-SNE, never a crash.

## Caveats / license

- UMAP is stochastic; we seed `random_state` for a deterministic bake.
- Distances between clusters in a UMAP plot are qualitative, not metric; read it as topology, not as a
  ruler. The DTW-MDS embedding remains the metric-faithful layout.
- BSD-3-Clause: redistribution-friendly.

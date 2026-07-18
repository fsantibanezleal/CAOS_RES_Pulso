# Framework card: `hdbscan`

## What & why

`hdbscan` (BSD-3, [scikit-learn-contrib/hdbscan](https://github.com/scikit-learn-contrib/hdbscan)) is the
density-based control in Pulso's P2a distances-and-clustering comparison. HDBSCAN (Campello, Moulavi &
Sander, *Density-Based Clustering Based on Hierarchical Density Estimates*, PAKDD 2013; McInnes & Healy,
*Accelerated Hierarchical Density Based Clustering*, ICDMW 2017) builds a hierarchy of density levels and
extracts the most stable flat clustering, with a genuine **noise label (-1)** and **no fixed k**.

It answers a question the k-fixed methods (DTW k-medoids, soft-DTW, k-Shape, spectral) cannot: *is the
number of flow behaviours we impose actually supported by the data density, or are we forcing k=2 onto a
continuum?* When HDBSCAN returns k=0 (all noise) or a very different k, that is an honest signal about the
ensemble, recorded rather than hidden.

## Install (exact, verified)

Pinned in `data-pipeline/requirements.txt`:

```
hdbscan>=0.8.0     # HDBSCAN density clustering (Campello 2013 / McInnes 2017)
```

Ships C-extension wheels for the major platforms; installs into the offline `.venv-pipeline`. offline-only
(baked into `method_comparison`), so it never touches the live lane. It is an *optional* extra: if the
wheel is absent, `compare_clusterings` records HDBSCAN as `skipped` instead of crashing.

## Usage

```python
from hdbscan import HDBSCAN
min_size = max(5, n // 20)
labels = HDBSCAN(min_cluster_size=min_size, metric="precomputed").fit_predict(D.astype("float64"))
# labels == -1 are noise points; unique(labels[labels >= 0]).size is the discovered k
```

## Applying it here

Called from `flowdnalab/methods/clustering.py::compare_clusterings` on the **precomputed DTW distance
matrix** directly (`metric="precomputed"`), so it clusters in the same shape geometry as the reference.
The silhouette drops the -1 noise points before scoring; the reported k is the count of non-noise clusters.
Result appears per-method in the trace `method_comparison` block. In the baked benchmark HDBSCAN agrees
with the DTW reference on the well-separated corpora (e.g. BENCH_C) and returns near-zero structure on the
harder derivative datasets, which is the intended diagnostic.

## Caveats / license

- `min_cluster_size` controls granularity; we scale it to the sample (`max(5, n//20)`) so it is not tuned
  to flatter one dataset.
- Density methods can label a large fraction as noise on smooth, overlapping ensembles; a k=0 result is
  information, not a failure, and is reported verbatim.
- Deterministic given the distance matrix (no random seed needed for the precomputed path).
- BSD-3-Clause.

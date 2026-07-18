# Framework card: `tslearn`

## What & why

`tslearn` (BSD-3, [tslearn-team/tslearn](https://github.com/tslearn-team/tslearn)) is Pulso's engine for
the two shape-clustering alternatives that the DTW k-medoids reference is measured against in the P2a
distances-and-clustering comparison:

- **soft-DTW k-means with DTW barycentres** (`TimeSeriesKMeans(metric="softdtw")`). soft-DTW (Cuturi &
  Blondel, *Soft-DTW: a Differentiable Loss Function for Time-Series*, ICML 2017, arXiv:1703.01541)
  replaces the min in DTW with a smooth soft-min, so a differentiable barycentre (DBA) can be optimised.
  It is the natural "centroid" counterpart to our medoid catalogue: same alignment-invariant idea, but a
  synthetic averaged prototype instead of a real member curve.
- **k-Shape** (`KShape`; Paparrizos & Gravano, *k-Shape: Efficient and Accurate Clustering of Time
  Series*, SIGMOD 2015). A normalized-cross-correlation shape distance with no DTW at all, so it is the
  right control for "does the answer depend on the DTW alignment specifically, or just on shape?".

These were chosen over hand-rolled versions because both algorithms have subtle, easy-to-get-wrong cores
(the soft-min recursion and the SBD/shape-extraction step); a maintained, cited reference implementation
is exactly what the Entry_point deep-work rule prescribes over a toy substitute.

## Install (exact, verified)

Pinned in `data-pipeline/requirements.txt`:

```
tslearn>=0.9.0     # soft-DTW k-means (Cuturi-Blondel 2017) + k-Shape (Paparrizos 2015)
```

Pure-Python + numpy/scipy/scikit-learn/numba wheels; installs into the offline `.venv-pipeline`. It is an
offline-only dependency (the comparison is baked, never run in the browser), so it never touches the live
lane or the Pyodide bundle.

## Usage

```python
from tslearn.clustering import KShape, TimeSeriesKMeans
Xt = X[:, :, None]                                   # tslearn wants (n, sz, d)
sdtw = TimeSeriesKMeans(n_clusters=k, metric="softdtw",
                        metric_params={"gamma": 1.0}, max_iter=20, random_state=seed)
labels_sdtw = sdtw.fit_predict(Xt)
labels_kshape = KShape(n_clusters=k, max_iter=20, random_state=seed).fit_predict(Xt)
```

## Applying it here

Called from `flowdnalab/methods/clustering.py::compare_clusterings`, which runs on the same preprocessed
curves as the reference catalogue and reports each method's k, silhouette (precomputed DTW), and Adjusted
Rand Index vs the DTW k-medoids labels. It runs only for cases with `compare_methods=True` (a
representative subset: WR01, REAL_A, BENCH_A/B/C) and on a seeded <=600 subsample for large corpora, so
the bake stays cheap. Output lands in the trace's `method_comparison` block (contract `pulso.study/v2`),
which the Benchmark page reads for the method-agreement view.

## Caveats / license

- soft-DTW and k-Shape iterate O(n) alignments; at benchmark scale (2000+ curves) that is minutes, hence
  the `_MAX_COMPARE_N=600` subsample cap. The reference labels are subsampled identically, so the ARI
  stays a fair comparison.
- `metric="softdtw"` optimises a synthetic barycentre; unlike our medoid it is not a real member curve, so
  do not read a soft-DTW centroid as an observed response.
- Both are seeded (`random_state`) for a deterministic bake.
- BSD-3-Clause: redistribution-friendly, no copyleft.

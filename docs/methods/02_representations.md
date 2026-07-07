# 02 · Representations (P2b)

**What this group answers.** The DTW distance geometry (the classical MDS embedding) is one lens on a
pressure-transient ensemble. This group adds three more, so the same committed ensemble can be laid out
and described in complementary ways: does a manifold method reveal structure MDS compresses? What are the
dominant modes of variation of the derivative response? Which interpretable features actually separate the
flow-behaviour clusters? All are computed OFFLINE on the SAME committed members as CONTRACT-3, so every
2D layout aligns row-for-row with the member curves and the viz needs no recomputation.

## The four representations

| Representation | Engine | What it gives | Reads as |
|---|---|---|---|
| **classical MDS** (have) | pygeotypes | 2D/3D layout preserving DTW distances | the metric-faithful map |
| **UMAP** | umap-learn | manifold 2D layout | topology (local + global), qualitative distances |
| **t-SNE** | scikit-learn | local-neighbourhood 2D layout | tight local clusters |
| **functional PCA** | numpy SVD | dominant modes of variation + per-member scores | interpretable eigen-shapes |
| **catch22** | pycatch22 | 22 canonical features per curve, per-cluster table | what distinguishes the clusters |

### Functional PCA (in-house, numpy SVD)

The curve matrix is centred and decomposed by SVD, $X_c = U\,S\,V^{\top}$. The rows of $V^{\top}$ are the
functional principal modes (eigen-shapes on the log-time grid); $S^2$ normalised gives the fraction of
ensemble variance each mode explains; $U S$ are the per-member scores (a 2D scatter on the first two
modes). Unlike UMAP/t-SNE, the modes are directly interpretable: mode 1 is the strongest axis along which
the derivative responses differ. This is the one representation computed in-house (a standard SVD, not a
substituted SOTA engine) per Ramsay & Silverman, *Functional Data Analysis* (2005).

### catch22 feature signature

Each committed curve is reduced to the 22 canonical catch22 features (Lubba et al. 2019). Aggregated to a
per-cluster mean +/- std, this describes each GeoType in named, well-studied feature terms (distribution
shape, autocorrelation, entropy, trend, outliers). The Representations tab ranks features by
between-cluster spread (normalised by within-cluster spread) and leads with the most discriminating ones.

## How it is scoped

Computed in `methods/representations.py::compute_representations` on the committed members, gated by the
same `spec.compare_methods` flag as the P2a comparison (the "rich-method" case set: WR01, REAL_A,
BENCH_A/B/C), so the ~seconds-per-method cost runs on a representative subset, not every bake. Result
lands in the trace `representations` block (`pulso.study/v2`). Optional engines (umap-learn, pycatch22)
degrade to a recorded `null` / `skipped`; the viz falls back gracefully.

## Where it runs

OFFLINE only. The App **Representations** tab reads the baked block, switches the 2D layout live (no
recomputation), draws the functional-PCA modes, and shows the catch22 cluster table. Bilingual, light +
dark.

## References

- L. McInnes, J. Healy, J. Melville. *UMAP: Uniform Manifold Approximation and Projection.*
  arXiv:1802.03426, 2018.
- L. van der Maaten, G. Hinton. *Visualizing Data using t-SNE.* JMLR 9, 2008.
- J. Ramsay, B. Silverman. *Functional Data Analysis*, 2nd ed. Springer, 2005.
- C. H. Lubba et al. *catch22: canonical time-series characteristics.* Data Mining and Knowledge
  Discovery 33, 2019.

# 01 · Distances & clustering (P2a)

**What this group answers.** Pulso's reference is a DTW k-medoids catalogue: pressure-derivative curves are
compared with a Sakoe-Chiba-banded Dynamic Time Warping distance, then partitioned by PAM (Partitioning
Around Medoids), so every "flow behaviour" prototype is a *real observed member curve*. This group runs the
main SOTA alternatives on the identical preprocessed curves and reports, honestly, how much they agree with
that reference and whether they find the same structure.

## The reference

**DTW + PAM k-medoids** (`pygeotypes`). DTW aligns two curves under monotonic time warping, absorbing the
rate/time-scale differences between wells so that *shape* drives the distance. PAM then picks k medoids
minimising total within-cluster distance on the precomputed matrix. k is chosen by a silhouette sweep. This
is the catalogue every other method is scored against.

$$ D_\text{DTW}(a,b) = \min_{\pi \in \Pi_w} \sum_{(i,j)\in\pi} \big(a_i - b_j\big)^2 $$

where $\Pi_w$ is the set of monotonic alignment paths inside the Sakoe-Chiba band of width $w$.

## The alternatives (all measured against the reference)

| Method | Engine | Distance / idea | What it controls for |
|---|---|---|---|
| **soft-DTW k-means** | tslearn | smooth soft-min DTW + differentiable barycentre | centroid vs medoid, same alignment idea (Cuturi-Blondel 2017) |
| **k-Shape** | tslearn | normalized cross-correlation (no DTW) | does the answer need DTW, or just shape? (Paparrizos 2015) |
| **hierarchical (average)** | scipy | agglomerative linkage on the DTW matrix | nested structure + the dendrogram (feeds P3) |
| **spectral (DTW affinity)** | scikit-learn | eigen-partition of a Gaussian DTW affinity | non-convex clusters (von Luxburg 2007) |
| **HDBSCAN** | hdbscan | density hierarchy on the DTW matrix, noise + free k | is k=2 imposed or supported? (Campello 2013) |
| **Euclidean k-medoids** | pygeotypes | PAM on point-wise Euclidean distance | ablation: does DTW earn its cost? |
| **correlation k-medoids** | pygeotypes | PAM on correlation distance | ablation: scale/offset-invariant baseline |

## How the comparison is scored

Two numbers per method, both computed on the same precomputed DTW distance matrix so they are comparable:

- **Silhouette** (precomputed metric). Cohesion vs separation of the clustering in DTW geometry. HDBSCAN's
  noise points (-1) are dropped before scoring.
- **Adjusted Rand Index (ARI)** vs the reference labels. Chance-corrected agreement of the partition with
  the DTW k-medoids catalogue: 1.0 = identical grouping, ~0 = random. This is the honest headline number.

For corpora above 600 curves the comparison runs on a seeded 600-curve subsample (the reference labels are
subsampled identically, so the ARI stays fair); the trace records this as e.g. `subsampled: "600/2288"`.

## What the baked benchmark actually shows

Real numbers from the committed artifacts (`method_comparison` block, contract `pulso.study/v2`):

- **REAL_A (low-perm real corpus)** and **BENCH_A (intensity sweep)**: six of seven methods agree with the
  DTW reference at ARI > 0.5. The structure is robust; DTW is confirmed but not uniquely required.
- **BENCH_C (sparse networks)**: soft-DTW, k-Shape, spectral, HDBSCAN and both baselines agree. HDBSCAN
  *independently recovers* the same behaviours without being told k, the strongest form of confirmation.
- **BENCH_B (backbone-derivative dataset)**: only spectral clustering agrees (ARI > 0.5). This is the
  honest hard case: the behaviours overlap in DTW geometry, so the choice of algorithm matters and the
  catalogue should be read with more caution. Reporting this, rather than hiding it, is the point of the
  comparison.

## Where it runs

Offline only, in `flowdnalab/methods/clustering.py::compare_clusterings`, gated by `spec.compare_methods`
(a representative subset of cases). It never runs in the browser; the Benchmark page reads the baked
`method_comparison` block. Optional engines (tslearn, hdbscan) degrade to a recorded `skipped` if absent,
never a crash.

## References

- M. Cuturi, M. Blondel. *Soft-DTW: a Differentiable Loss Function for Time-Series.* ICML 2017.
  arXiv:1703.01541.
- J. Paparrizos, L. Gravano. *k-Shape: Efficient and Accurate Clustering of Time Series.* SIGMOD 2015.
- U. von Luxburg. *A Tutorial on Spectral Clustering.* Statistics and Computing 17(4), 2007.
- R. Campello, D. Moulavi, J. Sander. *Density-Based Clustering Based on Hierarchical Density Estimates.*
  PAKDD 2013. (HDBSCAN; accelerated variant: McInnes & Healy, ICDMW 2017.)
- L. Kaufman, P. Rousseeuw. *Finding Groups in Data.* Wiley 1990. (PAM / silhouette.)
- H. Sakoe, S. Chiba. *Dynamic programming algorithm optimization for spoken word recognition.* IEEE
  TASSP 26(1), 1978. (the DTW band.)

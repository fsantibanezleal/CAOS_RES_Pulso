"""P2a: the distances-and-clustering method group (OFFLINE).

The DTW k-medoids catalogue (pygeotypes) is Pulso's reference clustering. This module runs the SOTA
alternatives on the SAME study data and reports an honest comparison (k, silhouette, and Adjusted Rand
Index vs the reference), so the Benchmark page can show which methods agree and where DTW earns its
cost. Each method has a verified primary source (see docs/methods):

- soft-DTW k-means + barycenters (tslearn) - Cuturi & Blondel 2017, arXiv:1703.01541.
- k-Shape (tslearn) - Paparrizos & Gravano 2015, SIGMOD (normalized cross-correlation; no DTW).
- hierarchical Ward + dendrogram (scipy) - textbook; the linkage feeds the dendrogram viz (P3).
- spectral clustering on a DTW affinity (scikit-learn) - von Luxburg 2007.
- HDBSCAN on the MDS embedding (hdbscan) - Campello 2013 / McInnes & Healy 2017 (variable density + noise).
- Euclidean & correlation k-medoids baselines (ablation: shows the DTW shape distance earns its cost).

All methods are seeded (deterministic). Missing optional libraries degrade to a recorded "skipped",
never a crash (core-only / CI without the extras).
"""
from __future__ import annotations

import warnings

import numpy as np


def _silhouette(D: np.ndarray, labels: np.ndarray) -> float | None:
    """Silhouette from a precomputed distance matrix (>= 2 clusters, each with >= 1 other point)."""
    from sklearn.metrics import silhouette_score
    labels = np.asarray(labels)
    if np.unique(labels[labels >= 0]).size < 2:
        return None
    mask = labels >= 0  # drop HDBSCAN noise (-1) from the silhouette
    if np.unique(labels[mask]).size < 2 or mask.sum() < 3:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return float(silhouette_score(D[np.ix_(mask, mask)], labels[mask], metric="precomputed"))
    except ValueError:
        return None


def _ari(a: np.ndarray, b: np.ndarray) -> float:
    from sklearn.metrics import adjusted_rand_score
    return float(adjusted_rand_score(np.asarray(a), np.asarray(b)))


def _euclid_medoids(X: np.ndarray, k: int, seed: int) -> np.ndarray:
    """A k-medoids baseline on the Euclidean distance of the curves (ablation vs DTW)."""
    from pygeotypes.cluster import pam_kmedoids
    from scipy.spatial.distance import squareform, pdist
    De = squareform(pdist(X, metric="euclidean"))
    return np.asarray(pam_kmedoids(De, k=k, n_init=4, seed=seed).labels, dtype=int)


def _corr_medoids(X: np.ndarray, k: int, seed: int) -> np.ndarray:
    """A k-medoids baseline on the correlation distance of the curves."""
    from pygeotypes.cluster import pam_kmedoids
    from scipy.spatial.distance import squareform, pdist
    Dc = squareform(pdist(X, metric="correlation"))
    return np.asarray(pam_kmedoids(Dc, k=k, n_init=4, seed=seed).labels, dtype=int)


def compare_clusterings(X: np.ndarray, D: np.ndarray, reference_labels: np.ndarray, k: int,
                        seed: int = 42) -> dict:
    """Run the alternative clusterings on the study data and compare to the reference DTW k-medoids.

    X: (n, n_points) preprocessed curves. D: (n, n) DTW distance matrix. reference_labels: the DTW
    k-medoids labels (the catalogue). k: the reference cluster count (alternatives use the same k where
    they take one). Returns {'reference': {...}, 'methods': [ {name, k, silhouette, ari, note}, ... ]}.
    """
    X = np.asarray(X, dtype=float)
    D = np.asarray(D, dtype=float)
    ref = np.asarray(reference_labels, dtype=int)
    # soft-DTW / k-Shape are O(n) iterations of O(n_points) alignments; at benchmark scale (thousands
    # of curves) that is minutes. Compare on a seeded subsample so the method-agreement numbers stay
    # cheap and representative (the reference labels are subsampled the same way, so ARI is fair).
    _MAX_COMPARE_N = 600
    if X.shape[0] > _MAX_COMPARE_N:
        rng = np.random.default_rng(seed)
        sub = np.sort(rng.choice(X.shape[0], size=_MAX_COMPARE_N, replace=False))
        X = X[sub]
        D = D[np.ix_(sub, sub)]
        ref = ref[sub]
        subsampled = f"{_MAX_COMPARE_N}/{reference_labels.shape[0]}"
    else:
        subsampled = None
    n = X.shape[0]
    out: list[dict] = []

    def add(name, labels, note=""):
        labels = np.asarray(labels, dtype=int)
        n_found = int(np.unique(labels[labels >= 0]).size)
        out.append({
            "name": name, "k": n_found,
            "silhouette": (round(v, 4) if (v := _silhouette(D, labels)) is not None else None),
            "ari": round(_ari(ref, labels), 4),
            "note": note,
        })

    # soft-DTW k-means + k-Shape (tslearn); the curves are (n, n_points) univariate series
    try:
        from tslearn.clustering import KShape, TimeSeriesKMeans
        Xt = X[:, :, None]  # tslearn wants (n, sz, d)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sdtw = TimeSeriesKMeans(n_clusters=k, metric="softdtw",
                                    metric_params={"gamma": 1.0}, max_iter=20, random_state=seed)
            add("soft-DTW k-means", sdtw.fit_predict(Xt), "Cuturi-Blondel 2017")
            ks = KShape(n_clusters=k, max_iter=20, random_state=seed)
            add("k-Shape", ks.fit_predict(Xt), "Paparrizos-Gravano 2015 (cross-correlation)")
    except ImportError:
        out.append({"name": "soft-DTW k-means", "note": "tslearn not installed", "skipped": True})
        out.append({"name": "k-Shape", "note": "tslearn not installed", "skipped": True})

    # hierarchical Ward on the DTW distances (condensed) + fcluster to k
    try:
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import squareform
        Z = linkage(squareform(D, checks=False), method="average")  # Ward needs Euclidean; use average on DTW
        add("hierarchical (average)", fcluster(Z, t=k, criterion="maxclust") - 1, "agglomerative on DTW")
    except Exception as e:  # noqa: BLE001
        out.append({"name": "hierarchical (average)", "note": str(e)[:60], "skipped": True})

    # spectral clustering on a DTW affinity (Gaussian kernel of the distances)
    try:
        from sklearn.cluster import SpectralClustering
        sigma = float(np.median(D[D > 0])) or 1.0
        A = np.exp(-(D ** 2) / (2.0 * sigma ** 2))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sc = SpectralClustering(n_clusters=k, affinity="precomputed", random_state=seed,
                                    assign_labels="discretize")
            add("spectral (DTW affinity)", sc.fit_predict(A), "von Luxburg 2007")
    except Exception as e:  # noqa: BLE001
        out.append({"name": "spectral (DTW affinity)", "note": str(e)[:60], "skipped": True})

    # HDBSCAN on the DTW distances directly (variable density + a noise label); k is discovered
    try:
        from hdbscan import HDBSCAN
        min_size = max(5, n // 20)
        hb = HDBSCAN(min_cluster_size=min_size, metric="precomputed")
        add("HDBSCAN", hb.fit_predict(D.astype(np.float64)),
            f"Campello 2013 (min_cluster_size={min_size}; -1 = noise)")
    except ImportError:
        out.append({"name": "HDBSCAN", "note": "hdbscan not installed", "skipped": True})

    # baselines: Euclidean + correlation k-medoids (ablation vs the DTW shape distance)
    try:
        add("Euclidean k-medoids", _euclid_medoids(X, k, seed), "ablation baseline")
        add("correlation k-medoids", _corr_medoids(X, k, seed), "ablation baseline")
    except Exception as e:  # noqa: BLE001
        out.append({"name": "Euclidean/correlation k-medoids", "note": str(e)[:60], "skipped": True})

    return {
        "reference": {"name": "DTW k-medoids", "k": int(np.unique(ref).size),
                      "silhouette": (round(v, 4) if (v := _silhouette(D, ref)) is not None else None)},
        "methods": out,
        "subsampled": subsampled,  # None, or "600/N" when the comparison ran on a subsample
    }

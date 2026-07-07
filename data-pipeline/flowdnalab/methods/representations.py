"""P2b: the representations method group (OFFLINE).

Beyond the DTW distance geometry (the classical MDS embedding, already committed), a pressure-transient
ensemble can be laid out and summarised by several complementary representations. This module computes
them on the SAME committed member curves as the CONTRACT-3 `members` block (so every 2D layout aligns
row-for-row with the curves and the MDS scatter), and returns a compact `representations` artifact block
the scatter/feature viz reads without recomputation. Each has a verified primary source (see docs/methods):

- **UMAP** 2D (umap-learn) - McInnes, Healy & Melville 2018, arXiv:1802.03426. Manifold layout that
  tends to preserve global structure better than t-SNE.
- **t-SNE** 2D (scikit-learn) - van der Maaten & Hinton 2008, JMLR. Local-neighbourhood layout.
- **functional PCA** eigen-shapes (in-house numpy SVD of the centred curve matrix) - Ramsay & Silverman
  2005. The dominant modes of variation of the derivative response + per-member scores (a 2D scatter on
  the first two modes, and the interpretable mode shapes themselves).
- **catch22** canonical time-series features (pycatch22) - Lubba et al. 2019, DAMI. A per-cluster feature
  table (mean +/- std of the 22 features), so the clusters are described in interpretable feature terms.

All are seeded (deterministic). Missing optional libraries degrade to a recorded null / "skipped", never
a crash (core-only / CI without the extras).
"""
from __future__ import annotations

import warnings

import numpy as np

_FPCA_MODES = 4  # dominant functional-PCA modes to commit (shape + explained variance)


def _round2(a: np.ndarray, nd: int = 4) -> list[list[float]]:
    return [[round(float(v), nd) for v in row] for row in np.asarray(a, dtype=float)]


def _fpca(X: np.ndarray) -> dict:
    """Functional PCA by SVD of the centred curve matrix: dominant modes of variation + member scores."""
    mean = X.mean(axis=0)
    Xc = X - mean
    # economy SVD: Xc = U S Vt; the rows of Vt are the functional principal modes (on the t_grid)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    m = min(_FPCA_MODES, Vt.shape[0])
    var = S**2
    evr = (var / var.sum())[:m] if var.sum() > 0 else np.zeros(m)
    modes = Vt[:m]                      # (m, n_points) the eigen-shapes
    scores = U[:, :m] * S[:m]           # (n, m) per-member scores
    return {
        "mean": [round(float(v), 4) for v in mean],
        "modes": _round2(modes),
        "explained_variance": [round(float(v), 4) for v in evr],
        "scores2d": _round2(scores[:, :2]) if m >= 2 else None,  # aligned to the committed members
    }


def _catch22(X: np.ndarray, labels: np.ndarray, k: int) -> dict:
    """Per-cluster mean +/- std of the 22 canonical catch22 features (interpretable cluster description)."""
    try:
        import pycatch22
    except ImportError:
        return {"skipped": True, "note": "pycatch22 not installed"}
    names: list[str] = []
    feats = np.full((X.shape[0], 22), np.nan)
    for i, row in enumerate(X):
        r = pycatch22.catch22_all(row.tolist())
        if not names:
            names = list(r["names"])
        feats[i] = np.asarray(r["values"], dtype=float)
    per_cluster = []
    for g in range(k):
        rows = feats[labels == g]
        if rows.shape[0] == 0:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            per_cluster.append({
                "geotype": int(g),
                "mean": [round(float(v), 4) for v in np.nanmean(rows, axis=0)],
                "std": [round(float(v), 4) for v in np.nanstd(rows, axis=0)],
            })
    return {"names": names, "per_cluster": per_cluster, "note": "22 features per member, aggregated per cluster"}


def compute_representations(X: np.ndarray, labels: np.ndarray, k: int, seed: int = 42) -> dict:
    """Compute the representations block on the committed member curves.

    X: (n, n_points) the committed member curves (same order as the CONTRACT-3 `members`). labels: (n,)
    the cluster label per committed member. k: cluster count. Returns
    {'umap2d', 'tsne2d', 'fpca', 'catch22'} with 2D layouts aligned row-for-row to X.
    """
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels, dtype=int)
    n = X.shape[0]

    # UMAP 2D (manifold layout). n_neighbors clamped for small n so UMAP does not error.
    umap2d = None
    try:
        import umap
        nn = int(max(2, min(15, n - 1)))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reducer = umap.UMAP(n_components=2, n_neighbors=nn, min_dist=0.1, random_state=seed)
            umap2d = _round2(reducer.fit_transform(X))
    except ImportError:
        umap2d = None  # recorded as absent; the viz falls back to MDS/t-SNE

    # t-SNE 2D (local-neighbourhood layout). perplexity must be < n.
    tsne2d = None
    try:
        from sklearn.manifold import TSNE
        perp = float(max(5, min(30, (n - 1) / 3)))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tsne2d = _round2(TSNE(n_components=2, perplexity=perp, init="pca",
                                  random_state=seed).fit_transform(X))
    except Exception:  # noqa: BLE001  (sklearn raises ValueError for degenerate n)
        tsne2d = None

    return {
        "umap2d": umap2d,        # [[x,y],...] per committed member, or null if umap-learn absent
        "tsne2d": tsne2d,        # [[x,y],...] per committed member, or null
        "fpca": _fpca(X),        # {mean, modes, explained_variance, scores2d}
        "catch22": _catch22(X, labels, k),  # {names, per_cluster} or {skipped}
    }

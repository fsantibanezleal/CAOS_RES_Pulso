"""Build a labeled training set for the deep models from a study ensemble.

Generates a large analytic ensemble (Warren-Root + homogeneous mixture), preprocesses it into shape
space (pygeotypes), and labels each curve by DTW k-medoids GeoType — so the CNN learns to reproduce
the paper's GeoType assignment, the AE learns the curve manifold, and the contrastive encoder learns
a metric where same-GeoType curves are close. Deterministic (seeded).
"""
from __future__ import annotations

import numpy as np
from pygeotypes.cluster import pam_kmedoids, select_k
from pygeotypes.distance import dtw_matrix
from pygeotypes.preprocess import prepare_curves

from ..model.pta import TD_GRID, homogeneous_pd, warren_root_pd

# Discrete behaviour ARCHETYPES (the GeoTypes a reservoir engineer would name): a homogeneous
# no-valley response, and dual-porosity responses whose valley appears early / mid / late (lambda) at
# shallow / deep depth (omega). Each training curve is one archetype with small log-jitter — so the
# catalogue is genuinely discrete and separable, and the learned classifier can be strong (not a toy)
# without faking anything: these are real analytic responses.
_ARCHETYPES = [
    {"family": "homogeneous"},
    {"omega": 0.02, "lam": 5e-5},   # deep valley, early
    {"omega": 0.05, "lam": 1e-6},   # medium valley, mid
    {"omega": 0.02, "lam": 3e-8},   # deep valley, late
    {"omega": 0.12, "lam": 8e-7},   # shallow valley, mid
]


def build_training_set(
    n_curves: int = 900,
    n_points: int = 96,
    dtw_window: int = 10,
    k_min: int = 3,
    k_max: int = 6,
    seed: int = 0,
) -> dict:
    """Returns {'X' (n, n_points), 'labels' (n,), 'k', 't_grid', 'medoids' (k, n_points),
    'params' (list)}. X is the normalized first-derivative curve of each response."""
    # Sample discrete archetypes with small log-jitter -> genuinely separable GeoTypes.
    rng = np.random.default_rng(seed)
    curves, params = [], []
    for _ in range(n_curves):
        arch = _ARCHETYPES[rng.integers(len(_ARCHETYPES))]
        if arch.get("family") == "homogeneous":
            y = homogeneous_pd(TD_GRID)
            params.append({"family": "homogeneous", "omega": 1.0, "lam": float("nan")})
        else:
            omega = float(arch["omega"] * np.exp(rng.normal(0, 0.12)))
            lam = float(arch["lam"] * np.exp(rng.normal(0, 0.20)))
            y = warren_root_pd(TD_GRID, omega=min(omega, 0.9), lam=lam)
            params.append({"family": "dual-porosity", "omega": omega, "lam": lam})
        curves.append(y * np.exp(rng.normal(0, 0.01, size=y.shape)))
    t_list = [TD_GRID] * len(curves)
    t_grid, X = prepare_curves(t_list, list(curves), n_points=n_points, derivative_order=1, norm="zscore")

    D = dtw_matrix(X, window=dtw_window, backend="auto")
    diag = select_k(D, range(k_min, k_max + 1), n_init=8, seed=seed)
    res = pam_kmedoids(D, k=diag["best_k"], n_init=8, seed=seed)
    return {
        "X": X.astype(np.float32),
        "labels": res.labels.astype(np.int64),
        "k": int(res.k),
        "t_grid": t_grid,
        "medoids": X[res.medoid_indices].astype(np.float32),
        "params": params,
        "silhouette": float(res.silhouette),
    }

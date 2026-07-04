"""Stage 3 — train (OFFLINE): build the GeoType catalogue + conformal calibration + attribution.

The research-chosen engines run here for real:
- pairwise DTW matrix over the training slice (pygeotypes; dtaidistance C backend when installed),
- K selection by silhouette over [k_min, k_max] + PAM k-medoids (seeded),
- class-conditional split-conformal calibration on a DISJOINT calibration slice,
- RF + TreeSHAP attribution of GeoType labels to descriptors (accuracy-gated; skipped with an
  honest note when the [attr] extra is unavailable).

The split (train/calibration/test) is a seeded permutation — leakage-safe by construction:
the catalogue never sees calibration or test curves.
"""
from __future__ import annotations

import numpy as np
from pygeotypes.assign import ConformalAssigner, nearest_medoid
from pygeotypes.catalogue import Catalogue, build_catalogue
from pygeotypes.cluster import pam_kmedoids, select_k
from pygeotypes.distance import dtw_matrix

from ..io.schema import EnsembleSpec, StudyArrays


def split_indices(n: int, spec: EnsembleSpec, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Seeded train/cal/test permutation split."""
    perm = rng.permutation(n)
    n_cal = max(1, int(round(spec.frac_cal * n)))
    n_test = max(1, int(round(spec.frac_test * n)))
    return {
        "cal": np.sort(perm[:n_cal]),
        "test": np.sort(perm[n_cal:n_cal + n_test]),
        "train": np.sort(perm[n_cal + n_test:]),
    }


def run(arrays: StudyArrays, spec: EnsembleSpec, rng: np.random.Generator, seed: int) -> dict:
    X = np.asarray(arrays.X, dtype=float)
    t_grid = np.asarray(arrays.t_grid, dtype=float)
    idx = split_indices(X.shape[0], spec, rng)
    X_train = X[idx["train"]]

    D = dtw_matrix(X_train, window=spec.dtw_window, backend="auto")
    diag = select_k(D, range(spec.k_min, spec.k_max + 1), n_init=10, seed=seed)
    res = pam_kmedoids(D, k=diag["best_k"], n_init=10, seed=seed)

    catalogue = build_catalogue(
        X_train, t_grid, D, k=res.k, dtw_window=spec.dtw_window,
        preprocessing={
            "derivative_order": spec.derivative_order, "L": spec.L,
            "norm": spec.norm, "n_points": spec.n_points,
        },
        provenance={"case_id": spec.case_id, "split": {k: v.tolist() for k, v in idx.items()}},
        result=res,
    )

    # conformal calibration on the disjoint slice, labeled by the catalogue's own metric
    X_cal = X[idx["cal"]]
    cal_labels = np.array([nearest_medoid(x, catalogue)[0] for x in X_cal], dtype=int)
    assigner = ConformalAssigner(catalogue=catalogue).fit(X_cal, cal_labels)

    attribution = _attribute(arrays, idx["train"], res.labels, seed)

    try:
        import dtaidistance  # noqa: F401
        dtw_backend = "dtaidistance"
    except ImportError:
        dtw_backend = "numpy"

    return {
        "catalogue": catalogue,
        "assigner": assigner,
        "split": idx,
        "k_diagnostics": diag,
        "attribution": attribution,
        "dtw_backend": dtw_backend,
    }


def _attribute(arrays: StudyArrays, train_idx: np.ndarray, labels: np.ndarray, seed: int) -> dict:
    """RF+SHAP attribution on the training slice; honest skip when [attr] deps are missing."""
    feats = np.asarray(arrays.features, dtype=float)[train_idx]
    # drop constant columns (e.g. skin fixed at 0, is_homogeneous in pure-WR cases): zero variance
    keep = [j for j in range(feats.shape[1]) if np.std(feats[:, j]) > 1e-12]
    if len(keep) == 0 or np.unique(labels).size < 2:
        return {"status": "skipped", "reason": "no varying descriptors or a single GeoType"}
    names = [arrays.feature_names[j] for j in keep]
    try:
        from pygeotypes.attribute import attribute_geotypes
        report = attribute_geotypes(feats[:, keep], labels, names, accuracy_gate=0.7, seed=seed)
        report["status"] = "ok"
        return report
    except ImportError:
        return {"status": "skipped", "reason": "pygeotypes[attr] extra not installed in this venv"}


def catalogue_to_dict(catalogue: Catalogue) -> dict:
    return catalogue.to_dict()

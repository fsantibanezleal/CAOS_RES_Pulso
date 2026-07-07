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

import warnings
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

    embedding = _mds_embedding(D, seed)

    return {
        "catalogue": catalogue,
        "assigner": assigner,
        "split": idx,
        "k_diagnostics": diag,
        "attribution": attribution,
        "dtw_backend": dtw_backend,
        # CONTRACT-3 (P0.2): keep the full-ensemble arrays so the study export can commit them
        "D": D,
        "labels": res.labels,
        "X_train": X_train,
        "embedding": embedding,
        "medoid_idx": [int(i) for i in res.medoid_indices],
    }


def _mds_embedding(D: np.ndarray, seed: int) -> dict:
    """Classical (metric) MDS 2D + 3D from a precomputed DTW distance matrix, for the shape-space
    scatter. Deterministic (fixed seed). Falls back to zeros if sklearn is unavailable (core-only)."""
    D = np.asarray(D, dtype=float)
    n = D.shape[0]
    try:
        from sklearn.manifold import MDS
    except ImportError:
        return {"mds2d": np.zeros((n, 2)), "mds3d": None, "stress": 0.0}
    Dsym = 0.5 * (D + D.T)
    np.fill_diagonal(Dsym, 0.0)
    # metric MDS from the precomputed dissimilarity; explicit init + raw stress (quiet across versions)
    common = dict(dissimilarity="precomputed", random_state=seed, normalized_stress=False,
                  max_iter=300)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m2 = MDS(n_components=2, n_init=4, **common)
        xy = m2.fit_transform(Dsym)
        mds3d = None
        if n > 3:
            m3 = MDS(n_components=3, n_init=2, **common)
            mds3d = m3.fit_transform(Dsym)
    return {"mds2d": xy, "mds3d": mds3d, "stress": float(m2.stress_)}


def _attribute(arrays: StudyArrays, train_idx: np.ndarray, labels: np.ndarray, seed: int) -> dict:
    """RF+SHAP attribution on the training slice; honest skip when [attr] deps are missing.

    The RF gate uses a stratified train/test split, which needs >= 2 members per GeoType. A SINGLETON
    GeoType (a lone outlier flow response, which the aperture-swept DFM ensembles can produce) cannot
    be learned or validated, so its sample is dropped from attribution (recorded honestly) and the
    remaining well-populated GeoTypes are attributed; if fewer than two survive, we skip rather than
    crash."""
    feats = np.asarray(arrays.features, dtype=float)[train_idx]
    # drop constant columns (e.g. skin fixed at 0, is_homogeneous in pure-WR cases): zero variance
    keep = [j for j in range(feats.shape[1]) if np.std(feats[:, j]) > 1e-12]
    if len(keep) == 0 or np.unique(labels).size < 2:
        return {"status": "skipped", "reason": "no varying descriptors or a single GeoType"}
    # keep only GeoTypes with >= 2 members (a stratified split needs that); drop singleton outliers
    vals, counts = np.unique(labels, return_counts=True)
    populated = vals[counts >= 2]
    n_singleton = int((counts < 2).sum())
    if populated.size < 2:
        return {"status": "skipped",
                "reason": f"fewer than 2 well-populated GeoTypes ({n_singleton} singleton(s))"}
    mask = np.isin(labels, populated)
    feats_a, labels_a = feats[mask], labels[mask]
    names = [arrays.feature_names[j] for j in keep]
    try:
        from pygeotypes.attribute import attribute_geotypes
        report = attribute_geotypes(feats_a[:, keep], labels_a, names, accuracy_gate=0.7, seed=seed)
        report["status"] = "ok"
        if n_singleton:
            report["singletons_excluded"] = n_singleton
        return report
    except ImportError:
        return {"status": "skipped", "reason": "pygeotypes[attr] extra not installed in this venv"}


def catalogue_to_dict(catalogue: Catalogue) -> dict:
    return catalogue.to_dict()

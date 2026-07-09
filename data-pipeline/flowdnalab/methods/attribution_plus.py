"""P2e: attribution-and-assignment depth (OFFLINE).

Extends the base RF+SHAP attribution and the class-conditional (Mondrian) split-conformal assigner with:

1. predictability-vs-K   - is the label structure attributable across K, or only at the chosen K?
2. ROM descriptor sweep  - which physical knobs move a curve across GeoType boundaries (an
                           assignment-sensitivity map from a fast RF surrogate).
3. dual-representation Mondrian conformal (NOVEL, beyond SOTA) - conformalize jointly across shape space
   (DTW distance to medoid) AND physics-descriptor space (RF implausibility), so a curve that is
   shape-close to the wrong physics is flagged. A coverage-controlled assignment that fuses two
   representations, beyond single-score conformal and beyond RF+SHAP (which has no coverage guarantee).

All seeded/deterministic. Gated by spec.compare_methods (the rich-method case set). Degrades honestly
(e.g. to shape-only conformal) when descriptors are absent or degenerate; never crashes.

References: Vovk et al. 2005 (conformal + Mondrian taxonomy); Breiman 2001 (RF); Lundberg et al. 2020
(TreeSHAP). The dual-representation conjunction is Pulso's proposal.
"""
from __future__ import annotations

import numpy as np


def _varying_columns(feats: np.ndarray) -> list[int]:
    return [j for j in range(feats.shape[1]) if np.std(feats[:, j]) > 1e-12]


def _rf(seed: int):
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_estimators=200, max_depth=None, min_samples_leaf=2,
                                  random_state=seed, n_jobs=1)


def _predictability_vs_k(D: np.ndarray, feats_train: np.ndarray, labels_at_k, k_range, seed: int) -> list[dict]:
    """For each K: PAM at K on the train DTW matrix, then the RF held-out accuracy of predicting those
    labels from the descriptors. Silhouette from the same PAM. A curve the UI overlays."""
    from sklearn.metrics import silhouette_score
    from sklearn.model_selection import cross_val_score
    from pygeotypes.cluster import pam_kmedoids

    out = []
    keep = _varying_columns(feats_train)
    Xd = feats_train[:, keep] if keep else feats_train
    for k in k_range:
        res = pam_kmedoids(D, k=k, n_init=6, seed=seed)
        lab = np.asarray(res.labels, dtype=int)
        try:
            sil = float(silhouette_score(D, lab, metric="precomputed")) if np.unique(lab).size > 1 else 0.0
        except ValueError:
            sil = 0.0
        acc = None
        vals, counts = np.unique(lab, return_counts=True)
        if keep and (counts >= 2).sum() >= 2 and np.unique(lab).size > 1:
            mask = np.isin(lab, vals[counts >= 2])
            try:
                folds = int(min(5, counts[counts >= 2].min()))
                if folds >= 2:
                    # balanced accuracy: on imbalanced ensembles a plain-accuracy score just tracks the
                    # majority baseline (predict-all-majority looks "good"); balanced accuracy scores the
                    # minority GeoTypes fairly, so predictability reflects REAL attributability.
                    acc = float(cross_val_score(_rf(seed), Xd[mask], lab[mask], cv=folds,
                                                scoring="balanced_accuracy").mean())
            except (ValueError, RuntimeError):
                acc = None
        out.append({"k": int(k), "silhouette": round(sil, 4),
                    "rf_accuracy": (round(acc, 4) if acc is not None else None)})
    return out


def _rom_sweep(feats_train: np.ndarray, feat_names: list[str], labels: np.ndarray, seed: int,
               steps: int = 11) -> dict:
    """Fit an RF descriptor->GeoType surrogate; sweep each descriptor across its p5..p95 range (others at
    the median) and measure how the predicted GeoType shifts. Sensitivity = fraction of the sweep whose
    argmax differs from the median-point prediction. The assignment-sensitivity map."""
    keep = _varying_columns(feats_train)
    if not keep or np.unique(labels).size < 2:
        return {"descriptors": [], "sensitivity": [], "sweeps": [], "note": "no varying descriptors"}
    vals, counts = np.unique(labels, return_counts=True)
    mask = np.isin(labels, vals[counts >= 2])
    if (counts >= 2).sum() < 2:
        return {"descriptors": [], "sensitivity": [], "sweeps": [], "note": "fewer than 2 populated GeoTypes"}
    X = feats_train[np.ix_(mask, keep)]
    y = labels[mask]
    names = [feat_names[j] for j in keep]
    rf = _rf(seed).fit(X, y)
    med = np.median(X, axis=0)
    # partial-dependence sensitivity: sweep each descriptor across its p5..p95 range (others at the
    # median) and measure the LARGEST swing in any GeoType probability. Unlike an argmax-flip count this
    # stays informative on imbalanced ensembles (where the argmax may never leave the majority class but
    # the probabilities still move), so the bars are never uniformly zero when a descriptor matters.
    descriptors, sensitivity, sweeps = [], [], []
    for j in range(X.shape[1]):
        lo, hi = np.percentile(X[:, j], 5), np.percentile(X[:, j], 95)
        if hi - lo < 1e-12:
            continue
        xs = np.linspace(lo, hi, steps)
        grid = np.tile(med, (steps, 1))
        grid[:, j] = xs
        proba = rf.predict_proba(grid)               # (steps, n_classes_seen)
        pred = rf.predict(grid).astype(int)
        sens = float(np.max(proba.max(axis=0) - proba.min(axis=0)))
        descriptors.append(names[j])
        sensitivity.append(round(sens, 4))
        sweeps.append({"name": names[j], "xs": [round(float(v), 4) for v in xs],
                       "argmax": [int(p) for p in pred]})
    order = np.argsort(sensitivity)[::-1]
    return {"descriptors": [descriptors[i] for i in order],
            "sensitivity": [sensitivity[i] for i in order],
            "sweeps": [sweeps[i] for i in order], "note": ""}


def _mondrian_pvals(score_by_class: dict[int, np.ndarray], scores: np.ndarray, k: int) -> np.ndarray:
    """Class-conditional (Mondrian) conformal p-values: rank of each per-class nonconformity `scores[g]`
    among the class-g calibration scores (>= convention, +1 smoothing)."""
    p = np.zeros(k)
    for g in range(k):
        s = score_by_class.get(g, np.array([]))
        if s.size == 0:
            p[g] = 0.0
            continue
        n_ge = s.size - np.searchsorted(s, scores[g], side="left")
        p[g] = (n_ge + 1) / (s.size + 1)
    return p


def _dual_conformal(arrays, trained, spec, seed: int) -> dict:
    """The NOVEL dual-representation Mondrian conformal: conform on BOTH shape (DTW to medoid) and
    physics-descriptor (RF implausibility) space; the prediction set is the per-class conjunction."""
    from pygeotypes.assign import distances_to_references_batch, nearest_medoid

    cat = trained["catalogue"]
    k = int(cat.k)
    alpha = float(spec.alpha)
    X = np.asarray(arrays.X, dtype=float)
    feats = np.asarray(arrays.features, dtype=float)
    idx = trained["split"]
    cal_i, test_i, train_i = idx["cal"], idx["test"], idx["train"]

    # --- shape space (existing nonconformity): DTW distance to each medoid ---
    def shape_scores(rows):
        return np.stack([distances_to_references_batch(rows, cat.medoid_curves[g], cat.dtw_window)
                         for g in range(k)], axis=1)  # (n, k)

    cal_lab = np.array([nearest_medoid(x, cat)[0] for x in X[cal_i]], dtype=int)
    test_lab = np.array([nearest_medoid(x, cat)[0] for x in X[test_i]], dtype=int)
    cal_shape = shape_scores(X[cal_i])
    test_shape = shape_scores(X[test_i])
    shape_cal_by_class = {g: np.sort(cal_shape[cal_lab == g, g]) for g in range(k)}

    # --- descriptor space (novel component): RF implausibility 1 - P(g | descriptors) ---
    keep = _varying_columns(feats[train_i])
    degenerate = len(keep) == 0 or np.unique(trained["labels"]).size < 2
    if not degenerate:
        vals, counts = np.unique(trained["labels"], return_counts=True)
        pmask = np.isin(trained["labels"], vals[counts >= 2])
        degenerate = (counts >= 2).sum() < 2
    if not degenerate:
        rf = _rf(seed).fit(feats[np.ix_(train_i, keep)][pmask], trained["labels"][pmask])
        classes = list(rf.classes_)

        def desc_scores(rows_idx):
            proba = rf.predict_proba(feats[np.ix_(rows_idx, keep)])  # (n, n_classes_seen)
            s = np.ones((len(rows_idx), k))
            for col, g in enumerate(classes):
                s[:, int(g)] = 1.0 - proba[:, col]
            return s

        cal_desc = desc_scores(cal_i)
        test_desc = desc_scores(test_i)
        desc_cal_by_class = {g: np.sort(cal_desc[cal_lab == g, g]) for g in range(k)}

    # --- assemble prediction sets over the test slice ---
    shape_cov = dual_cov = 0
    shape_sizes, dual_sizes, caught, examples = [], [], 0, []
    for i in range(len(test_i)):
        ps = _mondrian_pvals(shape_cal_by_class, test_shape[i], k)
        shape_set = [g for g in range(k) if ps[g] > alpha]
        if degenerate:
            dual_set = shape_set
        else:
            pd = _mondrian_pvals(desc_cal_by_class, test_desc[i], k)
            dual_set = [g for g in range(k) if ps[g] > alpha and pd[g] > alpha]
        true = int(test_lab[i])
        shape_cov += int(true in shape_set)
        dual_cov += int(true in dual_set)
        shape_sizes.append(len(shape_set))
        dual_sizes.append(len(dual_set))
        if shape_set and not dual_set:
            caught += 1
            if len(examples) < 8:
                examples.append({"test_index": int(i), "shape_set": [int(g) for g in shape_set],
                                 "dual_set": [], "reason": "shape-match but descriptors implausible"})
    n = max(1, len(test_i))
    return {
        "alpha": alpha,
        "coverage_shape": round(shape_cov / n, 4),
        "coverage_dual": round(dual_cov / n, 4),
        "mean_set_shape": round(float(np.mean(shape_sizes)) if shape_sizes else 0.0, 4),
        "mean_set_dual": round(float(np.mean(dual_sizes)) if dual_sizes else 0.0, 4),
        "caught_by_physics": int(caught),
        "n_test": int(len(test_i)),
        "examples": examples,
        "note": "descriptor-degenerate: dual == shape" if degenerate else "",
    }


def compute_attribution_plus(arrays, trained, spec, seed: int = 42) -> dict:
    """The P2e `attribution_plus` block: predictability-vs-K + ROM sweep + dual-representation conformal."""
    feats_train = np.asarray(arrays.features, dtype=float)[trained["split"]["train"]]
    labels = np.asarray(trained["labels"], dtype=int)
    k_range = range(spec.k_min, spec.k_max + 1)
    predictability = _predictability_vs_k(np.asarray(trained["D"], dtype=float), feats_train, labels,
                                          k_range, seed)
    rom = _rom_sweep(feats_train, list(arrays.feature_names), labels, seed)
    dual = _dual_conformal(arrays, trained, spec, seed)
    return {
        "predictability": predictability,
        "chosen_k": int(trained["catalogue"].k),
        "rom": rom,
        "dual_conformal": dual,
    }

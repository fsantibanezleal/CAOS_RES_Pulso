"""Stage 5 — evaluate (the TEST stage): honest, leakage-safe quality numbers for the manifest.

- Clustering quality: silhouette (train), the full K-selection table.
- Conformal validity: EMPIRICAL coverage on the held-out test slice (does the prediction set
  contain the nearest-medoid truth at least 1-alpha of the time?), mean set size, OOD rate.
- Attribution: the RF accuracy gate + SHAP/permutation rank agreement (or the skip reason).

Nothing here touches the training slice except through the frozen catalogue.
"""
from __future__ import annotations

import numpy as np
from pygeotypes.assign import nearest_medoid
from pygeotypes.catalogue import Catalogue

from ..io.schema import EnsembleSpec


def run(
    catalogue: Catalogue,
    assignments: list[dict],
    X_test: np.ndarray,
    spec: EnsembleSpec,
    k_diagnostics: dict,
    attribution: dict,
    dtw_backend: str,
) -> dict:
    X_test = np.asarray(X_test, dtype=float)
    n = len(assignments)
    covered = 0
    set_sizes = []
    ood = 0
    for a, x in zip(assignments, X_test):
        truth = nearest_medoid(x, catalogue)[0]
        if truth in a["prediction_set"]:
            covered += 1
        set_sizes.append(len(a["prediction_set"]))
        if a["out_of_catalogue"]:
            ood += 1
    coverage = covered / n if n else 0.0
    counts = catalogue.counts()
    metrics = {
        "k": int(catalogue.k),
        "silhouette_train": round(float(catalogue.silhouette), 4),
        "k_table": {
            "k": k_diagnostics["k"],
            "silhouette": [round(float(s), 4) for s in k_diagnostics["silhouette"]],
            "cost": [round(float(c), 2) for c in k_diagnostics["cost"]],
        },
        "geotype_counts": counts.tolist(),
        "conformal": {
            "alpha": spec.alpha,
            "empirical_coverage_test": round(coverage, 4),
            "target_coverage": round(1.0 - spec.alpha, 4),
            "mean_set_size": round(float(np.mean(set_sizes)) if set_sizes else 0.0, 3),
            "ood_rate": round(ood / n if n else 0.0, 4),
            "n_test": n,
        },
        "attribution": _attribution_summary(attribution),
        "dtw_backend": dtw_backend,
    }
    return metrics


def _attribution_summary(attribution: dict) -> dict:
    if attribution.get("status") != "ok":
        return {"status": attribution.get("status", "skipped"), "reason": attribution.get("reason")}
    gate = attribution["gate"]
    out = {
        "status": "ok",
        "rf_accuracy": round(float(gate["accuracy"]), 4),
        "gate_passed": bool(gate["passed"]),
        "rank_agreement_spearman": attribution.get("rank_agreement_spearman"),
    }
    if gate["passed"] and attribution.get("shap_mean_abs"):
        # top descriptor per GeoType (compact honest headline; full table lives in the trace)
        tops = {}
        for cls, imps in attribution["shap_mean_abs"].items():
            tops[cls] = max(imps, key=imps.get)
        out["top_descriptor_per_geotype"] = tops
    return out

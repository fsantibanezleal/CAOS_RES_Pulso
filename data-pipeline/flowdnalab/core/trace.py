"""The compact TRACE = the web-replay artifact. Part of CONTRACT 2: its shape is mirrored by
frontend/src/lib/contract.types.ts, so a drift fails the web build. Schema ids are versioned.

Two artifact kinds:
- flowdna.trace/v1  — a GeoType STUDY: grid, medoid curves, K diagnostics, per-GeoType sample
  curves, the conformal calibration scores (what the live lane needs to classify a user's curve
  with guarantees), assignment examples, attribution table.
- flowdna.dfn/v1    — a GeoDFN NETWORK ensemble: decimated 2-D fracture geometries + descriptor
  table (the transient-simulation phase plugs into these networks later — honestly labeled).
"""
from __future__ import annotations

import numpy as np

TRACE_SCHEMA = "flowdna.trace/v1"
DFN_TRACE_SCHEMA = "flowdna.dfn/v1"
MAX_SAMPLES_PER_GEOTYPE = 3   # example member curves committed per GeoType (besides the medoid)
MAX_ASSIGNMENT_EXAMPLES = 12
MAX_NETWORKS_IN_TRACE = 12    # decimated network geometries committed for the viewer
ROUND = 5


def _r(x, nd=ROUND):
    return [round(float(v), nd) for v in x]


def build_study_trace(
    *,
    case_id: str,
    t_grid: list[float],
    X: np.ndarray,
    catalogue,          # pygeotypes.Catalogue
    assigner,           # pygeotypes.ConformalAssigner (fitted)
    split: dict,
    assignments: list[dict],
    k_diagnostics: dict,
    attribution: dict,
    metrics: dict,
    params_sample: list[dict],
) -> dict:
    X = np.asarray(X, dtype=float)
    train_idx = split["train"]
    labels = catalogue.labels
    samples = []
    for g in range(catalogue.k):
        members = np.where(labels == g)[0][:MAX_SAMPLES_PER_GEOTYPE]
        for m in members:
            samples.append({"geotype": int(g), "curve": _r(X[train_idx[m]])})
    return {
        "schema": TRACE_SCHEMA,
        "case_id": case_id,
        "t_grid": _r(t_grid),
        "preprocessing": catalogue.preprocessing,
        "dtw_window": catalogue.dtw_window,
        "k": int(catalogue.k),
        "medoids": [_r(c) for c in catalogue.medoid_curves],
        "geotype_counts": catalogue.counts().tolist(),
        "silhouette": round(float(catalogue.silhouette), 4),
        "k_table": {
            "k": k_diagnostics["k"],
            "silhouette": [round(float(s), 4) for s in k_diagnostics["silhouette"]],
            "cost": [round(float(c), 2) for c in k_diagnostics["cost"]],
        },
        "samples": samples,
        "calibration_scores": {
            str(g): _r(s) for g, s in assigner.calibration_scores.items()
        },
        "assignments": assignments[:MAX_ASSIGNMENT_EXAMPLES],
        "attribution": attribution if attribution.get("status") == "ok" else
                       {"status": attribution.get("status"), "reason": attribution.get("reason")},
        "params_sample": params_sample[:20],
        "summary": {
            "coverage": metrics["conformal"]["empirical_coverage_test"],
            "target": metrics["conformal"]["target_coverage"],
            "ood_rate": metrics["conformal"]["ood_rate"],
            "mean_set_size": metrics["conformal"]["mean_set_size"],
        },
    }


def build_dfn_trace(*, case_id: str, networks: list[dict], descriptor_names: list[str],
                    descriptors: list[list[float]], stats: dict) -> dict:
    """networks: [{'segments': [[x1,y1,x2,y2], ...], 'n_fractures': int}] (already decimated)."""
    return {
        "schema": DFN_TRACE_SCHEMA,
        "case_id": case_id,
        "networks": networks[:MAX_NETWORKS_IN_TRACE],
        "descriptor_names": descriptor_names,
        "descriptors": [[round(float(v), 5) for v in row] for row in descriptors],
        "stats": stats,
        "transient_simulation": "pending (open-DARTS phase; geometry+descriptors only in this artifact)",
    }

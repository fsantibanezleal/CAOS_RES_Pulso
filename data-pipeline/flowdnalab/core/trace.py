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
STUDY_V2_SCHEMA = "pulso.study/v2"   # CONTRACT-3: the FULL-ensemble study artifact (P0.2)
DFN_TRACE_SCHEMA = "flowdna.dfn/v1"
DARTS_TRACE_SCHEMA = "flowdna.darts/v1"
DFM_TRACE_SCHEMA = "pulso.dfm/v2"    # a DFM study on the CONTRACT-3 full-ensemble base + a dfm block
MAX_SAMPLES_PER_GEOTYPE = 3   # example member curves committed per GeoType (besides the medoid)
MAX_ASSIGNMENT_EXAMPLES = 12
MAX_NETWORKS_IN_TRACE = 12    # decimated network geometries committed for the viewer
ROUND = 5
DISPLAY_COLS = 64             # min/max-per-pixel display width for committed member curves
MAX_DTW_N = 512              # cap the committed DTW matrix; larger ensembles ship a capped subsample


def _r(x, nd=ROUND):
    return [round(float(v), nd) for v in x]


def _decimate_minmax(row: np.ndarray, cols: int = DISPLAY_COLS) -> list[float]:
    """Min/max-per-pixel decimation: keep the extrema in each display column so spiky features (the
    dual-porosity valley, boundary rise) survive downsampling, unlike plain subsampling/LTTB. Returns
    2*ceil(cols/2) points (alternating min,max per bucket). Short rows pass through rounded."""
    row = np.asarray(row, dtype=float)
    n = row.size
    if n <= cols:
        return _r(row)
    buckets = cols // 2
    edges = np.linspace(0, n, buckets + 1).astype(int)
    out: list[float] = []
    for b in range(buckets):
        seg = row[edges[b]:max(edges[b + 1], edges[b] + 1)]
        if seg.size == 0:
            continue
        out.append(round(float(seg.min()), ROUND))
        out.append(round(float(seg.max()), ROUND))
    return out


def _quantize_matrix_uint8(M: np.ndarray) -> dict:
    """Quantize a nonnegative distance matrix to uint8 over [0, dmax] for compact transport."""
    M = np.asarray(M, dtype=float)
    dmax = float(M.max()) if M.size else 1.0
    if dmax <= 0:
        dmax = 1.0
    q = np.clip(np.round(M / dmax * 255.0), 0, 255).astype(int)
    return {"dmax": round(dmax, ROUND), "rows": [row.tolist() for row in q]}


def _cluster_order(labels: np.ndarray) -> np.ndarray:
    """A permutation that groups rows by cluster label (so the DTW matrix shows block structure)."""
    labels = np.asarray(labels)
    return np.concatenate([np.where(labels == g)[0] for g in np.unique(labels)]).astype(int)


def build_study_trace_v2(
    *,
    case_id: str,
    t_grid: list[float],
    X_train: np.ndarray,      # (n, n_points) the FULL training-slice curves
    labels: np.ndarray,       # (n,) cluster label per training curve
    D: np.ndarray,            # (n, n) DTW distance matrix over the training slice
    embedding: dict,          # {'mds2d': (n,2), 'mds3d': (n,3) | None, 'stress': float}
    medoid_idx: list[int],    # training-slice indices of the k medoids (mark them in the scatter)
    catalogue,
    assigner,
    split: dict,
    assignments: list[dict],
    k_diagnostics: dict,
    attribution: dict,
    metrics: dict,
) -> dict:
    """CONTRACT-3: commit the WHOLE ensemble so the web viz is rich without recomputation:
    every member curve (min/max-decimated), per-cluster p10/p50/p90 envelopes, the cluster-ordered
    DTW matrix (uint8), the MDS embedding, plus the v1 catalogue/conformal/attribution fields."""
    X_train = np.asarray(X_train, dtype=float)
    labels = np.asarray(labels, dtype=int)
    n = X_train.shape[0]
    k = int(catalogue.k)

    # every member curve, decimated (extrema-preserving), with its cluster label
    members = {
        "geotype": labels.tolist(),
        "curves": [_decimate_minmax(X_train[i]) for i in range(n)],
    }

    # per-cluster quantile envelopes on the full t_grid (the band the explorer draws for large N)
    envelopes = []
    for g in range(k):
        rows = X_train[labels == g]
        if rows.shape[0] == 0:
            envelopes.append({"geotype": g, "p10": [], "p50": [], "p90": []})
            continue
        envelopes.append({
            "geotype": g,
            "p10": _r(np.percentile(rows, 10, axis=0)),
            "p50": _r(np.percentile(rows, 50, axis=0)),
            "p90": _r(np.percentile(rows, 90, axis=0)),
        })

    # cluster-ordered DTW matrix (capped + quantized). Larger ensembles ship a capped random subsample.
    order = _cluster_order(labels)
    if n > MAX_DTW_N:
        rng = np.random.default_rng(0)
        keep = np.sort(rng.choice(n, size=MAX_DTW_N, replace=False))
        order = order[np.isin(order, keep)]
        dtw_note = f"capped random subsample {MAX_DTW_N}/{n}"
    else:
        dtw_note = "full"
    Dm = np.asarray(D, dtype=float)[np.ix_(order, order)]
    dtw = {**_quantize_matrix_uint8(Dm), "order": order.tolist(),
           "order_labels": labels[order].tolist(), "note": dtw_note}

    # the v1 base builder reads its example curves via X[split['train'][m]]; we already hold X_train,
    # so give it an identity train index into X_train (avoids double-indexing the sliced array).
    id_split = dict(split)
    id_split["train"] = np.arange(n)
    base = build_study_trace(
        case_id=case_id, t_grid=t_grid, X=X_train, catalogue=catalogue, assigner=assigner,
        split=id_split, assignments=assignments, k_diagnostics=k_diagnostics,
        attribution=attribution, metrics=metrics, params_sample=[],
    )
    base["schema"] = STUDY_V2_SCHEMA
    base["members"] = members
    base["envelopes"] = envelopes
    base["dtw"] = dtw
    base["embedding"] = {
        "mds2d": [[round(float(a), 4), round(float(b), 4)] for a, b in embedding["mds2d"]],
        "mds3d": ([[round(float(a), 4), round(float(b), 4), round(float(c), 4)]
                   for a, b, c in embedding["mds3d"]] if embedding.get("mds3d") is not None else None),
        "stress": round(float(embedding.get("stress", 0.0)), 5),
        "medoid_idx": [int(i) for i in medoid_idx],
    }
    base["stats"] = {
        "n_members": n, "display_cols": DISPLAY_COLS, "dtw_n": len(order), "dtw_note": dtw_note,
        "decimation": "min/max-per-pixel (extrema-preserving)",
    }
    return base


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


def build_darts_trace(
    *,
    case_id: str,
    tD: list[float],
    pwD_sim: list[float],
    pwD_analytic: list[float],
    dpwD_sim: list[float],
    dpwD_analytic: list[float],
    validation: dict,
    physical: dict,
) -> dict:
    """open-DARTS well-test artifact: the SIMULATED dimensionless response next to the ANALYTICAL
    homogeneous solution, plus the Bourdet derivative of each and the validation verdict. The web
    overlays sim vs analytic on a log-log plot — the honesty proof that the engine is correct."""
    return {
        "schema": DARTS_TRACE_SCHEMA,
        "case_id": case_id,
        "tD": _r(tD),
        "pwD_sim": _r(pwD_sim),
        "pwD_analytic": _r(pwD_analytic),
        "dpwD_sim": _r(dpwD_sim),
        "dpwD_analytic": _r(dpwD_analytic),
        "validation": validation,
        "physical": physical,
    }


def build_dfm_trace(
    *,
    case_id: str,
    study_trace: dict,
    sample_transient: dict,   # {tD, pwD, dpwD} of a representative simulated drawdown
    fidelity: dict,           # the MRST-ensemble gate on the ensemble median
    mesh_stats: dict,         # n_frac_cells / n_mat_cells / well_xyz / domain of the sample network
    physical: dict,           # matrix perm, fracture perm, aperture, rate, domain
    ensemble: dict,           # n_ok / n_fail / n_networks / geodfn_version
) -> dict:
    """A GeoType STUDY on SIMULATED DFM physics: the full study trace (catalogue / conformal /
    attribution) computed on open-DARTS pressure-transient derivatives, PLUS a `dfm` block with a
    representative simulated transient, the MRST fidelity gate, and the mesh/physics context. The
    `dfn` cases graduate here: `transient_simulation` is a real, gated result, not `pending`."""
    trace = dict(study_trace)
    trace["schema"] = DFM_TRACE_SCHEMA
    trace["dfm"] = {
        "sample_transient": {
            "tD": _r(sample_transient["tD"]), "pwD": _r(sample_transient["pwD"]),
            "dpwD": _r(sample_transient["dpwD"]),
        },
        "fidelity": fidelity,
        "mesh_stats": mesh_stats,
        "physical": physical,
        "ensemble": ensemble,
        "transient_simulation": "open-DARTS DFM single-phase drawdown (validated vs the MRST ensemble)",
    }
    return trace


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

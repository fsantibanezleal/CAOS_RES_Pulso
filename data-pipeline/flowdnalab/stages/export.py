"""Stage 6 — export (CONTRACT 2): write the compact trace artifact + the case manifest. The manifest records the
measured lane/gate verdict, the artifact byte size, the CONTRACT-1 flags, and the evaluation metrics."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.gate import classify_lane
from ..core.manifest import build_case_manifest
from ..core.trace import (
    DARTS_TRACE_SCHEMA,
    DFM_TRACE_SCHEMA,
    DFN_TRACE_SCHEMA,
    STUDY_V2_SCHEMA,
    TRACE_SCHEMA,
    build_darts_trace,
    build_dfm_trace,
    build_dfn_trace,
    build_study_trace,
    build_study_trace_v2,
)
from ..io.formats import write_json


def _measure_live_primitive(trace: dict) -> float:
    """Measured live-lane interaction: generate one Warren-Root curve + conformally classify it."""
    import time

    from ..live import classify_curve_json, generate_curve_json

    t0 = time.perf_counter()
    curve = generate_curve_json(omega=0.05, lam=1e-6, seed=1)
    classify_curve_json(trace, curve["t"], curve["p"])
    return (time.perf_counter() - t0) * 1000.0


def _cap_flags(flags: list[dict], cap: int = 10) -> list[dict]:
    """Keep manifests readable: many identical generated-ensemble flags collapse to a summary row."""
    if len(flags) <= cap:
        return flags
    return flags[:cap] + [{"flag_summary": f"...and {len(flags) - cap} more flags of the same kind"}]


def run_study(
    *,
    case: Any,
    arrays,
    trained: dict,
    assignments: list[dict],
    metrics: dict,
    seed: int,
    run_ms: float,
    flags: list[dict],
    derived_dir: str,
    manifests_dir: str,
) -> dict:
    import numpy as np

    # P2a: the distances-and-clustering method comparison (soft-DTW / k-Shape / hierarchical / spectral
    # / HDBSCAN / Euclidean+correlation baselines vs the DTW-PAM reference). It is ~seconds/method, so
    # it runs only for cases that opt in via spec.compare_methods (a representative subset), not on
    # every bake. Recorded in the trace's `method_comparison` block for the Benchmark method-agreement viz.
    comparison = None
    if getattr(case.spec, "compare_methods", False) and all(
        kk in trained for kk in ("D", "labels", "X_train")
    ):
        from ..methods.clustering import compare_clusterings
        comparison = compare_clusterings(
            np.asarray(trained["X_train"], dtype=float), np.asarray(trained["D"], dtype=float),
            np.asarray(trained["labels"], dtype=int), int(trained["catalogue"].k), seed=seed,
        )

    # CONTRACT-3 (P0.2): the FULL-ensemble study artifact (pulso.study/v2) when the train stage kept
    # the ensemble arrays; falls back to the v1 builder otherwise (e.g. an old cached trained dict).
    if all(kk in trained for kk in ("D", "labels", "X_train", "embedding")):
        trace = build_study_trace_v2(
            case_id=case.id, t_grid=arrays.t_grid,
            X_train=np.asarray(trained["X_train"], dtype=float),
            labels=np.asarray(trained["labels"], dtype=int),
            D=np.asarray(trained["D"], dtype=float),
            embedding=trained["embedding"], medoid_idx=trained.get("medoid_idx", []),
            catalogue=trained["catalogue"], assigner=trained["assigner"], split=trained["split"],
            assignments=assignments, k_diagnostics=trained["k_diagnostics"],
            attribution=trained["attribution"], metrics=metrics,
            with_representations=getattr(case.spec, "compare_methods", False), seed=seed,
        )
        schema = STUDY_V2_SCHEMA
    else:
        trace = build_study_trace(
            case_id=case.id, t_grid=arrays.t_grid, X=np.asarray(arrays.X, dtype=float),
            catalogue=trained["catalogue"], assigner=trained["assigner"], split=trained["split"],
            assignments=assignments, k_diagnostics=trained["k_diagnostics"],
            attribution=trained["attribution"], metrics=metrics, params_sample=[],
        )
        schema = TRACE_SCHEMA
    if comparison is not None:
        trace["method_comparison"] = comparison
    artifact_rel = f"{case.id}/trace.json"
    trace_bytes = write_json(Path(derived_dir) / artifact_rel, trace)
    # Live posture of a STUDY case: the browser re-generates ONE analytic curve + classifies it with
    # pygeotypes (numpy+scipy) against this baked catalogue. The offline DTW matrix/PAM never runs
    # live, so the gate's run_ms is a MEASUREMENT of that live primitive, not of the offline bake.
    live_ms = _measure_live_primitive(trace)
    gate = classify_lane(pure_python=True, wheels={"numpy", "scipy", "pygeotypes"},
                         run_ms=live_ms, trace_bytes=trace_bytes)
    del run_ms  # offline bake wall-clock: used for logging only, never committed (determinism)
    manifest = build_case_manifest(
        case=case, seed=seed, artifact_rel=artifact_rel, artifact_schema=schema,
        trace_bytes=trace_bytes, gate=gate, flags=_cap_flags(flags), metrics=metrics,
        extra_engines={"dtw_backend": trained["dtw_backend"]},
    )
    write_json(Path(manifests_dir) / f"{case.id}.json", manifest)
    return manifest


def run_dfm(
    *,
    case: Any,
    arrays,
    trained: dict,
    assignments: list[dict],
    metrics: dict,
    dfm: dict,             # sample_transient, fidelity, mesh_stats, physical, ensemble
    seed: int,
    run_ms: float,
    flags: list[dict],
    derived_dir: str,
    manifests_dir: str,
    geodfn_version: str,
    darts_version: str,
) -> dict:
    """A GeoType STUDY on SIMULATED DFM physics. Reuses the study trace (catalogue / conformal /
    attribution on the open-DARTS transient derivatives) + a `dfm` block (representative transient,
    MRST fidelity gate, mesh/physics). The live posture equals a study case: the browser re-generates
    + conformally classifies one curve against the baked catalogue; the DFM simulation is offline."""
    import numpy as np

    # CONTRACT-3: build the full-ensemble study base (members + envelopes + DTW + MDS) when the train
    # stage kept the ensemble arrays, so a DFM study is as rich as an analytic/real one; v1 fallback.
    if all(kk in trained for kk in ("D", "labels", "X_train", "embedding")):
        study_trace = build_study_trace_v2(
            case_id=case.id, t_grid=arrays.t_grid,
            X_train=np.asarray(trained["X_train"], dtype=float),
            labels=np.asarray(trained["labels"], dtype=int),
            D=np.asarray(trained["D"], dtype=float),
            embedding=trained["embedding"], medoid_idx=trained.get("medoid_idx", []),
            catalogue=trained["catalogue"], assigner=trained["assigner"], split=trained["split"],
            assignments=assignments, k_diagnostics=trained["k_diagnostics"],
            attribution=trained["attribution"], metrics=metrics,
            with_representations=getattr(case.spec, "compare_methods", False), seed=seed,
        )
    else:
        study_trace = build_study_trace(
            case_id=case.id, t_grid=arrays.t_grid, X=np.asarray(arrays.X, dtype=float),
            catalogue=trained["catalogue"], assigner=trained["assigner"], split=trained["split"],
            assignments=assignments, k_diagnostics=trained["k_diagnostics"],
            attribution=trained["attribution"], metrics=metrics, params_sample=[],
        )
    trace = build_dfm_trace(
        case_id=case.id, study_trace=study_trace, sample_transient=dfm["sample_transient"],
        fidelity=dfm["fidelity"], mesh_stats=dfm["mesh_stats"], physical=dfm["physical"],
        ensemble=dfm["ensemble"],
    )
    artifact_rel = f"{case.id}/trace.json"
    trace_bytes = write_json(Path(derived_dir) / artifact_rel, trace)
    live_ms = _measure_live_primitive(trace)
    gate = classify_lane(pure_python=True, wheels={"numpy", "scipy", "pygeotypes"},
                         run_ms=live_ms, trace_bytes=trace_bytes)
    del run_ms
    # surface the fidelity + ensemble outcome in the manifest metrics (the Experiments page reads it)
    metrics_out = dict(metrics)
    metrics_out["dfm_fidelity"] = dfm["fidelity"]
    metrics_out["dfm_ensemble"] = dfm["ensemble"]
    manifest = build_case_manifest(
        case=case, seed=seed, artifact_rel=artifact_rel, artifact_schema=DFM_TRACE_SCHEMA,
        trace_bytes=trace_bytes, gate=gate, flags=_cap_flags(flags), metrics=metrics_out,
        extra_engines={"open_darts": darts_version, "GeoDFN": geodfn_version,
                       "dtw_backend": trained["dtw_backend"]},
    )
    write_json(Path(manifests_dir) / f"{case.id}.json", manifest)
    return manifest


def run_darts(
    *,
    case: Any,
    curves: dict,          # tD, pwD_sim, pwD_analytic, dpwD_sim, dpwD_analytic
    validation: dict,      # rel_l2, plateau_error, passed, tol
    physical: dict,        # the physical + dimensionless scaling used
    metrics: dict,
    seed: int,
    run_ms: float,
    derived_dir: str,
    manifests_dir: str,
    darts_version: str,
) -> dict:
    trace = build_darts_trace(
        case_id=case.id, tD=curves["tD"], pwD_sim=curves["pwD_sim"],
        pwD_analytic=curves["pwD_analytic"], dpwD_sim=curves["dpwD_sim"],
        dpwD_analytic=curves["dpwD_analytic"], validation=validation, physical=physical,
    )
    artifact_rel = f"{case.id}/trace.json"
    trace_bytes = write_json(Path(derived_dir) / artifact_rel, trace)
    # a full reservoir simulation is native (vtk/gmsh/C++) -> never a live lane; the SPA replays it.
    gate = classify_lane(pure_python=False, wheels={"open-darts"}, run_ms=run_ms, trace_bytes=trace_bytes)
    manifest = build_case_manifest(
        case=case, seed=seed, artifact_rel=artifact_rel, artifact_schema=DARTS_TRACE_SCHEMA,
        trace_bytes=trace_bytes, gate=gate, flags=[], metrics=metrics,
        extra_engines={"open_darts": darts_version},
    )
    write_json(Path(manifests_dir) / f"{case.id}.json", manifest)
    return manifest


def run_dfn(
    *,
    case: Any,
    networks: list[dict],
    descriptor_names: list[str],
    descriptors: list[list[float]],
    stats: dict,
    metrics: dict,
    seed: int,
    run_ms: float,
    flags: list[dict],
    derived_dir: str,
    manifests_dir: str,
    geodfn_version: str,
) -> dict:
    trace = build_dfn_trace(case_id=case.id, networks=networks, descriptor_names=descriptor_names,
                            descriptors=descriptors, stats=stats)
    artifact_rel = f"{case.id}/trace.json"
    trace_bytes = write_json(Path(derived_dir) / artifact_rel, trace)
    # DFN generation needs the GeoDFN wheel -> never a live lane; the viewer replays the artifact.
    gate = classify_lane(pure_python=True, wheels={"GeoDFN"}, run_ms=run_ms, trace_bytes=trace_bytes)
    manifest = build_case_manifest(
        case=case, seed=seed, artifact_rel=artifact_rel, artifact_schema=DFN_TRACE_SCHEMA,
        trace_bytes=trace_bytes, gate=gate, flags=flags, metrics=metrics,
        extra_engines={"GeoDFN": geodfn_version},
    )
    write_json(Path(manifests_dir) / f"{case.id}.json", manifest)
    return manifest

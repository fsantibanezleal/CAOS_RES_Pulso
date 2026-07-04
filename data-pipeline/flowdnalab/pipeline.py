"""The offline pipeline orchestrator + CLI (ADR-0057). Runs the named stages per case, applies CONTRACT 1,
writes the compact artifact + manifest (CONTRACT 2) and a flat index.json.

    python -m flowdnalab.pipeline                 # all cases
    python -m flowdnalab.pipeline WR01_baseline --seed 7

Case kinds route through the same stage names:
- 'study': preprocess (generate/ingest + contract) -> feature_extraction (shape space + descriptors)
           -> train (DTW matrix, K selection, PAM, catalogue, conformal calibration, attribution)
           -> infer (conformal assignment of the held-out test slice)
           -> evaluate (silhouette, EMPIRICAL coverage, OOD rate, attribution gate)
           -> export (study trace + manifest)
- 'dfn':   the GeoDFN generation stage (real engine) -> descriptors -> export (dfn trace + manifest).
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from . import registry
from .core.manifest import build_index
from .core.rng import make_rng
from .io.formats import write_json
from .stages import evaluate, export, feature_extraction, infer, preprocess, train

# data-pipeline/flowdnalab/pipeline.py -> parents[2] = repo root (works under `pip install -e .` too)
REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED = REPO_ROOT / "data" / "derived"
MANIFESTS = DERIVED / "manifests"
MODELS = REPO_ROOT / "models"

STAGES = ("preprocess", "feature_extraction", "train", "infer", "evaluate", "export")


def _train_infer_evaluate(arrays, spec, seed: int) -> dict:
    """The shared study core: train (DTW/PAM/catalogue/conformal/attribution) -> infer (assign the
    held-out test slice) -> evaluate (silhouette, empirical coverage, OOD, attribution gate). Returns
    {trained, assignments, metrics}. Used by the study, real AND dfm paths."""
    rng = make_rng(seed)
    trained = train.run(arrays, spec, rng, seed)
    X = np.asarray(arrays.X, dtype=float)
    X_test = X[trained["split"]["test"]]
    assignments = infer.run(trained["assigner"], X_test, spec)
    metrics = evaluate.run(
        trained["catalogue"], assignments, X_test, spec,
        trained["k_diagnostics"], trained["attribution"], trained["dtw_backend"],
    )
    return {"trained": trained, "assignments": assignments, "metrics": metrics}


def _run_study_stages(case, arrays, spec, flags: list[dict], seed: int, t0: float) -> dict:
    """Shared study runner: train -> infer -> evaluate -> export. Used by the synthetic AND real
    paths (they differ only in how `arrays` + `flags` are built)."""
    r = _train_infer_evaluate(arrays, spec, seed)
    run_ms = (time.perf_counter() - t0) * 1000.0
    return export.run_study(
        case=case, arrays=arrays, trained=r["trained"], assignments=r["assignments"],
        metrics=r["metrics"], seed=seed, run_ms=run_ms, flags=flags,
        derived_dir=str(DERIVED), manifests_dir=str(MANIFESTS),
    )


def _precompute_study(case, seed: int) -> dict:
    rng = make_rng(seed)
    t0 = time.perf_counter()
    curveset, report = preprocess.run(case.spec, rng)
    arrays = feature_extraction.run(curveset, case.spec)
    return _run_study_stages(case, arrays, case.spec, report.flagged, seed, t0)


def _precompute_real(case, seed: int) -> dict:
    from .io import real_data
    from .io.contract import validate_curves
    from .stages.feature_extraction import arrays_from_curves

    spec = case.spec
    t0 = time.perf_counter()
    loaded = real_data.load_dataset(spec.dataset, spec.n_subsample, seed)
    # CONTRACT 1 on the real curves (the corpus is clean, but the gate must run on real data too)
    raw = [{"curve_id": f"{spec.dataset}_{cid}", "t": t.tolist(), "p": p.tolist()}
           for cid, t, p in zip(loaded["ids"], loaded["t"], loaded["p"])]
    report = validate_curves(raw)
    accepted_ids = {r["curve_id"] for r in report.accepted}
    keep = [i for i, cid in enumerate(loaded["ids"]) if f"{spec.dataset}_{cid}" in accepted_ids]
    if len(keep) < spec.k_max * 3:
        raise ValueError(f"real dataset {spec.dataset}: too few curves passed CONTRACT 1 ({len(keep)})")
    t_list = [loaded["t"][i] for i in keep]
    p_list = [loaded["p"][i] for i in keep]
    feats = [loaded["features"][i] for i in keep]
    arrays = arrays_from_curves(
        case.id, t_list, p_list, feats, loaded["feature_names"],
        n_points=spec.n_points, derivative_order=spec.derivative_order, L=spec.L, norm=spec.norm,
    )
    flags = report.flagged + [{"provenance": f"4TU Dataset {spec.dataset}: {len(keep)}/"
                               f"{loaded['n_available']} curves used (seeded subsample)"}]
    return _run_study_stages(case, arrays, spec, flags, seed, t0)


def _precompute_field(case, seed: int) -> dict:
    """REAL field pumping-test study: welltestpy campaigns -> transient drawdown curves -> Bourdet
    first derivative -> the GeoType (AquiferType) pipeline. Mirrors the 4TU real path; the curves are
    RAW drawdown, so preprocessing differentiates them (derivative_order=1)."""
    from .io import field_data
    from .io.contract import validate_curves
    from .stages.feature_extraction import arrays_from_curves

    spec = case.spec
    t0 = time.perf_counter()
    loaded = field_data.load_field(spec.sites)
    raw = [{"curve_id": cid, "t": t.tolist(), "p": p.tolist()}
           for cid, t, p in zip(loaded["ids"], loaded["t"], loaded["p"])]
    report = validate_curves(raw)
    accepted = {r["curve_id"] for r in report.accepted}
    keep = [i for i, cid in enumerate(loaded["ids"]) if cid in accepted]
    if len(keep) < spec.k_max * 3:
        raise ValueError(f"field study {case.id}: too few curves passed CONTRACT 1 ({len(keep)})")
    arrays = arrays_from_curves(
        case.id, [loaded["t"][i] for i in keep], [loaded["p"][i] for i in keep],
        [loaded["features"][i] for i in keep], loaded["feature_names"],
        n_points=spec.n_points, derivative_order=spec.derivative_order, L=spec.L, norm=spec.norm,
    )
    # provenance FIRST so it survives the manifest flag cap (field CONTRACT-1 can flag many curves)
    flags = [{"provenance": f"welltestpy field campaigns {spec.sites}: "
              f"{len(keep)}/{loaded['n_available']} usable transient drawdown curves "
              f"(MIT, Zenodo 4139374, vault-only)"}] + report.flagged
    return _run_study_stages(case, arrays, spec, flags, seed, t0)


def _precompute_darts(case, seed: int) -> dict:
    from .dfn import darts_welltest

    t0 = time.perf_counter()
    result = darts_welltest.run_drawdown(case.spec, seed=seed)
    run_ms = (time.perf_counter() - t0) * 1000.0
    return export.run_darts(
        case=case, curves=result["curves"], validation=result["validation"],
        physical=result["physical"], metrics=result["metrics"], seed=seed, run_ms=run_ms,
        derived_dir=str(DERIVED), manifests_dir=str(MANIFESTS), darts_version=result["darts_version"],
    )


def _precompute_dfm(case, seed: int) -> dict:
    """Step B graduation: mesh + DFM-simulate an ensemble of GeoDFN networks, then run the GeoType
    study on the SIMULATED pressure-transient derivatives (+ the MRST fidelity gate). The `dfn`
    cases graduate from geometry-only to real simulated-physics GeoTypes."""
    from .dfn import dfm_study
    from .stages.feature_extraction import arrays_from_curves

    spec = case.spec
    t0 = time.perf_counter()
    ens = dfm_study.run_dfm_ensemble(spec, seed=seed)
    if ens["n_ok"] < spec.k_max * 3:
        raise ValueError(f"dfm study {case.id}: too few valid DFM transients "
                         f"({ens['n_ok']} < {spec.k_max * 3}); increase n_networks")
    arrays = arrays_from_curves(
        case.id, ens["t"], ens["p"], ens["features"], ens["feature_names"],
        n_points=spec.n_points, derivative_order=spec.derivative_order, L=spec.L, norm=spec.norm,
    )
    r = _train_infer_evaluate(arrays, spec, seed)
    run_ms = (time.perf_counter() - t0) * 1000.0
    flags = [{"provenance": f"open-DARTS DFM ensemble: {ens['n_ok']} valid transients "
              f"({ens['n_fail']} networks skipped: meshing/Newton/invalid-drawdown)"}]
    return export.run_dfm(
        case=case, arrays=arrays, trained=r["trained"], assignments=r["assignments"],
        metrics=r["metrics"],
        dfm={"sample_transient": ens["sample_transient"], "fidelity": ens["fidelity"],
             "mesh_stats": ens["mesh_stats"], "physical": ens["physical"],
             "ensemble": {"n_networks": spec.n_networks, "n_ok": ens["n_ok"],
                          "n_fail": ens["n_fail"], "fidelity_dataset": spec.fidelity_dataset}},
        seed=seed, run_ms=run_ms, flags=flags,
        derived_dir=str(DERIVED), manifests_dir=str(MANIFESTS),
        geodfn_version=ens["geodfn_version"], darts_version="1.5.0",
    )


def _precompute_dfn(case, seed: int) -> dict:
    from .dfn import geodfn_adapter  # offline-only import (GeoDFN wheel)

    t0 = time.perf_counter()
    result = geodfn_adapter.generate_ensemble(case.spec, seed=seed)
    run_ms = (time.perf_counter() - t0) * 1000.0
    return export.run_dfn(
        case=case,
        networks=result["networks"],
        descriptor_names=result["descriptor_names"],
        descriptors=result["descriptors"],
        stats=result["stats"],
        metrics=result["metrics"],
        seed=seed, run_ms=run_ms, flags=result["flags"],
        derived_dir=str(DERIVED), manifests_dir=str(MANIFESTS),
        geodfn_version=result["geodfn_version"],
    )


def precompute(case_id: str, seed: int = 42) -> dict:
    case = registry.get_case(case_id)
    if case.kind == "study":
        return _precompute_study(case, seed)
    if case.kind == "real":
        return _precompute_real(case, seed)
    if case.kind == "field":
        return _precompute_field(case, seed)
    if case.kind == "darts":
        return _precompute_darts(case, seed)
    if case.kind == "dfm":
        return _precompute_dfm(case, seed)
    if case.kind == "dfn":
        return _precompute_dfn(case, seed)
    raise ValueError(f"unknown case kind {case.kind!r}")


def rebuild_index() -> list[dict]:
    """Rebuild `manifests/index.json` from the manifests ALREADY on disk (no re-bake). Every
    registered case whose manifest exists is listed. Use after baking cases individually (which does
    not touch the index) so the web sees them."""
    entries = []
    for c in registry.list_cases():
        if (MANIFESTS / f"{c.id}.json").exists():
            entries.append({"case_id": c.id, "category": c.category,
                            "manifest_path": f"manifests/{c.id}.json"})
    write_json(MANIFESTS / "index.json", build_index(entries))
    return entries


def _darts_available() -> bool:
    try:
        import darts  # noqa: F401
        return True
    except ImportError:
        return False


def run_all(seed: int = 42,
            kinds: tuple[str, ...] = ("study", "dfn", "real", "darts", "dfm", "field")) -> list[dict]:
    from .io import field_data, real_data

    real_ok = real_data.available()
    field_ok = field_data.available()
    darts_ok = _darts_available()
    entries = []
    for c in registry.list_cases():
        if c.kind not in kinds:
            continue
        if c.kind == "real" and not real_ok:
            print(f"  SKIP {c.id}: 4TU vault corpus not available (FLOWDNA_VAULT/real-curves)")
            continue
        if c.kind == "field" and not field_ok:
            print(f"  SKIP {c.id}: field campaigns not available (FLOWDNA_VAULT/field)")
            continue
        if c.kind in ("darts", "dfm") and not darts_ok:
            print(f"  SKIP {c.id}: open-darts not installed (offline-only heavy engine)")
            continue
        precompute(c.id, seed=seed)
        entries.append({"case_id": c.id, "category": c.category, "manifest_path": f"manifests/{c.id}.json"})
    write_json(MANIFESTS / "index.json", build_index(entries))
    return entries


def main() -> None:
    ap = argparse.ArgumentParser(prog="flowdnalab.pipeline")
    ap.add_argument("case", nargs="?", default="all",
                    help="a case id, 'all', or 'index' (rebuild index.json from existing manifests)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--kinds", default="study,dfn,real,darts,dfm,field",
                    help="comma list of case kinds to run (for 'all'): study,dfn,real,darts,dfm,field")
    args = ap.parse_args()
    if args.case == "index":
        entries = rebuild_index()
        print(f"rebuilt index over {len(entries)} cases -> {MANIFESTS / 'index.json'}")
    elif args.case == "all":
        entries = run_all(args.seed, kinds=tuple(args.kinds.split(",")))
        print(f"precomputed {len(entries)} cases -> {DERIVED}")
        for e in entries:
            print(f"  {e['case_id']:22s} [{e['category']}]")
        print(f"index -> {MANIFESTS / 'index.json'}")
    else:
        m = precompute(args.case, args.seed)
        print(f"precomputed {args.case}: lane={m['lane']} bytes={m['artifact']['bytes']} "
              f"-> {DERIVED / m['artifact']['path']}")


if __name__ == "__main__":
    main()

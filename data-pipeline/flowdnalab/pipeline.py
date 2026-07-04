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


def _precompute_study(case, seed: int) -> dict:
    rng = make_rng(seed)
    t0 = time.perf_counter()
    curveset, report = preprocess.run(case.spec, rng)
    arrays = feature_extraction.run(curveset, case.spec)
    trained = train.run(arrays, case.spec, rng, seed)
    X = np.asarray(arrays.X, dtype=float)
    X_test = X[trained["split"]["test"]]
    assignments = infer.run(trained["assigner"], X_test, case.spec)
    metrics = evaluate.run(
        trained["catalogue"], assignments, X_test, case.spec,
        trained["k_diagnostics"], trained["attribution"], trained["dtw_backend"],
    )
    run_ms = (time.perf_counter() - t0) * 1000.0
    return export.run_study(
        case=case, arrays=arrays, trained=trained, assignments=assignments, metrics=metrics,
        seed=seed, run_ms=run_ms, flags=report.flagged,
        derived_dir=str(DERIVED), manifests_dir=str(MANIFESTS),
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
    if case.kind == "dfn":
        return _precompute_dfn(case, seed)
    raise ValueError(f"unknown case kind {case.kind!r}")


def run_all(seed: int = 42, kinds: tuple[str, ...] = ("study", "dfn")) -> list[dict]:
    entries = []
    for c in registry.list_cases():
        if c.kind not in kinds:
            continue
        precompute(c.id, seed=seed)
        entries.append({"case_id": c.id, "category": c.category, "manifest_path": f"manifests/{c.id}.json"})
    write_json(MANIFESTS / "index.json", build_index(entries))
    return entries


def main() -> None:
    ap = argparse.ArgumentParser(prog="flowdnalab.pipeline")
    ap.add_argument("case", nargs="?", default="all", help="a case id, or 'all'")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--kinds", default="study,dfn", help="comma list of case kinds to run (for 'all')")
    args = ap.parse_args()
    if args.case == "all":
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

"""Stage 1 — preprocess: produce the validated CurveSet for a case.

For analytic cases the ensemble is GENERATED here (seeded, via the shared model core) and then run
through CONTRACT 1 exactly like external data would be — the contract is exercised on every run,
not only on the bring-your-own-data path. For real-data cases (4TU corpus / field campaigns) this
stage READS the vault files instead and the same contract gates them.
"""
from __future__ import annotations

import numpy as np

from ..io.contract import ContractReport, validate_curves, validate_spec
from ..io.schema import CurveSet, EnsembleSpec
from ..model.pta import TD_GRID, generate_ensemble


def run(spec: EnsembleSpec, rng: np.random.Generator) -> tuple[CurveSet, ContractReport]:
    spec_report = validate_spec(spec)
    if not spec_report.ok:
        raise ValueError(f"spec rejected by CONTRACT 1: {spec_report.rejected}")

    curves, params = generate_ensemble(
        kind=spec.kind,
        n_curves=spec.n_curves,
        omega_range=spec.omega_range,
        lam_range=spec.lam_range,
        skin_range=spec.skin_range,
        homogeneous_fraction=spec.homogeneous_fraction,
        noise_sd=spec.noise_sd,
        rng=rng,
    )
    raw = [
        {"curve_id": f"{spec.case_id}_{i:04d}", "t": TD_GRID.tolist(), "p": c.tolist()}
        for i, c in enumerate(curves)
    ]
    report = validate_curves(raw)
    report.flagged.extend(spec_report.flagged)
    if not report.ok:
        raise ValueError(f"generated ensemble rejected by CONTRACT 1: {report.summary()}")

    accepted_ids = {r["curve_id"] for r in report.accepted}
    kept_params = [p for r, p in zip(raw, params) if r["curve_id"] in accepted_ids]
    return (
        CurveSet(
            case_id=spec.case_id,
            t=[r["t"] for r in report.accepted],
            p=[r["p"] for r in report.accepted],
            params=kept_params,
            provenance={"generator": "flowdnalab.model.pta", "kind": spec.kind},
        ),
        report,
    )

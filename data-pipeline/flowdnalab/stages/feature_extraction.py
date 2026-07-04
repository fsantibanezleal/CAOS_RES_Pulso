"""Stage 2 — feature extraction: curves -> shape space + descriptor table.

Shape space: pygeotypes preprocessing (common log grid -> Bourdet derivative(s) -> normalization),
exactly the transform the live lane must replicate (the catalogue stores it as metadata).

Descriptors: the per-curve generation parameters (log-scaled where the physics is log-uniform).
For DFN-simulated ensembles these become the fracture-network descriptors instead.

Homogeneous-curve encoding (honesty note): a homogeneous radial response has no (ω, λ). Encoding
those as an out-of-range sentinel would make `log10_lam` a PERFECT proxy for `is_homogeneous`,
stealing the attribution. Instead we IMPUTE the dual-porosity population mean for the missing
(ω, λ) of homogeneous rows, so `is_homogeneous` is the only descriptor that separates the families
(the honest, intended signal). Same idea keeps a truly-constant descriptor column from being fit on
noise: it is dropped downstream by the attribution stage (zero variance).
"""
from __future__ import annotations

import math

import numpy as np
from pygeotypes.preprocess import prepare_curves

from ..io.schema import CurveSet, EnsembleSpec, StudyArrays

FEATURE_NAMES = ["log10_omega", "log10_lam", "skin", "is_homogeneous"]


def arrays_from_curves(
    case_id: str,
    t_list: list,
    p_list: list,
    features: list[list[float]],
    feature_names: list[str],
    *,
    n_points: int,
    derivative_order: int,
    L: float,
    norm: str,
) -> StudyArrays:
    """Shared builder: preprocess arbitrary (t, p) curves into shape space + attach a descriptor
    table. Used by BOTH the synthetic path (param descriptors) and the real-data path (real DFN
    descriptors, derivative_order=0 because the corpus is already the first derivative)."""
    t_grid, X = prepare_curves(
        [np.asarray(t) for t in t_list],
        [np.asarray(p) for p in p_list],
        n_points=n_points,
        derivative_order=derivative_order,
        L=L,
        norm=norm,
    )
    return StudyArrays(
        case_id=case_id,
        t_grid=t_grid.tolist(),
        X=X.tolist(),
        feature_names=list(feature_names),
        features=features,
    )


def run(curveset: CurveSet, spec: EnsembleSpec) -> StudyArrays:
    t_grid, X = prepare_curves(
        [np.asarray(t) for t in curveset.t],
        [np.asarray(p) for p in curveset.p],
        n_points=spec.n_points,
        derivative_order=spec.derivative_order,
        L=spec.L,
        norm=spec.norm,
    )

    # first pass: dual-porosity (ω, λ) so we can impute homogeneous rows with the DP population mean
    dp_logomega, dp_loglam = [], []
    for prm in curveset.params:
        if prm.get("family") != "homogeneous":
            dp_logomega.append(math.log10(max(prm.get("omega", 1.0), 1e-12)))
            lam = prm.get("lam")
            if isinstance(lam, float) and math.isfinite(lam) and lam > 0:
                dp_loglam.append(math.log10(lam))
    mean_logomega = float(np.mean(dp_logomega)) if dp_logomega else 0.0
    mean_loglam = float(np.mean(dp_loglam)) if dp_loglam else -6.0

    feats: list[list[float]] = []
    for prm in curveset.params:
        if prm.get("family") == "homogeneous":
            # impute the DP mean (non-separable) so is_homogeneous carries the family signal
            feats.append([mean_logomega, mean_loglam, float(prm.get("skin", 0.0)), 1.0])
        else:
            lam = prm.get("lam")
            lam_val = math.log10(lam) if isinstance(lam, float) and math.isfinite(lam) and lam > 0 else mean_loglam
            feats.append([
                math.log10(max(prm.get("omega", 1.0), 1e-12)),
                lam_val,
                float(prm.get("skin", 0.0)),
                0.0,
            ])
    return StudyArrays(
        case_id=curveset.case_id,
        t_grid=t_grid.tolist(),
        X=X.tolist(),
        feature_names=list(FEATURE_NAMES),
        features=feats,
    )

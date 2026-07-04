"""MRST fidelity gate for the open-DARTS DFM drawdown (OFFLINE-only, Step B).

Before trusting a FlowDNA DFM transient we check it against the SOURCE PAPER's reference: the 4TU
corpus ships ~4768 MRST-generated dimensionless first-derivative curves per dataset
(`Dataset_<X>_FirstDerivativeDimensionless.parquet`, GPL-3, vault-only). Those are an ENSEMBLE (one
curve per stochastic DFN), not a single labelled case, so the honest test is ensemble membership:
does our independently-simulated (open-DARTS, single-phase geothermal) Bourdet derivative fall inside
the MRST ensemble's p5-p95 envelope over the overlapping dimensionless-time window, and does its
shape track the ensemble median?

Both curves are the dimensionless first derivative p_D'(t_D). The paper normalizes t_D with the
network equivalent permeability; we use the matrix permeability, so the two conventions differ by a
log-translation in t_D (a constant k ratio). We therefore compare on the OVERLAPPING t_D window and
report the metrics as an ensemble-membership check, never a one-to-one curve match. This matches what
the meshio + engine probe already showed: the MRST derivatives sit in [0, ~0.48] with a suppressed
early plateau (conductive fractures) rising at late time, exactly the morphology open-DARTS produces.
"""
from __future__ import annotations

import os
import re
import warnings
from pathlib import Path

import numpy as np

__all__ = ["available", "load_mrst_reference", "fidelity_gate"]


def _vault_root() -> Path:
    root = os.environ.get("FLOWDNA_VAULT")
    if not root:
        raise RuntimeError("FLOWDNA_VAULT is not set (needed to locate the MRST reference corpus)")
    return Path(root) / "real-curves"


def available(dataset: str = "A") -> bool:
    """True iff the MRST reference parquet for `dataset` is present (CI / core-only envs skip)."""
    try:
        root = _vault_root()
    except RuntimeError:
        return False
    return (root / f"Dataset_{dataset}_FirstDerivativeDimensionless.parquet").exists()


def load_mrst_reference(dataset: str, tD_grid: np.ndarray, n_sample: int = 400, seed: int = 42) -> dict:
    """Build the MRST ensemble band (p5/p50/p95 of p_D') on `tD_grid` from `n_sample` reference curves.

    Each MRST curve is interpolated (in log t_D) onto the grid; a grid node is only kept if at least
    a third of the sampled curves cover it (so the band is not an extrapolation artefact). Returns
    {'tD', 'p5', 'p50', 'p95', 'n_curves', 'coverage_mask'}.
    """
    import pandas as pd

    path = _vault_root() / f"Dataset_{dataset}_FirstDerivativeDimensionless.parquet"
    df = pd.read_parquet(path)
    ids = sorted({m.group(1) for c in df.columns if (m := re.match(r"t_D_(\d+)$", c))})
    rng = np.random.default_rng(seed)
    if len(ids) > n_sample:
        ids = list(rng.choice(ids, size=n_sample, replace=False))

    log_grid = np.log10(tD_grid)
    stacked = np.full((len(ids), tD_grid.size), np.nan)
    for i, cid in enumerate(ids):
        tc = df[f"t_D_{cid}"].to_numpy(dtype=float)
        pc = df[f"p_D_prime_{cid}"].to_numpy(dtype=float)
        m = np.isfinite(tc) & np.isfinite(pc) & (tc > 0)
        if m.sum() < 4:
            continue
        tc, pc = tc[m], pc[m]
        order = np.argsort(tc)
        tc, pc = tc[order], pc[order]
        lt = np.log10(tc)
        # interpolate only within this curve's own t_D span (NaN outside -> not counted in the band)
        vals = np.interp(log_grid, lt, pc, left=np.nan, right=np.nan)
        stacked[i] = vals

    counts = np.sum(np.isfinite(stacked), axis=0)
    mask = counts >= max(4, len(ids) // 3)
    # percentiles only over covered nodes; NaN elsewhere (warnings on all-NaN columns are expected)
    covered = np.where(mask, stacked, np.nan)
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        p5 = np.nanpercentile(covered, 5, axis=0)
        p50 = np.nanpercentile(covered, 50, axis=0)
        p95 = np.nanpercentile(covered, 95, axis=0)
    return {"tD": tD_grid, "p5": p5, "p50": p50, "p95": p95,
            "n_curves": int(len(ids)), "coverage_mask": mask}


def fidelity_gate(tD_sim: np.ndarray, dpwD_sim: np.ndarray, dataset: str = "A",
                  n_sample: int = 400, seed: int = 42, n_grid: int = 40,
                  min_band_coverage: float = 0.5) -> dict:
    """Gate a simulated DFM derivative against the MRST ensemble band.

    Grid = log-uniform over the overlap of the simulated t_D span and the MRST corpus. Metrics:
    - `band_coverage`: fraction of grid nodes where dpwD_sim lies within [p5, p95] of the MRST band.
    - `median_rel_l2`: relative L2 of dpwD_sim vs the MRST median over the overlap.
    - `shape_corr`: Pearson correlation of dpwD_sim vs the MRST median (does it dip + rise the same).
    PASS iff band_coverage >= min_band_coverage (our curve is a plausible MRST ensemble member). If
    the corpus is unavailable the gate returns `reference: none` and does NOT pass (never faked).
    """
    tD_sim = np.asarray(tD_sim, dtype=float)
    dpwD_sim = np.asarray(dpwD_sim, dtype=float)
    m = np.isfinite(tD_sim) & np.isfinite(dpwD_sim) & (tD_sim > 0)
    tD_sim, dpwD_sim = tD_sim[m], dpwD_sim[m]

    if not available(dataset) or tD_sim.size < 4:
        return {"reference": "none", "dataset": dataset, "passed": False,
                "note": "MRST corpus unavailable or too few simulated points; curve stays unvalidated"}

    grid = np.logspace(np.log10(tD_sim.min()), np.log10(tD_sim.max()), n_grid)
    ref = load_mrst_reference(dataset, grid, n_sample=n_sample, seed=seed)
    mask = ref["coverage_mask"]
    if mask.sum() < 4:
        return {"reference": "insufficient_overlap", "dataset": dataset, "passed": False,
                "note": "MRST band does not overlap the simulated t_D window"}

    sim_on_grid = np.interp(np.log10(grid), np.log10(tD_sim), dpwD_sim)
    p5, p50, p95 = ref["p5"], ref["p50"], ref["p95"]
    inside = (sim_on_grid >= p5) & (sim_on_grid <= p95) & mask
    band_coverage = float(inside.sum() / mask.sum())

    s, r = sim_on_grid[mask], p50[mask]
    # the paper normalizes t_D/p_D' with the network k_eq, we with the matrix perm: the two derivative
    # levels differ by a scale. Isolate SHAPE with the least-squares scale a=<s,r>/<s,s>, so
    # shape_rel_l2 measures morphology mismatch independent of the normalization convention.
    a = float(np.dot(s, r) / np.dot(s, s)) if np.dot(s, s) > 0 else 1.0
    shape_rel_l2 = float(np.linalg.norm(a * s - r) / (np.linalg.norm(r) or 1.0))
    shape_corr = float(np.corrcoef(s, r)[0, 1]) if s.size > 2 and np.std(s) > 0 and np.std(r) > 0 else float("nan")

    passed = bool(band_coverage >= min_band_coverage)
    return {
        "reference": "mrst_ensemble", "dataset": dataset, "n_ref_curves": ref["n_curves"],
        "n_grid_overlap": int(mask.sum()),
        "band_coverage": round(band_coverage, 3),
        "shape_rel_l2": round(shape_rel_l2, 3),
        "scale_factor": round(a, 4),
        "shape_corr": round(shape_corr, 3) if np.isfinite(shape_corr) else None,
        "min_band_coverage": min_band_coverage,
        "passed": passed,
        # a downsampled band for the frontend overlay (keep the artifact light)
        "band": {"tD": grid[mask][::2].tolist(), "p5": p5[mask][::2].tolist(),
                 "p50": p50[mask][::2].tolist(), "p95": p95[mask][::2].tolist(),
                 "sim": sim_on_grid[mask][::2].tolist()},
    }

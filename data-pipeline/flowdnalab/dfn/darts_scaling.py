"""Dimensionless well-test scaling + analytical validation (pure numpy — offline lane helper).

Converts a PHYSICAL drawdown transient (BHP vs time from open-DARTS, field units) into the
dimensionless (t_D, p_wD) pair so it can be compared to the analytical line-source solution
`pygeotypes.synthetic.homogeneous_pd`, independent of the engine's unit system.

Radial dimensionless groups (oilfield-consistent, but we work in SI-derived ratios so only the
combination matters):

    t_D  = k · t / (phi · mu · c_t · r_w^2)
    p_wD = (2 · pi · k · h / (q · mu)) · (p_init - p_wf)

The homogeneous infinite-acting solution has p_wD ≈ 0.5·(ln t_D + 0.80907) at late time and a
Bourdet derivative plateau at 0.5 — the two invariants the validation checks.
"""
from __future__ import annotations

import numpy as np
from pygeotypes.preprocess import bourdet_derivative
from pygeotypes.synthetic import homogeneous_pd

__all__ = ["to_dimensionless", "validate_against_analytic"]


def to_dimensionless(
    t_day: np.ndarray,
    p_wf_bar: np.ndarray,
    *,
    perm_mD: float,
    poro: float,
    visc_cP: float,
    ct_1bar: float,
    rw_m: float,
    h_m: float,
    q_m3day: float,
    p_init_bar: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Physical (t[day], p_wf[bar]) -> (t_D, p_wD). Uses a consistent SI reduction so the
    dimensionless groups are unit-agnostic ratios (permeability mD->m2, etc.)."""
    t = np.asarray(t_day, dtype=float) * 86400.0                 # s
    dp = (p_init_bar - np.asarray(p_wf_bar, dtype=float)) * 1e5  # Pa
    k = perm_mD * 9.869233e-16                                   # m^2
    mu = visc_cP * 1e-3                                          # Pa.s
    ct = ct_1bar / 1e5                                           # 1/Pa
    q = q_m3day / 86400.0                                        # m^3/s
    tD = k * t / (poro * mu * ct * rw_m**2)
    pwD = (2.0 * np.pi * k * h_m / (q * mu)) * dp
    return tD, pwD


def validate_against_analytic(tD: np.ndarray, pwD_sim: np.ndarray, tol_rel_l2: float) -> dict:
    """Compare a simulated dimensionless drawdown to the analytical homogeneous solution, the
    well-test way.

    A grid-block well carries an apparent (mechanical) SKIN vs the ideal line source: the simulated
    p_wD is the analytical one plus a near-constant offset S over the infinite-acting window. That is
    expected physics, not an error, so validation is:

    1. **Derivative plateau at 0.5** over the infinite-acting window — the engine-agnostic radial-flow
       signature (the invariant well-test analysis actually uses).
    2. **Skin-corrected rel-L2**: fit the apparent skin S = median(p_wD_sim - p_wD_ana), then compare
       (p_wD_sim - S) to the analytical curve. This isolates the SHAPE match from the skin offset.

    Passes iff the derivative plateau sits at 0.5 (within tol) AND the skin-corrected shape matches
    (rel-L2 within tol). The window drops early points (wellbore/discretization) and the very latest
    (finite-grid boundary onset)."""
    tD = np.asarray(tD, dtype=float)
    pwD_sim = np.asarray(pwD_sim, dtype=float)
    order = np.argsort(tD)
    tD, pwD_sim = tD[order], pwD_sim[order]
    keep = tD > 0
    tD, pwD_sim = tD[keep], pwD_sim[keep]

    pwD_ana = homogeneous_pd(tD)
    dpwD_sim = bourdet_derivative(tD, pwD_sim)
    dpwD_ana = bourdet_derivative(tD, pwD_ana)

    n = tD.size
    lo, hi = int(0.25 * n), int(0.9 * n)
    win = slice(max(lo, 1), max(hi, lo + 2))

    skin = float(np.median(pwD_sim[win] - pwD_ana[win]))
    num = np.linalg.norm((pwD_sim[win] - skin) - pwD_ana[win])
    den = np.linalg.norm(pwD_ana[win]) or 1.0
    rel_l2 = float(num / den)
    plateau_error = float(np.abs(np.median(dpwD_sim[win]) - 0.5))
    passed = bool(rel_l2 <= tol_rel_l2 and plateau_error <= 0.1)

    return {
        "pwD_analytic": pwD_ana.tolist(),
        "dpwD_sim": dpwD_sim.tolist(),
        "dpwD_analytic": dpwD_ana.tolist(),
        "rel_l2": round(rel_l2, 5),
        "plateau_error": round(plateau_error, 5),
        "apparent_skin": round(skin, 4),
        "window": [int(win.start), int(win.stop)],
        "tol_rel_l2": tol_rel_l2,
        "tol_plateau": 0.1,
        "passed": passed,
    }

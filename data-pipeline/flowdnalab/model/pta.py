"""The shared pure-Python analytic PTA core (Pyodide-safe) — the ONLY code used by more than one lane.

Thin domain layer over `pygeotypes.synthetic` (Warren-Root / homogeneous radial via Gaver-Stehfest):
ensemble generation for the analytic cases, shared by the offline stages and the live browser lane.
Heavy engines (GeoDFN, open-DARTS) NEVER appear here — they live in stages/ and dfn/ (offline only).
"""
from __future__ import annotations

import numpy as np
from pygeotypes.synthetic import homogeneous_pd, warren_root_pd

__all__ = ["homogeneous_pd", "warren_root_pd", "generate_ensemble", "TD_GRID"]

TD_GRID = np.logspace(2, 10, 200)  # dimensionless time grid for analytic generation


def generate_ensemble(
    kind: str,
    n_curves: int,
    omega_range: tuple[float, float],
    lam_range: tuple[float, float],
    skin_range: tuple[float, float],
    homogeneous_fraction: float,
    noise_sd: float,
    rng: np.random.Generator,
) -> tuple[list[np.ndarray], list[dict]]:
    """Seeded analytic ensemble. Returns (curves, params); every curve lives on TD_GRID.

    kind='warren_root': all dual-porosity (log-uniform ω, λ; uniform skin).
    kind='mixture': a homogeneous_fraction of curves are homogeneous radial (the null behaviour);
    the rest dual-porosity — the catalogue must separate the two families.
    """
    curves: list[np.ndarray] = []
    params: list[dict] = []
    for i in range(n_curves):
        skin = float(rng.uniform(*skin_range))
        is_homog = kind == "mixture" and (i < homogeneous_fraction * n_curves)
        if is_homog:
            y = homogeneous_pd(TD_GRID, S=skin)
            prm = {"family": "homogeneous", "omega": 1.0, "lam": float("nan"), "skin": skin}
        else:
            omega = float(10 ** rng.uniform(np.log10(omega_range[0]), np.log10(omega_range[1])))
            lam = float(10 ** rng.uniform(np.log10(lam_range[0]), np.log10(lam_range[1])))
            y = warren_root_pd(TD_GRID, omega=omega, lam=lam, S=skin)
            prm = {"family": "dual-porosity", "omega": omega, "lam": lam, "skin": skin}
        if noise_sd > 0:
            y = y * np.exp(rng.normal(0.0, noise_sd, size=y.shape))
        curves.append(y)
        params.append(prm)
    return curves, params

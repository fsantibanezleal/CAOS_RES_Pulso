"""LIVE lane entrypoint (Pyodide-safe): what the browser runs — nothing else.

Two interactions, both pure numpy/scipy + pygeotypes core (no dtaidistance/sklearn/shap/GeoDFN):

1. `generate_curve_json` — tune (omega, lambda, skin, noise) and get a Warren-Root response +
   its Bourdet derivative, live.
2. `classify_curve_json` — preprocess a curve EXACTLY as the baked catalogue prescribes and
   conformally assign it (p-values, prediction set, out-of-catalogue flag) against the committed
   trace artifact. Guarantees carry into the browser because the calibration scores ship in the
   trace and the math is the same pygeotypes code path the offline pipeline used.
"""
from __future__ import annotations

import numpy as np
from pygeotypes.assign import ConformalAssigner
from pygeotypes.catalogue import Catalogue
from pygeotypes.preprocess import bourdet_derivative, log_resample, normalize, second_log_derivative

from .model.pta import TD_GRID, warren_root_pd


def generate_curve_json(omega: float = 0.05, lam: float = 1e-6, skin: float = 0.0,
                        noise_sd: float = 0.0, seed: int = 42) -> dict:
    rng = np.random.default_rng(int(seed))
    y = warren_root_pd(TD_GRID, omega=float(omega), lam=float(lam), S=float(skin))
    if noise_sd > 0:
        y = y * np.exp(rng.normal(0.0, float(noise_sd), size=y.shape))
    return {
        "t": TD_GRID.tolist(),
        "p": y.tolist(),
        "derivative": bourdet_derivative(TD_GRID, y).tolist(),
        "params": {"omega": omega, "lam": lam, "skin": skin, "noise_sd": noise_sd, "seed": seed},
    }


def _preprocess_like(trace: dict, t: np.ndarray, p: np.ndarray) -> np.ndarray:
    prep = trace["preprocessing"]
    tg = np.asarray(trace["t_grid"], dtype=float)
    _, y = log_resample(t, p, n_points=int(prep["n_points"]), t_min=float(tg[0]), t_max=float(tg[-1]))
    order = int(prep["derivative_order"])
    if order == 1:
        y = bourdet_derivative(tg, y, L=float(prep["L"]))
    elif order == 2:
        y = second_log_derivative(tg, y, L=float(prep["L"]))
    return normalize(y, method=prep.get("norm", "zscore"))


def classify_curve_json(trace: dict, t: list[float], p: list[float], alpha: float | None = None) -> dict:
    """Conformal assignment of a user's curve against a baked study trace (the classify-my-curve tab)."""
    catalogue = Catalogue(
        k=int(trace["k"]),
        t_grid=np.asarray(trace["t_grid"], dtype=float),
        medoid_curves=np.asarray(trace["medoids"], dtype=float),
        medoid_indices=np.arange(int(trace["k"])),
        labels=np.zeros(1, dtype=int),                    # not needed for assignment
        per_curve_distance=np.zeros(1, dtype=float),
        silhouette=float(trace["silhouette"]),
        dtw_window=trace.get("dtw_window"),
        preprocessing=trace["preprocessing"],
    )
    assigner = ConformalAssigner.from_dict({"calibration_scores": trace["calibration_scores"]}, catalogue)
    x = _preprocess_like(trace, np.asarray(t, dtype=float), np.asarray(p, dtype=float))
    if alpha is None:
        # the trace summary stores the TARGET COVERAGE (1 - alpha) the case was baked with
        alpha = 1.0 - float(trace.get("summary", {}).get("target", 0.85))
    result = assigner.predict(x, alpha=max(1e-6, min(0.5, float(alpha))))
    return result.to_dict()

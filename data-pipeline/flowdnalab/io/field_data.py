"""Loader for REAL field pumping-test campaigns (welltestpy) -> transient drawdown curves.

Source: GeoStat-Examples/welltestpy-field-site-analysis (MIT, Zenodo 4139374): `horkheim.cmp` +
`lauswiesen.cmp` welltestpy `Campaign` files for two field sites (Horkheimer Insel, Heilbronn;
Lauswiesen, Tuebingen). Vault-only (never vendored, like the 4TU corpus).

Each (pumping test, observation well) pair is a REAL transient drawdown s(t) at a known radial
distance r from the pumping well, with a known pumping rate Q. We cluster the Bourdet-derivative
SHAPE of these curves into "AquiferTypes" with the same DTW k-medoids + conformal + attribution
pipeline used for the fractured-reservoir studies. This demonstrates the GeoType methodology
generalizes from fractured reservoirs to real aquifer field data (the diagnostic-plot idea).

Domain honesty: aquifer pumping tests are a DIFFERENT physical system from fractured reservoirs; only
the derivative-shape diagnostic transfers. T and S are unknown (welltestpy estimates them), so curves
are clustered by shape, not a T/S-referenced dimensionless response. Returns the same contract as
`real_data.load_dataset` (ids, t, p, features, feature_names, n_available) so the study pipeline reuses.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

# campaign stem -> site code (attribution can test whether the SITE controls the AquiferType)
_SITES = {"horkheim": 0, "lauswiesen": 1}

# the interpretable controls the attribution layer ranks
DESCRIPTOR_COLUMNS = ["log_r", "log_Q", "site", "well_depth", "screen_size", "aquifer_depth"]


def _field_root() -> Path:
    """Locate the extracted campaign dir (holds horkheim.cmp + lauswiesen.cmp)."""
    root = os.environ.get("FLOWDNA_VAULT")
    if not root:
        raise RuntimeError("FLOWDNA_VAULT is not set (needed to locate the field campaigns)")
    hits = sorted((Path(root) / "field").glob("**/data/horkheim.cmp"))
    if not hits:
        raise FileNotFoundError("horkheim.cmp not found under $FLOWDNA_VAULT/field (download Zenodo 4139374)")
    return hits[0].parent


def available() -> bool:
    """True iff the extracted welltestpy campaigns are present (CI / core-only envs skip field cases)."""
    try:
        _field_root()
        return True
    except (RuntimeError, FileNotFoundError):
        return False


def _well_scalar(well, attr: str) -> float:
    """A guarded scalar read of an optional welltestpy Well descriptor (NaN when absent)."""
    v = getattr(well, attr, None)
    try:
        return float(np.atleast_1d(getattr(v, "value", v)).astype(float)[0])
    except (TypeError, ValueError, IndexError):
        return float("nan")


def load_field(sites: tuple[str, ...] = ("horkheim", "lauswiesen"), *, min_points: int = 10,
               min_drawdown: float = 1e-4, max_points: int = 400) -> dict:
    """Load usable transient drawdown curves + descriptors from the named campaigns.

    A curve is usable if it has >= `min_points` finite (t>0) samples, a real drawdown span, and a
    radial distance r > 0.1 m (not the pumping well itself). Very long series (Lauswiesen ~6300 pts)
    are decimated to `max_points` on a log grid to keep the committed study tractable.
    """
    import welltestpy as wtp

    root = _field_root()
    ids: list[str] = []
    t_list: list[np.ndarray] = []
    p_list: list[np.ndarray] = []
    feats: list[list[float]] = []

    for site in sites:
        cmp = wtp.load_campaign(str(root / f"{site}.cmp"))
        site_code = float(_SITES.get(site, -1))
        for tname, test in cmp.tests.items():
            q = float(np.atleast_1d(np.asarray(test.pumpingrate.value, dtype=float))[0])
            pw_pos = np.asarray(cmp.wells[test.pumpingwell].coordinates.value, dtype=float)
            for ow, obs in test.observations.items():
                tt = np.atleast_1d(np.asarray(obs.time, dtype=float))
                ss = np.atleast_1d(np.asarray(obs.observation, dtype=float))
                m = np.isfinite(tt) & np.isfinite(ss) & (tt > 0)
                if m.sum() < min_points:
                    continue
                tt, ss = tt[m], ss[m]
                order = np.argsort(tt)
                tt, ss = tt[order], ss[order]
                well = cmp.wells[ow]
                r = float(np.linalg.norm(np.asarray(well.coordinates.value, dtype=float) - pw_pos))
                if r <= 0.1 or np.ptp(np.abs(ss)) < min_drawdown:
                    continue
                # drawdown convention: a net-negative series is a head signal -> flip to drawdown
                if ss[-1] < ss[0]:
                    ss = -ss
                if tt.size > max_points:  # decimate long series on a log-time grid
                    grid = np.unique(np.geomspace(tt[0], tt[-1], max_points))
                    ss = np.interp(np.log10(grid), np.log10(tt), ss)
                    tt = grid
                feats.append([
                    float(np.log10(r)),
                    float(np.log10(q)) if q > 0 else float("nan"),
                    site_code,
                    _well_scalar(well, "welldepth"),
                    _well_scalar(well, "screensize"),
                    _well_scalar(well, "aquiferdepth"),
                ])
                t_list.append(tt)
                p_list.append(ss)
                ids.append(f"{site[:2].upper()}_{tname}_{ow}")

    if not ids:
        raise ValueError(f"no usable field curves in {sites}")
    # impute NaN descriptor columns with the column median so the RF attribution never sees NaNs
    feat_arr = np.asarray(feats, dtype=float)
    for j in range(feat_arr.shape[1]):
        col = feat_arr[:, j]
        nan = ~np.isfinite(col)
        if nan.any():
            med = np.nanmedian(col)
            feat_arr[nan, j] = med if np.isfinite(med) else 0.0
    return {
        "ids": ids, "t": t_list, "p": p_list,
        "features": feat_arr.tolist(), "feature_names": list(DESCRIPTOR_COLUMNS),
        "n_available": len(ids),
    }

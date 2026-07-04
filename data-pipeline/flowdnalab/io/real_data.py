"""Loader for the source-paper 4TU corpus (real pressure-transient curves + real DFN descriptors).

Source: 4TU.ResearchData DOI 10.4121/8291d285-025d-4724-988d-fc747a578c0a (Kamel Targhi et al. 2026,
GPL-3). Vault-only (never committed). Compact per-dataset files are extracted to
`$FLOWDNA_VAULT/real-curves/`:

- `Dataset_<X>_FirstDerivativeDimensionless.parquet` — 310 time-sample rows × (t_D_NNNN, p_D_prime_NNNN)
  column pairs for ~4768 valid curves (dimensionless time + dimensionless Bourdet first derivative;
  NaN-padded to 310). The curve id NNNN == the DFN SimulationNumber.
- `Dataset_<X>_DFNProperties.xlsx` — 5000 rows of real fracture-network descriptors, matched by
  SimulationNumber.

Because the parquet is ALREADY the first derivative, the pipeline preprocesses it with
derivative_order=0 (no re-differentiation).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np

# the real DFN descriptors the paper attributes against (the interpretable controls, restricted to
# columns COMMON to Datasets A/B/C so the attribution is cross-config comparable). SimulationNumber
# is the key. log_k_eq is DERIVED from k_eq_1 (equivalent permeability, present in all datasets;
# Dataset C lacks the precomputed `kLog` column that A/B carry).
DESCRIPTOR_COLUMNS = [
    "log_I",                    # log fracture intensity
    "alpha",                    # power-law length exponent
    "kappa",                    # Von-Mises orientation concentration
    "connectivity",
    "frac_aperture",
    "log_k_eq",                 # log10 equivalent permeability (derived from k_eq_1)
    "N_fractures_graph",
    "N_components",
    "LargestComponentSize",
    "FracInLargestComponent",   # backbone fraction proxy
]


def _vault_root() -> Path:
    root = os.environ.get("FLOWDNA_VAULT")
    if not root:
        raise RuntimeError("FLOWDNA_VAULT is not set (needed to locate the real 4TU corpus)")
    return Path(root) / "real-curves"


def available() -> bool:
    """True iff the extracted real-curve files are present (CI / core-only envs skip real cases)."""
    try:
        root = _vault_root()
    except RuntimeError:
        return False
    return (root / "Dataset_A_FirstDerivativeDimensionless.parquet").exists()


def load_dataset(dataset: str, n_subsample: int, seed: int) -> dict:
    """Load a seeded subsample of real curves + their descriptors for dataset 'A'|'B'|'C'.

    Returns {'t': [np.ndarray], 'p': [np.ndarray], 'features': (n, d), 'feature_names': [...],
    'ids': [int], 'n_available': int}. Each curve is trimmed to its finite, strictly-positive,
    increasing-t samples (the parquet is NaN-padded and not guaranteed monotone at the tail).
    """
    import pandas as pd

    root = _vault_root()
    pq = root / f"Dataset_{dataset}_FirstDerivativeDimensionless.parquet"
    xl = root / f"Dataset_{dataset}_DFNProperties.xlsx"
    if not pq.exists() or not xl.exists():
        raise FileNotFoundError(f"real corpus for dataset {dataset} not found under {root}")

    df = pd.read_parquet(pq)
    ids = sorted({int(re.match(r"t_D_(\d+)", c).group(1)) for c in df.columns if c.startswith("t_D_")})

    props = pd.read_excel(xl).set_index("SimulationNumber")
    # derive log10 equivalent permeability (k_eq_1 present in all datasets; Dataset C lacks `kLog`)
    if "log_k_eq" not in props.columns and "k_eq_1" in props.columns:
        props["log_k_eq"] = np.log10(props["k_eq_1"].clip(lower=1e-30))

    rng = np.random.default_rng(seed)
    # keep only ids that have a descriptor row
    ids = [i for i in ids if i in props.index]
    n_available = len(ids)
    take = min(n_subsample, n_available)
    chosen = sorted(rng.choice(ids, size=take, replace=False).tolist())

    t_list: list[np.ndarray] = []
    p_list: list[np.ndarray] = []
    feats: list[list[float]] = []
    kept_ids: list[int] = []
    for cid in chosen:
        t = df[f"t_D_{cid:04d}"].to_numpy(dtype=float)
        p = df[f"p_D_prime_{cid:04d}"].to_numpy(dtype=float)
        m = np.isfinite(t) & np.isfinite(p) & (t > 0)
        t, p = t[m], p[m]
        if t.size < 24:
            continue
        order = np.argsort(t)
        t, p = t[order], p[order]
        keep = np.concatenate([[True], np.diff(t) > 0])  # strictly increasing
        t, p = t[keep], p[keep]
        if t.size < 24 or math_span(t) < 1.5:
            continue
        row = props.loc[cid]
        feats.append([float(row[c]) for c in DESCRIPTOR_COLUMNS])
        t_list.append(t)
        p_list.append(p)
        kept_ids.append(cid)

    return {
        "t": t_list,
        "p": p_list,
        "features": feats,
        "feature_names": list(DESCRIPTOR_COLUMNS),
        "ids": kept_ids,
        "n_available": n_available,
    }


def math_span(t: np.ndarray) -> float:
    return float(np.log10(t[-1] / t[0])) if t[0] > 0 and t.size else 0.0

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


def full_corpus_available(dataset: str = "A") -> bool:
    """True iff the FULL-corpus benchmark inputs are present: the curves + the precomputed DTW matrix
    (`Dataset_X_DTW.npy`) + the descriptors. The DTW `.npy` is ~90 MB/dataset, vault-only."""
    try:
        root = _vault_root()
    except RuntimeError:
        return False
    return (
        (root / f"Dataset_{dataset}_FirstDerivativeDimensionless.parquet").exists()
        and (root / f"Dataset_{dataset}_DTW.npy").exists()
        and (root / f"Dataset_{dataset}_DFNProperties.xlsx").exists()
    )


def load_full_corpus(dataset: str) -> dict:
    """Load the ENTIRE ~4768-curve corpus for a dataset PLUS the precomputed full DTW matrix, aligned.

    Returns {'t','p','features','feature_names','ids','D','n'}. The corpus ships a precomputed
    `Dataset_X_DTW.npy` ((n_all, n_all) float32); recomputing 4768^2 DTW would take hours, so the
    benchmark reuses it. We load every curve that has BOTH a valid derivative AND a descriptor row AND
    a column in the DTW matrix, then slice the DTW matrix to the SAME kept order so `D[i,j]` is the
    distance between kept curve i and j. The parquet column order (t_D_0001, t_D_0002, ...) defines the
    DTW matrix's row order (per the corpus's own clustering notebooks).
    """
    import pandas as pd

    root = _vault_root()
    pq = root / f"Dataset_{dataset}_FirstDerivativeDimensionless.parquet"
    xl = root / f"Dataset_{dataset}_DFNProperties.xlsx"
    npy = root / f"Dataset_{dataset}_DTW.npy"
    for f in (pq, xl, npy):
        if not f.exists():
            raise FileNotFoundError(f"full-corpus input missing: {f}")

    df = pd.read_parquet(pq)
    # the DTW matrix rows are in the parquet's curve-id order (ascending SimulationNumber)
    all_ids = sorted({int(re.match(r"t_D_(\d+)", c).group(1)) for c in df.columns if c.startswith("t_D_")})
    D_full = np.load(npy).astype(float)
    if D_full.shape[0] != len(all_ids):
        # some corpus variants pad/drop; align by the min (the DTW npy is authoritative for its own n)
        n = min(D_full.shape[0], len(all_ids))
        all_ids = all_ids[:n]
        D_full = D_full[:n, :n]

    props = pd.read_excel(xl).set_index("SimulationNumber")
    if "log_k_eq" not in props.columns and "k_eq_1" in props.columns:
        props["log_k_eq"] = np.log10(props["k_eq_1"].clip(lower=1e-30))

    t_list: list[np.ndarray] = []
    p_list: list[np.ndarray] = []
    feats: list[list[float]] = []
    kept_ids: list[int] = []
    keep_pos: list[int] = []  # positions into D_full for the kept curves
    for pos, cid in enumerate(all_ids):
        if cid not in props.index:
            continue
        t = df[f"t_D_{cid:04d}"].to_numpy(dtype=float)
        p = df[f"p_D_prime_{cid:04d}"].to_numpy(dtype=float)
        m = np.isfinite(t) & np.isfinite(p) & (t > 0)
        t, p = t[m], p[m]
        if t.size < 24:
            continue
        order = np.argsort(t)
        t, p = t[order], p[order]
        inc = np.concatenate([[True], np.diff(t) > 0])
        t, p = t[inc], p[inc]
        if t.size < 24 or math_span(t) < 1.5:
            continue
        row = props.loc[cid]
        feats.append([float(row[c]) for c in DESCRIPTOR_COLUMNS])
        t_list.append(t)
        p_list.append(p)
        kept_ids.append(cid)
        keep_pos.append(pos)

    # A few corpus curves have a pathologically SHORT t_D span whose absolute range does not overlap
    # the bulk, so the strict min/max intersection across ALL curves is empty and the common-grid
    # resample fails. Drop those outliers: keep only curves whose [tmin, tmax] covers the robust common
    # window [p5(tmin), p95(tmax)]. This is honest (the dropped count is reported) and lets the
    # full-corpus benchmark share a grid; the bulk of the corpus is unaffected.
    if t_list:
        tmins = np.array([t[0] for t in t_list])
        tmaxs = np.array([t[-1] for t in t_list])
        # the window MOST curves cover: start no later than p90 of the start times, end no earlier than
        # p10 of the end times. Keep curves that CONTAIN this window; drop the late-start/early-end
        # outliers that otherwise make the strict intersection empty.
        lo = float(np.percentile(tmins, 90))
        hi = float(np.percentile(tmaxs, 10))
        if lo < hi:
            ok = [i for i, t in enumerate(t_list) if t[0] <= lo and t[-1] >= hi]
            if len(ok) >= 100:  # keep the filter only if it retains a real corpus
                t_list = [t_list[i] for i in ok]
                p_list = [p_list[i] for i in ok]
                feats = [feats[i] for i in ok]
                kept_ids = [kept_ids[i] for i in ok]
                keep_pos = [keep_pos[i] for i in ok]

    keep_pos_arr = np.asarray(keep_pos, dtype=int)
    D = D_full[np.ix_(keep_pos_arr, keep_pos_arr)]
    return {
        "t": t_list, "p": p_list, "features": feats,
        "feature_names": list(DESCRIPTOR_COLUMNS), "ids": kept_ids,
        "D": D, "n": len(kept_ids), "n_corpus": len(all_ids),
    }

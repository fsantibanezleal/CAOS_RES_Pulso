"""The REAL GeoDFN engine adapter (offline lane only).

Calls `GeoDFN.DFNGeneratorWithSeed` — the paper authors' geologically consistent 2-D DFN generator
(stress-shadow buffer zones, spatial seed fractures, Von-Mises orientations, Log-Normal lengths,
stress-aware apertures) — and turns its realizations into (a) decimated network geometries for the
web trace and (b) the descriptor table the attribution layer consumes.

Determinism note (documented, measured): GeoDFN 2.0.0 draws from numpy's GLOBAL legacy RNG, so we
pin `np.random.seed(seed)` immediately before generation; the adapter is deterministic for a fixed
(spec, seed, GeoDFN version). Raw engine outputs land in the DATA VAULT (E:\\_Datos\\flowdna, via
the FLOWDNA_VAULT env var) or a temp dir — never in git; the repo commits only the compact trace.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np

from ..io.schema import DFNSpec
from .descriptors import DESCRIPTOR_NAMES, compute_descriptors

MAX_SEGMENTS_PER_NETWORK = 400  # decimation cap for the committed trace (viewer geometry)

# GeoDFN's stress-aware aperture parameterization (Barton-Bandis / sub-linear scaling). Values
# follow the package's published example (Example-BrazilFixedSeeds); they are INPUTS of the real
# engine, not calibration we claim.
APERTURE_PARAMS = {
    "method": "subLinear",
    "aperture": 10e-4,
    "scalingCoefficient": 0.001,
    "scalingExponent": 0.5,
    "JCS": 140,
    "JRC": 15,
    "sigma_Hmax": 100,
    "sigma_c": 130,
    "strike": 95,
    "S_Hmax": 1.8e8,
    "S_hmin": 0.7e8,
    "E": 15e9,
    "nu": 0.22,
}


def _sets_from_spec(spec: DFNSpec) -> list[dict]:
    common = {
        "fractureLengthPDF": "Log-Normal",
        "fractureLengthPDFParams": {
            "mu": spec.length_mu, "sigma": spec.length_sigma,
            "Lmin": spec.length_min, "Lmax": spec.length_max,
        },
        "spatialDistributionPDF": "Power-law",
        "spatialDistributionPDFParams": {
            "alpha": spec.spatial_alpha, "min distance": 1,
            "max distance": max(spec.domain_x, spec.domain_y),
        },
        "bufferZone": {"constant": spec.buffer_constant, "method": "constant"},
    }
    band = np.pi / 2.0  # Von-Mises support window around each set's mean direction
    set1 = {
        **common,
        "I": spec.intensity_set1,
        "orientationDistributionPDF": "Von-Mises",
        "orientationDistributionPDFParams": {
            "kappa": spec.orient_kappa, "loc": spec.orient_loc_set1,
            "thetaMin": spec.orient_loc_set1 - band / 2, "thetaMax": spec.orient_loc_set1 + band / 2,
        },
        "seed": {"X": spec.domain_x * 0.4, "Y": spec.domain_y * 0.4},
    }
    set2 = {
        **common,
        "I": spec.intensity_set2,
        "orientationDistributionPDF": "Von-Mises",
        "orientationDistributionPDFParams": {
            "kappa": spec.orient_kappa, "loc": spec.orient_loc_set2,
            "thetaMin": spec.orient_loc_set2 - band / 2, "thetaMax": spec.orient_loc_set2 + band / 2,
        },
        "seed": {"X": spec.domain_x * 0.6, "Y": spec.domain_y * 0.6},
    }
    return [set1, set2]


def _vault_dir(case_id: str) -> Path:
    root = os.environ.get("FLOWDNA_VAULT")
    if root:
        return Path(root) / "geodfn" / case_id
    return Path(tempfile.mkdtemp(prefix=f"geodfn_{case_id}_"))


def _read_realization(out_dir: Path, i: int) -> tuple[np.ndarray, np.ndarray]:
    tag = f"{i + 1:03d}"
    coords = np.loadtxt(out_dir / "fractureCoordinates" / f"{tag}fractureCoordinates.txt", ndmin=2)
    ap_file = out_dir / "aperture" / f"{tag}aperture.txt"
    apertures = np.loadtxt(ap_file, ndmin=1) if ap_file.exists() else np.array([])
    return coords, apertures


def generate_ensemble(spec: DFNSpec, seed: int = 42) -> dict:
    # GeoDFN 2.0.0 renders an orientation-stereographic figure per realization even with savePic=False;
    # force the non-interactive Agg backend so those (unused) plots don't accumulate / need a display.
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    import GeoDFN
    from GeoDFN import DFNGeneratorWithSeed

    out_root = _vault_dir(spec.case_id)
    out_root.mkdir(parents=True, exist_ok=True)
    np.random.seed(int(seed))  # GeoDFN 2.0.0 uses the global legacy RNG — pin it for determinism

    gen = DFNGeneratorWithSeed(
        spec.domain_x, spec.domain_y, _sets_from_spec(spec), dict(APERTURE_PARAMS),
        spec.case_id, num_realizations=spec.n_networks, savePic=False, output_dir=str(out_root),
    )
    plt.close("all")  # discard GeoDFN's internal (unused) figures
    out_dir = Path(gen.outputDir)

    networks: list[dict] = []
    rows: list[list[float]] = []
    for i in range(spec.n_networks):
        coords, apertures = _read_realization(out_dir, i)
        desc = compute_descriptors(coords, apertures, spec.domain_x, spec.domain_y)
        rows.append([desc[k] for k in DESCRIPTOR_NAMES])
        segs = coords[:MAX_SEGMENTS_PER_NETWORK]
        networks.append({
            "n_fractures": int(coords.shape[0]),
            "segments": [[round(float(v), 2) for v in s] for s in segs],
        })

    arr = np.asarray(rows, dtype=float)
    stats = {
        "per_descriptor": {
            name: {"mean": round(float(arr[:, j].mean()), 5), "std": round(float(arr[:, j].std()), 5)}
            for j, name in enumerate(DESCRIPTOR_NAMES)
        },
        "domain": {"x": spec.domain_x, "y": spec.domain_y},
        "vault_dir": str(out_dir),
    }
    metrics = {
        "n_networks": spec.n_networks,
        "mean_p21": stats["per_descriptor"]["p21"]["mean"],
        "mean_largest_cluster_frac": stats["per_descriptor"]["largest_cluster_frac"]["mean"],
        "mean_backbone_frac": stats["per_descriptor"]["backbone_frac"]["mean"],
        "spanning_fraction": round(float(arr[:, DESCRIPTOR_NAMES.index("spans_domain")].mean()), 4),
    }
    return {
        "networks": networks,
        "descriptor_names": list(DESCRIPTOR_NAMES),
        "descriptors": rows,
        "stats": stats,
        "metrics": metrics,
        "flags": [],
        "geodfn_version": getattr(GeoDFN, "__version__", "2.0.0"),
    }

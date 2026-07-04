"""FlowDNA cases spanning CATEGORIES (the coverage matrix; docs/cases/README.md documents it).

Two case kinds:
- 'study'  — a GeoType ensemble study (curves -> catalogue -> conformal -> attribution).
- 'dfn'    — a GeoDFN 2-D network ensemble (real generation engine + descriptors; transient
             simulation on these networks is the open-DARTS phase, and that pending status is
             carried honestly in the artifact).

Every case declares: id, category, spec, expected band (what a reservoir engineer should see),
real|synthetic flag. CTRL_single_regime is the degenerate control the engine must survive.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from ..io.schema import DartsWellTestSpec, DFNSpec, EnsembleSpec, RealDataSpec


@dataclass(frozen=True)
class Case:
    id: str
    category: str
    kind: str                       # 'study' | 'real' | 'darts' | 'dfn'
    spec: Union[EnsembleSpec, RealDataSpec, DartsWellTestSpec, DFNSpec]
    expected_band: str
    real_or_synthetic: str


CASES: list[Case] = [
    Case(
        "WR01_baseline", "dual-porosity: broad ensemble", "study",
        EnsembleSpec(case_id="WR01_baseline", kind="warren_root", n_curves=120,
                     omega_range=(0.01, 0.5), lam_range=(1e-8, 1e-4), noise_sd=0.01, derivative_order=1),
        "K in 2-5; valley-shape families split by omega depth + lambda timing; coverage >= 1-alpha",
        "synthetic-analytic",
    ),
    Case(
        "WR02_depth_families", "dual-porosity: valley depth (omega) — the HARD case", "study",
        EnsembleSpec(case_id="WR02_depth_families", kind="warren_root", n_curves=120,
                     omega_range=(0.006, 0.35), lam_range=(1e-6, 1e-6), noise_sd=0.01,
                     derivative_order=1, norm="max"),
        "lambda constant, only omega (valley DEPTH) varies. HONEST FINDING: DTW+clustering separates "
        "depth far less cleanly than timing (WR03) or family (MIX04) — the RF gate correctly reports "
        "low attributability. depth is an amplitude feature; DTW is a shape-alignment metric. This "
        "sensitivity contrast is a real result, not a tuning failure (see docs/cases).",
        "synthetic-analytic",
    ),
    Case(
        "WR03_timing_families", "dual-porosity: valley timing (lambda)", "study",
        EnsembleSpec(case_id="WR03_timing_families", kind="warren_root", n_curves=120,
                     omega_range=(0.05, 0.05), lam_range=(1e-9, 1e-4), noise_sd=0.01,
                     derivative_order=1),
        "omega constant -> GeoTypes separate by valley TIMING; attribution names log10_lam top "
        "(log10_omega is dropped as zero-variance, so lambda is the only shape control left)",
        "synthetic-analytic",
    ),
    Case(
        "MIX04_homog_vs_dp", "mixture: homogeneous vs dual-porosity", "study",
        EnsembleSpec(case_id="MIX04_homog_vs_dp", kind="mixture", n_curves=120,
                     homogeneous_fraction=0.5, omega_range=(0.01, 0.05),
                     lam_range=(1e-6, 1e-6), noise_sd=0.01, derivative_order=1, norm="max",
                     k_min=2, k_max=4),
        "lambda constant + deep valleys, norm=max -> the dominant shape difference is valley-vs-flat, "
        "so the catalogue isolates the homogeneous family and is_homogeneous dominates attribution",
        "synthetic-analytic",
    ),
    Case(
        "WR05_noisy", "robustness: measurement noise", "study",
        EnsembleSpec(case_id="WR05_noisy", kind="warren_root", n_curves=120,
                     omega_range=(0.01, 0.5), lam_range=(1e-8, 1e-4), noise_sd=0.06,
                     derivative_order=1),
        "same families as WR01 despite 6% noise (first derivative: p'' too noise-amplified here)",
        "synthetic-analytic",
    ),
    Case(
        "CTRL_single_regime", "control: degenerate single behaviour", "study",
        EnsembleSpec(case_id="CTRL_single_regime", kind="warren_root", n_curves=60,
                     omega_range=(0.049, 0.051), lam_range=(9.5e-7, 1.05e-6), noise_sd=0.02,
                     derivative_order=1),
        "one true behaviour: silhouette collapses (~<0.2), K unstable — must run without crashing",
        "synthetic-analytic",
    ),
    # REAL DATA — the source paper's actual 4TU corpus (Datasets A/B/C = 3 matrix-fracture
    # permeability configs). The parquet is already the dimensionless Bourdet first derivative, so
    # derivative_order=0. Vault-only; skipped when FLOWDNA_VAULT/real-curves is absent.
    Case(
        "REAL_A_lowperm", "real 4TU: dataset A (matrix-fracture perm config A)", "real",
        RealDataSpec(case_id="REAL_A_lowperm", dataset="A", n_subsample=400),
        "REAL curves: GeoTypes from the paper's own transients; attribution over real DFN "
        "descriptors (log_I intensity, connectivity, kLog permeability, backbone) should surface "
        "fracture intensity + backbone as top controls (the paper's finding)",
        "real-4tu",
    ),
    Case(
        "REAL_B_midperm", "real 4TU: dataset B (matrix-fracture perm config B)", "real",
        RealDataSpec(case_id="REAL_B_midperm", dataset="B", n_subsample=400),
        "REAL curves, config B: catalogue + conformal + attribution on real data; cross-config "
        "GeoType stability is the Benchmark question the paper studied (64.1% retention)",
        "real-4tu",
    ),
    Case(
        "REAL_C_highperm", "real 4TU: dataset C (matrix-fracture perm config C)", "real",
        RealDataSpec(case_id="REAL_C_highperm", dataset="C", n_subsample=400),
        "REAL curves, config C: catalogue + conformal + attribution on real data",
        "real-4tu",
    ),
    # open-DARTS transient simulation (Step A): a REAL single-phase drawdown validated against the
    # analytical infinite-acting radial-flow solution. The engine's first real simulated transient.
    Case(
        "DARTS_homog_anchor", "open-darts: homogeneous drawdown (analytical anchor)", "darts",
        DartsWellTestSpec(case_id="DARTS_homog_anchor"),
        "REAL open-DARTS single-phase drawdown reproduces infinite-acting radial flow: the Bourdet "
        "derivative plateaus at 0.5 and the skin-corrected p_wD matches the analytical line-source "
        "to ~1%. Proves the SOTA simulator is correct before the DFN mesh (Step B).",
        "simulated-darts",
    ),
    Case(
        "DFN06_sparse", "geodfn: sparse network ensemble", "dfn",
        DFNSpec(case_id="DFN06_sparse", n_networks=30, intensity_set1=0.025, intensity_set2=0.02),
        "stress-shadowed sparse nets: P21 ~0.045, near-zero intersections/backbone (GeoDFN buffer "
        "zones repel crossings at these intensities — measured, matches GeoDFN's own connectivity)",
        "synthetic-geodfn",
    ),
    Case(
        "DFN07_dense", "geodfn: dense network ensemble", "dfn",
        DFNSpec(case_id="DFN07_dense", n_networks=30, intensity_set1=0.07, intensity_set2=0.06),
        "~3x sparse P21 (~0.13) and more intersections, but connectivity stays LOW (GeoDFN "
        "reports ~4e-3): stress-shadow placement suppresses crossings; spanning clusters rare",
        "synthetic-geodfn",
    ),
]

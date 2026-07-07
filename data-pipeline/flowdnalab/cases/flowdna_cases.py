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

from ..io.schema import (
    DartsWellTestSpec,
    DfmStudySpec,
    DFNSpec,
    EnsembleSpec,
    FieldDataSpec,
    RealDataSpec,
)


@dataclass(frozen=True)
class Case:
    id: str
    category: str
    kind: str                       # 'study' | 'real' | 'darts' | 'dfn' | 'dfm' | 'field'
    spec: Union[EnsembleSpec, RealDataSpec, DartsWellTestSpec, DFNSpec, DfmStudySpec, FieldDataSpec]
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
    # open-DARTS Step B (the payoff): the geometry-only dfn cases GRADUATE to GeoType studies on
    # SIMULATED physics. An ensemble of GeoDFN networks is meshed + drawn down with open-DARTS, the
    # fracture aperture is swept (log-uniform) to span conductivity regimes, and the resulting
    # dimensionless Bourdet derivatives are clustered into GeoTypes + attributed + fidelity-gated
    # against the paper's MRST ensemble. Vault + open-darts only; skipped otherwise.
    Case(
        "DFM01_geotypes", "open-darts DFM: GeoTypes on simulated transients (aperture sweep)", "dfm",
        DfmStudySpec(case_id="DFM01_geotypes", n_networks=200, intensity_set1=0.05, intensity_set2=0.04,
                     frac_aper_min=2.0e-4, frac_aper_max=4.0e-3, fidelity_dataset="A", k_max=6),
        "REAL simulated physics at SCALE (200 GeoDFN networks): open-DARTS DFM drawdowns cluster into "
        "GeoTypes; the wide aperture sweep (2e-4 to 4e-3 m) spans tight to open-fracture conductivity "
        "regimes so attribution can surface log_frac_aper as a real control alongside intensity/"
        "backbone; the ensemble-median derivative passes the MRST fidelity gate (Dataset A).",
        "simulated-dfm",
    ),
    Case(
        "DFM02_dense", "open-darts DFM: dense-network GeoTypes on simulated transients", "dfm",
        DfmStudySpec(case_id="DFM02_dense", n_networks=200, intensity_set1=0.07, intensity_set2=0.06,
                     frac_aper_min=2.0e-4, frac_aper_max=4.0e-3, fidelity_dataset="C", k_max=6),
        "denser networks (higher P21, 200 realizations) simulated + clustered: more fracture-dominated "
        "early flow; GeoType families driven by aperture + connectivity; MRST fidelity vs Dataset C. "
        "(Intensity capped ~0.07: very dense nets can make gmsh meshing pathological; the crash-safe "
        "isolated worker skips those and the honest n_ok/n_fail is recorded.)",
        "simulated-dfm",
    ),
    Case(
        "DFM03_sparse", "open-darts DFM: sparse-network GeoTypes (low intensity end of the sweep)", "dfm",
        DfmStudySpec(case_id="DFM03_sparse", n_networks=200, intensity_set1=0.03, intensity_set2=0.025,
                     frac_aper_min=2.0e-4, frac_aper_max=4.0e-3, fidelity_dataset="B", k_max=6),
        "sparse networks (low P21, 200 realizations): weakly-connected DFNs where the transient is "
        "matrix-dominated for longer; the catalogue should separate the rare well-connected outliers "
        "from the bulk near-radial responses. Completes the intensity sweep (sparse/mid/dense across "
        "DFM03/DFM01/DFM02); MRST fidelity vs Dataset B.",
        "simulated-dfm",
    ),
    # REAL FIELD DATA (the methodology generalizes beyond fractured reservoirs): welltestpy transient
    # pumping-test campaigns from two aquifer field sites, clustered by Bourdet-derivative shape into
    # AquiferTypes + attributed to radial distance / pumping rate / site. MIT, vault-only; skipped
    # when FLOWDNA_VAULT/field is absent. Honest: aquifer != fractured reservoir; the diagnostic-plot
    # SHAPE methodology is what transfers, and T/S are unknown so clustering is on shape only.
    Case(
        "FIELD_horkheim", "real field: Horkheimer Insel pumping tests (AquiferTypes)", "field",
        FieldDataSpec(case_id="FIELD_horkheim", sites=("horkheim",), k_max=4),
        "REAL transient drawdown at the Horkheimer Insel alluvial aquifer (Heilbronn): ~28 obs curves "
        "over 4 pumping tests. HONEST FINDING: the derivatives are predominantly ONE infinite-acting "
        "radial (Theis) AquiferType (bulk pairwise shape-correlation ~0.87), so the site is fairly "
        "homogeneous; observation well p45 stands out as a distinct AquiferType (a boundary / "
        "heterogeneity signature), which the catalogue correctly isolates. One dominant type + a lone "
        "outlier means attribution is honestly withheld (nothing robust to attribute).",
        "field-pumping",
    ),
    Case(
        "FIELD_lauswiesen", "real field: Lauswiesen pumping tests (AquiferTypes)", "field",
        FieldDataSpec(case_id="FIELD_lauswiesen", sites=("lauswiesen",), k_max=4),
        "REAL high-resolution drawdown at the Lauswiesen gravel aquifer (Tuebingen): ~16 obs curves, "
        "long dense series (decimated to a log grid). Predominantly one radial AquiferType plus an "
        "outlier well; a well-characterized quasi-homogeneous gravel aquifer, so the shape catalogue is "
        "dominated by the infinite-acting response and attribution is withheld (one dominant type).",
        "field-pumping",
    ),
    Case(
        "FIELD_combined", "real field: both sites (does the SITE control the AquiferType?)", "field",
        FieldDataSpec(case_id="FIELD_combined", sites=("horkheim", "lauswiesen"), k_max=5),
        "REAL drawdown pooled across BOTH aquifers (~44 curves). HONEST cross-site result: the drawdown "
        "SHAPE is predominantly one infinite-acting-radial type regardless of site, distance or rate "
        "(the RF attribution gate sits near chance ~0.5 and WITHHOLDS importances), i.e. the two "
        "aquifers are hydraulically similar in their transient diagnostic signature. A real null result: "
        "the methodology transfers, and it honestly reports 'no strong controlling factor here'.",
        "field-pumping",
    ),
]

# Changelog

All notable changes to FlowDNA. Format: `X.XX.XXX` (display) — see `flowdnalab.__version__`. Keep `0.x`
while the DARTS transient-on-DFN lane and the real-data (4TU) studies are pending. Tag every release.

## [0.03.000] — 2026-07-03

### Added
- **Real-data integration** (issue #4): the source paper's ACTUAL 4TU corpus runs through the
  GeoType pipeline, not synthetic data.
  - `io/real_data.py` loads the dimensionless first-derivative curves (t_D, p_D') from the
    per-dataset parquet + matches each to its real DFN descriptors (log_I, alpha, kappa,
    connectivity, frac_aperture, log_k_eq, graph size/components/largest-cluster/backbone) by
    SimulationNumber; robust to the A/B vs C column differences (derives log_k_eq from k_eq_1).
  - New `real` case kind + `RealDataSpec`; `REAL_A_lowperm / REAL_B_midperm / REAL_C_highperm`
    (the three matrix-fracture permeability configs), seeded 400-curve subsamples, run through the
    SAME train/infer/evaluate/export stages (pipeline refactored to a shared `_run_study_stages`).
    `derivative_order=0` (the corpus is already the first derivative). CONTRACT 1 runs on real
    curves too; a provenance flag records the subsample.
  - Cases skip gracefully when the vault corpus is absent (CI / core-only).
- **Honest real-data findings** (docs/cases): real transients cluster far more cleanly than the
  analytic ensembles (silhouette 0.58–0.86 vs 0.13–0.25); the controlling descriptor is
  config-dependent (aperture A / length-exponent B / **intensity + permeability C**); REAL_C's top
  control `log_I` partially reproduces the paper's fracture-intensity headline on the high-perm
  config; conformal coverage meets target and the RF gate passes on all three.
- Real compact curve files extracted to the vault (`E:\_Datos\flowdna\real-curves`, GPL-3,
  never committed); `tests/test_real_data.py` (skipped without the corpus).

## [0.02.000] — 2026-07-03

### Added
- **The real FlowDNA engine core** (replaces the template's SIR example, issue #1):
  - `flowdnalab` consumes **pygeotypes** (CAOS_GeoTypes): Bourdet/p'' preprocessing, banded DTW
    (dtaidistance backend offline), PAM k-medoids, `Catalogue`, class-conditional split-conformal
    assignment (p-values, prediction sets, out-of-catalogue flag), gated RF + TreeSHAP attribution.
  - Staged pipeline for **study** cases: generate/ingest (CONTRACT 1 on every run) → shape space +
    descriptors → catalogue + calibration + attribution → conformal assignment of the held-out test
    slice → honest metrics (silhouette, K table, EMPIRICAL coverage vs target, OOD rate, gate) →
    `flowdna.trace/v1` artifact + manifest.
  - **GeoDFN** (MIT, the paper authors' generator) wired for real via
    `dfn/geodfn_adapter.py`: seeded generation into the vault, coordinate/aperture parsing,
    fracture-network descriptors (P21, length stats, orientation R, intersection graph,
    largest-cluster/backbone fractions, spanning flag, well distance) → `flowdna.dfn/v1` artifact.
  - Live lane (`live.py`, numpy/scipy + pygeotypes core only): generate a Warren-Root curve +
    conformally classify any curve against a baked trace (calibration scores ship in the trace).
  - 8 committed cases across 8 categories (6 studies + 2 GeoDFN ensembles), baked + manifested;
    the lane gate now MEASURES the live primitive (generate+classify), not the offline bake.
  - Ingestion contract for bring-your-own curves (reject/flag policy incl. a material-sign-flip
    noise heuristic) + ensemble-spec validation (incl. conformal OOD-reachability flag).
  - Frontend CONTRACT-2 mirror updated (`StudyTrace`/`DfnTrace` union) + minimal replay renderers
    (medoid curves chart, DFN network view); contract test now validates EVERY committed case.
  - docs/: frameworks (pygeotypes, GeoDFN, dtaidistance, open-DARTS status), cases taxonomy +
    coverage matrix (+ the honest p' vs p'' finding), data contract + vault manifest.
- **open-DARTS 1.5.0 verified installed** on Windows/py3.12 (`.venv-pipeline`); transient-on-DFN
  simulation is the explicit next phase — DFN artifacts carry `transient_simulation: pending`.

### Fixed
- Segment-intersection orientation test had a sign error on the `u` parameter (all crossings
  rejected → connectivity ≡ 0); fixed + pinned by `tests/test_descriptors.py`. Note: GeoDFN
  stress-shadow networks still measure LOW connectivity (engine's own `connectivity=3.6e-3` on the
  dense case) — that is the physics of buffer-zone placement, now stated in the expected bands.

## [0.01.000] — 2026-07-03

### Added
- Initial instantiation from the CAOS product-repo template (ADR-0057): offline `data-pipeline/`
  (`flowdnalab`), the two data contracts, the named staged pipeline, seeded RNG, compact trace,
  manifest, measured live-vs-precompute gate, cases-by-category registry, tests, CI, docs skeleton.

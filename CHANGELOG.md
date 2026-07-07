# Changelog

All notable changes to Pulso (renamed from FlowDNA 2026-07-04). Format: `X.XX.XXX` (display). Keep
`0.x` during the rebuild to the product bar (plan `_CAOS_MANAGE/plans/pulso/`). Tag every release.

## [0.13.000] — 2026-07-07

### Added: rebuild phase P1c, full-corpus benchmark cases (BENCH_A/B/C)
- **`benchmark` case kind**: clusters the ENTIRE ~4768-curve 4TU corpus per dataset (A/B/C), reusing
  the corpus's own precomputed DTW matrix (`Dataset_X_DTW.npy`, ~90 MB, vault-only) so it does not
  recompute 4768^2 DTW. The honest FULL-corpus counterpart to the 400-subsample App `real` cases.
- `io/real_data.load_full_corpus` (curves + descriptors + precomputed DTW, aligned, with a
  late-start/early-end outlier filter so the corpus shares a common log-time grid; ~20% dropped for
  B/C, reported); `stages/train.run` accepts a precomputed DTW + scales the PAM restart count down for
  large matrices (PAM is ~8 s/run at 2800 curves); `_mds_embedding` subsamples the SMACOF MDS for
  large n (embed a representative subset, place the rest at their nearest embedded neighbour).
- CONTRACT-3 caps the committed members to a stratified subsample (`MAX_MEMBERS`, medoids always
  included) so a full-corpus artifact stays under the 2 MB budget while `stats.n_members` reports the
  FULL population (`n_committed` the committed count). TS mirror + tests updated.
- Result: BENCH_A k=2 sil 0.57, top control `log_I` (fracture intensity) at gate 0.92 - partially
  reproduces the paper's headline finding on the full corpus. Feeds the Benchmark page (P5) + the
  cross-dataset retention Sankey (P3).
- Docs: `docs/cases` full-corpus benchmark section. Tests: `test_contract3` benchmark case
  (caps members, reports full n, byte budget).

## [0.12.000] — 2026-07-04

### Changed: rebuild phase P1b, scale the DFM ensembles + DFM CONTRACT-3
- **DFM ensembles scaled 34 -> 200 networks/case** across an intensity sweep: `DFM03_sparse`
  (P21 ~0.03), `DFM01_geotypes` (~0.05), `DFM02_dense` (~0.07), each with a wide aperture sweep
  (2e-4 to 4e-3 m). At 200 networks the attribution is genuinely powered (was underpowered at 34):
  DFM01 k=2, silhouette 0.62, 185/200 valid transients, MRST fidelity PASS (corr 0.92), attribution OK.
- **Fixed a P0.2 gap**: the DFM export composed on the v1 `build_study_trace`, so DFM cases never got
  the CONTRACT-3 full-ensemble fields. `run_dfm` now builds on `build_study_trace_v2` (members +
  envelopes + DTW matrix + MDS embedding), schema `pulso.dfm/v2`; frontend `isStudyTraceV2`/`isDfmTrace`
  match it. So a DFM study is now as rich as an analytic/real one.
- Suppressed a GeoDFN matplotlib figure leak (200 leaked polar figures at scale).
- The crash-safe isolated worker + result caching make the overnight bakes tractable; honest n_ok/n_fail
  recorded per case (dense networks that hit gmsh/Newton failures are skipped, not hidden).

## [0.11.001] — 2026-07-04

### Added: rebuild phase P1a, the GPU training lane (`.venv-train`)
- Isolated **`.venv-train`** with **torch 2.6.0+cu124** for the learned tier (P2), verified on the
  RTX 4070 Laptop (sm_89, CUDA 12.4). Kept SEPARATE from `.venv-pipeline` (which stays CPU-only for the
  deterministic offline bake + open-DARTS). Never global.
- `data-pipeline/requirements-train.txt` (onnx/onnxscript/scikit-learn/pandas/pyarrow; torch installed
  from the CUDA index, not pinned). `scripts/setup.{ps1,sh}` provision it opt-in (`-Train` /
  `PULSO_TRAIN=1`) so a CPU-only checkout still sets up. `scripts/gpu_smoke.py` asserts CUDA + runs a
  1D-conv forward/backward on the GPU (exits non-zero if the GPU is unusable). `.venv-train` gitignored.
- Docs: `docs/guides/03_gpu-lane.md` (recreate + verify the lane).

## [0.11.000] — 2026-07-04

### Added: rebuild phase P0.2, CONTRACT-3 full-ensemble study artifact (kills the 2-medoid toy)
- **`pulso.study/v2`**: the study artifact now commits the WHOLE ensemble per case, not the medoids +
  3 samples per GeoType (the "2 curves is all" toy Felipe flagged). New fields: `members` (every
  training curve, min/max-per-pixel decimated + cluster label), `envelopes` (per-cluster p10/p50/p90),
  `dtw` (the cluster-ordered DTW distance matrix, uint8-quantized, capped at 512), `embedding`
  (classical MDS 2D/3D from the DTW matrix + medoid indices), `stats`. A superset of v1 (renderers keep
  working); ~64 KB for a 60-curve study, ~250 KB for a 200-curve real case (well under the 2 MB budget).
- `stages/train.py` returns the DTW matrix + labels + `X_train` + the MDS embedding; `core/trace.py`
  `build_study_trace_v2` builds the artifact; `stages/export.py` emits it for all study/real/field
  cases. TS mirror `StudyTraceV2` + `isStudyTraceV2`; the frontend contract test asserts the v2 shape
  against the real baked artifacts.
- All 12 study/real/field cases re-baked to v2. Tests: `tests/test_contract3.py` (full-ensemble shape,
  byte budget, extrema-preserving decimation, determinism) + updated schema assertions across the
  suite. Full python suite (37) + tsc + vitest (6) green.
- Docs: `docs/architecture/08_data-contracts.md` (CONTRACT-3 section).

> Note: the RICH visualizations that CONSUME these fields (ensemble explorer, DTW heatmap, shape-space
> scatter, box-whisker, Sankey) are phase P3. P0.2 produces + validates the data.

## [0.10.000] — 2026-07-04

### Changed: rebuild phase P0.1, adopt the shared shell (was hand-rolled, no footer)
- **Product renamed FlowDNA to Pulso.** The old name was the source paper's "geological DNA" metaphor;
  the paper is inspiration plus one SOTA reference, not the product. Pulso: a well test is a pressure
  pulse; the product catalogues pressure pulses into flow-behaviour types. Repo `CAOS_RES_FlowDNA` to
  `CAOS_RES_Pulso` (old auto-redirects); frontend package `flowdna-frontend` to `pulso-frontend`.
- **Adopted `@fasl-work/caos-app-shell` (ADR-0016 + ADR-0058).** Replaced the hand-rolled header (which
  had NO footer and a stale, invisible version) with the shared shell: `AppShell` header (brand + six
  routes + GitHub/personal/portfolio + language + theme + the info button) and the shell FOOTER (name,
  version, "Developed by Felipe Santibanez-Leal", engine/data provenance + licenses, honest one-liner).
  Version single-sourced from `package.json` to the footer. The shell owns theme + language
  (`useShellLang`); removed the app-local `useUI` store and the i18next runtime init. Removed the
  hand-rolled `Header.tsx` + `ArchitectureModal.tsx`; the shell's `ArchitectureModal` renders the five
  Pulso arch tabs (bilingual body text now; deep SVG artwork in phase P4).
- Screenshot-verified in light + dark, 0 console errors; tsc + vitest (6) green.
- Docs: `docs/architecture/09_frontend-shell.md`.

> Note: this phase adopts the SHELL only. The App workbench, the ~22-method ladder, the
> rubric-compliant visualizations and the graduate-level page content are rebuilt in phases P2-P4.

## [0.07.000] — 2026-07-04 (as FlowDNA)

### Added — bringing FlowDNA to the product bar (deeper SOTA + live web)
- **The learned tier (deep-learning SOTA, the missing piece)**: three real deep models trained
  offline with PyTorch on the GeoType curves and exported to self-contained ONNX (opset 18,
  parity-checked < 1e-4) — a 1D-CNN GeoType classifier (test acc ~0.85), a convolutional autoencoder
  (latent + reconstruction-error OOD, MSE ~0.48), and a contrastive triplet encoder (retrieval@1
  ~0.91). `flowdnalab/deep/` + `scripts/train-deep.*`; models committed under `models/deep/` +
  `reference.json` (medoids + calibration + embedding/latent clouds). Offline hard-processing lane;
  torch is never shipped to the browser.
- **The live method-ladder web** (the bar's live + play-with-controls): the App's **Live lab** lands
  the user in a workbench — drag ω/λ/skin/noise and every tool recomputes on the tuned curve.
  - `frontend/src/engine/` TS live lane, parity-tested vs Python (< 2e-3): Warren-Root / homogeneous
    via Gaver-Stehfest + Bessel K0, Bourdet derivative, Sakoe-Chiba banded DTW, split-conformal.
    Classical diagnostics, SOTA DTW-to-medoid, and the novel conformal assignment run instantly.
  - **onnxruntime-web** runs the learned models **live in-browser** on the committed ONNX (WASM,
    no server, no COOP/COEP): CNN class probabilities, AE latent point + anomaly, contrastive
    embedding + nearest-neighbour retrieval.
  - `pages/LiveLab.tsx` with tiered method tabs (classical / SOTA / novel / learned), each a reactive
    live viz (log-log diagnostic, DTW/p-value bars, class probabilities, latent-space scatter).
  - Screenshot-verified: CNN predicts a GeoType at 99% live, AE anomaly + latent scatter, 0 console
    errors, EN/ES + light/dark.
- Methodology page gains the learned-tier section; `docs/frameworks/torch` + `docs/frameworks/onnxruntime-web`.
- Deploy target confirmed **GitHub Pages** (ADR-0055/0057); LICENSE (Apache-2.0) added.

## [0.06.000] — 2026-07-04

### Added
- **open-DARTS Step B foundation** (issue #13): DFN conformal meshing works. `dfn/dfn_mesh.py`
  turns a GeoDFN network (`[[x1,y1,x2,y2], ...]` segments) into a conformal discrete-fracture-matrix
  (DFM) `.msh` mesh via open-DARTS' `frac_preprocessing` (MIT, de Hoop & Voskov) + gmsh — the hard,
  novel part of the transient-on-DFN phase. The GeoDFN output format matches `frac_preprocessing`'s
  input, so the two engines compose directly; verified end-to-end in `tests/test_dfn_mesh.py`
  (GeoDFN network → conformal `.msh`). A package-inconsistency in open-darts 1.5.0 is worked around
  and documented (`create_geo_file` requires an `input_data` layer config that `frac_preprocessing`
  never passes; we inject a single-reservoir-layer default).
- The remaining Step-B sub-step (UnstructReservoir DFM drawdown on the mesh + MRST fidelity gate) is
  documented in `docs/frameworks/open-darts` with the concrete API path; the `dfn` cases keep
  `transient_simulation: pending` until it lands.

## [0.05.000] — 2026-07-04

### Added
- **The full ADR-0016 six-page web shell + ADR-0058 architecture modal** (issue #10), replacing the
  contract-exercising replay skeleton with the real product UI (mirrors CAOS_SIMLAB):
  - Header: brand + nav + architecture (ⓘ), language (EN/ES), theme (light/dark) and GitHub icons.
  - Six pages via react-router (hash): **App** (the workbench) + **Introduction / Methodology /
    Implementation / Experiments / Benchmark** as detailed prose + KaTeX equations + DOI references
    (not card grids).
  - **App = a real workbench** (ADR-0016, never meta-tabs): a first-level SOURCE selector
    (Synthetic ensemble / Real 4TU sample / open-DARTS anchor), then a case, then genuine domain
    views — GeoType catalogue (live cursor read-out), Classify-a-curve (conformal p-values +
    prediction set + OOD, stepping the baked assignments), Attribution (RF/SHAP importances, gated),
    Fracture network, DARTS validation, and Context. Every view runs on the committed artifact.
  - i18n EN (source) + ES translation (react-i18next; the permitted app-i18n Spanish per ADR-0066),
    light/dark theming (zustand + CSS variables, persisted), KaTeX, lucide icons, per-panel error
    boundary, zero internal repo paths in UI text.
  - Screenshot-verified across pages and both themes/languages (App workbench, Attribution,
    Methodology KaTeX, Experiments table, architecture modal, light+ES) — 0 console errors.

## [0.04.000] — 2026-07-04

### Added
- **open-DARTS transient simulation, Step A** (issue #7): a REAL single-phase drawdown validated
  against the analytical infinite-acting radial-flow solution.
  - `dfn/darts_welltest.py` builds a `StructReservoir` + `Geothermal` (single-phase water,
    isothermal) homogeneous reservoir with a rate-controlled centre well, run transiently over
    log-spaced report times; reads BHP(t) from the well time-data.
  - `dfn/darts_scaling.py` converts the physical BHP transient to dimensionless (t_D, p_wD) and
    validates it the well-test way: the Bourdet derivative must plateau at 0.5 (the radial-flow
    signature) AND the skin-corrected p_wD must match the analytical line-source
    (`pygeotypes.synthetic.homogeneous_pd`). A grid-block well's apparent skin is fit + removed
    (expected physics, not error).
  - **Validated:** derivative plateau error 0.041, skin-corrected rel-L2 0.011, apparent skin ~0.4
    — the SOTA simulator produces correct pressure transients. New `darts` case kind +
    `DartsWellTestSpec` + `DARTS_homog_anchor` case + `flowdna.darts/v1` artifact (sim vs analytical
    overlay). `tests/test_darts.py` (pure-numpy scaling tests always; the full engine run skipped
    without open-darts). Frontend `DartsChart` overlays simulated vs analytical p_wD + derivatives.
  - This de-risks the whole DARTS integration; **Step B** (mesh the GeoDFN networks into an
    `UnstructReservoir` + MRST fidelity gate) is the next phase — the `dfn` cases keep
    `transient_simulation: pending` until then.

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

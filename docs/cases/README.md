# Cases — the category taxonomy + coverage matrix

A FlowDNA case is a **study** (an ensemble of pressure-transient responses turned into a GeoType
catalogue with conformal assignment + attribution), a **dfn** ensemble (GeoDFN network generation +
fracture descriptors), a **darts** anchor (one open-DARTS drawdown validated vs the analytical
solution), or a **dfm** study (a GeoType study on open-DARTS DFM transients simulated over a GeoDFN
ensemble — the graduation of the `dfn` cases from geometry to simulated physics).
`registry.list_categories()` groups them; the **App shows ONE selected case**;
**Experiments/Benchmark show cross-case summaries by category** (never mixed into the App).

## Categories

| Category | Kind | What it exercises |
|---|---|---|
| dual-porosity: broad ensemble | study | the full (ω, λ) continuum; the baseline catalogue |
| dual-porosity: valley depth (omega) | study | λ pinned; GeoTypes must separate by valley DEPTH; attribution must name `log10_omega` |
| dual-porosity: valley timing (lambda) | study | ω pinned; separation by valley TIMING; attribution must name `log10_lam` |
| mixture: homogeneous vs dual-porosity | study | family separation (no-valley vs valley); `is_homogeneous` drives attribution |
| robustness: measurement noise | study | 6% multiplicative noise; same families must survive |
| control: degenerate single behaviour | study | ONE true behaviour: silhouette must collapse, the RF gate must withhold importances, the run must not crash |
| geodfn: sparse network ensemble | dfn | sub-percolation networks: low connectivity/backbone/spanning |
| geodfn: dense network ensemble | dfn | connected networks: high largest-cluster fraction, backbone, spanning |
| open-darts: homogeneous drawdown | darts | the SOTA simulator reproduces infinite-acting radial flow (derivative plateau 0.5) |
| open-darts DFM: GeoTypes on simulated transients | dfm | GeoType study on simulated DFM physics; aperture sweep; MRST fidelity gate; attribution over real descriptors + `log_frac_aper` |

## Coverage matrix (what each case proves)

| Case | Catalogue | Conformal (coverage/OOD) | Attribution | GeoDFN engine | Real data |
|---|---|---|---|---|---|
| WR01_baseline | ✔ | ✔ | ✔ (continuum: gate may honestly fail) | — | — |
| WR02_depth_families | ✔ | ✔ | ✔ target `log10_omega` | — | — |
| WR03_timing_families | ✔ | ✔ | ✔ target `log10_lam` | — | — |
| MIX04_homog_vs_dp | ✔ | ✔ | ✔ target `is_homogeneous` | — | — |
| WR05_noisy | ✔ | ✔ | ✔ under noise | — | — |
| CTRL_single_regime | ✔ (degenerate) | ✔ (stress) | gate must FAIL | — | — |
| REAL_A_lowperm | ✔ | ✔ | ✔ real DFN descriptors | — | ✔ 4TU |
| REAL_B_midperm | ✔ | ✔ | ✔ real DFN descriptors | — | ✔ 4TU |
| REAL_C_highperm | ✔ | ✔ | ✔ real DFN descriptors | — | ✔ 4TU |
| DFN06_sparse | — | — | descriptor table | ✔ | — |
| DFN07_dense | — | — | descriptor table | ✔ | — |
| DARTS_homog_anchor | — | — | — | — | simulated (validated vs analytic) |
| DFM01_geotypes | ✔ | ✔ | ✔ over descriptors + `log_frac_aper` | ✔ | simulated (MRST-gated) |
| DFM02_dense | ✔ | ✔ | ✔ | ✔ | simulated (MRST-gated) |
| *(next phase)* welltestpy field campaigns | ✔ | ✔ | ✔ | — | ✔ field |

## REAL DATA — the paper's own 4TU corpus (2026-07-03)

The `real` cases run the **source paper's actual pressure-transient curves** (4TU DOI
10.4121/8291d285, Datasets A/B/C = three matrix-fracture permeability configs) through the exact
same pygeotypes pipeline. Each dataset ships ~4768 dimensionless first-derivative curves (t_D,
p_D') + 5000 real DFN-descriptor rows; we take a seeded 400-curve subsample per case (the
full-corpus run is the offline Benchmark). Because the corpus IS already the Bourdet first
derivative, preprocessing uses `derivative_order=0`.

| Case | Config | K | Silhouette | Coverage | RF acc | Top descriptor(s) |
|---|---|---|---|---|---|---|
| REAL_A_lowperm | A | 2 | **0.72** | 0.94 | 0.84 | frac_aperture |
| REAL_B_midperm | B | 2 | **0.86** | 0.89 | 0.84 | alpha (length exponent) |
| REAL_C_highperm | C | 3 | 0.58 | 0.91 | 0.76 | **log_I (intensity)**, log_k_eq (permeability) |

**Findings (honest):**
- **Real transients cluster far more cleanly than the analytic ensembles** (silhouette 0.58–0.86 vs
  0.13–0.25 synthetic): real reservoir responses carry sharper behavioural structure than
  Warren-Root analytic curves. (Note: these are 400-curve subsamples; the paper reports 0.37–0.46
  over the full corpus at K=4 — the subsample + K choice inflates silhouette, so this is a
  *relative* not absolute claim, resolved in the Benchmark.)
- **The controlling descriptor is config-dependent**: aperture (low-perm A), fracture length
  exponent (mid-perm B), fracture **intensity + permeability** (high-perm C). REAL_C's top control
  `log_I` **partially reproduces the paper's headline finding** (fracture intensity among the top
  controls) on the high-permeability config.
- Conformal coverage meets the 0.85 target on all three real configs; the RF attribution gate
  passes on all three (unlike the synthetic depth case).
- Cross-config GeoType stability (the paper's 64.1% retention) is the Benchmark question, not baked
  into these per-config App cases.

## Findings worth recording (2026-07-03)

**1. p' vs p''.** The Freites-2023 recipe clusters the SECOND derivative p'' (offset removal on
measured data). On these analytic ensembles p'' at 96-point grids destroyed the class structure
(silhouette ~0.17, RF gate failing), while the FIRST Bourdet derivative preserved it. Both remain
supported (`EnsembleSpec.derivative_order`); the analytic cases pin `derivative_order=1`, and the
p''-vs-p' comparison is an explicit Benchmark axis for the real-data phase (where the offset problem
p'' exists for actually matters).

**2. DTW sensitivity is timing > family > depth (a genuine methodological result).** Baking the six
study cases (seed 42) gives a clean sensitivity ranking of what DTW+PAM can attribute:

| Case | Varying control | Silhouette | RF gate | Top descriptor |
|---|---|---|---|---|
| WR03 timing | λ (valley timing) | 0.25 | PASS | `log10_lam` ✓ |
| MIX04 family | homogeneous vs DP | 0.32 | PASS | `is_homogeneous` ✓ |
| WR05 noisy | ω + λ (6% noise) | 0.18 | PASS | `log10_omega` ✓ |
| WR01 baseline | ω + λ continuum | 0.18 | PASS | `log10_lam` (timing dominates) |
| WR02 depth | ω only (valley depth) | 0.14 | **FAIL** | none (low attributability) |
| CTRL | one regime | 0.14 | **FAIL** (by design) | none |

Valley **timing** (a phase feature) and **family** (valley vs no-valley) are cleanly recovered;
valley **depth** (a pure amplitude feature) is NOT, even with amplitude-preserving `norm=max` — DTW
is a shape-*alignment* metric, less sensitive to amplitude than to phase/topology. WR02 is kept as
the honest hard case: the RF accuracy gate correctly withholds a false attribution rather than
reporting depth-noise as a finding. This is exactly why the attribution stage HAS a gate.

**3. Encoding honesty.** Homogeneous curves have no (ω, λ); encoding those as an out-of-range
sentinel made `log10_lam` a perfect proxy for `is_homogeneous` and stole the attribution. Fixed by
imputing the dual-porosity population mean for homogeneous rows (`feature_extraction.py`), so
`is_homogeneous` is the only honest family discriminator.

**4. GeoDFN connectivity.** Stress-shadow buffer-zone placement keeps measured connectivity near
zero even for the dense case (engine's own `connectivity≈3.6e-3` at P21≈0.13); "dense ⇒ connected"
was a wrong prior, now stated in the DFN expected bands.

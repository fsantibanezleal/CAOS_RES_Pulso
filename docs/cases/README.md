# Cases — the category taxonomy + coverage matrix

A FlowDNA case is either a **study** (an ensemble of pressure-transient responses turned into a
GeoType catalogue with conformal assignment + attribution) or a **dfn** ensemble (GeoDFN network
generation + fracture descriptors; transient simulation on them is the open-DARTS phase).
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

## Coverage matrix (what each case proves)

| Case | Catalogue | Conformal (coverage/OOD) | Attribution | GeoDFN engine | Real data |
|---|---|---|---|---|---|
| WR01_baseline | ✔ | ✔ | ✔ (continuum: gate may honestly fail) | — | — |
| WR02_depth_families | ✔ | ✔ | ✔ target `log10_omega` | — | — |
| WR03_timing_families | ✔ | ✔ | ✔ target `log10_lam` | — | — |
| MIX04_homog_vs_dp | ✔ | ✔ | ✔ target `is_homogeneous` | — | — |
| WR05_noisy | ✔ | ✔ | ✔ under noise | — | — |
| CTRL_single_regime | ✔ (degenerate) | ✔ (stress) | gate must FAIL | — | — |
| DFN06_sparse | — | — | descriptor table | ✔ | — |
| DFN07_dense | — | — | descriptor table | ✔ | — |
| *(next phase)* 4TU real-curve studies + DARTS-simulated DFN studies + welltestpy field campaigns | ✔ | ✔ | ✔ (fracture descriptors) | ✔ | ✔ |

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

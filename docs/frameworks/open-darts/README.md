# open-DARTS — transient flow simulation on DFNs (the SOTA offline engine)

**What / why.** [open-DARTS](https://gitlab.com/open-darts/open-darts) (GPL-3, TU Delft) is the
selected simulator for pressure transients ON the GeoDFN networks: the only real DFN-capable flow
simulator that pip-installs natively on the Windows workstation (wheels for py3.10-3.13), with
wells first-class; GeoDFN lists DARTS among its supported downstream targets, and it comes from
the same TU Delft group as the source paper. Alternatives assessed in the SOTA dossier
(`_CAOS_MANAGE/wip/flowdna/research-sota-landscape-2026-07-03.md`): PorePy (WSL-only here, kept as
an optional cross-check), dfnWorks (Docker, the future 3-D path), MRST (MATLAB, dataset
provenance only).

**License posture.** GPL-3: open-DARTS is an OFFLINE engine dependency of the precompute lane —
never vendored into this repo, never shipped to the web artifact. Pipeline outputs (data) are not
derivative code; the FlowDNA repo stays non-GPL.

**Install status (verified 2026-07-03).** `pip install open-darts` → open-darts 1.5.0 +
open-darts-flash 0.12.2 installed into `.venv-pipeline` on Windows/Python 3.12; `import darts`
OK. Heavy deps it brings: vtk 9.6, gmsh 4.13, meshio, netCDF4, xarray.

**API path (verified 2026-07-03).** The concrete open-DARTS building blocks for a well test are
confirmed available in the installed 1.5.0:
- `darts.reservoirs.struct_reservoir.StructReservoir(nx, ny, nz, dx, dy, dz, permx/y/z, poro, ...)`
  for a structured single-phase model (the analytical-anchor step);
- `darts.reservoirs.unstruct_reservoir.UnstructReservoir` for the meshed DFN (the `dfm`/`edfm` path);
- `darts.physics.geothermal.physics.Geothermal` for single-phase water (the simplest liquid
  well-test physics; a dead-oil single-phase is the alternative);
- `DartsModel.set_wells / set_well_controls / run` for perforation, rate/BHP control and timestepping.

**Integration plan (two steps, both real, gated):**

*Step A — structured analytical anchor (de-risks the engine):* a `StructReservoir` homogeneous
single-phase drawdown at a rate-controlled centre well; compare the simulated BHP transient to the
analytical homogeneous-radial solution `pygeotypes.synthetic.homogeneous_pd` (late-time
`0.5(ln tD + 0.80907)`, derivative plateau 0.5). This proves open-DARTS produces correct transients
before any DFN complexity.

*Step B — the DFN model (the payoff):* mesh the GeoDFN 2-D networks (gmsh, in the DARTS toolchain)
into an `UnstructReservoir` with discrete fractures (DFM), single-phase drawdown, BHP recorded on a
log grid; fidelity-gated against the paper's MRST reference curves (4TU corpus in the vault).

**Integration status — Step A DONE (2026-07-04), Step B pending.**

*Step A (DONE, v0.04.000):* `dfn/darts_welltest.py` builds a real `StructReservoir` + `Geothermal`
(single-phase water, isothermal) homogeneous drawdown with a rate-controlled centre well, run
transiently over log-spaced report times; `dfn/darts_scaling.py` converts the simulated BHP(t) to
dimensionless (t_D, p_wD) and validates against `pygeotypes.synthetic.homogeneous_pd`. **Result: the
simulated Bourdet derivative plateaus at 0.5 (the infinite-acting radial-flow signature) and the
skin-corrected p_wD matches the analytical line-source to ~1% (rel-L2 0.011), with an apparent skin
of ~0.4 from the grid-block well.** Case `DARTS_homog_anchor`; validated in `tests/test_darts.py`.
Concrete API notes (for Step B): `DrawdownModel(DartsModel)` sets `self.reservoir` + `self.physics`
in `__init__`; `set_sim_params()` MUST precede `init()`; the Geothermal property container needs the
full `GeothermalIAPWSFluidProps` evaluators + custom rock evaluators; BHP is read from
`output.store_well_time_data()['well_<name>_BHP']`; a large domain + short test keep the response
infinite-acting.

*Step B — FOUNDATION DONE (2026-07-04): DFN conformal meshing works.* `dfn/dfn_mesh.py` turns a
GeoDFN network (`[[x1,y1,x2,y2], ...]` segments) into a conformal DFM `.msh` mesh via open-DARTS'
`frac_preprocessing` (MIT, de Hoop & Voskov) + gmsh: it cleans the network (intersections, merging),
writes a `.geo`, and meshes it. The GeoDFN output format matches `frac_preprocessing`'s input, so the
two engines compose directly. Verified end-to-end in `tests/test_dfn_mesh.py` (a GeoDFN network →
127 KB conformal `.msh`). Package-inconsistency workaround documented in the module:
`create_geo_file` reads `input_data['rsv_layers']` (+ over/under-burden layers) but
`frac_preprocessing` never passes `input_data`; we inject a single-reservoir-layer default (the 2-D
DFN → 1-layer 2.5-D reservoir a single-phase areal well test needs).

*Step B — DONE (2026-07-04): the UnstructReservoir DFM drawdown + the MRST fidelity gate + the
GeoType graduation.* `dfn/darts_dfm.py` loads the conformal `.msh` into an `UnstructReservoir`
(matrix perm via `permx/y/z`; fracture perm via `frac_aper` and the discretizer's cubic law
`perm_frac = (aper**2/12)*1e15` mD), categorizes every gmsh physical tag (matrix 9991-9995,
fractures >= 90000, box sides/caps otherwise — `read_physical_tags`, else `load_mesh` raises), places
a rate-controlled well on the nearest MATRIX cell at the domain centre (the `[frac, matrix]` cell
ordering), runs the exact Step A geothermal single-phase drawdown, and extracts (t_D, p_wD) + the
Bourdet derivative. **Result: a valid DFN drawdown (verified on the probe network in ~18 s: 64
fracture + 952 matrix cells, ~6 bar drawdown) with the characteristic morphology — a suppressed early
derivative from the conductive fracture network rising to a closed-domain late-time signature.**

`dfn/dfm_fidelity.py` gates the simulated derivative against the paper's MRST reference ENSEMBLE
(4TU `Dataset_<X>_FirstDerivativeDimensionless.parquet`, vault-only): ensemble-membership by p5-p95
band coverage + a scale-aligned shape metric (the paper normalizes t_D with the network k_eq, we with
matrix perm; the fitted scale ~0.06-0.11 implies k_eq/k_matrix ~10-17, a sensible fracture-enhanced
permeability). Honest + discriminating: Datasets A and C pass (shape corr 0.85-0.96), B fails (0.09);
a missing corpus returns `reference: none` and never passes.

`dfn/dfm_study.py` + the `dfm` case kind (`DFM01_geotypes`, `DFM02_dense`) are the GRADUATION: an
ensemble of GeoDFN networks is meshed + DFM-drawn-down (fracture aperture swept log-uniform to span
conductivity regimes), and the resulting dimensionless derivatives are clustered into GeoTypes (DTW
k-medoids + conformal split + RF/SHAP attribution over the real GeoDFN descriptors + `log_frac_aper`)
exactly like the analytic/real studies. The `flowdna.dfm/v1` artifact carries the study + a
representative transient + the MRST fidelity gate. `transient_simulation` is now a real, gated result
- NOT `pending`. Tests: `tests/test_dfm.py` (tag reader + gate honesty without the corpus + the full
engine run on a freshly-meshed network, skipped without open-darts).

*Original Step-B plan, step-by-step:*

1. Mesh the GeoDFN 2-D networks into a DARTS reservoir model (DFM/EDFM-style discrete fracture
   representation; gmsh is available via the DARTS toolchain).
2. Single-phase slightly-compressible drawdown with a rate-controlled well at the domain centre;
   record BHP vs time on a log grid.
3. **Fidelity gate before trusting our curves:** reproduce a subset of the paper's
   MRST-generated reference transients (4TU corpus, `Cross_Dataset_Comparison.zip` + DOE cases in
   the vault) within tolerance; the gate result gets recorded here and in the case manifests.
4. Feed the simulated ensembles into the same study pipeline (the `dfn` cases then graduate from
   geometry+descriptors to full GeoType studies on simulated physics).

Until then, every `flowdna.dfn/v1` artifact carries
`"transient_simulation": "pending (open-DARTS phase; ...)"` — the viewer must show that state,
never fake curves.

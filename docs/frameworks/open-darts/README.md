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

**Integration status: PENDING (honest).** Step-by-step:

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

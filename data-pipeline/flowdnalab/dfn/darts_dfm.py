"""open-DARTS DFM (discrete-fracture-matrix) drawdown on a meshed GeoDFN network (OFFLINE-only, Step B).

The payoff of the transient-on-DFN phase: a conformal DFM `.msh` (from `dfn.dfn_mesh.mesh_network`)
is loaded into an open-DARTS `UnstructReservoir`; a tight matrix + conductive discrete fractures
(fracture permeability = cubic-law from the aperture) produce a single-phase drawdown at a rate-
controlled centre well. The simulated BHP transient is made dimensionless and its Bourdet derivative
is what the fidelity gate compares to the paper's MRST reference ensemble. Physics is the exact Step A
geothermal single-phase water setup (the physics operates on the `conn_mesh`, so structured vs
unstructured is transparent).

Never imported by the live lane (open-darts is native vtk/gmsh/C++; GPL-3, offline dependency only).

Verified facts about the installed open-darts 1.5.0 that this module relies on
(see `_CAOS_MANAGE/wip/flowdna/step-b-dfm-plan-2026-07-04.md`):
- `UnstructReservoir(timer, mesh_file, permx, permy, permz, poro, rcond, hcap, frac_aper, ...)`;
  matrix conductivity from `permx/y/z`, fracture conductivity from `frac_aper` via
  `perm_frac = (aper**2/12)*1e15` mD (the discretizer's cubic law).
- Every gmsh physical tag must be assigned to matrix/fracture/boundary/... or `load_mesh` raises
  `ValueError`. The `frac_preprocessing` mesh uses matrix `Physical Volume` 9991-9995, fractures
  `Physical Surface(90000+i)`, box sides/caps `1..6` -> read dynamically by tag range.
- `centroid_all_cells` is ordered `[fracture ... matrix]`; matrix cells are indices
  `>= frac_cells_tot`. Well placed at the mesh bbox centre on the nearest MATRIX cell (a standard
  well-test geometry; avoids an extreme Peaceman index on a tiny fracture cell).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np

from ..io.schema import DfmDrawdownSpec
from .darts_scaling import to_dimensionless

# matrix (over/under-burden) volume tags written by frac_preprocessing; fractures are >= 90000
_MATRIX_TAGS = {9991, 9992, 9993, 9994, 9995}
_FRACTURE_TAG_MIN = 90000

# fluid/rock reference for the dimensionless scaling (single-phase liquid water @ ~350 K), matches Step A
WATER_VISC_CP = 0.35
TOTAL_COMPR_1BAR = 5e-5


def read_physical_tags(mesh_file: str | Path) -> dict:
    """Categorize every gmsh physical tag in `mesh_file` into matrix / fracture / boundary.

    Uses the `frac_preprocessing` tag convention (matrix in {9991..9995}, fractures >= 90000, box
    sides + caps otherwise). Asserts every tag present is covered so `UnstructReservoir.discretize`
    never hits its `ValueError('Unsupported physical tag')`. Returns
    {'matrix': [...], 'fracture': [...], 'boundary': [...]} with sorted int tags.
    """
    import meshio

    m = meshio.read(str(mesh_file))
    phys = m.cell_data_dict.get("gmsh:physical", {})
    tags: set[int] = set()
    for arr in phys.values():
        tags.update(int(t) for t in np.unique(arr))
    if not tags:
        raise ValueError(f"no gmsh:physical tags in {mesh_file}")

    matrix = sorted(t for t in tags if t in _MATRIX_TAGS)
    fracture = sorted(t for t in tags if t >= _FRACTURE_TAG_MIN)
    boundary = sorted(t for t in tags if t not in matrix and t not in fracture)
    if not matrix:
        raise ValueError(f"no matrix tag (expected one of {_MATRIX_TAGS}) in {mesh_file}; found {sorted(tags)}")
    if not fracture:
        raise ValueError(f"no fracture tags (>= {_FRACTURE_TAG_MIN}) in {mesh_file}; found {sorted(tags)}")
    covered = set(matrix) | set(fracture) | set(boundary)
    assert covered == tags, f"uncovered physical tags: {tags - covered}"
    return {"matrix": matrix, "fracture": fracture, "boundary": boundary}


def _report_times(total_day: float, n: int) -> np.ndarray:
    """Log-spaced report times (a well test samples early-time densely)."""
    return np.unique(np.concatenate([[0.0], np.logspace(-4, np.log10(total_day), n)]))


def run_dfm_drawdown(spec: DfmDrawdownSpec, seed: int = 42) -> dict:
    """Build + run the DARTS DFM drawdown on `spec.mesh_file`, return curves + mesh stats.

    Raises on a DARTS import/build failure (the caller documents the blocker honestly). The physics
    setup mirrors `darts_welltest.run_drawdown` (Step A) verbatim; only the reservoir (unstructured
    DFM from a `.msh`) and the well placement (nearest matrix cell) differ.
    """
    import darts
    from darts.engines import value_vector, well_control_iface
    from darts.models.darts_model import DartsModel
    from darts.physics.geothermal.geothermal import GeothermalIAPWSFluidProps, GeothermalIAPWSProperties
    from darts.physics.geothermal.physics import Geothermal
    from darts.physics.properties.iapws.custom_rock_property import (
        custom_rock_compaction_evaluator,
        custom_rock_energy_evaluator,
    )
    from darts.physics.properties.iapws.iapws_property import iapws_total_enthalpy_evalutor
    from darts.reservoirs.unstruct_reservoir import UnstructReservoir

    mesh_file = str(spec.mesh_file)
    if not os.path.isfile(mesh_file):
        raise FileNotFoundError(f"DFM mesh not found: {mesh_file}")
    ptags = read_physical_tags(mesh_file)

    outdir = Path(os.environ.get("FLOWDNA_VAULT", tempfile.mkdtemp())) / "darts" / spec.case_id
    outdir.mkdir(parents=True, exist_ok=True)

    # captured from the built model for the artifact (mesh stats + perforated-cell diagnostics)
    stats: dict = {}

    class DfmDrawdownModel(DartsModel):
        def __init__(self):
            super().__init__()
            self.set_reservoir()
            self.set_physics()

        def set_reservoir(self):
            self.reservoir = UnstructReservoir(
                self.timer, mesh_file=mesh_file,
                permx=spec.matrix_perm, permy=spec.matrix_perm, permz=spec.matrix_perm,
                poro=spec.matrix_poro, rcond=2.0, hcap=2200.0, frac_aper=spec.frac_aper,
            )
            # categorize physical tags BEFORE discretize (init() -> init_reservoir() -> discretize())
            self.reservoir.physical_tags["matrix"] = ptags["matrix"]
            self.reservoir.physical_tags["fracture"] = ptags["fracture"]
            self.reservoir.physical_tags["boundary"] = ptags["boundary"]

        def set_physics(self):
            # single-phase liquid water: keep enthalpy within the liquid range for ~350 K (Step A)
            self.physics = Geothermal(self.timer, n_points=128, min_p=1.0, max_p=400.0,
                                      min_e=1000.0, max_e=10000.0, cache=False)
            pc = GeothermalIAPWSProperties()
            pc.Mw = [18.015]
            pc.rock = [value_vector([spec.p_init, 1e-5, 273.15])]
            pc.rock_compaction_ev = custom_rock_compaction_evaluator(pc.rock)
            pc.rock_energy_ev = custom_rock_energy_evaluator(pc.rock)
            fluid = GeothermalIAPWSFluidProps()
            pc.temperature_ev = fluid.temperature_ev
            pc.density_ev = fluid.density_ev
            pc.viscosity_ev = fluid.viscosity_ev
            pc.relperm_ev = fluid.relperm_ev
            pc.enthalpy_ev = fluid.enthalpy_ev
            pc.saturation_ev = fluid.saturation_ev
            pc.conduction_ev = fluid.conduction_ev
            self.physics.add_property_region(pc)

        def set_wells(self):
            d = self.reservoir.discretizer
            n_frac = int(d.frac_cells_tot)
            centroids = np.asarray(d.centroid_all_cells, dtype=float)
            centre = (centroids.min(axis=0) + centroids.max(axis=0)) / 2.0
            # nearest MATRIX cell (indices >= n_frac in the [frac, matrix] ordering)
            mat = centroids[n_frac:]
            local = int(np.argmin(np.linalg.norm(mat - centre, axis=1)))
            well_cell = n_frac + local
            # distance from the perforated matrix cell to the nearest fracture cell (diagnostic)
            frac_dist = (float(np.min(np.linalg.norm(centroids[:n_frac] - centroids[well_cell], axis=1)))
                         if n_frac > 0 else float("nan"))
            stats.update(n_frac_cells=n_frac, n_mat_cells=int(d.mat_cells_tot),
                         well_cell=well_cell, well_xyz=centroids[well_cell].tolist(),
                         well_to_nearest_frac_m=round(frac_dist, 3),
                         domain=(centroids.max(axis=0) - centroids.min(axis=0)).tolist())
            self.reservoir.add_well("PROD")
            self.reservoir.add_perforation("PROD", res_cell_idx=well_cell,
                                           well_diameter=2.0 * spec.well_radius, skin=spec.well_skin)

        def set_initial_conditions(self):
            d = self.reservoir.discretizer
            n = int(d.mat_cells_tot + d.frac_cells_tot)
            enth = iapws_total_enthalpy_evalutor()
            h = enth.evaluate(value_vector([spec.p_init]), spec.temperature)
            self.physics.set_initial_conditions_from_array(
                mesh=self.reservoir.mesh,
                input_distribution={"pressure": np.full(n, spec.p_init),
                                    "enthalpy": np.full(n, h)},
            )

        def set_well_controls(self):
            for w in self.reservoir.wells:
                self.physics.set_well_controls(
                    wctrl=w.control, control_type=well_control_iface.VOLUMETRIC_RATE,
                    is_inj=False, target=spec.well_rate,
                )

    m = DfmDrawdownModel()
    # DFM cells (tiny fractures) are stiffer than the Step A structured grid: start small, ramp gently
    m.set_sim_params(first_ts=1e-5, mult_ts=1.2, max_ts=spec.total_time / 20.0,
                     runtime=spec.total_time, tol_newton=1e-2, tol_linear=1e-4)
    m.init(discr_type="tpfa", platform="cpu")
    m.set_output(output_folder=str(outdir))

    times = _report_times(spec.total_time, spec.n_report_steps)
    for k in range(1, times.size):
        m.run(days=float(times[k] - times[k - 1]), verbose=False)

    td = m.output.store_well_time_data(save_output_files=False)
    darts_version = getattr(darts, "__version__", "1.5.0")
    return _process(td, spec, times, stats, darts_version)


def _process(time_data: dict, spec: DfmDrawdownSpec, times: np.ndarray, stats: dict,
             darts_version: str) -> dict:
    """Convert the raw DARTS well time-data into the dimensionless drawdown + Bourdet derivative.

    Matrix-referenced dimensionless groups (the fracture flow shows as the early-time signature); the
    Bourdet derivative SHAPE is what the MRST fidelity gate compares, and it is robust to the choice
    of reference permeability (a constant k scales t_D in log space without changing the derivative
    structure).
    """
    from pygeotypes.preprocess import bourdet_derivative

    t = np.asarray(time_data.get("time", times[1:]), dtype=float)
    bhp_key = next((k for k in time_data if "BHP" in k or "bhp" in k), None)
    if bhp_key is None:
        raise RuntimeError(f"no BHP series in DARTS time_data (keys: {list(time_data)[:12]})")
    p_wf = np.asarray(time_data[bhp_key], dtype=float)
    n = min(t.size, p_wf.size)
    t, p_wf = t[:n], p_wf[:n]

    tD, pwD = to_dimensionless(
        t, p_wf, perm_mD=spec.matrix_perm, poro=spec.matrix_poro, visc_cP=WATER_VISC_CP,
        ct_1bar=TOTAL_COMPR_1BAR, rw_m=spec.well_radius, h_m=spec.ref_thickness,
        q_m3day=spec.well_rate, p_init_bar=spec.p_init,
    )
    order = np.argsort(tD)
    tD, pwD = tD[order], pwD[order]
    keep = tD > 0
    tD, pwD = tD[keep], pwD[keep]
    dpwD = bourdet_derivative(tD, pwD)

    # a valid drawdown is essentially non-increasing in BHP: allow a numerical bump that is small
    # RELATIVE to the drawdown (a few-milibar early-time wiggle on a multi-bar drawdown is solver
    # noise, not a physical non-monotonicity) rather than a brittle absolute-monotone test.
    max_bump_bar = float(max(0.0, np.diff(p_wf).max())) if p_wf.size > 1 else 0.0
    drawdown_bar = float(spec.p_init - p_wf.min())
    bump_tol = max(1e-2, 5e-3 * drawdown_bar)

    return {
        "curves": {"tD": tD.tolist(), "pwD": pwD.tolist(), "dpwD": dpwD.tolist()},
        "physical": {"matrix_perm_mD": spec.matrix_perm, "matrix_poro": spec.matrix_poro,
                     "frac_aper_m": spec.frac_aper, "perm_frac_mD": (spec.frac_aper**2) / 12 * 1e15,
                     "rw_m": spec.well_radius, "h_m": spec.ref_thickness, "q_m3day": spec.well_rate,
                     "p_init_bar": spec.p_init, "visc_cP": WATER_VISC_CP, "ct_1bar": TOTAL_COMPR_1BAR},
        "mesh_stats": stats,
        "metrics": {"n_points": int(tD.size), "drawdown_bar": round(drawdown_bar, 4),
                    "max_bump_bar": round(max_bump_bar, 6), "bump_tol_bar": round(bump_tol, 6),
                    "valid_drawdown": bool(max_bump_bar <= bump_tol and drawdown_bar > 1e-3)},
        "darts_version": darts_version,
    }

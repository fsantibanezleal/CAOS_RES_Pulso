"""open-DARTS structured single-phase drawdown well test (OFFLINE-only, Step A).

A homogeneous square reservoir with a rate-controlled centre well, run transiently with the DARTS
geothermal (single-phase water, isothermal) physics. The simulated BHP transient is converted to
dimensionless (t_D, p_wD) and validated against the analytical line-source homogeneous solution
(pygeotypes). This proves open-DARTS produces correct pressure transients before any DFN complexity.

Never imported by the live lane (open-darts is native vtk/gmsh/C++). Run outputs land in the vault.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np

from ..io.schema import DartsWellTestSpec
from .darts_scaling import to_dimensionless, validate_against_analytic

# fixed fluid/rock reference used for the dimensionless scaling (single-phase liquid water @ ~350 K)
WATER_VISC_CP = 0.35        # cP (liquid water near 350 K)
TOTAL_COMPR_1BAR = 5e-5     # 1/bar (rock + slightly-compressible water)


def _report_times(total_day: float, n: int) -> np.ndarray:
    """Log-spaced report times (a well test samples early-time densely)."""
    return np.unique(np.concatenate([[0.0], np.logspace(-3, np.log10(total_day), n)]))


def run_drawdown(spec: DartsWellTestSpec, seed: int = 42) -> dict:
    """Build + run the DARTS drawdown, return curves + validation. Raises on a DARTS import/build
    failure (the caller documents the blocker honestly)."""
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
    from darts.reservoirs.struct_reservoir import StructReservoir

    outdir = Path(os.environ.get("FLOWDNA_VAULT", tempfile.mkdtemp())) / "darts" / spec.case_id
    outdir.mkdir(parents=True, exist_ok=True)

    ic = min(spec.nx // 2, spec.nx - 1)
    jc = min(spec.ny // 2, spec.ny - 1)

    class DrawdownModel(DartsModel):
        def __init__(self):
            super().__init__()
            self.set_reservoir()
            self.set_physics()

        def set_reservoir(self):
            n = spec.nx * spec.ny * spec.nz
            self.reservoir = StructReservoir(
                self.timer, nx=spec.nx, ny=spec.ny, nz=spec.nz,
                dx=spec.dx, dy=spec.dy, dz=spec.dz,
                permx=spec.permeability, permy=spec.permeability, permz=spec.permeability,
                poro=spec.porosity, depth=1000.0,
            )
            self.reservoir.hcap = np.full(n, 2200.0)   # J/m3/K rock heat capacity
            self.reservoir.conduction = np.full(n, 2.0)

        def set_physics(self):
            # single-phase liquid: keep enthalpy within the liquid range for ~350 K water
            self.physics = Geothermal(self.timer, n_points=128, min_p=1.0, max_p=400.0,
                                      min_e=1000.0, max_e=10000.0, cache=False)
            # canonical IAPWS property container (matches GeothermalBase.set_physics)
            pc = GeothermalIAPWSProperties()
            pc.Mw = [18.015]
            pc.rock = [value_vector([spec.p_init, 1e-5, 273.15])]  # ref_p[bar], compressibility, ref_T[K]
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
            self.reservoir.add_well("PROD")
            self.reservoir.add_perforation("PROD", res_cell_idx=(ic + 1, jc + 1, 1),
                                           well_diameter=2.0 * spec.well_radius)

        def set_initial_conditions(self):
            # uniform P + enthalpy from (P, T): the PH-state initial enthalpy for single-phase water
            enth = iapws_total_enthalpy_evalutor()
            h = enth.evaluate(value_vector([spec.p_init]), spec.temperature)
            self.physics.set_initial_conditions_from_array(
                mesh=self.reservoir.mesh,
                input_distribution={"pressure": np.full(spec.nx * spec.ny * spec.nz, spec.p_init),
                                    "enthalpy": np.full(spec.nx * spec.ny * spec.nz, h)},
            )

        def set_well_controls(self):
            for w in self.reservoir.wells:
                self.physics.set_well_controls(
                    wctrl=w.control, control_type=well_control_iface.VOLUMETRIC_RATE,
                    is_inj=False, target=spec.well_rate,
                )

    m = DrawdownModel()
    m.set_sim_params(first_ts=1e-4, mult_ts=1.4, max_ts=spec.total_time / 10.0,
                     runtime=spec.total_time, tol_newton=1e-3, tol_linear=1e-4)
    m.init(discr_type="tpfa", platform="cpu")
    m.set_output(output_folder=str(outdir))

    times = _report_times(spec.total_time, spec.n_report_steps)
    for k in range(1, times.size):
        m.run(days=float(times[k] - times[k - 1]), verbose=False)

    td = m.output.store_well_time_data(save_output_files=False)
    darts_version = getattr(darts, "__version__", "1.5.0")
    return _process(td, spec, times, darts_version)


def _process(time_data: dict, spec: DartsWellTestSpec, times: np.ndarray, darts_version: str) -> dict:
    """Convert the raw DARTS well time-data into the dimensionless comparison + validation."""
    # find the BHP series + time vector in the time_data dict (keys are discovered at runtime)
    t = np.asarray(time_data.get("time", times[1:]), dtype=float)
    bhp_key = next((k for k in time_data if "BHP" in k or "bhp" in k), None)
    if bhp_key is None:
        raise RuntimeError(f"no BHP series in DARTS time_data (keys: {list(time_data)[:12]})")
    p_wf = np.asarray(time_data[bhp_key], dtype=float)
    n = min(t.size, p_wf.size)
    t, p_wf = t[:n], p_wf[:n]

    tD, pwD = to_dimensionless(
        t, p_wf, perm_mD=spec.permeability, poro=spec.porosity, visc_cP=WATER_VISC_CP,
        ct_1bar=TOTAL_COMPR_1BAR, rw_m=spec.well_radius, h_m=spec.dz,
        q_m3day=spec.well_rate, p_init_bar=spec.p_init,
    )
    v = validate_against_analytic(tD, pwD, spec.tol_rel_l2)
    return {
        "curves": {
            "tD": tD.tolist(), "pwD_sim": pwD.tolist(),
            "pwD_analytic": v.pop("pwD_analytic"),
            "dpwD_sim": v.pop("dpwD_sim"), "dpwD_analytic": v.pop("dpwD_analytic"),
        },
        "validation": v,
        "physical": {"perm_mD": spec.permeability, "poro": spec.porosity, "rw_m": spec.well_radius,
                     "h_m": spec.dz, "q_m3day": spec.well_rate, "p_init_bar": spec.p_init,
                     "visc_cP": WATER_VISC_CP, "ct_1bar": TOTAL_COMPR_1BAR},
        "metrics": {"rel_l2": v["rel_l2"], "plateau_error": v["plateau_error"],
                    "passed": v["passed"], "n_points": int(n)},
        "darts_version": darts_version,
    }

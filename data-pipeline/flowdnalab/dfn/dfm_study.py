"""DFM GeoType study on SIMULATED physics (OFFLINE-only, Step B graduation).

Turns an ensemble of GeoDFN networks into an ensemble of open-DARTS DFM pressure-transient
derivatives, so the geometry-only `dfn` cases graduate to full GeoType studies on simulated flow
(the same DTW k-medoids + conformal + attribution machinery the analytic and real studies use). Each
network is meshed (`dfn_mesh`) and drawn down (`darts_dfm`); failures (disconnected networks, meshing
or Newton blow-ups) are skipped and logged, never faked. The ensemble median derivative is
fidelity-gated against the paper's MRST reference (`dfm_fidelity`).

Never imported by the live lane (open-darts + GeoDFN + gmsh are native offline dependencies).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from ..io.schema import DfmStudySpec, DFNSpec
from .dfm_fidelity import fidelity_gate

# per-network wall-clock budget: open-DARTS on a pathological dense network can hang (Newton never
# converges) or segfault. The isolated worker (_dfm_worker) is killed past this and the network skipped.
_WORKER_TIMEOUT_S = 90


def _run_network_isolated(req: dict) -> dict:
    """Mesh + draw one network in a fresh process so a native hang/segfault is survivable. The worker
    writes its result to `req['result_file']` (stdout is polluted by open-DARTS/gmsh native chatter);
    a timeout or crash leaves no file -> reported as ok=False. Never raises."""
    result_file = Path(req["out_dir"]) / "result.json"
    result_file.parent.mkdir(parents=True, exist_ok=True)
    if result_file.exists():
        result_file.unlink()
    req = {**req, "result_file": str(result_file)}
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    env.setdefault("PYTHONUTF8", "1")
    try:
        subprocess.run(
            [sys.executable, "-m", "flowdnalab.dfn._dfm_worker"],
            input=json.dumps(req), capture_output=True, text=True,
            timeout=_WORKER_TIMEOUT_S, env=env,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout > {_WORKER_TIMEOUT_S}s (native hang)"}
    if not result_file.exists():
        return {"ok": False, "error": "worker left no result (native crash/segfault)"}
    try:
        return json.loads(result_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"ok": False, "error": "worker wrote invalid result JSON"}


def _resample(tD: np.ndarray, y: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """Interpolate a derivative onto a common log-t_D grid (NaN outside the curve's own span)."""
    m = np.isfinite(tD) & np.isfinite(y) & (tD > 0)
    tD, y = tD[m], y[m]
    order = np.argsort(tD)
    return np.interp(np.log10(grid), np.log10(tD[order]), y[order], left=np.nan, right=np.nan)


def run_dfm_ensemble(spec: DfmStudySpec, seed: int = 42) -> dict:
    """Generate + mesh + DFM-simulate `spec.n_networks` GeoDFN networks; return the per-network
    dimensionless derivatives (t + p lists, curves ARE the derivative), the matched GeoDFN
    descriptors, a representative transient, the mesh stats, the MRST fidelity gate on the ensemble
    median, and the skip log. Raises only on a total generation failure. Each network is meshed +
    drawn in an isolated subprocess (`_run_network_isolated`) so a native hang/segfault is survived."""
    from .geodfn_adapter import generate_ensemble

    dfn_spec = DFNSpec(
        case_id=spec.case_id, n_networks=spec.n_networks, domain_x=spec.domain_x, domain_y=spec.domain_y,
        intensity_set1=spec.intensity_set1, intensity_set2=spec.intensity_set2,
        length_mu=spec.length_mu, length_sigma=spec.length_sigma,
        length_min=spec.length_min, length_max=spec.length_max,
        orient_loc_set1=spec.orient_loc_set1, orient_loc_set2=spec.orient_loc_set2,
        orient_kappa=spec.orient_kappa, spatial_alpha=spec.spatial_alpha,
        buffer_constant=spec.buffer_constant,
    )
    ens = generate_ensemble(dfn_spec, seed=seed)
    networks = ens["networks"]
    descriptors = ens["descriptors"]
    # log10(aperture) joins the geometry descriptors: it is a real control on the flow regime, so
    # attribution can (and should) surface it alongside intensity/backbone.
    descriptor_names = list(ens["descriptor_names"]) + ["log_frac_aper"]

    # per-network fracture aperture, log-uniform over the sweep range (deterministic in seed)
    rng = np.random.default_rng(seed + 9973)
    apertures = 10.0 ** rng.uniform(np.log10(spec.frac_aper_min), np.log10(spec.frac_aper_max),
                                    size=len(networks))

    vault = Path(os.environ.get("FLOWDNA_VAULT", ".")) / "darts" / "dfm_study" / spec.case_id

    t_list: list[list[float]] = []
    p_list: list[list[float]] = []
    feats_ok: list[list[float]] = []
    sample_transient = None
    mesh_stats_sample = None
    fails: list[dict] = []

    for i, net in enumerate(networks):
        segs = np.asarray(net["segments"], dtype=float)
        if segs.ndim != 2 or segs.shape[0] < 2:
            fails.append({"network": i, "reason": "too few fractures"})
            continue
        aper = float(apertures[i])
        # mesh + draw in an isolated subprocess: a native hang/segfault on a pathological network is
        # survived (skipped + logged) instead of killing the ensemble bake.
        out = _run_network_isolated({
            "segments": segs.tolist(), "domain_x": spec.domain_x, "domain_y": spec.domain_y,
            "char_len": spec.char_len, "filename_base": f"net{i:03d}",
            "out_dir": str(vault / f"net{i:03d}"), "case_id": f"{spec.case_id}_{i:03d}",
            "matrix_perm": spec.matrix_perm, "matrix_poro": spec.matrix_poro, "frac_aper": aper,
            "well_rate": spec.well_rate, "total_time": spec.total_time,
            "n_report_steps": spec.n_report_steps, "ref_thickness": spec.ref_thickness,
            "seed": seed + i,
        })
        if not out.get("ok"):
            fails.append({"network": i, "reason": out.get("error", "unknown")})
            continue
        r = out["result"]
        if not r["metrics"]["valid_drawdown"]:
            fails.append({"network": i, "reason": f"invalid drawdown {r['metrics']}"})
            continue
        c = r["curves"]
        t_list.append(c["tD"])
        p_list.append(c["dpwD"])
        feats_ok.append([*descriptors[i], float(np.log10(aper))])
        if sample_transient is None:
            sample_transient = c
            mesh_stats_sample = {**r["mesh_stats"], "sample_frac_aper_m": aper}

    n_ok = len(t_list)
    if n_ok == 0:
        raise RuntimeError(f"DFM ensemble produced no valid transients ({len(fails)} failures)")

    # ensemble-median derivative on the common overlap -> MRST fidelity gate
    fidelity = {"reference": "none", "passed": False, "note": "ensemble too small to gate"}
    if n_ok >= 3:
        lo = max(np.nanmin([np.min(t) for t in t_list]), 1e-3)
        hi = min(np.nanmax([np.max(t) for t in t_list]), 1e9)
        grid = np.logspace(np.log10(lo), np.log10(hi), 60)
        stacked = np.vstack([_resample(np.asarray(t), np.asarray(p), grid)
                             for t, p in zip(t_list, p_list)])
        with np.errstate(invalid="ignore"):
            med = np.nanmedian(stacked, axis=0)
        gmask = np.isfinite(med)
        if gmask.sum() >= 4:
            fidelity = fidelity_gate(grid[gmask], med[gmask], dataset=spec.fidelity_dataset)

    return {
        "t": t_list, "p": p_list, "features": feats_ok, "feature_names": descriptor_names,
        "sample_transient": sample_transient, "mesh_stats": mesh_stats_sample,
        "fidelity": fidelity, "n_ok": n_ok, "n_fail": len(fails), "fails": fails[:12],
        "geodfn_version": ens.get("geodfn_version", "unknown"),
        "physical": {"matrix_perm_mD": spec.matrix_perm, "matrix_poro": spec.matrix_poro,
                     "frac_aper_min_m": spec.frac_aper_min, "frac_aper_max_m": spec.frac_aper_max,
                     "perm_frac_min_mD": (spec.frac_aper_min**2) / 12 * 1e15,
                     "perm_frac_max_mD": (spec.frac_aper_max**2) / 12 * 1e15,
                     "well_rate_m3day": spec.well_rate, "domain": [spec.domain_x, spec.domain_y]},
    }

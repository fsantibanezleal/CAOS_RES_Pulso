"""GeoDFN network → conformal DFM mesh (open-DARTS `frac_preprocessing` + gmsh). Step B foundation.

This is the hard, novel part of the transient-on-DFN phase: turning a stochastic discrete fracture
network into a conformal discrete-fracture-matrix (DFM) mesh that a reservoir simulator can use.
open-DARTS ships `frac_preprocessing` (MIT, de Hoop & Voskov, TU Delft) which cleans the network
(intersections, merging), writes a `.geo`, and runs gmsh to produce the `.msh`. Its input format is
`[[x1,y1,x2,y2], ...]` — exactly what `geodfn_adapter` produces, so the two engines compose directly.

Offline-only (native gmsh + heavy). The produced mesh is the input to the open-DARTS UnstructReservoir
DFM drawdown (the remaining Step-B sub-step; see docs/frameworks/open-darts).

Package inconsistency worked around (documented): in open-darts 1.5.0, `graph_code.create_geo_file`
reads `input_data['rsv_layers']` (+ over/under-burden layer fields) but `frac_preprocessing` does not
pass `input_data`, so the default path crashes. We inject a single-reservoir-layer default (no
over/under-burden) via a narrow wrapper — the 2-D DFN maps to a 1-layer 2.5-D reservoir, which is
exactly what a single-phase areal well test needs.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

# a single reservoir layer, no over/under-burden: the 2-D DFN -> 1-layer 2.5-D reservoir
_SINGLE_LAYER = {
    "rsv_layers": 1,
    "overburden_thickness": 0.0, "overburden_layers": 0,
    "overburden_2_thickness": 0.0, "overburden_2_layers": 0,
    "underburden_thickness": 0.0, "underburden_layers": 0,
    "underburden_2_thickness": 0.0, "underburden_2_layers": 0,
}


def _install_geo_workaround() -> None:
    """Inject the single-layer input_data default into create_geo_file (idempotent)."""
    import darts.tools.fracture_network.graph_code as gc
    import darts.tools.fracture_network.preprocessing_code as pc

    if getattr(gc.create_geo_file, "_flowdna_patched", False):
        return
    orig = gc.create_geo_file

    def patched(*args, **kwargs):
        if kwargs.get("input_data") is None:
            kwargs["input_data"] = dict(_SINGLE_LAYER)
        return orig(*args, **kwargs)

    patched._flowdna_patched = True  # type: ignore[attr-defined]
    gc.create_geo_file = patched
    pc.create_geo_file = patched


def mesh_network(
    segments: np.ndarray,
    output_dir: str | Path,
    domain_x: float,
    domain_y: float,
    char_len: float = 8.0,
    filename_base: str = "dfn",
    margin: float = 10.0,
) -> dict:
    """Mesh a 2-D fracture network into a conformal DFM `.msh`.

    segments: (n, 4) array of [x1, y1, x2, y2] fractures (e.g. from geodfn_adapter).
    Returns {'mesh_file', 'geo_file', 'n_fractures_raw', 'domain'}; raises on a meshing failure.
    """
    # gmsh CLI (venv Scripts, installed via the gmsh wheel) must be on PATH for the subprocess call
    scripts = str(Path(sys.executable).parent)
    if scripts not in os.environ.get("PATH", ""):
        os.environ["PATH"] = scripts + os.pathsep + os.environ.get("PATH", "")

    _install_geo_workaround()
    from darts.tools.fracture_network.preprocessing_code import frac_preprocessing

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    segs = np.ascontiguousarray(np.asarray(segments, dtype=float))
    box = np.array([[0.0, 0.0], [domain_x, 0.0], [domain_x, domain_y], [0.0, domain_y]])

    frac_preprocessing(
        frac_data_raw=segs,
        char_len=char_len,
        output_dir=str(out),
        filename_base=filename_base,
        box_data=box,
        margin=margin,
        mesh_clean=True,
        mesh_raw=False,
    )

    msh = sorted(out.glob(f"{filename_base}_*clean*.msh"))
    if not msh:
        raise RuntimeError(f"meshing produced no .msh in {out}")
    geo = sorted(out.glob(f"{filename_base}_*clean*.geo"))
    return {
        "mesh_file": str(msh[0]),
        "geo_file": str(geo[0]) if geo else None,
        "n_fractures_raw": int(segs.shape[0]),
        "domain": {"x": domain_x, "y": domain_y},
        "char_len": char_len,
    }

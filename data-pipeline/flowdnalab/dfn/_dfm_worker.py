"""Isolated worker: mesh + DFM-draw ONE GeoDFN network in a fresh process (OFFLINE-only).

open-DARTS is a native (C++) engine: a pathological dense network can make it HANG (Newton never
converges) or hard-CRASH (segfault) mid-run. Neither is catchable from the parent's `try/except` -
a hang blocks forever and a segfault takes down the interpreter. Running each network in this worker
subprocess makes both survivable: `dfm_study` calls it with a timeout and reads the exit code, so a
bad network is skipped (logged) instead of killing the whole ensemble bake.

Protocol: a single JSON request object on stdin (segments + domain + physics params + a `result_file`
path). The result JSON ({"ok": true, "result": {...}} or {"ok": false, "error": "..."}) is written to
`result_file`, NOT stdout: open-DARTS + gmsh spew native text to stdout/stderr, so the file is the
only clean channel. Exit 0 on a produced result (even an invalid drawdown), non-zero on an uncaught
failure; a native hang/segfault leaves no result_file, which the parent reads as a skip.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _write(path: str, obj: dict) -> None:
    Path(path).write_text(json.dumps(obj), encoding="utf-8")


def main() -> int:
    try:
        req = json.load(sys.stdin)
        result_file = req["result_file"]
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"bad request: {e}\n")
        return 2

    try:
        import numpy as np

        from .darts_dfm import run_dfm_drawdown
        from .dfn_mesh import mesh_network
        from ..io.schema import DfmDrawdownSpec

        segs = np.asarray(req["segments"], dtype=float)
        mout = mesh_network(segs, req["out_dir"], domain_x=req["domain_x"], domain_y=req["domain_y"],
                            char_len=req["char_len"], filename_base=req["filename_base"])
        spec = DfmDrawdownSpec(
            case_id=req["case_id"], mesh_file=mout["mesh_file"],
            matrix_perm=req["matrix_perm"], matrix_poro=req["matrix_poro"], frac_aper=req["frac_aper"],
            well_rate=req["well_rate"], total_time=req["total_time"],
            n_report_steps=req["n_report_steps"], ref_thickness=req["ref_thickness"],
        )
        r = run_dfm_drawdown(spec, seed=req["seed"])
        _write(result_file, {"ok": True, "result": {
            "curves": r["curves"], "metrics": r["metrics"], "mesh_stats": r["mesh_stats"]}})
        return 0
    except Exception as e:  # noqa: BLE001
        _write(result_file, {"ok": False, "error": str(e)[:200]})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

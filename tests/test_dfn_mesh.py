"""DFN conformal meshing (Step B foundation). Skipped without open-darts + GeoDFN; slow (gmsh)."""
import numpy as np
import pytest

darts = pytest.importorskip("darts")
GeoDFN = pytest.importorskip("GeoDFN")


def test_geodfn_network_meshes_to_dfm(tmp_path, monkeypatch):
    """A GeoDFN network is meshed into a conformal DFM .msh via open-DARTS frac_preprocessing +
    gmsh. This is the hard part of the transient-on-DFN phase; the mesh feeds the UnstructReservoir
    DFM drawdown (the remaining Step-B sub-step)."""
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))
    from flowdnalab.dfn import dfn_mesh, geodfn_adapter
    from flowdnalab.io.schema import DFNSpec

    spec = DFNSpec(case_id="T_MESH", n_networks=1, domain_x=100.0, domain_y=100.0,
                   intensity_set1=0.02, intensity_set2=0.015)
    res = geodfn_adapter.generate_ensemble(spec, seed=7)
    segs = np.array(res["networks"][0]["segments"], dtype=float)
    assert segs.shape[1] == 4 and len(segs) > 0

    out = dfn_mesh.mesh_network(segs, tmp_path / "mesh", domain_x=100.0, domain_y=100.0, char_len=8.0)
    from pathlib import Path

    mesh = Path(out["mesh_file"])
    assert mesh.exists() and mesh.stat().st_size > 1000
    assert mesh.suffix == ".msh"
    assert out["n_fractures_raw"] == len(segs)
    # the mesh file is a valid gmsh mesh (has a $Nodes / $Elements section)
    head = mesh.read_text(encoding="utf-8", errors="ignore")[:4000]
    assert "$MeshFormat" in head

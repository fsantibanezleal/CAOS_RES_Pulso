"""open-DARTS DFM drawdown (Step B) tests. The tag-reader + gate honesty are tested WITHOUT the
engine or the vault corpus; the full DFM simulation is skipped when open-darts/GeoDFN are absent
(CI / core-only) and is slow (gmsh + a transient reservoir run)."""
import numpy as np
import pytest

from flowdnalab.dfn.dfm_fidelity import fidelity_gate

try:
    import darts  # noqa: F401
    HAS_DARTS = True
except ImportError:
    HAS_DARTS = False


def test_fidelity_gate_is_honest_without_corpus(tmp_path, monkeypatch):
    """With no MRST corpus reachable the gate must report `reference: none` and NOT pass — a DFM
    curve is never silently 'validated' against a missing reference."""
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))  # empty -> available() is False
    tD = np.logspace(0, 5, 60)
    dpwD = 0.1 + 0.4 * (tD / tD.max())
    g = fidelity_gate(tD, dpwD, dataset="A")
    assert g["reference"] == "none"
    assert g["passed"] is False


def test_fidelity_gate_rejects_too_few_points(tmp_path, monkeypatch):
    """A degenerate (near-empty) simulated curve cannot pass the gate."""
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))
    g = fidelity_gate(np.array([1.0, 2.0]), np.array([0.1, 0.2]), dataset="A")
    assert g["passed"] is False


@pytest.mark.skipif(not HAS_DARTS, reason="open-darts not installed (offline-only heavy engine)")
def test_read_physical_tags_categorizes_dfm_mesh(tmp_path, monkeypatch):
    """Every gmsh physical tag in a GeoDFN DFM mesh is categorized (matrix/fracture/boundary) so
    UnstructReservoir.discretize never hits its 'Unsupported physical tag' ValueError."""
    pytest.importorskip("GeoDFN")
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))
    from flowdnalab.dfn import darts_dfm, dfn_mesh, geodfn_adapter
    from flowdnalab.io.schema import DFNSpec

    spec = DFNSpec(case_id="T_DFM_TAGS", n_networks=1, domain_x=100.0, domain_y=100.0,
                   intensity_set1=0.02, intensity_set2=0.015)
    net = geodfn_adapter.generate_ensemble(spec, seed=7)["networks"][0]
    segs = np.array(net["segments"], dtype=float)
    out = dfn_mesh.mesh_network(segs, tmp_path / "mesh", domain_x=100.0, domain_y=100.0, char_len=8.0)

    tags = darts_dfm.read_physical_tags(out["mesh_file"])
    assert tags["matrix"], "no matrix tag found"
    assert tags["fracture"], "no fracture tags found"
    assert all(t >= 90000 for t in tags["fracture"])  # frac_preprocessing convention
    assert all(t in (9991, 9992, 9993, 9994, 9995) for t in tags["matrix"])


@pytest.mark.skipif(not HAS_DARTS, reason="open-darts not installed (offline-only heavy engine)")
def test_dfm_drawdown_runs_and_produces_valid_transient(tmp_path, monkeypatch):
    """The full Step B run: mesh a GeoDFN network, load it into an UnstructReservoir, run the
    single-phase drawdown, and get a valid (non-increasing BHP, positive drawdown) transient with a
    Bourdet derivative. SLOW (~30 s)."""
    pytest.importorskip("GeoDFN")
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))
    from flowdnalab.dfn import darts_dfm, dfn_mesh, geodfn_adapter
    from flowdnalab.io.schema import DFNSpec, DfmDrawdownSpec

    spec_dfn = DFNSpec(case_id="T_DFM", n_networks=1, domain_x=100.0, domain_y=100.0,
                       intensity_set1=0.03, intensity_set2=0.02)
    net = geodfn_adapter.generate_ensemble(spec_dfn, seed=3)["networks"][0]
    segs = np.array(net["segments"], dtype=float)
    out = dfn_mesh.mesh_network(segs, tmp_path / "mesh", domain_x=100.0, domain_y=100.0, char_len=8.0)

    spec = DfmDrawdownSpec(case_id="T_DFM", mesh_file=out["mesh_file"], matrix_perm=1.0,
                           frac_aper=1.0e-3, well_rate=5.0, total_time=1.0, n_report_steps=20)
    r = darts_dfm.run_dfm_drawdown(spec, seed=1)

    assert r["metrics"]["valid_drawdown"] is True, f"not a valid drawdown: {r['metrics']}"
    assert r["mesh_stats"]["n_mat_cells"] > 0 and r["mesh_stats"]["n_frac_cells"] > 0
    c = r["curves"]
    assert len(c["tD"]) == len(c["pwD"]) == len(c["dpwD"]) > 5
    assert np.all(np.asarray(c["tD"]) > 0)

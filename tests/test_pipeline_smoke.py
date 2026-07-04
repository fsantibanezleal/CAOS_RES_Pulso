"""Pipeline smoke: the degenerate control runs without crashing (and reports honestly bad numbers),
the index builder inventories cases, and the GeoDFN lane produces geometry + descriptors (skipped
when the GeoDFN wheel is absent, e.g. the core-only environment)."""
import json

import pytest

from flowdnalab import pipeline, registry
from flowdnalab.cases.flowdna_cases import Case
from flowdnalab.core.manifest import build_index
from flowdnalab.io.schema import DFNSpec


def test_degenerate_control_runs_and_reports_low_quality():
    m = pipeline.precompute("CTRL_single_regime", seed=1)
    trace = json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))
    assert trace["schema"].startswith("flowdna.trace/")
    # one true behaviour: the clustering must NOT report a confident structure
    assert m["metrics"]["silhouette_train"] < 0.4
    # and the RF attribution gate must withhold importances (labels ~ noise within one regime)
    attr = m["metrics"]["attribution"]
    assert attr["status"] in ("ok", "skipped")
    if attr["status"] == "ok":
        assert attr["gate_passed"] is False


def test_registry_categories_cover_kinds():
    cats = registry.list_categories()
    assert len(cats) >= 6
    kinds = {c.kind for c in registry.list_cases()}
    assert kinds == {"study", "dfn"}


def test_index_builder():
    entries = [
        {"case_id": c.id, "category": c.category, "manifest_path": f"manifests/{c.id}.json"}
        for c in registry.list_cases()
    ]
    idx = build_index(entries)
    assert idx["schema"].startswith("flowdna.index/")
    assert idx["n_cases"] == len(entries)


def test_geodfn_lane_generates_geometry_and_descriptors(tmp_path, monkeypatch):
    pytest.importorskip("GeoDFN")
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path / "derived")
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "derived" / "manifests")
    # NOTE: keep the default 100x100 domain — GeoDFN's placement retry loop effectively hangs when
    # length_max (40) approaches the domain size (observed on a 60x60 attempt, 2026-07-03).
    tiny = Case(
        "T02_dfn_tiny", "test: tiny dfn", "dfn",
        DFNSpec(case_id="T02_dfn_tiny", n_networks=2,
                intensity_set1=0.03, intensity_set2=0.02),
        "two small networks with descriptors", "synthetic-geodfn",
    )
    m = pipeline._precompute_dfn(tiny, seed=3)
    assert m["artifact"]["trace_schema"].startswith("flowdna.dfn/")
    assert m["lane"] == "precompute"  # GeoDFN wheel is not Pyodide-safe -> never live
    trace = json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))
    assert len(trace["networks"]) == 2
    assert trace["networks"][0]["n_fractures"] > 0
    assert len(trace["descriptors"]) == 2
    assert len(trace["descriptor_names"]) == len(trace["descriptors"][0])
    assert "pending" in trace["transient_simulation"]

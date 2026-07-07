"""CONTRACT 2 (artifact) tests on a tiny study case: the manifest points to a real artifact with the
recorded byte size, the lane verdict agrees with the gate, the schema ids are FlowDNA's, and the
bake is deterministic (same seed -> byte-identical trace)."""
import json

import pytest

from flowdnalab import pipeline
from flowdnalab.cases.flowdna_cases import Case
from flowdnalab.io.schema import EnsembleSpec

TINY = Case(
    "T01_tiny", "test: tiny study", "study",
    EnsembleSpec(case_id="T01_tiny", kind="warren_root", n_curves=32, n_points=48,
                 dtw_window=6, k_min=2, k_max=3, alpha=0.25, noise_sd=0.01),
    "runs fast; k in 2-3", "synthetic-analytic",
)


@pytest.fixture(autouse=True)
def _isolated_derived(tmp_path, monkeypatch):
    """Test bakes go to tmp — the committed data/derived holds only the registry cases."""
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path)
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "manifests")


def test_manifest_matches_artifact_and_gate():
    m = pipeline._precompute_study(TINY, seed=7)
    artifact = pipeline.DERIVED / m["artifact"]["path"]
    assert artifact.exists(), "manifest points to a non-existent artifact"
    assert artifact.stat().st_size == m["artifact"]["bytes"], "manifest byte size drifted from the artifact"
    assert m["schema"].startswith("flowdna.manifest/")
    assert m["artifact"]["trace_schema"] in ("flowdna.trace/v1", "pulso.study/v2")
    assert m["lane"] in ("live", "precompute")
    assert m["gate"]["lane"] == m["lane"], "manifest lane disagrees with the gate verdict"
    # a study case's live primitive (generate one curve + classify) is numpy/scipy pure and its
    # trace is compact => must classify LIVE
    assert m["lane"] == "live", f"expected live lane, got {m['lane']} ({m['gate']['reasons']})"
    assert m["engine"]["package"] == "flowdnalab"
    assert "pygeotypes" in m["engine"]


def test_bake_is_deterministic_for_seed():
    a = pipeline._precompute_study(TINY, seed=11)
    ta = (pipeline.DERIVED / a["artifact"]["path"]).read_bytes()
    b = pipeline._precompute_study(TINY, seed=11)
    tb = (pipeline.DERIVED / b["artifact"]["path"]).read_bytes()
    assert ta == tb, "same (spec, seed) must produce a byte-identical trace"
    assert a["artifact"]["bytes"] == b["artifact"]["bytes"]


def test_metrics_are_honest_shape():
    m = pipeline._precompute_study(TINY, seed=7)
    mt = m["metrics"]
    assert 2 <= mt["k"] <= 3
    conf = mt["conformal"]
    assert 0.0 <= conf["empirical_coverage_test"] <= 1.0
    assert conf["n_test"] > 0
    trace = json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))
    assert trace["schema"] in ("flowdna.trace/v1", "pulso.study/v2")
    assert len(trace["medoids"]) == mt["k"]
    assert set(trace["calibration_scores"].keys()) == {str(g) for g in range(mt["k"])}

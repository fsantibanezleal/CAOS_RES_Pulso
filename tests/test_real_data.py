"""Real-data path tests. Skipped when the 4TU vault corpus is absent (CI / core-only envs) — the
loader's availability gate keeps the suite green without the ~25 GB corpus."""
import json

import pytest

from flowdnalab import pipeline
from flowdnalab.cases.flowdna_cases import Case
from flowdnalab.io import real_data
from flowdnalab.io.schema import RealDataSpec

pytestmark = pytest.mark.skipif(not real_data.available(),
                                reason="4TU vault corpus not available (FLOWDNA_VAULT/real-curves)")


@pytest.fixture(autouse=True)
def _isolated_derived(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path)
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "manifests")


def test_loader_matches_curves_to_descriptors():
    loaded = real_data.load_dataset("A", n_subsample=60, seed=1)
    assert 30 < len(loaded["ids"]) <= 60
    assert len(loaded["t"]) == len(loaded["p"]) == len(loaded["features"]) == len(loaded["ids"])
    assert len(loaded["feature_names"]) == len(loaded["features"][0])
    assert loaded["n_available"] > 4000  # ~4768 valid curves in dataset A
    # each curve is trimmed to finite, strictly-increasing, positive t
    import numpy as np
    for t in loaded["t"]:
        assert t[0] > 0 and np.all(np.diff(t) > 0) and t.size >= 24


def test_real_case_bakes_a_real_catalogue():
    tiny = Case(
        "T_REAL_tiny", "test: real tiny", "real",
        RealDataSpec(case_id="T_REAL_tiny", dataset="A", n_subsample=120, n_points=64,
                     dtw_window=8, k_min=2, k_max=3, alpha=0.2),
        "real curves, small subsample", "real-4tu",
    )
    m = pipeline._precompute_real(tiny, seed=3)
    assert m["real_or_synthetic"] == "real-4tu"
    assert m["artifact"]["trace_schema"].startswith("flowdna.trace/")
    trace = json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))
    assert trace["preprocessing"]["derivative_order"] == 0  # the corpus is already the derivative
    assert len(trace["medoids"]) == m["metrics"]["k"]
    # real transients cluster more cleanly than the analytic ensembles
    assert m["metrics"]["silhouette_train"] > 0.3
    # a provenance flag records the seeded subsample
    assert any("4TU Dataset A" in str(f) for f in m["flags"])


def test_real_bake_is_deterministic():
    tiny = Case(
        "T_REAL_det", "test: real det", "real",
        RealDataSpec(case_id="T_REAL_det", dataset="A", n_subsample=100, n_points=48,
                     dtw_window=6, k_min=2, k_max=2, alpha=0.25),
        "determinism", "real-4tu",
    )
    a = pipeline._precompute_real(tiny, seed=5)
    ta = (pipeline.DERIVED / a["artifact"]["path"]).read_bytes()
    b = pipeline._precompute_real(tiny, seed=5)
    tb = (pipeline.DERIVED / b["artifact"]["path"]).read_bytes()
    assert ta == tb, "same (spec, seed) must produce a byte-identical real-data trace"

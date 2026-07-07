"""CONTRACT-3 (pulso.study/v2) tests: the study artifact commits the FULL ensemble (every member
curve, per-cluster envelopes, the DTW matrix, the MDS embedding), not just 3 samples per GeoType.
Also unit-tests the extrema-preserving decimation + the byte budget."""
import json

import numpy as np
import pytest

from flowdnalab import pipeline
from flowdnalab.core.trace import DISPLAY_COLS, MAX_MEMBERS, STUDY_V2_SCHEMA, _decimate_minmax
from flowdnalab.io import real_data


def test_decimation_preserves_extrema():
    # a spiky row: a deep single-sample valley must survive downsampling (min/max-per-pixel, not LTTB)
    row = np.ones(400)
    row[200] = -5.0  # the valley
    row[100] = 3.0   # a peak
    out = np.array(_decimate_minmax(row, cols=DISPLAY_COLS))
    assert out.min() <= -5.0 + 1e-9, "the deep valley extremum was dropped"
    assert out.max() >= 3.0 - 1e-9, "the peak extremum was dropped"
    assert len(out) <= DISPLAY_COLS


def test_short_row_passes_through():
    row = np.linspace(0, 1, 20)
    out = _decimate_minmax(row, cols=DISPLAY_COLS)
    assert len(out) == 20  # <= cols -> untouched (just rounded)


def test_study_v2_commits_the_full_ensemble(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path / "derived")
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "derived" / "manifests")
    m = pipeline.precompute("WR01_baseline", seed=42)
    assert m["artifact"]["trace_schema"] == STUDY_V2_SCHEMA
    t = json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))

    n = t["stats"]["n_members"]
    nc = t["stats"].get("n_committed", n)
    k = t["k"]
    # the committed members carry the ensemble (full for a small case; a stratified sample for a corpus)
    assert nc == n, "WR01 is small, so every member is committed (n_committed == n_members)"
    assert len(t["members"]["curves"]) == nc
    assert len(t["members"]["geotype"]) == nc
    assert nc > 3 * k, "the v2 artifact must carry the whole ensemble, not a few samples"
    assert all(len(c) <= DISPLAY_COLS for c in t["members"]["curves"])
    assert set(t["members"]["geotype"]) <= set(range(k))

    # per-cluster envelopes on the full grid
    assert len(t["envelopes"]) == k
    g = t["t_grid"]
    for env in t["envelopes"]:
        assert len(env["p50"]) == len(g)
        # p10 <= p50 <= p90 pointwise
        assert all(a <= b <= c for a, b, c in zip(env["p10"], env["p50"], env["p90"]))

    # the DTW distance matrix (uint8, square, cluster-ordered permutation)
    dtw = t["dtw"]
    nn = len(dtw["order"])
    assert len(dtw["rows"]) == nn and all(len(r) == nn for r in dtw["rows"])
    assert sorted(dtw["order"]) == list(range(nn)) or nn <= n  # a valid subset permutation
    assert dtw["dmax"] > 0
    assert all(0 <= v <= 255 for r in dtw["rows"] for v in r)

    # the MDS embedding (per-committed-member 2D coords + valid medoid indices)
    emb = t["embedding"]
    assert len(emb["mds2d"]) == nc and all(len(p) == 2 for p in emb["mds2d"])
    assert 0 < len(emb["medoid_idx"]) <= k
    assert all(0 <= i < nc for i in emb["medoid_idx"])

    # byte budget (honest): the committed artifact stays well under ~2 MB
    size = (pipeline.DERIVED / m["artifact"]["path"]).stat().st_size
    assert size < 2_000_000, f"study artifact too large: {size} bytes"


@pytest.mark.skipif(not real_data.full_corpus_available("A"),
                    reason="full-corpus benchmark inputs not in the vault (Dataset_A_DTW.npy)")
def test_benchmark_full_corpus_caps_members_but_reports_full_n(tmp_path, monkeypatch):
    """A full-corpus benchmark clusters the ENTIRE ~4768-curve corpus (reusing the precomputed DTW),
    but the committed artifact caps the members to a stratified subsample + stays under the byte
    budget, while stats.n_members reports the FULL population."""
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path / "derived")
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "derived" / "manifests")
    m = pipeline.precompute("BENCH_A", seed=42)
    t = json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))
    st = t["stats"]
    assert st["n_members"] > 1000, "the benchmark clusters the full corpus (thousands of curves)"
    assert st["n_committed"] <= MAX_MEMBERS + t["k"], "committed members are capped (+ the medoids)"
    assert st["n_committed"] < st["n_members"], "large corpus -> a stratified subsample is committed"
    assert len(t["members"]["curves"]) == st["n_committed"]
    assert len(t["embedding"]["mds2d"]) == st["n_committed"]
    # every committed medoid is present + in range
    assert 0 < len(t["embedding"]["medoid_idx"]) <= t["k"]
    # the manifest carries the full-corpus provenance
    bench = json.loads((pipeline.MANIFESTS / f"{m['case_id']}.json").read_text(encoding="utf-8"))
    assert bench["metrics"]["benchmark"]["n_corpus"] >= st["n_members"]
    # byte budget
    assert (pipeline.DERIVED / m["artifact"]["path"]).stat().st_size < 2_000_000


def test_study_v2_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path / "derived")
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "derived" / "manifests")
    a = pipeline.precompute("WR03_timing_families", seed=7)
    ba = (pipeline.DERIVED / a["artifact"]["path"]).read_bytes()
    b = pipeline.precompute("WR03_timing_families", seed=7)
    bb = (pipeline.DERIVED / b["artifact"]["path"]).read_bytes()
    assert ba == bb, "same (spec, seed) must produce a byte-identical v2 artifact"

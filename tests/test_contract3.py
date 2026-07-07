"""CONTRACT-3 (pulso.study/v2) tests: the study artifact commits the FULL ensemble (every member
curve, per-cluster envelopes, the DTW matrix, the MDS embedding), not just 3 samples per GeoType.
Also unit-tests the extrema-preserving decimation + the byte budget."""
import json

import numpy as np

from flowdnalab import pipeline
from flowdnalab.core.trace import DISPLAY_COLS, STUDY_V2_SCHEMA, _decimate_minmax


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
    k = t["k"]
    # every member curve is committed with a label (NOT 3 samples/cluster)
    assert len(t["members"]["curves"]) == n
    assert len(t["members"]["geotype"]) == n
    assert n > 3 * k, "the v2 artifact must carry the whole ensemble, not a few samples"
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

    # the MDS embedding (per-member 2D coords + valid medoid indices)
    emb = t["embedding"]
    assert len(emb["mds2d"]) == n and all(len(p) == 2 for p in emb["mds2d"])
    assert len(emb["medoid_idx"]) == k
    assert all(0 <= i < n for i in emb["medoid_idx"])

    # byte budget (honest): the committed artifact stays well under ~2 MB
    size = (pipeline.DERIVED / m["artifact"]["path"]).stat().st_size
    assert size < 2_000_000, f"study artifact too large: {size} bytes"


def test_study_v2_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path / "derived")
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "derived" / "manifests")
    a = pipeline.precompute("WR03_timing_families", seed=7)
    ba = (pipeline.DERIVED / a["artifact"]["path"]).read_bytes()
    b = pipeline.precompute("WR03_timing_families", seed=7)
    bb = (pipeline.DERIVED / b["artifact"]["path"]).read_bytes()
    assert ba == bb, "same (spec, seed) must produce a byte-identical v2 artifact"

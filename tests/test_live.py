"""Live-lane tests: the browser primitives (generate + conformal classify against a baked trace)
work on the committed artifact contract alone, with pygeotypes core only."""
import numpy as np
import pytest

from flowdnalab import pipeline
from flowdnalab.cases.flowdna_cases import Case
from flowdnalab.io.schema import EnsembleSpec
from flowdnalab.live import classify_curve_json, generate_curve_json


@pytest.fixture(autouse=True)
def _isolated_derived(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "DERIVED", tmp_path)
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "manifests")


def _baked_trace():
    # frac_cal=0.3 of 48 -> ~14 calibration curves (~5-7 per class): the conformal p-value floor
    # 1/(n_c+1) stays well below alpha=0.25, so out-of-catalogue verdicts are reachable.
    tiny = Case(
        "T03_live", "test: live lane", "study",
        EnsembleSpec(case_id="T03_live", kind="warren_root", n_curves=48, n_points=48,
                     dtw_window=6, k_min=2, k_max=3, alpha=0.25, frac_cal=0.3, noise_sd=0.01),
        "live primitives", "synthetic-analytic",
    )
    m = pipeline._precompute_study(tiny, seed=5)
    import json
    return json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))


def test_generate_curve_shape_and_determinism():
    a = generate_curve_json(omega=0.05, lam=1e-6, noise_sd=0.02, seed=9)
    b = generate_curve_json(omega=0.05, lam=1e-6, noise_sd=0.02, seed=9)
    assert a["p"] == b["p"]
    assert len(a["t"]) == len(a["p"]) == len(a["derivative"])


def test_classify_in_catalogue_curve():
    trace = _baked_trace()
    c = generate_curve_json(omega=0.05, lam=1e-6, seed=1)
    out = classify_curve_json(trace, c["t"], c["p"])
    assert len(out["p_values"]) == trace["k"]
    assert 0 <= out["point_prediction"] < trace["k"]
    assert isinstance(out["prediction_set"], list)


def test_classify_alien_curve_flags_ood():
    trace = _baked_trace()
    t = np.logspace(2, 10, 200)
    p = np.sin(np.linspace(0, 40 * np.pi, 200)) * 5 + 10  # oscillation: no PTA shape at all
    out = classify_curve_json(trace, t.tolist(), p.tolist(), alpha=0.25)
    assert out["out_of_catalogue"] is True

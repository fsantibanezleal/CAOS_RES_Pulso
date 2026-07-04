"""CONTRACT 1 (ingestion) tests: good curves validate; broken curves are rejected with a reason;
suspicious curves are flagged; unphysical ensemble specs are rejected."""
import numpy as np

from flowdnalab.io.contract import validate_curves, validate_spec
from flowdnalab.io.schema import EnsembleSpec


def _good_curve(cid="ok", n=64, decades=3.0):
    t = np.logspace(1, 1 + decades, n)
    p = np.log(t) + 0.05 * np.log(t) ** 1.2
    return {"curve_id": cid, "t": t.tolist(), "p": p.tolist()}


def test_good_curves_accepted():
    rep = validate_curves([_good_curve()])
    assert rep.ok and len(rep.accepted) == 1 and not rep.rejected


def test_bad_curves_rejected_not_coerced():
    good = _good_curve()
    rows = [
        {"curve_id": "short", "t": [1, 2, 3], "p": [1, 2, 3]},                       # too few points
        {"curve_id": "neg_t", "t": [-1.0] + good["t"][1:], "p": good["p"]},          # t <= 0
        {"curve_id": "nonmono", "t": list(reversed(good["t"])), "p": good["p"]},     # not increasing
        {"curve_id": "nan", "t": good["t"], "p": [float("nan")] * len(good["t"])},   # NaN
        {"curve_id": "lenmix", "t": good["t"], "p": good["p"][:-3]},                 # unequal length
        {"curve_id": "narrow", **{k: v for k, v in _good_curve(n=40, decades=1.0).items() if k != "curve_id"}},
    ]
    rep = validate_curves(rows)
    assert len(rep.accepted) == 0
    assert len(rep.rejected) == len(rows)
    assert all("reason" in r for r in rep.rejected)


def test_noisy_curve_flagged_but_accepted():
    rng = np.random.default_rng(0)
    c = _good_curve("noisy")
    p = np.asarray(c["p"])
    c["p"] = (p + rng.normal(0, 0.35 * p.std(), size=p.shape)).tolist()
    rep = validate_curves([c])
    assert rep.ok
    assert any("noisy" in f["flag"] for f in rep.flagged)


def test_spec_validation():
    ok = EnsembleSpec(case_id="t_ok", n_curves=40)
    assert validate_spec(ok).ok
    bad = EnsembleSpec(case_id="t_bad", n_curves=40, omega_range=(0.2, 1.5))  # omega > 1
    rep = validate_spec(bad)
    assert not rep.ok and "omega" in rep.rejected[0]["reason"]
    tiny_alpha = EnsembleSpec(case_id="t_alpha", n_curves=40, alpha=0.01)  # OOD unreachable
    rep2 = validate_spec(tiny_alpha)
    assert rep2.ok and any("unreachable" in f["flag"] for f in rep2.flagged)

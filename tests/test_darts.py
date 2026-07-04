"""open-DARTS drawdown tests. The scaling/validation logic is tested WITHOUT the engine (pure
numpy); the full simulation test is skipped when open-darts is absent (CI / core-only) and is slow."""
import numpy as np
import pytest

from flowdnalab.dfn.darts_scaling import to_dimensionless, validate_against_analytic

try:
    import darts  # noqa: F401
    HAS_DARTS = True
except ImportError:
    HAS_DARTS = False


def test_scaling_self_consistency():
    """Feeding the analytical curve back must validate with zero skin + zero shape error."""
    from pygeotypes.synthetic import homogeneous_pd

    tD = np.logspace(1, 7, 80)
    pwD = homogeneous_pd(tD)
    v = validate_against_analytic(tD, pwD, tol_rel_l2=0.05)
    assert v["rel_l2"] < 1e-6
    assert v["plateau_error"] < 0.05
    assert abs(v["apparent_skin"]) < 1e-6
    assert v["passed"] is True


def test_skin_offset_is_corrected():
    """A constant skin offset must be absorbed (shape still matches) — the well-test convention."""
    from pygeotypes.synthetic import homogeneous_pd

    tD = np.logspace(1, 7, 80)
    pwD = homogeneous_pd(tD) + 1.3  # constant skin
    v = validate_against_analytic(tD, pwD, tol_rel_l2=0.05)
    assert abs(v["apparent_skin"] - 1.3) < 0.05
    assert v["rel_l2"] < 0.02  # shape unchanged after skin removal
    assert v["passed"] is True


def test_wrong_shape_fails():
    """A genuinely wrong shape (not a skin offset) must fail even after skin correction."""
    from pygeotypes.synthetic import homogeneous_pd

    tD = np.logspace(1, 7, 80)
    pwD = homogeneous_pd(tD) * 1.5  # slope wrong, not a constant offset
    v = validate_against_analytic(tD, pwD, tol_rel_l2=0.05)
    assert v["passed"] is False


def test_dimensionless_groups_are_ratios():
    """to_dimensionless returns finite positive tD and a pwD that scales linearly with drawdown."""
    t = np.array([0.01, 0.1, 1.0])
    p = np.array([199.0, 198.0, 197.0])
    tD, pwD = to_dimensionless(t, p, perm_mD=50, poro=0.2, visc_cP=0.35, ct_1bar=5e-5,
                               rw_m=0.1, h_m=10, q_m3day=20, p_init_bar=200)
    assert np.all(tD > 0) and np.all(np.isfinite(tD))
    assert np.all(pwD > 0) and pwD[2] > pwD[0]  # more drawdown -> higher pwD


@pytest.mark.skipif(not HAS_DARTS, reason="open-darts not installed (offline-only heavy engine)")
def test_darts_drawdown_validates_against_analytic(tmp_path, monkeypatch):
    """The full engine run: a homogeneous single-phase drawdown reproduces infinite-acting radial
    flow (derivative plateau at 0.5, skin-corrected shape match). SLOW (~30 s)."""
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))
    from flowdnalab.dfn import darts_welltest
    from flowdnalab.io.schema import DartsWellTestSpec

    # a smaller grid than the committed case to keep the test tractable, same physics
    spec = DartsWellTestSpec(case_id="T_DARTS", nx=61, ny=61, dx=20.0, dy=20.0,
                             permeability=50.0, well_rate=20.0, total_time=1.0, n_report_steps=30)
    out = darts_welltest.run_drawdown(spec, seed=1)
    v = out["validation"]
    assert v["passed"] is True, f"DARTS drawdown did not validate: {v}"
    assert v["plateau_error"] <= 0.1     # derivative sits at ~0.5
    assert v["rel_l2"] <= 0.05           # skin-corrected shape match
    assert len(out["curves"]["pwD_sim"]) == len(out["curves"]["pwD_analytic"])

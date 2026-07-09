"""P2e: attribution-and-assignment depth. Tests the pure helpers (ROM sweep, Mondrian p-values,
predictability-vs-K) with synthetic inputs, so they run without a full study bake."""
import numpy as np

from flowdnalab.methods.attribution_plus import _mondrian_pvals, _predictability_vs_k, _rom_sweep


def test_rom_sweep_flags_the_separating_descriptor():
    # descriptor 0 perfectly separates two labels; descriptor 1 is noise -> 0 should be most sensitive
    rng = np.random.default_rng(0)
    n = 80
    labels = np.array([i % 2 for i in range(n)])
    feats = np.column_stack([labels + rng.normal(0, 0.05, n), rng.normal(0, 1, n)])
    r = _rom_sweep(feats, ["separating", "noise"], labels, seed=1)
    assert r["descriptors"][0] == "separating"
    assert r["sensitivity"][0] > r["sensitivity"][-1]
    # each sweep records xs + argmax of equal length
    for s in r["sweeps"]:
        assert len(s["xs"]) == len(s["argmax"])


def test_mondrian_pvals_rank_convention():
    # calibration scores {0: sorted distances}; a test score at the max should get a small p-value,
    # a test score below the min should get p ~ 1 (very conforming)
    cal = {0: np.array([0.1, 0.2, 0.3, 0.4, 0.5]), 1: np.array([1.0, 2.0])}
    p_far = _mondrian_pvals(cal, np.array([0.6, 5.0]), k=2)
    p_near = _mondrian_pvals(cal, np.array([0.0, 0.0]), k=2)
    assert p_far[0] < p_near[0]         # a larger distance is less conforming (smaller p)
    assert 0 < p_far[0] <= 1 and 0 < p_near[0] <= 1


def test_predictability_vs_k_shape():
    # a clean 2-cluster distance matrix + separable descriptors
    rng = np.random.default_rng(0)
    n = 60
    labels = np.array([i % 2 for i in range(n)])
    x = labels + rng.normal(0, 0.1, n)
    D = np.abs(x[:, None] - x[None, :])
    feats = np.column_stack([x, rng.normal(0, 1, n)])
    out = _predictability_vs_k(D, feats, labels, range(2, 5), seed=1)
    assert [o["k"] for o in out] == [2, 3, 4]
    for o in out:
        assert "silhouette" in o and "rf_accuracy" in o
    # at K=2 (the true structure) the descriptors should predict the labels well
    acc2 = next(o["rf_accuracy"] for o in out if o["k"] == 2)
    assert acc2 is None or acc2 > 0.7

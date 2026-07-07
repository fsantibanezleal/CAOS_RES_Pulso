"""P2a: the distances-and-clustering method comparison. Runs the SOTA alternatives on a small
synthetic 2-behaviour set and checks the comparison shape + that a method that recovers the ground
truth scores a high ARI. Gracefully records skips when an optional lib is absent (CI/core-only)."""
import numpy as np

from flowdnalab.methods.clustering import compare_clusterings


def _two_behaviour_set(n=60, seed=0):
    """Two clearly separable curve shapes + their DTW-like distance matrix + true labels."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, 48)
    a = np.sin(2 * np.pi * t)      # behaviour A
    b = np.sign(t - 0.5) * 0.8     # behaviour B (a step)
    X, labels = [], []
    for i in range(n):
        base = a if i % 2 == 0 else b
        X.append(base + rng.normal(0, 0.05, t.size))
        labels.append(i % 2)
    X = np.array(X)
    labels = np.array(labels)
    from scipy.spatial.distance import pdist, squareform
    D = squareform(pdist(X, metric="euclidean"))
    return X, D, labels


def test_comparison_shape_and_recovers_structure():
    X, D, truth = _two_behaviour_set()
    r = compare_clusterings(X, D, truth, k=2, seed=1)
    assert set(r) >= {"reference", "methods", "subsampled"}
    assert r["reference"]["name"] == "DTW k-medoids"
    assert isinstance(r["methods"], list) and len(r["methods"]) >= 5
    for m in r["methods"]:
        assert "name" in m
        if not m.get("skipped"):
            assert m["ari"] is not None
    # at least one non-skipped method recovers the true 2-behaviour split well (ARI high)
    aris = [m["ari"] for m in r["methods"] if not m.get("skipped") and m.get("ari") is not None]
    assert any(a > 0.8 for a in aris), f"no method recovered the clear structure: {aris}"


def test_comparison_subsamples_large_inputs():
    # a large input must be compared on a <=600 subsample (recorded), so the bake stays cheap
    X, D, truth = _two_behaviour_set(n=1400, seed=2)
    r = compare_clusterings(X, D, truth, k=2, seed=1)
    assert r["subsampled"] is not None
    assert r["subsampled"].startswith("600/")

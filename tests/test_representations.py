"""P2b: the representations method group. Checks the block shape + that every 2D layout aligns
row-for-row with the input members, that functional PCA recovers the dominant mode, and that catch22 /
UMAP degrade gracefully rather than crash when optional libs are absent."""
import numpy as np

from flowdnalab.methods.representations import compute_representations


def _two_behaviour_set(n=60, seed=0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, 48)
    a = np.sin(2 * np.pi * t)
    b = np.sign(t - 0.5) * 0.8
    X, labels = [], []
    for i in range(n):
        X.append((a if i % 2 == 0 else b) + rng.normal(0, 0.05, t.size))
        labels.append(i % 2)
    return np.array(X), np.array(labels)


def test_block_shape_and_alignment():
    X, labels = _two_behaviour_set(n=60)
    r = compute_representations(X, labels, k=2, seed=1)
    assert set(r) == {"umap2d", "tsne2d", "fpca", "catch22"}
    # every present 2D layout has exactly one point per input member (row-for-row alignment)
    for key in ("umap2d", "tsne2d"):
        if r[key] is not None:
            assert len(r[key]) == X.shape[0]
            assert all(len(p) == 2 for p in r[key])
    fp = r["fpca"]
    assert len(fp["mean"]) == X.shape[1]
    assert len(fp["modes"]) == len(fp["explained_variance"])
    assert all(len(m) == X.shape[1] for m in fp["modes"])  # each mode is a shape on the t_grid
    if fp["scores2d"] is not None:
        assert len(fp["scores2d"]) == X.shape[0]


def test_fpca_dominant_mode_captures_the_split():
    # two clearly different shapes -> the first functional-PCA mode should dominate the variance
    X, labels = _two_behaviour_set(n=80)
    r = compute_representations(X, labels, k=2, seed=1)
    evr = r["fpca"]["explained_variance"]
    assert evr[0] > 0.5, f"first fPCA mode should dominate, got {evr}"


def test_catch22_table_or_skip():
    X, labels = _two_behaviour_set(n=40)
    r = compute_representations(X, labels, k=2, seed=1)
    c22 = r["catch22"]
    if c22.get("skipped"):
        assert "note" in c22
    else:
        assert len(c22["names"]) == 22
        assert len(c22["per_cluster"]) >= 1
        for row in c22["per_cluster"]:
            assert len(row["mean"]) == 22 and len(row["std"]) == 22

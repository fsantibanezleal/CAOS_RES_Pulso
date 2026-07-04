"""Fracture-descriptor unit tests (the intersection test pins the u-sign bug fixed 2026-07-03)."""
import numpy as np
import pytest

pytest.importorskip("networkx")

from flowdnalab.dfn.descriptors import DESCRIPTOR_NAMES, _seg_intersections, compute_descriptors


def test_crossing_pair_intersects():
    segs = np.array([
        [0.0, 0.0, 1.0, 1.0],   # diagonal
        [1.0, 0.0, 0.0, 1.0],   # anti-diagonal -> crosses at (0.5, 0.5)
    ])
    assert _seg_intersections(segs) == [(0, 1)]


def test_parallel_and_disjoint_do_not_intersect():
    segs = np.array([
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 1.0, 1.0],   # parallel
        [3.0, 3.0, 4.0, 4.0],   # far away
    ])
    assert _seg_intersections(segs) == []


def test_descriptors_on_connected_cross():
    segs = np.array([
        [10.0, 50.0, 90.0, 50.0],   # horizontal spanning fracture
        [50.0, 10.0, 50.0, 90.0],   # vertical spanning fracture -> connected cross
        [2.0, 2.0, 6.0, 6.0],       # isolated short fracture
    ])
    d = compute_descriptors(segs, apertures=np.array([1e-3, 2e-3, 3e-3]), domain_x=100, domain_y=100)
    assert set(d.keys()) == set(DESCRIPTOR_NAMES)
    assert d["n_fractures"] == 3
    assert d["intersections_per_fracture"] == pytest.approx(2 / 3)
    assert d["largest_cluster_frac"] == pytest.approx(2 / 3)
    assert d["spans_domain"] == 0.0  # 80 m < 0.9 * 100 m in both axes
    assert d["well_distance"] == 0.0  # the well (50,50) sits ON the cross
    assert d["p21"] == pytest.approx((80 + 80 + np.hypot(4, 4)) / 10000)

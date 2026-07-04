"""Fracture-network descriptors from 2-D segment geometry (numpy + networkx, offline lane).

These are the candidate controls the attribution layer ranks (the paper's finding: fracture
intensity, wellbore fracture length and backbone fraction dominate the flow behaviour). Computed
per network from the raw segments (x1, y1, x2, y2) + apertures:

- n_fractures, P21 (total length / area), mean/max/cv of length
- orientation dispersion: circular resultant length R (1 = perfectly aligned, 0 = uniform)
- mean aperture (from GeoDFN's Barton-Bandis/sub-linear stress-aware apertures)
- connectivity: segment-intersection graph -> intersections per fracture, largest-cluster
  fraction, backbone fraction (2-core of the largest cluster), and whether the largest cluster
  spans the domain in x or y (a percolation indicator)
- distance from the domain-centre "well" to the closest fracture (wellbore access proxy)
"""
from __future__ import annotations

import numpy as np

DESCRIPTOR_NAMES = [
    "n_fractures",
    "p21",
    "mean_length",
    "max_length",
    "cv_length",
    "orient_R",
    "mean_aperture",
    "intersections_per_fracture",
    "largest_cluster_frac",
    "backbone_frac",
    "spans_domain",
    "well_distance",
]


def _seg_intersections(segs: np.ndarray) -> list[tuple[int, int]]:
    """All intersecting pairs among n segments (O(n^2) exact orientation test; n<=few hundred)."""
    p = segs[:, 0:2]
    q = segs[:, 2:4]
    d = q - p
    n = segs.shape[0]
    pairs: list[tuple[int, int]] = []
    for i in range(n):
        # vectorized cross products of segment i against all j > i
        j = np.arange(i + 1, n)
        if j.size == 0:
            continue
        r = d[i]
        s = d[j]
        qp = p[j] - p[i]
        # p_i + t*r = p_j + u*s  =>  t = cross(qp, s)/cross(r, s), u = cross(qp, r)/cross(r, s)
        rxs = r[0] * s[:, 1] - r[1] * s[:, 0]
        qpxr = qp[:, 0] * r[1] - qp[:, 1] * r[0]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (qp[:, 0] * s[:, 1] - qp[:, 1] * s[:, 0]) / rxs
            u = qpxr / rxs
        hit = (np.abs(rxs) > 1e-12) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        for k in j[hit]:
            pairs.append((i, int(k)))
    return pairs


def compute_descriptors(segments: np.ndarray, apertures: np.ndarray | None,
                        domain_x: float, domain_y: float) -> dict[str, float]:
    """Descriptor vector for ONE network. segments: (n, 4) as x1,y1,x2,y2."""
    import networkx as nx

    segs = np.asarray(segments, dtype=float)
    n = segs.shape[0]
    if n == 0:
        return {k: 0.0 for k in DESCRIPTOR_NAMES}
    lengths = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
    area = domain_x * domain_y
    theta = np.arctan2(segs[:, 3] - segs[:, 1], segs[:, 2] - segs[:, 0])
    # axial data: double the angle so 0 and pi are the same orientation
    R = float(np.hypot(np.mean(np.cos(2 * theta)), np.mean(np.sin(2 * theta))))

    pairs = _seg_intersections(segs)
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(pairs)
    comps = list(nx.connected_components(g))
    largest = max(comps, key=len)
    largest_frac = len(largest) / n
    # backbone proxy: the 2-core of the largest cluster (dead-end fractures pruned)
    sub = g.subgraph(largest)
    core = nx.k_core(sub, k=2) if len(largest) > 2 else sub.subgraph([])
    backbone_frac = core.number_of_nodes() / n

    idx = np.array(sorted(largest), dtype=int)
    xs = np.concatenate([segs[idx, 0], segs[idx, 2]]) if idx.size else np.array([0.0])
    ys = np.concatenate([segs[idx, 1], segs[idx, 3]]) if idx.size else np.array([0.0])
    spans = 1.0 if (xs.max() - xs.min() >= 0.9 * domain_x or ys.max() - ys.min() >= 0.9 * domain_y) else 0.0

    # well at the domain centre: distance to the closest segment
    w = np.array([domain_x / 2.0, domain_y / 2.0])
    a = segs[:, 0:2]
    b = segs[:, 2:4]
    ab = b - a
    tt = np.clip(np.einsum("ij,ij->i", w - a, ab) / np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-12), 0, 1)
    proj = a + tt[:, None] * ab
    well_d = float(np.min(np.hypot(*(w - proj).T)))

    return {
        "n_fractures": float(n),
        "p21": float(lengths.sum() / area),
        "mean_length": float(lengths.mean()),
        "max_length": float(lengths.max()),
        "cv_length": float(lengths.std() / lengths.mean()) if lengths.mean() > 0 else 0.0,
        "orient_R": R,
        "mean_aperture": float(np.mean(apertures)) if apertures is not None and len(apertures) else 0.0,
        "intersections_per_fracture": float(2 * len(pairs) / n),
        "largest_cluster_frac": float(largest_frac),
        "backbone_frac": float(backbone_frac),
        "spans_domain": spans,
        "well_distance": well_d,
    }

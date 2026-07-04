"""Typed objects passed between pipeline stages — the inter-stage contract. Plain dataclasses (Pyodide-safe)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EnsembleSpec:
    """One validated ensemble-study operating point (a FlowDNA *case* of kind 'study').

    Defines how the pressure-transient ensemble is produced and how the GeoType catalogue is built:
    generation (analytic Warren-Root / mixture; later: real 4TU curves), preprocessing (grid,
    Bourdet window, derivative order, normalization), clustering (DTW band, K range) and the
    conformal split. A run is a pure function of (spec, seed).
    """

    case_id: str
    kind: str = "warren_root"            # 'warren_root' | 'mixture' (homogeneous + dual-porosity)
    n_curves: int = 120
    omega_range: tuple[float, float] = (0.01, 0.5)
    lam_range: tuple[float, float] = (1e-8, 1e-4)
    skin_range: tuple[float, float] = (0.0, 0.0)
    homogeneous_fraction: float = 0.0    # only used by kind='mixture'
    noise_sd: float = 0.01               # multiplicative log-normal measurement noise
    # preprocessing
    n_points: int = 96
    derivative_order: int = 2            # p'' per Freites et al. 2023
    L: float = 0.2                       # Bourdet smoothing window (log cycles)
    norm: str = "zscore"
    # clustering
    dtw_window: int = 10                 # Sakoe-Chiba half-width (grid cells)
    k_min: int = 2
    k_max: int = 6
    # conformal split (fractions of the ensemble; the rest is the training/catalogue part)
    frac_cal: float = 0.25
    frac_test: float = 0.25
    alpha: float = 0.15


@dataclass(frozen=True)
class DFNSpec:
    """One validated GeoDFN network-ensemble operating point (a FlowDNA *case* of kind 'dfn').

    Generates geologically consistent 2-D discrete fracture networks with the REAL GeoDFN engine
    (Kamel Targhi et al., MIT) — the fields mirror GeoDFN's own vocabulary (Log-Normal lengths,
    Von-Mises orientations, power-law spatial clustering, stress-shadow buffer zones, a spatial
    seed fracture per set). Two conjugate sets by default, like the companion paper's setups.
    Transient simulation on these networks is the open-DARTS phase; until then the artifact is
    geometry + descriptors (honestly labeled in the trace).
    """

    case_id: str
    n_networks: int = 30
    domain_x: float = 100.0              # domain size [m]
    domain_y: float = 100.0
    # per-set areal intensity P21 [1/m] (set 2 mirrors set 1 rotated ~90 deg)
    intensity_set1: float = 0.04
    intensity_set2: float = 0.03
    # Log-Normal fracture length parameters (GeoDFN vocabulary)
    length_mu: float = 2.0
    length_sigma: float = 0.6
    length_min: float = 2.0
    length_max: float = 40.0
    # Von-Mises orientation: mean direction [rad] + concentration
    orient_loc_set1: float = 0.8
    orient_loc_set2: float = 2.35        # ~ set1 + pi/2 (conjugate set)
    orient_kappa: float = 10.0
    # power-law spatial clustering + stress-shadow buffer
    spatial_alpha: float = 0.6
    buffer_constant: float = 1.0


@dataclass(frozen=True)
class RealDataSpec:
    """One validated REAL-data operating point (a FlowDNA *case* of kind 'real').

    Points at the paper's 4TU corpus (dimensionless first-derivative curves + real DFN descriptors)
    in the vault. The data IS already the Bourdet first derivative, so preprocessing uses
    derivative_order=0 (no re-differentiation). A seeded subsample keeps the committed artifact and
    the O(n^2) DTW matrix tractable; the full-corpus run is the offline Benchmark.
    """

    case_id: str
    dataset: str = "A"                   # 'A' | 'B' | 'C' (matrix-fracture permeability config)
    n_subsample: int = 400               # seeded curve subsample for the committed case
    # preprocessing (data is already p_D'): resample onto a common grid + normalize
    n_points: int = 96
    derivative_order: int = 0            # 0 = cluster the provided derivative as-is
    L: float = 0.2                       # unused at order 0; kept for schema uniformity
    norm: str = "zscore"
    # clustering
    dtw_window: int = 10
    k_min: int = 2
    k_max: int = 6
    # conformal split
    frac_cal: float = 0.25
    frac_test: float = 0.25
    alpha: float = 0.15


@dataclass(frozen=True)
class CurveSet:
    """The preprocessed-ready ensemble handed from preprocess -> feature_extraction."""

    case_id: str
    t: list[list[float]]                 # per-curve time arrays (may share one grid)
    p: list[list[float]]                 # per-curve pressure-change arrays
    params: list[dict]                   # per-curve generation params (omega/lam/skin | 'homogeneous')
    provenance: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StudyArrays:
    """feature_extraction output: shape-space matrix + descriptor table (inter-stage contract)."""

    case_id: str
    t_grid: list[float]                  # common log-uniform grid
    X: list[list[float]]                 # (n, n_points) preprocessed curves (derivative order per spec)
    feature_names: list[str]             # descriptor columns for attribution
    features: list[list[float]]          # (n, n_features)

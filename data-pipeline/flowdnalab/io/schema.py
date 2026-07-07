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
    # P2a: run the distances-and-clustering method comparison (soft-DTW/k-Shape/hierarchical/spectral/
    # HDBSCAN/baselines vs DTW-PAM). ~seconds/method, so opt-in on a representative subset of cases.
    compare_methods: bool = False


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
class DartsWellTestSpec:
    """One validated open-DARTS well-test operating point (a FlowDNA *case* of kind 'darts').

    Step A: a homogeneous structured single-phase drawdown validated vs the analytical solution.
    A rate-controlled centre well produces from a square homogeneous reservoir; the simulated BHP
    transient is compared to `pygeotypes.synthetic.homogeneous_pd`. Physical inputs are chosen so
    the dimensionless response is engine-independent (validation is on p_wD vs t_D).
    """

    case_id: str
    # grid (square areal, single layer). A large domain keeps the response infinite-acting (the
    # pressure front stays far from the boundary) over the whole test — validated 2026-07-04.
    nx: int = 101
    ny: int = 101
    nz: int = 1
    dx: float = 20.0                      # cell size [m]
    dy: float = 20.0
    dz: float = 10.0                      # thickness [m]
    # rock + fluid
    permeability: float = 50.0           # [mD]
    porosity: float = 0.2
    p_init: float = 200.0                # initial pressure [bar]
    temperature: float = 350.0           # [K] (geothermal single-phase water)
    # well
    well_rate: float = 20.0              # production rate [m3/day] (mild drawdown, stable Newton)
    well_radius: float = 0.1             # [m]
    # transient sampling
    total_time: float = 1.0              # [day] (short enough to stay infinite-acting)
    n_report_steps: int = 40             # log-spaced report times
    # validation (skin-corrected shape + derivative plateau, well-test convention)
    tol_rel_l2: float = 0.05


@dataclass(frozen=True)
class DfmDrawdownSpec:
    """One validated open-DARTS DFM (discrete-fracture-matrix) drawdown on a meshed GeoDFN network
    (a FlowDNA *case* of kind 'dfm'). Step B: the transient-on-DFN payoff.

    A conformal DFM `.msh` (from `dfn.dfn_mesh.mesh_network`) is loaded into an `UnstructReservoir`;
    a tight matrix + conductive fractures (fracture permeability = cubic-law from `frac_aper`)
    produce a single-phase drawdown at a rate-controlled centre well. The simulated BHP transient is
    made dimensionless (matrix-referenced) and its Bourdet derivative is fidelity-gated against the
    paper's MRST reference ensemble. Physics reuses the Step A geothermal single-phase water setup.
    """

    case_id: str
    mesh_file: str                        # conformal DFM `.msh` (vault path; never committed)
    # rock + fracture (matrix perm sets the matrix; frac_aper sets fracture perm via a^2/12 cubic law)
    matrix_perm: float = 1.0             # [mD] tight matrix
    matrix_poro: float = 0.15
    frac_aper: float = 1.0e-3            # [m] fracture aperture -> perm_frac = (aper^2/12)*1e15 mD
    frac_poro: float = 0.5
    p_init: float = 200.0                # initial pressure [bar]
    temperature: float = 350.0          # [K] geothermal single-phase water
    # well (placed at the mesh bbox centre; perforates the nearest cell)
    well_rate: float = 5.0              # [m3/day] mild drawdown (tight matrix -> keep Newton stable)
    well_radius: float = 0.1            # [m]
    well_skin: float = 0.0
    # transient sampling
    total_time: float = 2.0             # [day]
    n_report_steps: int = 40            # log-spaced report times
    # dimensionless reference (matrix-referenced; the Bourdet SHAPE is what the gate compares)
    ref_thickness: float = 10.0         # [m] extruded layer thickness (well-test h)
    tol_rel_l2: float = 0.25            # DFM vs MRST derivative-shape tolerance (looser than Step A)


@dataclass(frozen=True)
class DfmStudySpec:
    """One validated DFM GeoType STUDY on SIMULATED physics (a FlowDNA *case* of kind 'dfm').

    The payoff of Step B and the graduation of the geometry-only `dfn` cases: an ensemble of GeoDFN
    networks is meshed + drawn down with open-DARTS (see `DfmDrawdownSpec`), and the resulting
    dimensionless Bourdet derivatives are clustered into GeoTypes (DTW k-medoids + conformal split +
    RF/SHAP attribution against the real GeoDFN descriptors) exactly like the analytic/real studies.
    A representative simulated transient + the MRST-ensemble fidelity gate are carried in the artifact.
    """

    case_id: str
    n_networks: int = 26                 # meshed + simulated (>= k_max*3 valid needed for the study)
    domain_x: float = 100.0
    domain_y: float = 100.0
    # GeoDFN generation (mirrors DFNSpec vocabulary; two conjugate sets)
    intensity_set1: float = 0.05
    intensity_set2: float = 0.04
    length_mu: float = 2.0
    length_sigma: float = 0.6
    length_min: float = 2.0
    length_max: float = 40.0
    orient_loc_set1: float = 0.8
    orient_loc_set2: float = 2.35
    orient_kappa: float = 10.0
    spatial_alpha: float = 0.6
    buffer_constant: float = 1.0
    # meshing + DFM physics (per network)
    char_len: float = 8.0
    matrix_perm: float = 1.0             # [mD]
    matrix_poro: float = 0.15
    # fracture aperture SWEEP across the ensemble (log-uniform): aperture sets fracture conductivity
    # via the cubic law, so a range spans tight->open-fracture flow regimes -> genuine GeoType
    # families. log10(aperture) is added to the attribution descriptors (it is a real control).
    frac_aper_min: float = 3.0e-4        # [m]
    frac_aper_max: float = 3.0e-3        # [m]
    well_rate: float = 5.0              # [m3/day]
    total_time: float = 2.0             # [day]
    n_report_steps: int = 30
    ref_thickness: float = 10.0
    # preprocessing (curves ARE derivatives -> order 0) + clustering + conformal (study contract)
    n_points: int = 96
    derivative_order: int = 0
    L: float = 0.2
    norm: str = "zscore"
    dtw_window: int = 10
    k_min: int = 2
    k_max: int = 6
    frac_cal: float = 0.25
    frac_test: float = 0.25
    alpha: float = 0.15
    # fidelity
    fidelity_dataset: str = "A"          # MRST reference dataset for the ensemble gate


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
    compare_methods: bool = False  # P2a clustering comparison (opt-in; ~seconds/method)


@dataclass(frozen=True)
class FieldDataSpec:
    """One validated REAL field pumping-test operating point (a FlowDNA *case* of kind 'field').

    Real transient drawdown curves from welltestpy campaigns (Horkheimer Insel + Lauswiesen, MIT,
    vault-only) clustered by Bourdet-derivative SHAPE into AquiferTypes. The curves are RAW drawdown
    s(t), so preprocessing uses derivative_order=1 (the Bourdet first derivative), unlike the 4TU
    corpus which is already the derivative. T and S are unknown, so clustering is on shape only.
    """

    case_id: str
    sites: tuple[str, ...] = ("horkheim", "lauswiesen")
    # preprocessing (raw drawdown -> Bourdet first derivative on a common log-time grid)
    n_points: int = 96
    derivative_order: int = 1
    L: float = 0.2                        # Bourdet smoothing window (log cycles)
    norm: str = "zscore"
    # clustering
    dtw_window: int = 10
    k_min: int = 2
    k_max: int = 5
    # conformal split
    frac_cal: float = 0.25
    frac_test: float = 0.25
    alpha: float = 0.15


@dataclass(frozen=True)
class BenchmarkSpec:
    """One FULL-corpus benchmark operating point (a Pulso *case* of kind 'benchmark').

    Runs the ENTIRE ~4768-curve 4TU corpus for a dataset through the GeoType pipeline, reusing the
    vault's precomputed DTW matrix (`Dataset_X_DTW.npy`) so it does not recompute 4768^2 DTW. The
    honest full-corpus silhouette/K/attribution numbers feed the Benchmark PAGE (contrasted with the
    400-subsample App `real` cases, which inflate silhouette). Vault-only; skipped without the corpus.
    """

    case_id: str
    dataset: str = "A"                   # 'A' | 'B' | 'C'
    n_points: int = 96
    derivative_order: int = 0            # the corpus is already the Bourdet first derivative
    L: float = 0.2
    norm: str = "zscore"
    dtw_window: int = 10                 # unused (DTW is precomputed) but kept for schema uniformity
    k_min: int = 2
    k_max: int = 6
    frac_cal: float = 0.2
    frac_test: float = 0.2
    alpha: float = 0.15
    compare_methods: bool = False  # P2a clustering comparison (opt-in; ~seconds/method)


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

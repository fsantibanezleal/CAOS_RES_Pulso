// CONTRACT 2 mirror (frontend side). MUST stay in lock-step with the Python schemas in
// data-pipeline/flowdnalab/core/{trace.py, manifest.py}. A drift here makes `tsc` fail -> the contract is
// enforced at BUILD time (the web cannot ship reading a shape the pipeline does not produce).

export interface KTable {
  k: number[];
  silhouette: number[];
  cost: number[];
}

export interface GeoTypeSample {
  geotype: number;
  curve: number[];
}

export interface ConformalAssignment {
  point_prediction: number;
  p_values: number[];
  prediction_set: number[];
  alpha: number;
  distances: number[];
  out_of_catalogue: boolean;
  test_index?: number;
}

export interface StudySummary {
  coverage: number;
  target: number;
  ood_rate: number;
  mean_set_size: number;
}

export interface AttributionReport {
  status: string;
  reason?: string | null;
  gate?: { accuracy: number; passed: boolean; threshold: number; n_test: number };
  kept_features?: string[];
  dropped_features?: Array<{ dropped: string; kept_as: string; rho: number }>;
  shap_mean_abs?: Record<string, Record<string, number>> | null;
  permutation_importance?: Record<string, { mean: number; std: number }> | null;
  rank_agreement_spearman?: number | null;
}

export interface StudyTrace {
  schema: string; // "flowdna.trace/v1" or "pulso.study/v2"
  case_id: string;
  t_grid: number[];
  preprocessing: { derivative_order: number; L: number; norm: string; n_points: number };
  dtw_window: number | null;
  k: number;
  medoids: number[][];
  geotype_counts: number[];
  silhouette: number;
  k_table: KTable;
  samples: GeoTypeSample[];
  calibration_scores: Record<string, number[]>;
  assignments: ConformalAssignment[];
  attribution: AttributionReport;
  params_sample: Array<Record<string, number | string>>;
  summary: StudySummary;
}

// CONTRACT-3 (pulso.study/v2): the FULL-ensemble study artifact. A superset of StudyTrace that also
// commits every member curve (decimated), per-cluster envelopes, the DTW distance matrix and the MDS
// embedding, so the P3 visualizations render the whole ensemble without recomputation in the browser.
export interface EnsembleMembers {
  geotype: number[]; // per-committed-curve cluster label
  curves: number[][]; // per-committed-curve decimated (min/max-per-pixel) values
  note?: string; // "full" or "stratified subsample K/N" (large corpora are capped)
}
export interface ClusterEnvelope {
  geotype: number;
  p10: number[]; // on t_grid
  p50: number[];
  p90: number[];
}
export interface DtwMatrix {
  dmax: number;
  rows: number[][]; // NxN uint8 (0..255), value = distance/dmax*255
  order: number[]; // cluster-ordered permutation into the member arrays
  order_labels: number[]; // the cluster label per ordered row
  note: string; // "full" or "capped random subsample K/N"
}
export interface MdsEmbedding {
  mds2d: Array<[number, number]>;
  mds3d: Array<[number, number, number]> | null;
  stress: number;
  medoid_idx: number[]; // member indices of the k medoids
}
export interface StudyTraceV2 extends StudyTrace {
  members: EnsembleMembers;
  envelopes: ClusterEnvelope[];
  dtw: DtwMatrix;
  embedding: MdsEmbedding;
  stats: {
    n_members: number; // the full population size
    n_committed?: number; // curves actually committed (== n_members unless capped)
    members_note?: string;
    display_cols: number;
    dtw_n: number;
    dtw_note: string;
    decimation: string;
  };
}

export interface DfnNetwork {
  n_fractures: number;
  segments: number[][]; // [x1, y1, x2, y2]
}

export interface DfnTrace {
  schema: string; // "flowdna.dfn/v1"
  case_id: string;
  networks: DfnNetwork[];
  descriptor_names: string[];
  descriptors: number[][];
  stats: {
    per_descriptor: Record<string, { mean: number; std: number }>;
    domain: { x: number; y: number };
    vault_dir: string;
  };
  transient_simulation: string;
}

export interface DartsTrace {
  schema: string; // "flowdna.darts/v1"
  case_id: string;
  tD: number[];
  pwD_sim: number[];
  pwD_analytic: number[];
  dpwD_sim: number[];
  dpwD_analytic: number[];
  validation: {
    rel_l2: number;
    plateau_error: number;
    apparent_skin: number;
    window: number[];
    tol_rel_l2: number;
    tol_plateau: number;
    passed: boolean;
  };
  physical: Record<string, number>;
}

export interface DfmFidelity {
  reference: string; // 'mrst_ensemble' | 'none' | 'insufficient_overlap'
  dataset?: string;
  passed: boolean;
  band_coverage?: number;
  shape_rel_l2?: number;
  scale_factor?: number;
  shape_corr?: number | null;
  n_ref_curves?: number;
  n_grid_overlap?: number;
  min_band_coverage?: number;
  note?: string;
  band?: { tD: number[]; p5: number[]; p50: number[]; p95: number[]; sim: number[] };
}

export interface DfmBlock {
  sample_transient: { tD: number[]; pwD: number[]; dpwD: number[] };
  fidelity: DfmFidelity;
  mesh_stats: Record<string, number | number[]>;
  physical: Record<string, number | number[]>;
  ensemble: { n_networks: number; n_ok: number; n_fail: number; fidelity_dataset: string };
  transient_simulation: string;
}

// a DFM case IS a GeoType study (catalogue / conformal / attribution) computed on SIMULATED
// open-DARTS transients, PLUS the `dfm` block (representative transient + MRST fidelity gate).
export interface DfmTrace extends StudyTrace {
  dfm: DfmBlock;
}

export type Trace = StudyTrace | StudyTraceV2 | DfnTrace | DartsTrace | DfmTrace;

// a DfmTrace is structurally + semantically a study, so the study renderers apply to it too. The
// CONTRACT-3 v2 study artifact is also a study (superset).
export function isStudyTrace(t: Trace): t is StudyTrace {
  return (
    t.schema.startsWith('flowdna.trace/') ||
    t.schema.startsWith('pulso.study/') ||
    t.schema.startsWith('flowdna.dfm/') ||
    t.schema.startsWith('pulso.dfm/')
  );
}

// the full-ensemble CONTRACT-3 study (members + envelopes + dtw + embedding present). Both the plain
// study v2 and the DFM v2 (a study on simulated physics) carry these fields.
export function isStudyTraceV2(t: Trace): t is StudyTraceV2 {
  return t.schema.startsWith('pulso.study/') || t.schema.startsWith('pulso.dfm/');
}

export function isDfmTrace(t: Trace): t is DfmTrace {
  return t.schema.startsWith('flowdna.dfm/') || t.schema.startsWith('pulso.dfm/');
}

export function isDfnTrace(t: Trace): t is DfnTrace {
  return t.schema.startsWith('flowdna.dfn/');
}

export function isDartsTrace(t: Trace): t is DartsTrace {
  return t.schema.startsWith('flowdna.darts/');
}

export interface ArtifactRef {
  path: string;
  format: string;
  trace_schema: string;
  bytes: number;
}

export interface GateVerdict {
  lane: string;
  pure_python: boolean;
  wheels: string[];
  trace_bytes: number;
  run_ms_budget: number;
  trace_bytes_budget: number;
  reasons: string[];
}

export interface EngineBlock {
  package: string;
  version: string;
  pygeotypes: string;
  dtw_backend?: string;
  GeoDFN?: string;
}

export interface CaseManifest {
  schema: string; // "flowdna.manifest/v1"
  case_id: string;
  category: string;
  real_or_synthetic: string;
  expected_band: string;
  engine: EngineBlock;
  params: Record<string, unknown>;
  seed: number;
  artifact: ArtifactRef;
  lane: 'live' | 'precompute';
  gate: GateVerdict;
  flags: Array<Record<string, string>>;
  metrics: Record<string, unknown>;
}

export interface CaseIndexEntry {
  case_id: string;
  category: string;
  manifest_path: string;
}

export interface CaseIndex {
  schema: string; // "flowdna.index/v1"
  engine_version: string;
  n_cases: number;
  cases: CaseIndexEntry[];
}

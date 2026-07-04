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
  schema: string; // "flowdna.trace/v1"
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

export type Trace = StudyTrace | DfnTrace;

export function isStudyTrace(t: Trace): t is StudyTrace {
  return t.schema.startsWith('flowdna.trace/');
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

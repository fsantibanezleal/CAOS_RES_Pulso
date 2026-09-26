# The staged precompute pipeline

`data-pipeline/pipeline/pipeline.py` (run through `data-pipeline/run.py`) orchestrates the **named stages** of the
`fracpta` engine (frozen names/signatures) and this product's export:

| Stage | Module | Does |
|---|---|---|
| preprocess | `fracpta.stages.preprocess` | generate or ingest the curves under **CONTRACT 1** (validate + outlier policy) |
| feature_extraction | `fracpta.stages.feature_extraction` | log-time grid, Bourdet derivative or p'', normalisation, the shape arrays |
| train | `fracpta.stages.train` | DTW matrix, K selection, PAM catalogue, conformal calibration, RF+SHAP attribution |
| infer | `fracpta.stages.infer` | conformal assignment of the held-out slice |
| evaluate | `fracpta.stages.evaluate` | silhouette, empirical coverage, out-of-catalogue rate, the attribution gate |
| export | `data-pipeline/pipeline/export.py` | **CONTRACT 2**, the artifact (the engine's trace) + this product's manifest and lane gate |

Run: `python data-pipeline/run.py [all|<case_id>] [--seed N]` (or `scripts/precompute.{sh,ps1}`). It writes
`data/derived/<case>/trace.json` + `data/derived/manifests/<case>.json` + `index.json`.

The engine is pinned in `data-pipeline/requirements.txt` (`fracpta==0.1.0`, which brings `pygeotypes`) and documented
in [../frameworks/](../frameworks/); the study core the orchestrator calls is `fracpta.study.train_infer_evaluate`.

# data-pipeline/: the offline bake

The science is the [`fracpta`](https://github.com/fsantibanezleal/CAOS_FracPTA) package (PyPI), pinned in
`requirements.txt`; it was this product's internal package `flowdnalab` until 0.26.000 and now lives in its own
repository, as a product's engine must (`conventions/no-internal-packages.md`). Nothing under this directory
re-implements it. What lives here is Pulso's build tooling, invoked by path and never installed:

| Path | What it is |
|---|---|
| `run.py` | the entry point: `python data-pipeline/run.py [all|<case>|index] [--seed N] [--kinds study,dfn,...]` |
| `pipeline/pipeline.py` | the orchestrator: which engine stages run for each case kind, where the artifacts go |
| `pipeline/cases.py`, `pipeline/registry.py` | the twenty-one cases of this product, grouped by category |
| `pipeline/manifest.py` | CONTRACT 2, the manifest of a baked case (params, seed, engine and pygeotypes versions, artifact size, lane verdict, flags, metrics) and the flat index |
| `pipeline/export.py` | writes each artifact (the engine's study, DFN, DARTS and DFM traces) and its manifest, and measures the lane gate |
| `pipeline/gate.py` | the lane gate (pure Python, wheels, measured live cost, trace size) |
| `export_live_sources.py` | writes `data/derived/pyodide/sources.json` from the installed engine for the optional Pyodide lane (served at `/data/pyodide/sources.json`) |
| `requirements.txt`, `requirements-train.txt` | the pinned offline lane (`.venv-pipeline`) and the GPU training lane (`.venv-train`) |

The engine's own layout (analytic ensembles, GeoDFN and open-DARTS wrappers, contracts, the clustering ladder,
attribution, the learned tier, the study stages, the trace builders and the live entry) is documented in the
`fracpta` repository.

## Environments

- `.venv-pipeline`: `pip install -r data-pipeline/requirements.txt` (the engine with its heavy extras: GeoDFN,
  open-DARTS, scikit-learn, tslearn, hdbscan, umap-learn, shap, dtaidistance, torch for the DFM fidelity gate).
- `.venv-train`: `pip install -r data-pipeline/requirements-train.txt` for `python -m fracpta.deep.train`
  (`scripts/train-deep.*`).
- The vault datasets (4TU real corpus, welltestpy field campaigns) are read from `FRACPTA_VAULT`
  (`FLOWDNA_VAULT` still accepted); cases that need them are skipped when it is absent.

## Running

`scripts/setup.{sh,ps1}` builds the environments, `scripts/precompute.{sh,ps1}` runs `run.py`. A case bake is a
pure function of (spec, seed); `run.py all --kinds ...` writes only the baked entries to the index, so end a
partial bake with `run.py index`, which rebuilds `data/derived/manifests/index.json` from every manifest on
disk. `scripts/check_artifacts.py` then verifies CONTRACT 2 (index, manifests, artifacts, sizes, lanes).
See [../docs/architecture/05_precompute-pipeline.md](../docs/architecture/05_precompute-pipeline.md).

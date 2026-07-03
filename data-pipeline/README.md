# data-pipeline/ — the offline engine (`flowdnalab`)

Rename `flowdnalab` → `<slug>lab` per product. The **single source of physics/algorithm truth**; `frontend/` and
`app/` consume it, never re-implement it. Its own venv: **`.venv-pipeline`** (heavy SOTA engines, local-only).

## Layout (the package lives directly under `data-pipeline/`)
- `flowdnalab/pipeline.py` — orchestrator + CLI (`python -m flowdnalab.pipeline [all|<case>] [--seed N]`)
- `flowdnalab/registry.py` — cases grouped by CATEGORY · `flowdnalab/live.py` — Pyodide live entrypoint
- `flowdnalab/io/` — `contract.py` (**CONTRACT 1**) · `formats.py` (standard readers/writers) · `schema.py` (types)
- `flowdnalab/core/` — `rng.py` (seeded determinism) · `trace.py` · `manifest.py` (**CONTRACT 2**) · `gate.py`
- `flowdnalab/model/` — the shared pure-Python core (Pyodide-safe); EXAMPLE = SIR
- `flowdnalab/stages/` — `preprocess → feature_extraction → train → infer → evaluate → export`
- `flowdnalab/cases/` — documented cases

Setup + run: `scripts/setup.{sh,ps1}` then `scripts/precompute.{sh,ps1}`. See
[../docs/architecture/05_precompute-pipeline.md](../docs/architecture/05_precompute-pipeline.md).

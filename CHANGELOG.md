# Changelog

All notable changes to FlowDNA. Format: `X.XX.XXX` (display) — see `flowdnalab.__version__`. Keep `0.x`
while on the template example engine / synthetic-only data. Tag every release.

## [0.01.000] — 2026-07-03

### Added
- Initial instantiation from the CAOS product-repo template (ADR-0057): offline `data-pipeline/`
  (`flowdnalab`), the two data contracts (ingestion + artifact), the named staged pipeline
  (preprocess → feature_extraction → train → infer → evaluate → export), seeded RNG, compact trace,
  manifest, and the measured live-vs-precompute gate.
- Template EXAMPLE engine (deterministic SIR, numpy-only, Pyodide-safe) still in place — to be
  replaced by the FlowDNA engines selected in the binding research dossiers
  (`_CAOS_MANAGE/wip/flowdna/research-*-2026-07-03.md`): DFN generation + pressure-transient
  simulation (offline lane), analytical PTA core (live lane), DTW k-medoids GeoTypes + RF/SHAP.
- Cases-by-category registry (template regimes + degenerate control); live-lane entrypoint
  (`live.py`); tests for both contracts + pipeline determinism.

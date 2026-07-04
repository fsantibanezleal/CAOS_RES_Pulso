# FlowDNA — the geological DNA of fractured reservoirs

[![CI](https://img.shields.io/github/actions/workflow/status/fsantibanezleal/CAOS_RES_FlowDNA/ci.yml?branch=main&label=CI)](https://github.com/fsantibanezleal/CAOS_RES_FlowDNA/actions)
[![License](https://img.shields.io/github/license/fsantibanezleal/CAOS_RES_FlowDNA)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/fsantibanezleal/CAOS_RES_FlowDNA?label=version&sort=semver)](https://github.com/fsantibanezleal/CAOS_RES_FlowDNA/tags)

**FlowDNA** asks whether fractured reservoirs have a *geological DNA*: recurring fluid-flow behaviours
hidden in the shape of their pressure-transient responses. It builds a catalogue of **GeoTypes** —
flow-behaviour classes discovered by unsupervised learning over geologically consistent discrete
fracture network (DFN) ensembles — and an attribution layer that identifies **which fracture-network
properties control each behaviour**, to constrain geological uncertainty, support early-stage
reservoir characterisation and guide data acquisition toward the most influential fracture properties.

The methodology reproduces and extends:

> E. Kamel Targhi, G. Rongier, P.-O. Bruna, A. Daniilidis, S. Geiger,
> *Unsupervised learning for geologically consistent fluid flow analysis in fractured reservoirs*,
> Computational Geosciences 30, 57 (2026). DOI
> [10.1007/s10596-026-10459-w](https://doi.org/10.1007/s10596-026-10459-w) (open access, CC BY 4.0).

and generalizes to **any response signal whose shape reflects the underlying physical system**
(hydrogeology pumping tests, geothermal, thermal response tests).

## Pipeline (offline) → web app (static replay + live lane)

```
GeoDFN ensembles ──► pressure-transient simulation ──► Bourdet derivative + curve features
   (MIT, pip)          (offline heavy lane)                     │
                                                                ▼
        RF + SHAP attribution ◄── GeoType catalogue ◄── DTW K-medoids clustering
        (what controls what)       (medoids + membership)
```

- **Offline lane** (`data-pipeline/flowdnalab`, `.venv-pipeline`): the research-chosen SOTA engines,
  staged pipeline `preprocess → feature_extraction → train → infer → evaluate → export`, committed
  compact artifacts + manifests (deterministic, seeded).
- **Live lane** (Pyodide, browser): pure-Python analytical PTA core (Bourdet derivative +
  Warren-Root dual-porosity via Stehfest inversion) + classify-my-curve against the baked medoids.
- **Web** (`frontend/`): React/Vite SPA — App workbench (Synthetic vs Real source selector) /
  Introduction / Methodology / Implementation / Experiments / Benchmark, EN/ES, light/dark, ⓘ
  architecture modal. Replays only committed, audited artifacts.

This repo is an instantiation of the CAOS product-repo archetype (ADR-0057): frozen base, rework
only in the core (models, visualization, content). Status: **v0.02.000 — engines wired**: the
staged pipeline runs the real core end-to-end (pygeotypes + GeoDFN; 8 committed cases with honest
metrics: silhouette, K table, empirical conformal coverage, OOD rate, gated attribution).
open-DARTS 1.5.0 is installed and the transient-on-DFN lane is the explicit next phase (DFN
artifacts carry `transient_simulation: pending` — no fake curves). The web app is still the
contract-exercising replay skeleton; the full ADR-0016 six-page shell is next.

## Data & licenses

- Reference corpus: the paper's dataset (4,850 GeoDFN networks + pressure transients, ~24.8 GB,
  GPL-3.0) from 4TU.ResearchData, DOI
  [10.4121/8291d285-025d-4724-988d-fc747a578c0a](https://doi.org/10.4121/8291d285-025d-4724-988d-fc747a578c0a)
  — kept in the local data vault, **never committed**; this repo ships only derived compact
  artifacts. GPL workflow code is **not vendored**; the shape machinery is
  [pygeotypes](https://github.com/fsantibanezleal/CAOS_GeoTypes) (Apache-2.0, ours) on
  dtaidistance + scikit-learn + shap.
- DFN generation: [GeoDFN](https://github.com/kamelelahe/GeoDFN) (MIT) — used as a real engine.
- Transient flow on DFNs: [open-DARTS](https://gitlab.com/open-darts/open-darts) (GPL-3) —
  offline-only engine dependency, never vendored/shipped; integration pending (next phase).
- See `data/README.md` for the ingestion contract and the full provenance manifest.

## Quickstart

```powershell
.\scripts\setup.ps1                       # reproducible .venv + pinned requirements
.\scripts\precompute.ps1                  # staged pipeline → data/ artifacts + manifests
.\.venv\Scripts\python.exe -m pytest      # contracts + determinism + gate tests
cd frontend ; npm install ; npm run dev   # the SPA (copy-data enforces the artifact contract)
```

(bash equivalents in `scripts/*.sh`.)

## Docs

The `docs/` wiki (architecture, frameworks, cases, guides) is authored **as the product is built**
(ADR-0056): see [docs/README.md](docs/README.md).

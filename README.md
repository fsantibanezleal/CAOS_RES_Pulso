# Pulso — the geological DNA of fractured reservoirs

[![CI](https://img.shields.io/github/actions/workflow/status/fsantibanezleal/CAOS_RES_Pulso/ci.yml?branch=main&label=CI)](https://github.com/fsantibanezleal/CAOS_RES_Pulso/actions)
[![License](https://img.shields.io/github/license/fsantibanezleal/CAOS_RES_Pulso)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/fsantibanezleal/CAOS_RES_Pulso?label=version&sort=semver)](https://github.com/fsantibanezleal/CAOS_RES_Pulso/tags)

**Pulso** asks whether fractured reservoirs have a *geological DNA*: recurring fluid-flow behaviours
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
- **Web** (`frontend/`): React 19 + Vite SPA (react-router, react-i18next, KaTeX, zustand). The
  full ADR-0016 six-page shell — **App** workbench (Synthetic / Real 4TU / open-DARTS source
  selector, then genuine domain views: GeoType catalogue with cursor read-out, conformal
  classify-a-curve, RF/SHAP attribution, fracture network, DARTS validation, context) plus
  **Introduction / Methodology / Implementation / Experiments / Benchmark** as detailed prose +
  KaTeX + DOI refs — with EN/ES, light/dark, and the ⓘ architecture modal. Replays only committed,
  audited artifacts.

This repo is an instantiation of the CAOS product-repo archetype (ADR-0057): frozen base, rework
only in the core (models, visualization, content). Status: **v0.24.001 — six-page app live with real data**:
the staged pipeline runs the real core end-to-end (pygeotypes + GeoDFN) over **11 committed cases**
— 6 analytic Warren-Root/mixture studies, **3 real studies on the paper's own 4TU corpus**
(Datasets A/B/C), and 2 GeoDFN network ensembles — all with honest metrics (silhouette, K table,
empirical conformal coverage, OOD rate, gated attribution). The real transients cluster more cleanly
than the analytic ones (silhouette up to 0.86) and REAL_C's top attribution `log_I` partially
reproduces the paper's fracture-intensity finding. open-DARTS 1.5.0 is installed and the
transient-on-DFN lane is the next phase (DFN artifacts carry `transient_simulation: pending` — no
fake curves). The full ADR-0016 six-page shell ships in the web app.

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

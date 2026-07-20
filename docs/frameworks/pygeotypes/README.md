# pygeotypes — the shape-catalogue engine

**What / why.** `pygeotypes` (repo [CAOS_GeoTypes](https://github.com/fsantibanezleal/CAOS_GeoTypes),
Apache-2.0) is the research-chosen core for everything shape-related in Pulso: Bourdet
derivative + p'' preprocessing, Sakoe-Chiba banded DTW, PAM k-medoids on precomputed distance
matrices, the persistent `Catalogue` artifact, **class-conditional split-conformal assignment**
(p-values, prediction sets, out-of-catalogue flag — Pulso's novel-beyond-SOTA layer) and the
gated RF + TreeSHAP attribution. It was created for Pulso because no maintained, permissively
licensed, Pyodide-safe package couples those pieces (scikit-learn-extra unmaintained; the Rust
`kmedoids` is GPL-3; tslearn/aeon require numba). Decision dossier:
`_CAOS_MANAGE/wip/flowdna/engine-decision-2026-07-03.md`.

**Install.**
```bash
# until the PyPI release (private repo): from the sibling checkout
pip install -e ../CAOS_GeoTypes[fast,attr]     # offline pipeline venv (.venv-pipeline)
pip install -e ../CAOS_GeoTypes                # runtime venv (core only)
# note: PyPI dist+import name is pygeotypes (bare geotypes is taken by an unrelated package)
```

**How Pulso uses it (all lanes).**

| Pulso stage | pygeotypes API |
|---|---|
| `feature_extraction` | `preprocess.prepare_curves` (log grid → Bourdet/p'' → z-score) |
| `train` | `distance.dtw_matrix` (dtaidistance backend offline) · `cluster.select_k` + `pam_kmedoids` · `catalogue.build_catalogue` · `assign.ConformalAssigner.fit` · `attribute.attribute_geotypes` |
| `infer` | `assign.ConformalAssigner.predict` over the held-out test slice |
| live lane (`flowdnalab/live.py`) | `synthetic.warren_root_pd` (generate) · `Catalogue.from_*` + `ConformalAssigner.from_dict` + `predict` (classify-my-curve, pure numpy/scipy) |

**Runnable example.** See `data-pipeline/flowdnalab/stages/train.py` (the real call site) and the
package's own `docs/quickstart.md`. The committed study traces under `data/derived/` are its
outputs.

**Version pinned.** 0.1.2 (editable, 2026-07-03). Gotcha: conformal OOD verdicts need
`n_cal_per_class >= 1/alpha - 1` (the CONTRACT-1 spec validator flags violations).

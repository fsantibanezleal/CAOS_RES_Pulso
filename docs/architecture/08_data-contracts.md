# The two data contracts

A product is only real if data flows through two **enforced** contracts. Both are CI-checked.

## CONTRACT 1 — ingestion (`raw → pipeline`) — the *bring-your-own-data* gate
`data-pipeline/flowdnalab/io/contract.py`. Declares the required schema (columns, units, ranges) + an explicit
**outlier policy** (reject / clip / flag). A dataset is accepted iff it passes; bad rows are rejected **with a
reason**, never silently coerced; suspicious-but-plausible rows are flagged (the flag is recorded in the
manifest). This is what lets a third party point the tool at THEIR data instead of only replaying baked cases.

EXAMPLE (SIR): columns `case_id,beta,gamma,N,I0[,days]`; ranges per `RANGES`; reject NaN/Inf/out-of-range/`I0>N`;
flag `R0>20`. Full table: [`data/README.md`](../../data/README.md).

## CONTRACT 2 — artifact (`pipeline → web`)
`data-pipeline/flowdnalab/core/{trace.py, manifest.py}`. Every run writes a compact trace (`example.trace/v1`) +
a manifest (`example.manifest/v2`) recording params, seed, engine+version, the artifact byte size, the measured
**[lane/gate](03_the-gate.md)** verdict, the Contract-1 flags, and the evaluation metrics. A flat
`data/derived/manifests/index.json` inventories every case.

**Enforcement:** `frontend/src/lib/contract.types.ts` mirrors this schema — a drift fails `tsc`. `scripts/check_artifacts.py`
(run in CI) verifies index→manifests→artifacts exist, byte sizes match, and lane==gate. The web loads **only** these
artifacts; it never recomputes (except the optional live lane, which emits the same trace schema).

## CONTRACT 3 — the full-ensemble study artifact (`pulso.study/v2`)

Added in the rebuild (v0.11.000, phase P0.2). The v1 study trace committed only the medoid curves +
3 example curves per GeoType, which is the "2 curves is all" toy: the visualizations had nothing to
show. CONTRACT-3 commits the WHOLE ensemble per case so the rich P3 visualizations render without any
recomputation in the browser:

- `members` — EVERY training-slice curve, decimated **min/max-per-pixel** (extrema-preserving, so the
  dual-porosity valley and boundary rise survive), each with its cluster label.
- `envelopes` — per GeoType, the p10/p50/p90 curve band over its members on `t_grid` (what the
  ensemble explorer draws when N is large, instead of spaghetti).
- `dtw` — the cluster-ordered DTW distance matrix, quantized to **uint8** over `[0, dmax]`, with the
  ordering permutation + per-row labels. Capped to `MAX_DTW_N=512` (a documented random subsample for
  larger ensembles, honest `note`), so a study stays well under the ~2 MB/case byte budget.
- `embedding` — the classical (metric) **MDS 2D (+ 3D)** coordinates from the DTW matrix, per member,
  with the medoid indices marked (the shape-space scatter reads these directly).
- `stats` — n_members, display columns, dtw_n, the decimation method (provenance / honesty).

v2 is a **superset** of v1 (all v1 fields kept), so the existing renderers keep working while the P3
viz consumes the new fields. Produced by `core/trace.py` `build_study_trace_v2` (from the DTW matrix,
labels, `X_train` and the MDS embedding returned by `stages/train.py`); mirrored by
`frontend/src/lib/contract.types.ts` (`StudyTraceV2` + `isStudyTraceV2`), asserted by the frontend
contract test and `tests/test_contract3.py` (full-ensemble shape + the byte budget + extrema-preserving
decimation + determinism).

## Why this matters
Without Contract 1 the app can't be applied to new data (it's a demo). Without Contract 2 the web can silently
drift from what the pipeline produced. Without Contract 3 the visualizations have only medoids to draw (a toy).
The contracts are the seam that makes the product a tool, not a slideshow.

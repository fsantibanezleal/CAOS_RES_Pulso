# Frameworks

One card per research-chosen engine/library — **the deep research, made binding**. Every engine the pipeline uses
gets a card here AND an exact pin in the matching `requirements-*.txt`. No hand-rolled toy substitute for a SOTA
engine the research prescribed.

- [00 — card TEMPLATE](frameworks/00_TEMPLATE.md) — copy per engine to `frameworks/<NN>_<tool>/<tool>.md`

**Cards (one per research-chosen engine):**

- [pygeotypes](frameworks/pygeotypes/README.md) — the shape-catalogue core (DTW, PAM k-medoids, conformal assignment, RF+SHAP)
- [dtaidistance](frameworks/dtaidistance/) — C-fast pairwise DTW matrices (offline distance backend)
- [tslearn](frameworks/tslearn/tslearn.md) — soft-DTW k-means + k-Shape (P2a clustering comparison)
- [hdbscan](frameworks/hdbscan/hdbscan.md) — density clustering with noise + no fixed k (P2a comparison control)
- [umap-learn](frameworks/umap-learn/umap-learn.md) — UMAP manifold layout (P2b representations)
- [pycatch22](frameworks/pycatch22/pycatch22.md) — catch22 canonical TS features (P2b representations)
- [open-darts](frameworks/open-darts/) — DFM reservoir simulation (offline physics lane)
- [geodfn](frameworks/geodfn/) — discrete fracture network generation
- [torch](frameworks/torch/) — GPU training of the learned tier (exported to ONNX)
- [onnxruntime-web](frameworks/onnxruntime-web/) — in-browser inference of the learned tier
- [welltestpy](frameworks/welltestpy/) — analytic well-test references

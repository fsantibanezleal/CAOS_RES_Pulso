# Docs — the product wiki

SimLab-style navigable wiki (ADR-0056), authored **as the product is built**, not at the end. The pipeline +
its validation + these docs are the primary product; the web app is a projection of a validated subset.

## Map
- **[architecture/](architecture/)** — how the repo works: the frozen base, the two data contracts, determinism +
  trace, the live/precompute gate, the staged pipeline, model evaluation, deploy.
- **[frameworks/](frameworks/)** — one card per research-chosen engine/library (what/why · install · usage ·
  applying). The deep research, made binding (each is pinned in a `requirements-*.txt`).
- **[methods/](methods.md)** — the method ladder: the reference DTW k-medoids catalogue and the SOTA
  alternatives it is honestly measured against (silhouette + ARI), grouped by what each operates on.
- **[guides/](guides/)** — runnable how-tos: **instantiate the template**, run the precompute pipeline,
  **bring your own data**, the GPU lane, run the API.
- **[cases/](cases/)** — the category taxonomy + the coverage matrix + one page per documented case.

## Honesty + data policy
- Numbers come from the calibrated engine / committed artifacts, never from a claim. The example engine (SIR) is
  synthetic and clearly labelled; a real product states sources, licenses and what is real vs synthetic.
- Public derived artifacts are committed (`data/derived/`); raw/private sources stay out of git (`data/raw/`,
  vault) per ADR-0055. The two data contracts ([architecture/08_data-contracts.md](architecture/08_data-contracts.md))
  govern raw→pipeline and pipeline→web.

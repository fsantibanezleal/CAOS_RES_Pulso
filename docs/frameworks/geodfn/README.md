# GeoDFN — geologically consistent DFN generation (the paper authors' engine)

**What / why.** [GeoDFN](https://github.com/kamelelahe/GeoDFN) (MIT, `pip install GeoDFN`) is the
2-D stochastic discrete-fracture-network generator by the Pulso source-paper group (Kamel Targhi
et al., TU Delft; companion paper DOI 10.1144/geoenergy2025-028). "Geologically consistent" is its
point: stress-shadow **buffer zones**, a spatial **seed fracture** per set, Von-Mises orientations,
Log-Normal truncated lengths, power-law spatial clustering, and stress-aware (Barton-Bandis /
sub-linear) **apertures**. The paper's 4,850-network corpus was generated with it; Pulso uses the
same engine rather than a hand-rolled Poisson generator.

**Install.** `pip install GeoDFN==2.0.0` (Python ≥3.11; pulls matplotlib + streamlit for its own UI).
Offline lane only — never imported by the live lane (enforced by the gate's LIVE_WHEELS).

**How Pulso calls it.** `data-pipeline/flowdnalab/dfn/geodfn_adapter.py`:

```python
np.random.seed(seed)                       # GeoDFN 2.0.0 draws from numpy's GLOBAL legacy RNG
DFNGeneratorWithSeed(domain_x, domain_y, [set1, set2], APERTURE_PARAMS, case_id,
                     num_realizations=n, savePic=False, output_dir=vault_dir)
```

- The constructor runs the generation and writes per-realization files:
  `fractureCoordinates/NNNfractureCoordinates.txt` (x1 y1 x2 y2 per fracture),
  `aperture/NNNaperture.txt`, `outputProperties*`.
- The adapter parses those, computes the descriptor table
  (`dfn/descriptors.py`: P21, length stats, orientation dispersion R, intersections graph,
  largest-cluster / backbone fractions, spanning flag, well distance) and bakes the decimated
  geometries into the `flowdna.dfn/v1` trace.
- Raw engine output lands in the vault (`FLOWDNA_VAULT=E:\_Datos\flowdna` → `geodfn/<case>/`),
  never in git.

**Determinism (measured).** With the global seed pinned, repeated runs reproduce identical
realizations for a fixed GeoDFN version. The 'seed' key inside a set config is a spatial seed
FRACTURE position (the geological conditioning), not an RNG seed — do not confuse them.

**Gotchas.**
- `DFNGeneratorWithSeed` generates in `__init__` (no separate `.run()`); realizations are also
  retained in memory (`gen.realizations`) but the adapter reads the published text files (the
  stable public format).
- `savePic=True` (default) renders matplotlib PNGs per realization — keep it `False` in the
  pipeline (slow, unneeded).
- Set intensities are per-set areal intensity `I` (P21-like); the measured P21 descriptor lands
  within ~10-20% of the requested totals on 100 m domains (truncation + rejection effects).

**Next phase.** These networks are the input geometry for the open-DARTS transient simulation
(the artifact carries `transient_simulation: pending` until that lands — no fake curves).

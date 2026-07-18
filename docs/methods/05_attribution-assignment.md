# 05 · Attribution & assignment (P2e)

**What this group answers.** Two questions beyond the base RF+SHAP attribution and the class-conditional
(Mondrian) split-conformal assigner: *how deep is the label structure* (is it attributable across K, and
which physical knob moves a curve across GeoType boundaries?), and *can we make the assignment safer* by
fusing shape and physics into one coverage-controlled decision. All computed offline on the rich-method
cases and committed to the trace `attribution_plus` block.

## What already existed (the base)

- **RF + TreeSHAP attribution**, accuracy-gated (honest withholding when the forest cannot predict labels).
- **Mondrian / class-conditional split-conformal** (`pygeotypes.assign.ConformalAssigner`): per-class
  calibration of the DTW-distance-to-medoid nonconformity score; p-values, prediction set, out-of-catalogue.

## 1. Predictability-vs-K

For each candidate K in the silhouette sweep, we rebuild the catalogue at K, label the training curves,
and measure the RF held-out accuracy of predicting those labels from the physical descriptors (plus the
silhouette). Where the accuracy peaks is where the labels are most *attributable*; the chosen catalogue
size K* is marked. It answers "is the structure real and explainable, or an artefact of a particular K?".

## 2. ROM descriptor sensitivity sweep

A fast reduced-order surrogate (an RF mapping descriptors -> GeoType) is swept one descriptor at a time
across its p5..p95 range (others held at the median); the sensitivity is the fraction of the sweep that
flips the predicted GeoType. The top bars are the physical knobs that move a curve across GeoType
boundaries, an assignment-sensitivity map rather than a static importance table. (On the analytic families
`log10_lambda` dominates, exactly as expected: lambda sets the interporosity transition timing that
separates the dual-porosity behaviours.)

## 3. Beyond-SOTA: dual-representation Mondrian conformal

Standard and Mondrian conformal use one nonconformity score. A real pressure transient can be
**shape-close to the wrong physics**: a curve that matches a medoid by DTW shape yet whose physical
descriptors are atypical for that GeoType. Our proposal conformalizes jointly across two representations:

- **shape score** $s_\text{shape}(x,g)$ = DTW distance of $x$ to medoid $g$ (the existing score).
- **descriptor score** $s_\text{desc}(x,g) = 1 - \text{RF}(g\mid\text{descriptors}(x))$ (the implausibility
  of $x$'s physical descriptors under GeoType $g$, from the attribution RF).

Both are calibrated per class (Mondrian) on the disjoint calibration slice, giving $p_\text{shape}$ and
$p_\text{desc}$. The dual prediction set is the per-class **conjunction**:

$$ \Gamma^\alpha(x) = \{\, g : p_\text{shape}(x,g) > \alpha \ \wedge\ p_\text{desc}(x,g) > \alpha \,\} $$

A curve is accepted for $g$ only if it is both shape-consistent and descriptor-consistent; a shape-match
with implausible physics is excluded. This is beyond single-score conformal and beyond RF+SHAP (which has
no coverage guarantee): a coverage-controlled assignment that fuses shape space and physics-descriptor
space.

**Reported honestly.** The panel compares the dual set to the shape-only set: empirical marginal coverage
(the dual conjunction trades a little coverage for tighter sets), mean set size, and the count of test
curves the dual layer flags as out-of-catalogue that shape-only conformal ACCEPTS, the "right shape, wrong
physics" value-add. When descriptors are absent or degenerate (some real cases), the dual layer degrades
to shape-only and says so.

## Where it runs

Offline, `methods/attribution_plus.py`, gated by `spec.compare_methods` (WR01, REAL_A, BENCH_A/B/C). The
App **Assignment -> Attribution+** SubTab reads the baked block: the predictability-vs-K chart, the ROM
sensitivity bars, and the dual-vs-shape conformal comparison. No new dependency (scikit-learn + pygeotypes).

## References

- V. Vovk, A. Gammerman, G. Shafer. *Algorithmic Learning in a Random World.* Springer 2005 (conformal +
  the Mondrian taxonomy).
- A. Angelopoulos, S. Bates. *Conformal Prediction: A Gentle Introduction.* Found. Trends ML 16(4), 2023.
- L. Breiman. *Random Forests.* Machine Learning 45, 2001.
- S. Lundberg et al. *From local explanations to global understanding with explainable AI for trees.*
  Nature Machine Intelligence 2, 2020. (TreeSHAP.)

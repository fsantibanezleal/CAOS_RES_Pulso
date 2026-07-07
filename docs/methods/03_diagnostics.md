# 03 · Diagnostics (P2c)

**What this group answers.** Given a single pressure transient, what flow regimes does it pass through,
and which analytic reservoir model actually explains it? This is the interpretive layer a well-test
engineer reads off a log-log diagnostic plot, made **live**: it runs in the browser (TypeScript, no
server, no baked artifact) on the tuned curve, extending the Bourdet-derivative engine in `engine/pta.ts`.

## What it computes (all live)

### Flow-regime auto-detection + marking

The log-log slope of the Bourdet derivative is the fingerprint of the flow regime (Bourdet 1989). The
detector classifies each point and shades contiguous regimes on the plot:

| Regime | Derivative signature |
|---|---|
| wellbore storage | unit slope at early time (derivative rises with pressure) |
| radial flow | derivative plateau at 0.5 |
| linear flow | log-log slope 1/2 |
| bilinear flow | log-log slope 1/4 |
| dual-porosity transition | the derivative dips **below** the 0.5 plateau (the valley) |
| boundary | unit slope at late time |

The dual-porosity valley is detected by value (the derivative well below 0.5), not by slope, because the
valley flanks are steep. Detection runs on the smoothed derivative and a despeckling pass removes
noise-flipped points, so a Warren-Root curve reads cleanly as radial then transition then radial.

### Live parameter recovery: Warren-Root and Theis fits

Two analytic responses are fitted to the tuned curve live, each recovering its physical parameters:

- **Warren-Root** dual-porosity (Warren & Root 1963): recover the storativity ratio omega and the
  interporosity flow coefficient lambda by a coarse grid over (omega, log lambda) then a local
  refinement, minimising the log-pressure residual on a downsampled grid (kept cheap enough to run on
  every slider change).
- **Theis** homogeneous radial (Theis 1935): recover the skin S by a 1D search.

The lower-RMSE model is the one the data supports, and the workbench reports **recovered vs. the value
you set**: a fitter that recovers your inputs on a clean curve is the honest test of the method. On a
dual-porosity curve the Warren-Root fit wins and recovers (omega, lambda); Theis fits a spurious skin and
loses. The winning response is overlaid (dashed) on the plot.

### p'' second logarithmic derivative

The curvature of the derivative (the Bourdet derivative of the Bourdet derivative), shown in a compact
linear panel with a zero line. It sharpens regime boundaries: the transition valley is a curvature
excursion. Read off the smoothed derivative (the raw second derivative amplifies noise).

## Why live, not baked

These are interpretive tools that must react to the curve the user is tuning, so they belong in the TS
engine, not in a committed artifact. The analytic responses reused here (`warrenRootPd`, `homogeneousPd`)
already match `pygeotypes.synthetic` to < 2e-3 relative (`engine/__tests__/parity.test.ts`), and the
diagnostics engine has its own recovery tests (`engine/__tests__/diagnostics.test.ts`): the fits must
recover the generating parameters on clean synthetic curves.

## Where it runs

The App **Live lab** (synthetic source), the classical `Bourdet diagnostics` tool: the log-log plot with
shaded regimes and the dashed best-fit, the p'' curvature strip, the detected-regime chips, and the
recovered-vs-set parameter table. Reacts to every slider live, bilingual, light + dark.

## References

- D. Bourdet, J. A. Ayoub, Y. M. Pirard. *Use of Pressure Derivative in Well Test Interpretation.* SPE
  Formation Evaluation 4(2), 1989.
- J. E. Warren, P. J. Root. *The Behavior of Naturally Fractured Reservoirs.* SPE Journal 3(3), 1963.
- C. V. Theis. *The relation between the lowering of the piezometric surface and the rate and duration of
  discharge of a well using groundwater storage.* Transactions AGU 16, 1935.

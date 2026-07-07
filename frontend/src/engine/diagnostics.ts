// P2c — well-test DIAGNOSTICS (live, TS). Extends the Bourdet-derivative engine (pta.ts) with the
// interpretive layer a reservoir engineer reads off a pressure transient:
//   - flow-regime auto-detection + marking on the log-log derivative (wellbore storage, radial,
//     linear, bilinear, dual-porosity transition, boundary) - Bourdet 1989.
//   - Warren-Root fit: recover (omega, lambda) from the curve by matching the analytic dual-porosity
//     response - Warren & Root 1963.
//   - Theis fit + skin: recover the homogeneous-radial response + skin - Theis 1935.
//   - p'' second logarithmic derivative (curvature of the derivative) - surfaced for the workbench.
// All run LIVE in the browser on the tuned curve; nothing is baked. The analytic engines reused here
// (homogeneousPd / warrenRootPd) already match pygeotypes.synthetic to <2e-3 (see parity.test.ts).
import { bourdet, homogeneousPd, warrenRootPd } from './pta';

export type RegimeKind =
  | 'wellbore-storage'
  | 'radial'
  | 'linear'
  | 'bilinear'
  | 'dual-porosity-transition'
  | 'boundary';

export interface RegimeSegment {
  kind: RegimeKind;
  iStart: number;
  iEnd: number;
  slope: number; // mean log-log slope of the derivative over the segment
}

// canonical log-log slopes of the Bourdet derivative for each single-regime signature
const CANONICAL: Array<{ kind: RegimeKind; slope: number }> = [
  { kind: 'bilinear', slope: 0.25 },
  { kind: 'linear', slope: 0.5 },
  { kind: 'boundary', slope: 1.0 },
];

/** Local log-log slope of a positive series y(t): d ln y / d ln t over a +/- window. */
function loglogSlope(lt: number[], y: number[], i: number, win: number): number {
  const n = y.length;
  const a = Math.max(0, i - win);
  const b = Math.min(n - 1, i + win);
  const ya = Math.max(y[a], 1e-9);
  const yb = Math.max(y[b], 1e-9);
  const dlt = lt[b] - lt[a];
  return dlt !== 0 ? (Math.log(yb) - Math.log(ya)) / dlt : 0;
}

/** p'' — the second logarithmic derivative (Bourdet derivative of the Bourdet derivative). */
export function secondLogDerivative(tD: number[], dp: number[], L = 0.3): number[] {
  return bourdet(tD, dp, L);
}

/**
 * Auto-detect flow regimes on the log-log Bourdet derivative and return contiguous segments.
 * Heuristic, honest: classify each interior point by (a) proximity of p' to the 0.5 radial plateau
 * and (b) the local log-log slope vs the canonical values; a dip below the radial plateau flanked by
 * flatter shoulders is the dual-porosity transition valley (omega/lambda signature).
 */
export function detectRegimes(tD: number[], dp: number[], opts: { win?: number; minLen?: number } = {}): RegimeSegment[] {
  const n = tD.length;
  const win = opts.win ?? 4;
  const minLen = opts.minLen ?? 6;
  const lt = tD.map((v) => Math.log(v));
  const slope = dp.map((_, i) => loglogSlope(lt, dp, i, win));

  // classify each interior point
  const kindOf = (i: number): RegimeKind => {
    const s = slope[i];
    const d = dp[i];
    // radial: derivative near the 0.5 plateau with a flat slope
    if (Math.abs(d - 0.5) < 0.12 && Math.abs(s) < 0.15) return 'radial';
    // dual-porosity transition: the derivative sits WELL BELOW the 0.5 radial plateau (the valley).
    // This is value-driven, not slope-driven: the valley flanks are steep, so a slope test would miss
    // them. Checked before wellbore/boundary so a dip is never mistaken for a unit-slope regime.
    if (d < 0.4) return 'dual-porosity-transition';
    // wellbore storage: unit slope at early time (first third of the log span)
    if (s > 0.75 && i < n / 3) return 'wellbore-storage';
    // boundary: unit slope at late time
    if (s > 0.75) return 'boundary';
    // otherwise the nearest canonical positive slope (linear ½ / bilinear ¼ / boundary unit)
    let best = CANONICAL[0];
    for (const c of CANONICAL) if (Math.abs(s - c.slope) < Math.abs(s - best.slope)) best = c;
    if (Math.abs(s - best.slope) < 0.15) return best.kind;
    return 'radial';
  };

  const labels: RegimeKind[] = [];
  for (let i = 0; i < n; i++) labels.push(i === 0 || i === n - 1 ? kindOf(Math.min(Math.max(i, 1), n - 2)) : kindOf(i));

  // despeckle: reassign runs shorter than minLen to their left neighbour, so a few noise-flipped points
  // do not fragment an otherwise contiguous regime. Repeat until stable (short runs can chain).
  for (let pass = 0; pass < 3; pass++) {
    let changed = false;
    let s0 = 0;
    for (let i = 1; i <= n; i++) {
      if (i === n || labels[i] !== labels[s0]) {
        if (i - s0 < minLen && s0 > 0) {
          for (let j = s0; j < i; j++) labels[j] = labels[s0 - 1];
          changed = true;
        }
        s0 = i;
      }
    }
    if (!changed) break;
  }

  // segment the despeckled labels into contiguous runs (drop any leading short run)
  const segs: RegimeSegment[] = [];
  let s0 = 0;
  for (let i = 1; i <= n; i++) {
    if (i === n || labels[i] !== labels[s0]) {
      if (i - s0 >= minLen) {
        const mid = ((s0 + i - 1) / 2) | 0;
        segs.push({ kind: labels[s0], iStart: s0, iEnd: i - 1, slope: slope[mid] });
      }
      s0 = i;
    }
  }
  return segs;
}

/** Sum of squared residuals in log-pressure between a curve and a model, on the shared grid. */
function logRss(p: number[], model: number[]): number {
  let s = 0;
  for (let i = 0; i < p.length; i++) {
    const a = Math.log(Math.max(p[i], 1e-9));
    const b = Math.log(Math.max(model[i], 1e-9));
    s += (a - b) ** 2;
  }
  return s;
}

/** Downsample (t, p) to k log-spaced indices to keep the live fit cheap. */
function subIndices(n: number, k: number): number[] {
  const idx: number[] = [];
  for (let j = 0; j < k; j++) idx.push(Math.round((j * (n - 1)) / (k - 1)));
  return Array.from(new Set(idx));
}

export interface WarrenRootFit {
  omega: number;
  lam: number;
  rmse: number; // RMS log-pressure residual on the fit grid
}

/**
 * Recover (omega, lambda) by matching the analytic Warren-Root response: a coarse grid over
 * (omega, log10 lambda) then a local refinement, evaluated on a downsampled grid so it stays live.
 */
export function fitWarrenRoot(tD: number[], p: number[]): WarrenRootFit {
  const idx = subIndices(tD.length, 48);
  const tt = idx.map((i) => tD[i]);
  const pp = idx.map((i) => p[i]);
  const evalRss = (omega: number, lam: number) => logRss(pp, warrenRootPd(tt, omega, lam));

  let best = { omega: 0.05, lam: 1e-6, rss: Infinity };
  const omegas = Array.from({ length: 10 }, (_, i) => 0.01 + (0.49 * i) / 9);
  const logLams = Array.from({ length: 8 }, (_, i) => -9 + (5 * i) / 7);
  for (const omega of omegas) {
    for (const ll of logLams) {
      const rss = evalRss(omega, Math.pow(10, ll));
      if (rss < best.rss) best = { omega, lam: Math.pow(10, ll), rss };
    }
  }
  // local refinement around the grid winner
  const lo = Math.log10(best.lam);
  for (let step = 0; step < 2; step++) {
    const dO = 0.03 / (step + 1), dL = 0.4 / (step + 1);
    for (let a = -2; a <= 2; a++) {
      for (let b = -2; b <= 2; b++) {
        const omega = Math.min(0.5, Math.max(0.005, best.omega + a * dO));
        const lam = Math.pow(10, lo + b * dL);
        const rss = evalRss(omega, lam);
        if (rss < best.rss) best = { omega, lam, rss };
      }
    }
  }
  return { omega: best.omega, lam: best.lam, rmse: Math.sqrt(best.rss / pp.length) };
}

export interface TheisFit {
  skin: number;
  rmse: number;
}

/** Recover the homogeneous-radial (Theis) response + skin by a 1D search over skin. */
export function fitTheis(tD: number[], p: number[]): TheisFit {
  const idx = subIndices(tD.length, 48);
  const tt = idx.map((i) => tD[i]);
  const pp = idx.map((i) => p[i]);
  let best = { skin: 0, rss: Infinity };
  for (let s = 0; s <= 6; s += 0.25) {
    const rss = logRss(pp, homogeneousPd(tt, s));
    if (rss < best.rss) best = { skin: s, rss };
  }
  // parabolic refinement around the grid winner
  for (let s = best.skin - 0.2; s <= best.skin + 0.2; s += 0.05) {
    if (s < 0) continue;
    const rss = logRss(pp, homogeneousPd(tt, s));
    if (rss < best.rss) best = { skin: s, rss };
  }
  return { skin: best.skin, rmse: Math.sqrt(best.rss / pp.length) };
}

export const REGIME_COLORS: Record<RegimeKind, string> = {
  'wellbore-storage': '#8b8bd8',
  radial: '#41c98d',
  linear: '#4f9cf9',
  bilinear: '#2bbfd0',
  'dual-porosity-transition': '#d8a14a',
  boundary: '#f97b4f',
};

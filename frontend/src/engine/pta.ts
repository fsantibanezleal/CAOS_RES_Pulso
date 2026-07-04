// TS analytic pressure-transient engine — the LIVE lane for the classical tools. Ports the
// pygeotypes/flowdnalab analytic core so the browser can generate + diagnose a response live as the
// user drags omega/lambda/skin/noise. Parity-tested vs the Python (src/engine/__tests__).

// Modified Bessel K0 via the Abramowitz & Stegun 9.8.5/9.8.6 rational approximations (abs err ~1e-7).
export function besselK0(x: number): number {
  if (x <= 0) return Infinity;
  if (x <= 2) {
    // I0(x) via A&S 9.8.1 uses t = (x/3.75)^2; the K0 series (9.8.5) uses y = (x/2)^2. (Distinct!)
    const t = (x / 3.75) ** 2;
    const i0 =
      1 + t * (3.5156229 + t * (3.0899424 + t * (1.2067492 + t * (0.2659732 + t * (0.0360768 + t * 0.0045813)))));
    const y = (x * x) / 4;
    return (
      -Math.log(x / 2) * i0 +
      (-0.57721566 +
        y * (0.42278420 + y * (0.23069756 + y * (0.03488590 + y * (0.00262698 + y * (0.00010750 + y * 0.0000074))))))
    );
  }
  const y = 2 / x;
  return (
    (Math.exp(-x) / Math.sqrt(x)) *
    (1.25331414 +
      y * (-0.07832358 + y * (0.02189568 + y * (-0.01062446 + y * (0.00587872 + y * (-0.00251540 + y * 0.00053208))))))
  );
}

// Gaver-Stehfest weights V_i (i=1..N, N even).
function stehfestWeights(N: number): number[] {
  const fact = (n: number): number => (n <= 1 ? 1 : n * fact(n - 1));
  const half = N / 2;
  const V: number[] = [];
  for (let i = 1; i <= N; i++) {
    let s = 0;
    for (let k = Math.floor((i + 1) / 2); k <= Math.min(i, half); k++) {
      s +=
        (Math.pow(k, half) * fact(2 * k)) /
        (fact(half - k) * fact(k) * fact(k - 1) * fact(i - k) * fact(2 * k - i));
    }
    V.push(Math.pow(-1, i + half) * s);
  }
  return V;
}
const V12 = stehfestWeights(12);

// Invert a Laplace-space function F(s) at time t (Gaver-Stehfest, N=12).
function stehfest(F: (s: number) => number, t: number): number {
  const ln2t = Math.LN2 / t;
  let out = 0;
  for (let i = 1; i <= 12; i++) out += V12[i - 1] * F(i * ln2t);
  return out * ln2t;
}

function withWellbore(Fpd: (s: number) => number, CD: number, S: number): (s: number) => number {
  if (CD <= 0 && S === 0) return Fpd;
  return (s: number) => {
    const spd = s * Fpd(s) + S;
    return spd / (s * (1 + CD * s * spd));
  };
}

// Homogeneous radial line-source dimensionless wellbore pressure.
export function homogeneousPd(tD: number[], S = 0): number[] {
  const F = withWellbore((s) => besselK0(Math.sqrt(s)) / s, 0, S);
  return tD.map((t) => stehfest(F, t));
}

// Warren-Root dual-porosity (pseudo-steady interporosity) dimensionless wellbore pressure.
export function warrenRootPd(tD: number[], omega: number, lam: number, S = 0): number[] {
  const f = (s: number) => (omega * (1 - omega) * s + lam) / ((1 - omega) * s + lam);
  const F = withWellbore((s) => besselK0(Math.sqrt(s * f(s))) / s, 0, S);
  return tD.map((t) => stehfest(F, t));
}

// Bourdet logarithmic derivative dp/d ln t with a smoothing window of L log-cycles.
export function bourdet(tD: number[], p: number[], L = 0.2): number[] {
  const x = tD.map((t) => Math.log(t));
  const n = x.length;
  const half = (L / 2) * Math.LN10;
  const dp = new Array(n).fill(0);
  for (let i = 0; i < n; i++) {
    let jl = i - 1;
    while (jl > 0 && x[i] - x[jl] < half) jl--;
    let jr = i + 1;
    while (jr < n - 1 && x[jr] - x[i] < half) jr++;
    if (i === 0) dp[i] = (p[jr] - p[i]) / (x[jr] - x[i]);
    else if (i === n - 1) dp[i] = (p[i] - p[jl]) / (x[i] - x[jl]);
    else {
      const dxl = x[i] - x[jl];
      const dxr = x[jr] - x[i];
      const sl = (p[i] - p[jl]) / dxl;
      const sr = (p[jr] - p[i]) / dxr;
      dp[i] = (sl * dxr + sr * dxl) / (dxl + dxr);
    }
  }
  return dp;
}

// z-score normalization (matches pygeotypes.preprocess.normalize 'zscore').
export function zscore(y: number[]): number[] {
  const mu = y.reduce((a, b) => a + b, 0) / y.length;
  const sd = Math.sqrt(y.reduce((a, b) => a + (b - mu) ** 2, 0) / y.length);
  return sd > 0 ? y.map((v) => (v - mu) / sd) : y.map(() => 0);
}

// Resample onto a log-uniform grid of n points over [tMin, tMax] (linear interp in log10 t).
export function logResample(t: number[], y: number[], n: number, tMin: number, tMax: number): { t: number[]; y: number[] } {
  const lo = Math.log10(tMin);
  const hi = Math.log10(tMax);
  const lt = t.map((v) => Math.log10(v));
  const tg: number[] = [];
  const yg: number[] = [];
  for (let i = 0; i < n; i++) {
    const lg = lo + ((hi - lo) * i) / (n - 1);
    tg.push(Math.pow(10, lg));
    // linear interp in log-time
    let j = 0;
    while (j < lt.length - 1 && lt[j + 1] < lg) j++;
    const t0 = lt[j];
    const t1 = lt[Math.min(j + 1, lt.length - 1)];
    const f = t1 > t0 ? (lg - t0) / (t1 - t0) : 0;
    yg.push(y[j] + f * (y[Math.min(j + 1, y.length - 1)] - y[j]));
  }
  return { t: tg, y: yg };
}

export const TD_GRID: number[] = Array.from({ length: 200 }, (_, i) => Math.pow(10, 2 + (8 * i) / 199));

// Model-ready curve: match pygeotypes.prepare_curves (resample pressure to n_points -> Bourdet
// derivative order 1 -> z-score). This is the exact preprocessing the medoids + ONNX models expect.
export function preprocessForModels(tD: number[], p: number[], nPoints: number, L = 0.2): { tGrid: number[]; x: number[] } {
  const { t, y } = logResample(tD, p, nPoints, tD[0], tD[tD.length - 1]);
  const dp = bourdet(t, y, L);
  return { tGrid: t, x: zscore(dp) };
}

// A full live response: generate Warren-Root (or homogeneous) + its Bourdet derivative.
export function generateResponse(omega: number, lam: number, skin: number, noiseSd: number, seed = 1): {
  tD: number[];
  p: number[];
  dp: number[];
} {
  let s = seed >>> 0;
  const rand = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  const gauss = () => Math.sqrt(-2 * Math.log(rand() + 1e-12)) * Math.cos(2 * Math.PI * rand());
  const base = omega >= 0.999 ? homogeneousPd(TD_GRID, skin) : warrenRootPd(TD_GRID, omega, lam, skin);
  const p = base.map((v) => (noiseSd > 0 ? v * Math.exp(noiseSd * gauss()) : v));
  return { tD: TD_GRID, p, dp: bourdet(TD_GRID, p) };
}

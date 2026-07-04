// TS DTW + conformal assignment — the LIVE lane for the SOTA (DTW-to-medoid) + NOVEL (conformal)
// tools. Ports pygeotypes.distance.dtw_banded + assign. Runs on the tuned curve against the baked
// catalogue medoids + calibration scores in the browser.

// Sakoe-Chiba banded DTW distance (sqrt of accumulated squared cost) — matches pygeotypes.
export function dtwBanded(x: number[], y: number[], window: number): number {
  const n = x.length;
  const m = y.length;
  const w = Math.max(window, Math.abs(n - m));
  let prev = new Array(m + 1).fill(Infinity);
  prev[0] = 0;
  for (let i = 1; i <= n; i++) {
    const cur = new Array(m + 1).fill(Infinity);
    const lo = Math.max(1, i - w);
    const hi = Math.min(m, i + w);
    for (let j = lo; j <= hi; j++) {
      const c = (x[i - 1] - y[j - 1]) ** 2;
      cur[j] = c + Math.min(prev[j], prev[j - 1], cur[j - 1]);
    }
    prev = cur;
  }
  return Math.sqrt(prev[m]);
}

export function distancesToMedoids(x: number[], medoids: number[][], window: number): number[] {
  return medoids.map((m) => dtwBanded(x, m, window));
}

// split-conformal assignment against baked class-conditional calibration scores (sorted ascending).
export interface ConformalResult {
  point: number;
  pValues: number[];
  set: number[];
  ood: boolean;
  distances: number[];
}

export function conformalAssign(
  distances: number[],
  calibrationScores: Record<string, number[]>,
  alpha: number,
): ConformalResult {
  const k = distances.length;
  const p: number[] = [];
  for (let g = 0; g < k; g++) {
    const s = calibrationScores[String(g)] ?? [];
    if (s.length === 0) {
      p.push(0);
      continue;
    }
    // count of calibration scores >= the query distance (>= convention)
    let ge = 0;
    for (const v of s) if (v >= distances[g]) ge++;
    p.push((ge + 1) / (s.length + 1));
  }
  const point = distances.indexOf(Math.min(...distances));
  const set: number[] = [];
  for (let g = 0; g < k; g++) if (p[g] > alpha) set.push(g);
  return { point, pValues: p, set, ood: set.length === 0, distances };
}

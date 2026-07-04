// Minimal replay renderers for the two FlowDNA artifact kinds (the full ADR-0016 six-page shell is
// the next phase; this keeps the contract exercised end-to-end: index -> manifest -> trace -> pixels).
import type { DfnTrace, StudyTrace } from '../lib/contract.types';

const W = 860;
const H = 380;
const PAD = 44;
const COLORS = ['#4f9cf9', '#f97b4f', '#41c98d', '#c94fd0', '#d8c14a', '#7a8699'];

function toPath(xs: number[], ys: number[], sx: (x: number) => number, sy: (y: number) => number): string {
  return xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${sx(x).toFixed(1)},${sy(ys[i]).toFixed(1)}`).join(' ');
}

export function StudyChart({ trace }: { trace: StudyTrace }) {
  const lx = trace.t_grid.map((t) => Math.log10(t));
  const all = trace.medoids.flat();
  const yMin = Math.min(...all);
  const yMax = Math.max(...all);
  const sx = (x: number) => PAD + ((x - lx[0]) / (lx[lx.length - 1] - lx[0])) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - yMin) / (yMax - yMin || 1)) * (H - 2 * PAD);
  return (
    <figure>
      <svg width={W} height={H} role="img" aria-label="GeoType medoid curves">
        <rect width={W} height={H} fill="#0d1117" rx={8} />
        {trace.samples.map((s, i) => (
          <path
            key={`s${i}`}
            d={toPath(lx, s.curve, sx, sy)}
            fill="none"
            stroke={COLORS[s.geotype % COLORS.length]}
            strokeOpacity={0.25}
            strokeWidth={1}
          />
        ))}
        {trace.medoids.map((m, g) => (
          <path
            key={`m${g}`}
            d={toPath(lx, m, sx, sy)}
            fill="none"
            stroke={COLORS[g % COLORS.length]}
            strokeWidth={2.5}
          />
        ))}
        <text x={PAD} y={H - 12} fill="#7a8699" fontSize={12}>
          log10 tD →
        </text>
        {trace.medoids.map((_, g) => (
          <text key={`l${g}`} x={W - PAD - 90} y={PAD + 16 * g} fill={COLORS[g % COLORS.length]} fontSize={12}>
            GT{g} (n={trace.geotype_counts[g]})
          </text>
        ))}
      </svg>
      <figcaption style={{ color: '#7a8699', fontSize: 13 }}>
        K={trace.k} medoids (bold) + member samples (faint), preprocessed order-
        {trace.preprocessing.derivative_order} derivative, silhouette {trace.silhouette.toFixed(3)} ·
        conformal coverage {trace.summary.coverage.toFixed(2)} / target {trace.summary.target.toFixed(2)} ·
        OOD rate {trace.summary.ood_rate.toFixed(2)}
      </figcaption>
    </figure>
  );
}

export function DfnChart({ trace }: { trace: DfnTrace }) {
  const net = trace.networks[0];
  const dom = trace.stats.domain;
  const S = Math.min((W - 2 * PAD) / dom.x, (H - 2 * PAD) / dom.y);
  return (
    <figure>
      <svg width={W} height={H} role="img" aria-label="GeoDFN network (first realization)">
        <rect width={W} height={H} fill="#0d1117" rx={8} />
        {net?.segments.map((s, i) => (
          <line
            key={i}
            x1={PAD + s[0] * S}
            y1={H - PAD - s[1] * S}
            x2={PAD + s[2] * S}
            y2={H - PAD - s[3] * S}
            stroke="#4f9cf9"
            strokeWidth={1}
          />
        ))}
      </svg>
      <figcaption style={{ color: '#7a8699', fontSize: 13 }}>
        Realization 1 of {trace.networks.length} committed ({net?.n_fractures} fractures) ·
        descriptors per network: {trace.descriptor_names.length} · {trace.transient_simulation}
      </figcaption>
    </figure>
  );
}

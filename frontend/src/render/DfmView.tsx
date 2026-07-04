// DFM simulation view (open-DARTS Step B): the representative simulated pressure transient + the
// MRST-ensemble fidelity band + the gate verdict + mesh/physics stats. The GeoType catalogue,
// conformal classifier and attribution for a DFM case are rendered by the SHARED study views (a
// DfmTrace is-a StudyTrace); this view adds the simulated-physics evidence.
import type { DfmTrace } from '../lib/contract.types';

const W = 860;
const H = 360;
const PAD = 46;

function toPath(xs: number[], ys: number[], sx: (x: number) => number, sy: (y: number) => number): string {
  return xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${sx(x).toFixed(1)},${sy(ys[i]).toFixed(1)}`).join(' ');
}

function num(v: number | number[] | null | undefined, d = 3): string {
  return typeof v === 'number' ? v.toFixed(d) : '-';
}

function TransientChart({ trace }: { trace: DfmTrace }) {
  const s = trace.dfm.sample_transient;
  const lx = s.tD.map((t) => Math.log10(t));
  const all = [...s.pwD, ...s.dpwD].filter((v) => v > 0).map((v) => Math.log10(v));
  const yMin = Math.min(...all);
  const yMax = Math.max(...all);
  const sx = (x: number) => PAD + ((x - lx[0]) / (lx[lx.length - 1] - lx[0] || 1)) * (W - 2 * PAD);
  const sy = (y: number) =>
    H - PAD - ((Math.log10(Math.max(y, 1e-6)) - yMin) / (yMax - yMin || 1)) * (H - 2 * PAD);
  return (
    <figure>
      <svg width={W} height={H} role="img" aria-label="simulated DFM pressure transient">
        <rect width={W} height={H} fill="#0d1117" rx={8} />
        <path d={toPath(lx, s.pwD, sx, sy)} fill="none" stroke="#4f9cf9" strokeWidth={2.5} />
        <path d={toPath(lx, s.dpwD, sx, sy)} fill="none" stroke="#f97b4f" strokeWidth={2.5} />
        <text x={W - PAD - 210} y={PAD} fill="#4f9cf9" fontSize={12}>p_wD (dimensionless drawdown)</text>
        <text x={W - PAD - 210} y={PAD + 16} fill="#f97b4f" fontSize={12}>Bourdet derivative</text>
        <text x={PAD} y={H - 12} fill="#7a8699" fontSize={12}>log10 tD →</text>
      </svg>
      <figcaption style={{ color: '#7a8699', fontSize: 13 }}>
        A representative open-DARTS DFM single-phase drawdown on one meshed GeoDFN network
        ({num(trace.dfm.mesh_stats.n_frac_cells, 0)} fracture cells,{' '}
        {num(trace.dfm.mesh_stats.n_mat_cells, 0)} matrix cells). The suppressed early derivative is
        the conductive fracture network; the late rise is the closed-domain signature.
      </figcaption>
    </figure>
  );
}

function FidelityChart({ trace }: { trace: DfmTrace }) {
  const f = trace.dfm.fidelity;
  if (!f.band || !f.band.tD.length) {
    return (
      <p className="muted">
        MRST fidelity: <b>{f.reference}</b>
        {f.note ? ` — ${f.note}` : ''}
      </p>
    );
  }
  const b = f.band;
  const lx = b.tD.map((t) => Math.log10(t));
  const all = [...b.p5, ...b.p95, ...b.sim].filter((v) => v > 0);
  const yMax = Math.max(...all) * 1.1;
  const sx = (x: number) => PAD + ((x - lx[0]) / (lx[lx.length - 1] - lx[0] || 1)) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - (y / (yMax || 1)) * (H - 2 * PAD);
  // shaded p5-p95 band as a closed polygon
  const bandPath =
    b.tD.map((_, i) => `${i === 0 ? 'M' : 'L'}${sx(lx[i]).toFixed(1)},${sy(b.p95[i]).toFixed(1)}`).join(' ') +
    ' ' +
    b.tD
      .map((_, i) => `L${sx(lx[b.tD.length - 1 - i]).toFixed(1)},${sy(b.p5[b.tD.length - 1 - i]).toFixed(1)}`)
      .join(' ') +
    ' Z';
  return (
    <figure>
      <svg width={W} height={H} role="img" aria-label="DFM derivative vs MRST reference band">
        <rect width={W} height={H} fill="#0d1117" rx={8} />
        <path d={bandPath} fill="#41c98d" fillOpacity={0.15} stroke="none" />
        <path d={toPath(lx, b.p50, sx, sy)} fill="none" stroke="#41c98d" strokeWidth={2} strokeDasharray="5 4" />
        <path d={toPath(lx, b.sim, sx, sy)} fill="none" stroke="#f97b4f" strokeWidth={2.5} />
        <text x={W - PAD - 220} y={PAD} fill="#41c98d" fontSize={12}>MRST ensemble p5-p95 + median</text>
        <text x={W - PAD - 220} y={PAD + 16} fill="#f97b4f" fontSize={12}>FlowDNA DFM ensemble median</text>
        <text x={PAD} y={H - 12} fill="#7a8699" fontSize={12}>log10 tD →</text>
      </svg>
      <figcaption style={{ color: '#7a8699', fontSize: 13 }}>
        Ensemble-median Bourdet derivative vs the paper's MRST reference (Dataset {f.dataset}) ·{' '}
        <b style={{ color: f.passed ? '#41c98d' : '#f85149' }}>{f.passed ? 'FIDELITY PASS' : 'fidelity fail'}</b> ·
        band coverage {num(f.band_coverage, 2)} (min {num(f.min_band_coverage, 2)}) · shape corr{' '}
        {num(f.shape_corr, 2)} · scale-aligned shape rel-L2 {num(f.shape_rel_l2, 2)} ({f.n_ref_curves} MRST curves)
      </figcaption>
    </figure>
  );
}

export function DfmView({ trace }: { trace: DfmTrace }) {
  const d = trace.dfm;
  const p = d.physical;
  const e = d.ensemble;
  const rows: Array<[string, string]> = [
    ['valid transients', `${e.n_ok} / ${e.n_networks} networks (${e.n_fail} skipped)`],
    ['matrix permeability', `${num(p.matrix_perm_mD, 2)} mD`],
    [
      'fracture permeability (cubic law)',
      `${num(p.perm_frac_min_mD, 0)} - ${num(p.perm_frac_max_mD, 0)} mD`,
    ],
    ['fracture aperture sweep', `${num(p.frac_aper_min_m, 5)} - ${num(p.frac_aper_max_m, 5)} m`],
    ['well rate', `${num(p.well_rate_m3day, 1)} m3/day`],
    ['well to nearest fracture', `${num(d.mesh_stats.well_to_nearest_frac_m, 2)} m`],
  ];
  return (
    <div className="grid" style={{ gap: '1rem' }}>
      <p style={{ marginBottom: 0 }}>
        The <b>dfn</b> cases graduate here: real open-DARTS DFM drawdowns replace geometry-only
        descriptors. {d.transient_simulation}.
      </p>
      <TransientChart trace={trace} />
      <FidelityChart trace={trace} />
      <div className="scroll-x">
        <table>
          <thead>
            <tr><th>DFM simulation</th><th>value</th></tr>
          </thead>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k}><td>{k}</td><td className="tag">{v}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

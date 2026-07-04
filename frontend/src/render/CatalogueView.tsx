// GeoType catalogue with a live cursor read-out (interactive per ADR-0016): hover to read the
// dimensionless time and each medoid's value at the cursor.
import { useRef, useState } from 'react';
import type { StudyTrace } from '../lib/contract.types';
import { useT } from '../i18n/useT';

const W = 860;
const H = 400;
const PAD = 46;
const COLORS = ['var(--geo-0)', 'var(--geo-1)', 'var(--geo-2)', 'var(--geo-3)', 'var(--geo-4)'];

export function CatalogueView({ trace }: { trace: StudyTrace }) {
  const t = useT();
  const svgRef = useRef<SVGSVGElement>(null);
  const [ci, setCi] = useState<number | null>(null);

  const lx = trace.t_grid.map((v) => Math.log10(v));
  const all = trace.medoids.flat();
  const yMin = Math.min(...all);
  const yMax = Math.max(...all);
  const sx = (x: number) => PAD + ((x - lx[0]) / (lx[lx.length - 1] - lx[0])) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - yMin) / (yMax - yMin || 1)) * (H - 2 * PAD);
  const path = (ys: number[]) => ys.map((y, i) => `${i === 0 ? 'M' : 'L'}${sx(lx[i]).toFixed(1)},${sy(y).toFixed(1)}`).join(' ');

  const onMove = (e: React.MouseEvent) => {
    const r = svgRef.current!.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    const frac = (px - PAD) / (W - 2 * PAD);
    const idx = Math.round(frac * (lx.length - 1));
    setCi(idx >= 0 && idx < lx.length ? idx : null);
  };

  return (
    <div>
      <p className="muted">{t.app.catalogue.desc}</p>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', margin: '.5rem 0' }}>
        <span className="readout">{t.app.catalogue.k}: {trace.k}</span>
        <span className="readout">{t.common.silhouette}: {trace.silhouette.toFixed(3)}</span>
        {trace.geotype_counts.map((c, g) => (
          <span key={g} className="readout" style={{ color: COLORS[g % COLORS.length] }}>GT{g}: {c} {t.app.catalogue.members}</span>
        ))}
      </div>
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} width="100%" onMouseMove={onMove} onMouseLeave={() => setCi(null)}
        role="img" aria-label="GeoType medoid curves" style={{ cursor: 'crosshair' }}>
        <rect width={W} height={H} rx={8} fill="var(--bg-3)" />
        {trace.samples.map((s, i) => (
          <path key={`s${i}`} d={path(s.curve)} fill="none" stroke={COLORS[s.geotype % COLORS.length]} strokeOpacity={0.18} strokeWidth={1} />
        ))}
        {trace.medoids.map((m, g) => (
          <path key={`m${g}`} d={path(m)} fill="none" stroke={COLORS[g % COLORS.length]} strokeWidth={2.5} />
        ))}
        {ci !== null && (
          <>
            <line x1={sx(lx[ci])} y1={PAD} x2={sx(lx[ci])} y2={H - PAD} stroke="var(--fg-2)" strokeDasharray="3 3" />
            {trace.medoids.map((m, g) => (
              <circle key={g} cx={sx(lx[ci])} cy={sy(m[ci])} r={3.5} fill={COLORS[g % COLORS.length]} />
            ))}
          </>
        )}
        <text x={PAD} y={H - 14} fill="var(--fg-2)" fontSize={12}>log10 tD →</text>
      </svg>
      {ci !== null && (
        <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', marginTop: '.5rem' }}>
          <span className="readout">tD = {trace.t_grid[ci].toExponential(2)}</span>
          {trace.medoids.map((m, g) => (
            <span key={g} className="readout" style={{ color: COLORS[g % COLORS.length] }}>GT{g} = {m[ci].toFixed(3)}</span>
          ))}
        </div>
      )}
    </div>
  );
}

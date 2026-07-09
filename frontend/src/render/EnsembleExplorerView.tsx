// Ensemble explorer (S2/P3): renders the WHOLE committed ensemble that CONTRACT-3 ships but nothing
// rendered before - every member curve (min/max-decimated, coloured by GeoType) plus the per-cluster
// p10/p50/p90 envelope bands that summarise the FULL population. A cursor reads each cluster's median
// at the hovered dimensionless time. Theme-aware; the member spaghetti is capped for responsiveness
// (the envelopes always summarise every member, so nothing is hidden - the cap is stated).
import { useMemo, useRef, useState } from 'react';
import type { StudyTraceV2 } from '../lib/contract.types';
import { useT } from '../i18n/useT';

const COLORS = ['var(--geo-0)', 'var(--geo-1)', 'var(--geo-2)', 'var(--geo-3)', 'var(--geo-4)'];
const W = 860, H = 420, PAD = 48;
const MAX_DRAWN = 260; // cap the member polylines drawn (envelopes still summarise all members)

type ShowMode = 'both' | 'members' | 'envelopes';

export function EnsembleExplorerView({ trace }: { trace: StudyTraceV2 }) {
  const t = useT();
  const svgRef = useRef<SVGSVGElement>(null);
  const [mode, setMode] = useState<ShowMode>('both');
  const [cx, setCx] = useState<number | null>(null);

  const { members, envelopes } = trace;
  const tgrid = trace.t_grid;
  const lt = useMemo(() => tgrid.map((v) => Math.log10(v)), [tgrid]);

  // y-range across everything drawn (members + envelope bands)
  const { yMin, yMax } = useMemo(() => {
    let lo = Infinity, hi = -Infinity;
    for (const c of members.curves) for (const v of c) { if (v < lo) lo = v; if (v > hi) hi = v; }
    for (const e of envelopes) for (const arr of [e.p10, e.p90]) for (const v of arr) { if (v < lo) lo = v; if (v > hi) hi = v; }
    if (!Number.isFinite(lo)) { lo = 0; hi = 1; }
    return { yMin: lo, yMax: hi };
  }, [members, envelopes]);

  const sx = (f: number) => PAD + f * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - yMin) / (yMax - yMin || 1)) * (H - 2 * PAD);
  // member curves are decimated onto their own even grid; the fraction across the log-time span aligns
  // them with the envelopes (both span the same range), so index i/(n-1) == the envelope's log-t fraction.
  const memPath = (c: number[]) => c.map((y, i) => `${i === 0 ? 'M' : 'L'}${sx(i / (c.length - 1)).toFixed(1)},${sy(y).toFixed(1)}`).join(' ');
  const envX = (j: number) => sx((lt[j] - lt[0]) / (lt[lt.length - 1] - lt[0] || 1));
  const bandPath = (p10: number[], p90: number[]) => {
    const up = p90.map((y, j) => `${j === 0 ? 'M' : 'L'}${envX(j).toFixed(1)},${sy(y).toFixed(1)}`).join(' ');
    const dn = p10.map((_, j) => `L${envX(p10.length - 1 - j).toFixed(1)},${sy(p10[p10.length - 1 - j]).toFixed(1)}`).join(' ');
    return `${up} ${dn} Z`;
  };
  const line = (arr: number[]) => arr.map((y, j) => `${j === 0 ? 'M' : 'L'}${envX(j).toFixed(1)},${sy(y).toFixed(1)}`).join(' ');

  // per-cluster member counts (committed) + which members to draw (capped, stratified by cluster)
  const counts = useMemo(() => {
    const c: Record<number, number> = {};
    for (const g of members.geotype) c[g] = (c[g] ?? 0) + 1;
    return c;
  }, [members]);
  const drawnIdx = useMemo(() => {
    const n = members.curves.length;
    if (n <= MAX_DRAWN) return members.curves.map((_, i) => i);
    const step = n / MAX_DRAWN;
    return Array.from({ length: MAX_DRAWN }, (_, k) => Math.floor(k * step));
  }, [members]);

  const onMove = (e: React.MouseEvent) => {
    const r = svgRef.current!.getBoundingClientRect();
    const f = ((e.clientX - r.left) / r.width * W - PAD) / (W - 2 * PAD);
    setCx(f >= 0 && f <= 1 ? f : null);
  };
  const jHover = cx === null ? null : Math.round(cx * (lt.length - 1));

  const nMembers = trace.stats.n_members;
  const nCommitted = trace.stats.n_committed ?? members.curves.length;
  const drawnNote = drawnIdx.length < members.curves.length
    ? t.app.explorer.drawnCap.replace('{k}', String(drawnIdx.length)).replace('{n}', String(nCommitted))
    : '';

  return (
    <div>
      <p className="muted">{t.app.explorer.desc}</p>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', margin: '.5rem 0', alignItems: 'center' }}>
        {(['both', 'envelopes', 'members'] as ShowMode[]).map((m) => (
          <span key={m} className={`chip ${mode === m ? 'on' : ''}`} onClick={() => setMode(m)}>{t.app.explorer[m]}</span>
        ))}
        <span className="readout">{t.app.explorer.population}: {nMembers}{nCommitted !== nMembers ? ` (${nCommitted} ${t.app.explorer.committed})` : ''}</span>
        {envelopes.map((e) => (
          <span key={e.geotype} className="readout" style={{ color: COLORS[e.geotype % COLORS.length] }}>
            GT{e.geotype}: {counts[e.geotype] ?? 0}
          </span>
        ))}
      </div>

      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} width="100%" onMouseMove={onMove} onMouseLeave={() => setCx(null)}
        role="img" aria-label={t.app.explorer.aria} style={{ background: 'var(--bg-3)', borderRadius: 8, cursor: 'crosshair' }}>
        {/* p10-p90 bands (behind) + p50 medians */}
        {(mode === 'both' || mode === 'envelopes') && envelopes.map((e) => e.p50.length > 0 && (
          <g key={`e${e.geotype}`}>
            <path d={bandPath(e.p10, e.p90)} fill={COLORS[e.geotype % COLORS.length]} fillOpacity={0.14} stroke="none" />
            <path d={line(e.p50)} fill="none" stroke={COLORS[e.geotype % COLORS.length]} strokeWidth={2.4} />
          </g>
        ))}
        {/* member spaghetti (faint), capped + stratified */}
        {(mode === 'both' || mode === 'members') && drawnIdx.map((i) => (
          <path key={`m${i}`} d={memPath(members.curves[i])} fill="none"
            stroke={COLORS[members.geotype[i] % COLORS.length]} strokeOpacity={mode === 'members' ? 0.28 : 0.13} strokeWidth={1} />
        ))}
        {/* hover cursor + per-cluster median readout */}
        {jHover !== null && (
          <>
            <line x1={envX(jHover)} y1={PAD} x2={envX(jHover)} y2={H - PAD} stroke="var(--fg-2)" strokeDasharray="3 3" />
            {envelopes.map((e) => e.p50[jHover] !== undefined && (
              <circle key={`h${e.geotype}`} cx={envX(jHover)} cy={sy(e.p50[jHover])} r={3.5} fill={COLORS[e.geotype % COLORS.length]} />
            ))}
          </>
        )}
        <text x={PAD} y={H - 14} fill="var(--fg-2)" fontSize={12}>log10 tD</text>
      </svg>

      <div style={{ display: 'flex', gap: '.6rem', marginTop: '.5rem', flexWrap: 'wrap', minHeight: '1.4rem' }}>
        {jHover !== null && (
          <>
            <span className="readout">log10 tD: {lt[jHover].toFixed(2)}</span>
            {envelopes.map((e) => e.p50[jHover] !== undefined && (
              <span key={`r${e.geotype}`} className="readout" style={{ color: COLORS[e.geotype % COLORS.length] }}>
                GT{e.geotype} p50: {e.p50[jHover].toFixed(3)}
              </span>
            ))}
          </>
        )}
      </div>
      {drawnNote && <p className="muted" style={{ fontSize: '.8em', marginTop: '.3rem' }}>{drawnNote}</p>}
      {members.note && members.note !== 'full' && (
        <p className="muted" style={{ fontSize: '.8em', marginTop: '.2rem' }}>{t.app.explorer.membersNote}: {members.note}</p>
      )}
    </div>
  );
}

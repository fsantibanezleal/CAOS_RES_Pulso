// Attribution+ (P2e): the depth beyond RF+SHAP. Three panels, all read from the baked `attribution_plus`
// block: predictability-vs-K (is the label structure attributable across K?), the ROM descriptor
// sensitivity sweep (which physical knob moves the GeoType?), and the NOVEL dual-representation Mondrian
// conformal (shape-space DTW conformal INTERSECT descriptor-space RF conformal) compared to shape-only.
import type { AttributionPlus } from '../lib/contract.types';
import { useT } from '../i18n/useT';

const COLORS = ['var(--geo-0)', 'var(--geo-1)', 'var(--geo-2)', 'var(--geo-3)', 'var(--geo-4)'];

function Predictability({ ap }: { ap: AttributionPlus }) {
  const t = useT();
  const W = 520, H = 240, PAD = 40;
  const pts = ap.predictability;
  const ks = pts.map((p) => p.k);
  const kmin = Math.min(...ks), kmax = Math.max(...ks);
  const sx = (k: number) => PAD + ((k - kmin) / (kmax - kmin || 1)) * (W - 2 * PAD);
  const sy = (v: number) => H - PAD - v * (H - 2 * PAD); // both series in [0,1]
  const path = (sel: (p: typeof pts[number]) => number | null) => pts
    .filter((p) => sel(p) !== null)
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${sx(p.k).toFixed(1)},${sy(sel(p)!).toFixed(1)}`).join(' ');
  return (
    <div>
      <h4 style={{ margin: '0 0 .2rem' }}>{t.app.attrplus.predTitle}</h4>
      <p className="muted" style={{ fontSize: '.85em', marginTop: 0 }}>{t.app.attrplus.predDesc}</p>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: 520, background: 'var(--bg-3)', borderRadius: 8 }} role="img" aria-label={t.app.attrplus.predTitle}>
        {[0, 0.25, 0.5, 0.75, 1].map((g) => (
          <g key={g}><line x1={PAD} y1={sy(g)} x2={W - PAD} y2={sy(g)} stroke="var(--fg-2)" strokeOpacity={0.15} />
            <text x={8} y={sy(g) + 3} fill="var(--fg-2)" fontSize={9}>{g.toFixed(2)}</text></g>
        ))}
        <line x1={sx(ap.chosen_k)} y1={PAD} x2={sx(ap.chosen_k)} y2={H - PAD} stroke="var(--accent, #4f9cf9)" strokeDasharray="4 3" />
        <text x={sx(ap.chosen_k) + 3} y={PAD + 10} fill="var(--fg-2)" fontSize={10}>K*={ap.chosen_k}</text>
        <path d={path((p) => p.silhouette)} fill="none" stroke="#8b8bd8" strokeWidth={2} />
        <path d={path((p) => p.rf_accuracy)} fill="none" stroke="#41c98d" strokeWidth={2} />
        {pts.map((p) => p.rf_accuracy !== null && <circle key={`a${p.k}`} cx={sx(p.k)} cy={sy(p.rf_accuracy)} r={2.6} fill="#41c98d" />)}
        {pts.map((p) => <circle key={`s${p.k}`} cx={sx(p.k)} cy={sy(p.silhouette)} r={2.6} fill="#8b8bd8" />)}
        {ks.map((k) => <text key={k} x={sx(k)} y={H - PAD + 14} fill="var(--fg-2)" fontSize={9} textAnchor="middle">{k}</text>)}
        <text x={W / 2} y={H - 6} fill="var(--fg-2)" fontSize={10} textAnchor="middle">K</text>
      </svg>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', marginTop: '.3rem' }}>
        <span className="readout" style={{ color: '#8b8bd8' }}>{t.app.attrplus.silhouette}</span>
        <span className="readout" style={{ color: '#41c98d' }}>{t.app.attrplus.rfAcc}</span>
      </div>
    </div>
  );
}

function Rom({ ap }: { ap: AttributionPlus }) {
  const t = useT();
  const rom = ap.rom;
  if (!rom.descriptors.length) return <p className="muted">{rom.note || t.app.attrplus.romNone}</p>;
  const max = Math.max(...rom.sensitivity, 1e-6);
  return (
    <div>
      <h4 style={{ margin: '0 0 .2rem' }}>{t.app.attrplus.romTitle}</h4>
      <p className="muted" style={{ fontSize: '.85em', marginTop: 0 }}>{t.app.attrplus.romDesc}</p>
      <div style={{ display: 'grid', gap: '.35rem', maxWidth: 520 }}>
        {rom.descriptors.map((name, i) => (
          <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
            <span className="tag" style={{ width: 130, flexShrink: 0, fontSize: '.8em' }}>{name}</span>
            <div style={{ flex: 1, height: 12, background: 'var(--bg-2)', borderRadius: 4 }}>
              <div style={{ width: `${(rom.sensitivity[i] / max) * 100}%`, height: 12, background: COLORS[i % COLORS.length], borderRadius: 4 }} />
            </div>
            <span className="tag" style={{ width: 48, textAlign: 'right' }}>{rom.sensitivity[i].toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Dual({ ap }: { ap: AttributionPlus }) {
  const t = useT();
  const d = ap.dual_conformal;
  return (
    <div>
      <h4 style={{ margin: '0 0 .2rem' }}>{t.app.attrplus.dualTitle}</h4>
      <p className="muted" style={{ fontSize: '.85em', marginTop: 0 }}>{t.app.attrplus.dualDesc}</p>
      {d.note && <p className="muted" style={{ fontSize: '.8em' }}>{d.note}</p>}
      <div className="scroll-x">
        <table style={{ maxWidth: 560 }}>
          <thead>
            <tr><th>{t.app.attrplus.metric}</th><th>{t.app.attrplus.shapeOnly}</th><th>{t.app.attrplus.dual}</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>{t.app.attrplus.coverage} (1-α={(1 - d.alpha).toFixed(2)})</td>
              <td className="tag">{d.coverage_shape.toFixed(3)}</td>
              <td className="tag">{d.coverage_dual.toFixed(3)}</td>
            </tr>
            <tr>
              <td>{t.app.attrplus.meanSet}</td>
              <td className="tag">{d.mean_set_shape.toFixed(2)}</td>
              <td className="tag">{d.mean_set_dual.toFixed(2)}</td>
            </tr>
            <tr>
              <td>{t.app.attrplus.caught}</td>
              <td className="tag">—</td>
              <td><span className="badge ok">{d.caught_by_physics} / {d.n_test}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      {d.examples.length > 0 && (
        <p className="muted" style={{ fontSize: '.82em', marginTop: '.4rem' }}>
          {t.app.attrplus.examples}: {d.examples.map((e) => `#${e.test_index} (shape {${e.shape_set.join(',')}})`).join(', ')}
        </p>
      )}
    </div>
  );
}

export function AttributionPlusView({ ap }: { ap: AttributionPlus }) {
  const t = useT();
  if (ap.error) return <p className="muted">{t.app.attrplus.unavailable}: {ap.error}</p>;
  return (
    <div style={{ display: 'grid', gap: '1.2rem' }}>
      <Predictability ap={ap} />
      <Rom ap={ap} />
      <Dual ap={ap} />
    </div>
  );
}

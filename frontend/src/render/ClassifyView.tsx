// Classify-a-curve: step through the held-out test curves the offline pipeline conformally assigned
// (baked in the trace) and read the point prediction, p-values and prediction set. Interactive: the
// selected assignment updates the read-outs + the highlighted medoid.
import { useState } from 'react';
import type { StudyTrace } from '../lib/contract.types';
import { useT } from '../i18n/useT';

const COLORS = ['var(--geo-0)', 'var(--geo-1)', 'var(--geo-2)', 'var(--geo-3)', 'var(--geo-4)'];

export function ClassifyView({ trace }: { trace: StudyTrace }) {
  const t = useT();
  const [i, setI] = useState(0);
  const a = trace.assignments[i];
  if (!a) return <p className="muted">{t.common.panelError}</p>;

  return (
    <div>
      <p className="muted">{t.app.classify.desc}</p>
      <label className="tag" style={{ display: 'block', margin: '.5rem 0' }}>
        {t.app.classify.pick}: {i + 1} / {trace.assignments.length}
        <input
          type="range"
          min={0}
          max={trace.assignments.length - 1}
          value={i}
          onChange={(e) => setI(Number(e.target.value))}
          style={{ display: 'block', width: 320, maxWidth: '100%', marginTop: '.35rem' }}
        />
      </label>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', margin: '.5rem 0' }}>
        <span className="readout">
          {t.app.classify.pred}: <b style={{ color: COLORS[a.point_prediction % COLORS.length] }}>GT{a.point_prediction}</b>
        </span>
        <span className="readout">
          {t.app.classify.set}: {a.prediction_set.length ? a.prediction_set.map((g) => `GT${g}`).join(', ') : '∅'}
        </span>
        {a.out_of_catalogue && <span className="badge bad">{t.app.classify.ood}</span>}
      </div>
      <div className="scroll-x">
        <table>
          <thead>
            <tr><th>GeoType</th><th>{t.app.classify.pvalues}</th><th>in set</th></tr>
          </thead>
          <tbody>
            {a.p_values.map((p, g) => (
              <tr key={g}>
                <td style={{ color: COLORS[g % COLORS.length] }}>GT{g}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                    <div style={{ width: 120, height: 8, background: 'var(--bg-2)', borderRadius: 4 }}>
                      <div style={{ width: `${Math.min(100, p * 100)}%`, height: 8, background: COLORS[g % COLORS.length], borderRadius: 4 }} />
                    </div>
                    <span className="tag">{p.toFixed(3)}</span>
                  </div>
                </td>
                <td>{a.prediction_set.includes(g) ? '✓' : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted" style={{ fontSize: '.82rem' }}>
        α = {a.alpha} · {t.common.coverage} {t.common.target} {(1 - a.alpha).toFixed(2)}
      </p>
    </div>
  );
}

// Attribution: the RF + SHAP importances per GeoType (baked in the trace), gated on held-out
// accuracy. When the gate did not pass, the importances are honestly withheld.
import type { StudyTrace } from '../lib/contract.types';
import { useT } from '../i18n/useT';

const COLORS = ['var(--geo-0)', 'var(--geo-1)', 'var(--geo-2)', 'var(--geo-3)', 'var(--geo-4)'];

export function AttributionView({ trace }: { trace: StudyTrace }) {
  const t = useT();
  const attr = trace.attribution;
  const ok = attr.status === 'ok' && attr.gate?.passed && attr.shap_mean_abs;

  return (
    <div>
      <p className="muted">{t.app.attribution.desc}</p>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', margin: '.5rem 0' }}>
        <span className="readout">
          {t.app.attribution.gate}: {attr.gate ? attr.gate.accuracy.toFixed(2) : '—'}
        </span>
        <span className={`badge ${ok ? 'ok' : 'bad'}`}>{ok ? t.app.attribution.passed : t.app.attribution.withheld}</span>
      </div>
      {ok ? (
        <div className="scroll-x">
          <table>
            <thead>
              <tr>
                <th>GeoType</th>
                <th>{t.app.attribution.descriptor} ({t.common.topControl})</th>
                <th>SHAP</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(attr.shap_mean_abs!).map(([cls, imps]) => {
                const entries = Object.entries(imps).sort((a, b) => b[1] - a[1]);
                const max = entries[0]?.[1] || 1;
                return (
                  <tr key={cls}>
                    <td style={{ color: COLORS[Number(cls) % COLORS.length] }}>GT{cls}</td>
                    <td>
                      {entries.slice(0, 3).map(([f, v]) => (
                        <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '.5rem', marginBottom: 2 }}>
                          <div style={{ width: 90, height: 7, background: 'var(--bg-2)', borderRadius: 4 }}>
                            <div style={{ width: `${(v / max) * 100}%`, height: 7, background: COLORS[Number(cls) % COLORS.length], borderRadius: 4 }} />
                          </div>
                          <span className="tag">{f}</span>
                        </div>
                      ))}
                    </td>
                    <td className="tag">{entries[0]?.[1].toFixed(3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="muted">
          {attr.reason ?? 'The Random Forest could not predict the GeoType labels from the descriptors above the accuracy gate, so importances are withheld rather than reported as noise. This is itself an honest finding (see Experiments).'}
        </p>
      )}
    </div>
  );
}

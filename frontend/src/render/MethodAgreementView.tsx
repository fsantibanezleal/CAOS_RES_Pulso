// Method agreement (P2a): the SOTA clustering alternatives run OFFLINE on this exact ensemble, scored
// against the reference DTW k-medoids catalogue by silhouette (cluster quality in DTW geometry) and
// Adjusted Rand Index (chance-corrected agreement with the reference labels). It reads the baked
// `method_comparison` block, so it reacts to the case selector like every other App view. No live compute.
import type { MethodComparison } from '../lib/contract.types';
import { useT } from '../i18n/useT';

function ariClass(ari: number | undefined): string {
  if (ari === undefined || ari === null) return 'bad';
  if (ari >= 0.75) return 'ok';
  if (ari >= 0.5) return 'warn';
  return 'bad';
}

export function MethodAgreementView({ mc }: { mc: MethodComparison }) {
  const t = useT();
  const ref = mc.reference;
  return (
    <div>
      <p className="muted">{t.app.methods.desc}</p>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', margin: '.5rem 0' }}>
        <span className="readout">
          {t.app.methods.reference}: {ref.name} (K={ref.k})
        </span>
        <span className="readout">
          {t.app.methods.silhouette}: {ref.silhouette !== null ? ref.silhouette.toFixed(3) : 'n/a'}
        </span>
        {mc.subsampled && (
          <span className="tag" title={t.app.methods.subsampledHelp}>
            {t.app.methods.subsampled}: {mc.subsampled}
          </span>
        )}
      </div>
      <div className="scroll-x">
        <table>
          <thead>
            <tr>
              <th>{t.app.methods.method}</th>
              <th>K</th>
              <th>{t.app.methods.silhouette}</th>
              <th>{t.app.methods.ari}</th>
              <th>{t.app.methods.note}</th>
            </tr>
          </thead>
          <tbody>
            {mc.methods.map((m) => (
              <tr key={m.name} style={{ opacity: m.skipped ? 0.5 : 1 }}>
                <td>{m.name}</td>
                <td className="tag">{m.skipped ? '' : m.k}</td>
                <td className="tag">
                  {m.skipped || m.silhouette === null || m.silhouette === undefined
                    ? 'n/a'
                    : m.silhouette.toFixed(3)}
                </td>
                <td>
                  {m.skipped ? (
                    <span className="tag">skipped</span>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
                      <div style={{ width: 90, height: 7, background: 'var(--bg-2)', borderRadius: 4 }}>
                        <div
                          style={{
                            width: `${Math.max(0, Math.min(1, m.ari ?? 0)) * 100}%`,
                            height: 7,
                            background: `var(--${ariClass(m.ari)}, var(--accent))`,
                            borderRadius: 4,
                          }}
                        />
                      </div>
                      <span className={`badge ${ariClass(m.ari)}`}>{(m.ari ?? 0).toFixed(2)}</span>
                    </div>
                  )}
                </td>
                <td className="muted" style={{ fontSize: '.85em' }}>
                  {m.note}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted" style={{ fontSize: '.85em', marginTop: '.5rem' }}>
        {t.app.methods.legend}
      </p>
    </div>
  );
}

// Representations (P2b): four complementary ways to lay out + describe the same committed ensemble,
// read from the baked `representations` block (aligned row-for-row with `members`). A switchable 2D
// scatter (MDS / UMAP / t-SNE / functional-PCA scores) coloured by GeoType with the medoids ringed,
// the dominant functional-PCA mode shapes, and the catch22 feature table describing the clusters. No
// live compute; reacts to the case selector like every App view.
import { useMemo, useState } from 'react';
import type { StudyTraceV2 } from '../lib/contract.types';
import { useT } from '../i18n/useT';

const COLORS = ['var(--geo-0)', 'var(--geo-1)', 'var(--geo-2)', 'var(--geo-3)', 'var(--geo-4)'];
type Layout = 'mds' | 'umap' | 'tsne' | 'fpca';

function Scatter({ pts, labels, medoids }: { pts: Array<[number, number]>; labels: number[]; medoids: number[] }) {
  const W = 520, H = 380, PAD = 24;
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
  const sx = (x: number) => PAD + ((x - xmin) / (xmax - xmin || 1)) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - ymin) / (ymax - ymin || 1)) * (H - 2 * PAD);
  const medoidSet = new Set(medoids);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="representation scatter">
      <rect width={W} height={H} rx={8} fill="var(--bg-3)" />
      {pts.map((p, i) => (
        <circle key={i} cx={sx(p[0])} cy={sy(p[1])} r={medoidSet.has(i) ? 0 : 2.6}
          fill={COLORS[(labels[i] ?? 0) % COLORS.length]} fillOpacity={0.55} />
      ))}
      {pts.map((p, i) => medoidSet.has(i) ? (
        <circle key={`m${i}`} cx={sx(p[0])} cy={sy(p[1])} r={5.5} fill="none"
          stroke={COLORS[(labels[i] ?? 0) % COLORS.length]} strokeWidth={2.2} />
      ) : null)}
    </svg>
  );
}

function FpcaModes({ modes, t_grid, evr }: { modes: number[][]; t_grid: number[]; evr: number[] }) {
  const W = 520, H = 150, PAD = 20;
  const lx = t_grid.map((v) => Math.log10(v));
  const sx = (i: number) => PAD + (i / (lx.length - 1)) * (W - 2 * PAD);
  return (
    <div style={{ display: 'grid', gap: '.5rem' }}>
      {modes.slice(0, 3).map((mode, m) => {
        const ymin = Math.min(...mode), ymax = Math.max(...mode);
        const sy = (y: number) => H - PAD - ((y - ymin) / (ymax - ymin || 1)) * (H - 2 * PAD);
        const path = mode.map((y, i) => `${i === 0 ? 'M' : 'L'}${sx(i).toFixed(1)},${sy(y).toFixed(1)}`).join(' ');
        return (
          <div key={m}>
            <span className="tag">mode {m + 1} · {(100 * (evr[m] ?? 0)).toFixed(1)}% var</span>
            <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`fPCA mode ${m + 1}`}>
              <rect width={W} height={H} rx={6} fill="var(--bg-3)" />
              <line x1={PAD} y1={sy(0)} x2={W - PAD} y2={sy(0)} stroke="var(--fg-2)" strokeOpacity={0.4} strokeDasharray="3 3" />
              <path d={path} fill="none" stroke={COLORS[m % COLORS.length]} strokeWidth={2} />
            </svg>
          </div>
        );
      })}
    </div>
  );
}

export function RepresentationsView({ trace }: { trace: StudyTraceV2 }) {
  const t = useT();
  const reps = trace.representations!;
  const labels = trace.members.geotype;
  const medoids = trace.embedding.medoid_idx;
  const [layout, setLayout] = useState<Layout>('mds');

  const available: Array<[Layout, string, Array<[number, number]> | null]> = [
    ['mds', 'MDS (DTW)', trace.embedding.mds2d],
    ['umap', 'UMAP', reps.umap2d],
    ['tsne', 't-SNE', reps.tsne2d],
    ['fpca', 'fPCA scores', reps.fpca.scores2d],
  ];
  const pts = available.find((a) => a[0] === layout)?.[2] ?? null;

  // the catch22 features that most separate the clusters (largest between-cluster spread of the mean,
  // normalised by the pooled within-cluster std), so the table leads with the discriminating features.
  const topFeatures = useMemo(() => {
    const c = reps.catch22;
    if (c.skipped || !c.names || !c.per_cluster || c.per_cluster.length < 2) return [];
    return c.names.map((name, j) => {
      const means = c.per_cluster!.map((pc) => pc.mean[j]);
      const stds = c.per_cluster!.map((pc) => pc.std[j]);
      const spread = Math.max(...means) - Math.min(...means);
      const pooled = stds.reduce((a, b) => a + b, 0) / stds.length || 1;
      return { name, means, score: Math.abs(spread) / (pooled + 1e-9) };
    }).sort((a, b) => b.score - a.score).slice(0, 6);
  }, [reps.catch22]);

  return (
    <div>
      <p className="muted">{t.app.representations.desc}</p>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', margin: '.5rem 0' }}>
        {available.map(([k, label, data]) => (
          <span key={k} className={`chip ${layout === k ? 'on' : ''}`}
            style={{ opacity: data ? 1 : 0.4, pointerEvents: data ? 'auto' : 'none' }}
            onClick={() => data && setLayout(k)}>
            {label}{!data ? ' (n/a)' : ''}
          </span>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr)', gap: '1rem' }}>
        {pts ? <Scatter pts={pts} labels={labels} medoids={medoids} /> : <p className="muted">{t.app.representations.unavailable}</p>}
      </div>

      <h4 style={{ margin: '1rem 0 .3rem' }}>{t.app.representations.fpcaTitle}</h4>
      <p className="muted" style={{ fontSize: '.85em', marginTop: 0 }}>{t.app.representations.fpcaDesc}</p>
      <FpcaModes modes={reps.fpca.modes} t_grid={trace.t_grid} evr={reps.fpca.explained_variance} />

      <h4 style={{ margin: '1rem 0 .3rem' }}>{t.app.representations.catch22Title}</h4>
      {topFeatures.length ? (
        <>
          <p className="muted" style={{ fontSize: '.85em', marginTop: 0 }}>{t.app.representations.catch22Desc}</p>
          <div className="scroll-x">
            <table>
              <thead>
                <tr>
                  <th>{t.app.representations.feature}</th>
                  {reps.catch22.per_cluster!.map((pc) => (
                    <th key={pc.geotype} style={{ color: COLORS[pc.geotype % COLORS.length] }}>GT{pc.geotype}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {topFeatures.map((f) => (
                  <tr key={f.name}>
                    <td className="tag" style={{ fontSize: '.8em' }}>{f.name}</td>
                    {f.means.map((mv, g) => (
                      <td key={g} className="tag">{mv.toFixed(3)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p className="muted">{t.app.representations.catch22Unavailable}</p>
      )}
    </div>
  );
}

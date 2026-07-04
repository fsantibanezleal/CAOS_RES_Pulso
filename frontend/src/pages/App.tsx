// The App = a real workbench (ADR-0016, never meta-tabs). First-level SOURCE selector
// (Synthetic / Real 4TU / open-DARTS), then a CASE, then genuine domain views. Every view runs on
// the committed artifact of the selected case.
import { useEffect, useMemo, useState } from 'react';
import { loadIndex, loadManifest, loadTrace } from '../api/artifacts';
import type { CaseManifest, Trace } from '../lib/contract.types';
import { isDartsTrace, isDfmTrace, isDfnTrace, isStudyTrace } from '../lib/contract.types';
import { useT } from '../i18n/useT';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { CatalogueView } from '../render/CatalogueView';
import { ClassifyView } from '../render/ClassifyView';
import { AttributionView } from '../render/AttributionView';
import { DartsChart, DfnChart } from '../render/CurveChart';
import { DfmView } from '../render/DfmView';
import { LiveLab } from './LiveLab';

type Source = 'synthetic' | 'real' | 'darts';

function sourceOf(m: { real_or_synthetic: string }): Source {
  // real data = the 4TU fractured-reservoir corpus + the welltestpy field pumping-test campaigns
  if (m.real_or_synthetic === 'real-4tu' || m.real_or_synthetic === 'field-pumping') return 'real';
  // the simulation source displays the open-DARTS anchor, the GeoDFN networks + the DFM GeoTypes
  if (
    m.real_or_synthetic === 'simulated-darts' ||
    m.real_or_synthetic === 'synthetic-geodfn' ||
    m.real_or_synthetic === 'simulated-dfm'
  )
    return 'darts';
  return 'synthetic'; // analytic studies -> covered by the live lab
}

export function AppPage() {
  const t = useT();
  const [manifests, setManifests] = useState<Record<string, CaseManifest>>({});
  const [source, setSource] = useState<Source>('synthetic');
  const [sel, setSel] = useState('');
  const [trace, setTrace] = useState<Trace | null>(null);
  const [tab, setTab] = useState('');
  const [err, setErr] = useState('');

  useEffect(() => {
    loadIndex()
      .then(async (ix) => {
        const ms = await Promise.all(ix.cases.map((c) => loadManifest(c.case_id)));
        setManifests(Object.fromEntries(ms.map((m) => [m.case_id, m])));
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const casesForSource = useMemo(
    () => Object.values(manifests).filter((m) => sourceOf(m) === source).map((m) => m.case_id).sort(),
    [manifests, source],
  );

  useEffect(() => {
    if (casesForSource.length && !casesForSource.includes(sel)) setSel(casesForSource[0]);
  }, [casesForSource, sel]);

  useEffect(() => {
    if (!sel || !manifests[sel]) return;
    loadTrace(manifests[sel].artifact.path).then(setTrace).catch((e) => setErr(String(e)));
  }, [sel, manifests]);

  const tabs = useMemo(() => {
    if (!trace) return [];
    // a dfm trace is-a study trace, so check it FIRST to add the simulated-physics tab
    if (isDfmTrace(trace)) return ['catalogue', 'classify', 'attribution', 'simulation', 'context'];
    if (isStudyTrace(trace)) return ['catalogue', 'classify', 'attribution', 'context'];
    if (isDartsTrace(trace)) return ['anchor', 'context'];
    return ['network', 'context'];
  }, [trace]);
  useEffect(() => {
    if (tabs.length && !tabs.includes(tab)) setTab(tabs[0]);
  }, [tabs, tab]);

  const manifest = manifests[sel];
  const sources: Array<[Source, string, string]> = [
    ['synthetic', t.app.sourceSynthetic, t.app.sourceSyntheticHelp],
    ['real', t.app.sourceReal, t.app.sourceRealHelp],
    ['darts', t.app.sourceDarts, t.app.sourceDartsHelp],
  ];

  return (
    <div className="grid" style={{ gap: '1.25rem' }}>
      <div>
        <h1 style={{ marginBottom: '.25rem' }}>{t.app.title}</h1>
        <p className="muted" style={{ marginTop: 0 }}>{t.app.intro}</p>
      </div>
      {err && <div className="panel" style={{ borderColor: 'var(--bad)' }}>{t.common.error}: {err}</div>}

      <div className="panel">
        <div className="tag" style={{ marginBottom: '.5rem' }}>{t.app.source}</div>
        <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
          {sources.map(([s, label]) => (
            <span key={s} className={`chip ${source === s ? 'on' : ''}`} onClick={() => setSource(s)}>
              {label}
            </span>
          ))}
        </div>
        <p className="muted" style={{ fontSize: '.85rem', margin: '.6rem 0 0' }}>
          {sources.find((x) => x[0] === source)?.[2]}
        </p>
      </div>

      {source === 'synthetic' ? (
        <LiveLab />
      ) : (
      <div className="panel">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <label className="tag">
            {t.app.case}{' '}
            <select value={sel} onChange={(e) => setSel(e.target.value)}>
              {casesForSource.map((id) => (
                <option key={id} value={id}>{id}</option>
              ))}
            </select>
          </label>
          {manifest && (
            <span className="readout">
              {t.common.silhouette in (manifest.metrics as object) ? '' : ''}
              lane {manifest.lane} · engine {manifest.engine.package} {manifest.engine.version}
            </span>
          )}
        </div>

        <div className="tabs" style={{ marginTop: '1rem' }}>
          {tabs.map((k) => (
            <span key={k} className={`tab ${tab === k ? 'on' : ''}`} onClick={() => setTab(k)}>
              {t.app.tabs[k as keyof typeof t.app.tabs]}
            </span>
          ))}
        </div>

        <ErrorBoundary label={tab} key={sel + tab}>
          {trace && manifest && (
            <>
              {tab === 'catalogue' && isStudyTrace(trace) && <CatalogueView trace={trace} />}
              {tab === 'classify' && isStudyTrace(trace) && <ClassifyView trace={trace} />}
              {tab === 'attribution' && isStudyTrace(trace) && <AttributionView trace={trace} />}
              {tab === 'anchor' && isDartsTrace(trace) && <DartsChart trace={trace} />}
              {tab === 'simulation' && isDfmTrace(trace) && <DfmView trace={trace} />}
              {tab === 'network' && isDfnTrace(trace) && <DfnChart trace={trace} />}
              {tab === 'context' && <ContextView manifest={manifest} />}
            </>
          )}
        </ErrorBoundary>
      </div>
      )}
    </div>
  );
}

function ContextView({ manifest }: { manifest: CaseManifest }) {
  return (
    <div>
      <p style={{ fontSize: '1rem' }}>{manifest.expected_band}</p>
      <div className="scroll-x">
        <table>
          <thead>
            <tr><th>parameter</th><th>value</th></tr>
          </thead>
          <tbody>
            {Object.entries(manifest.params).map(([k, v]) => (
              <tr key={k}><td>{k}</td><td className="tag">{JSON.stringify(v)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

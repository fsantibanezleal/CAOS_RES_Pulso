// The App = a real workbench (ADR-0016, never meta-tabs). A first-level MODE selector
// (Explore a case / Live lab / Guided scenarios), then genuine domain views grouped into families
// (Ensemble / Assignment / Methods / Physics / Context) via the shared-shell Tabs + SubTabs. Every
// view runs on the committed artifact of the selected case. Case selection uses the shell CaseSelector
// (grouped by category, URL-synced); the tab chrome uses the shell Tabs/SubTabs (keyboard + ARIA).
import { useEffect, useMemo, useState } from 'react';
import { CaseSelector, SubTabs, Tabs, readCaseParam, useShellLang, type CaseDef, type SubTabDef, type TabDef } from '@fasl-work/caos-app-shell';
import { loadIndex, loadManifest, loadTrace } from '../api/artifacts';
import type { CaseManifest, Trace } from '../lib/contract.types';
import { isDartsTrace, isDfmTrace, isDfnTrace, isStudyTrace, isStudyTraceV2 } from '../lib/contract.types';
import { useT } from '../i18n/useT';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { CatalogueView } from '../render/CatalogueView';
import { ClassifyView } from '../render/ClassifyView';
import { AttributionView } from '../render/AttributionView';
import { DartsChart, DfnChart } from '../render/CurveChart';
import { DfmView } from '../render/DfmView';
import { MethodAgreementView } from '../render/MethodAgreementView';
import { RepresentationsView } from '../render/RepresentationsView';
import { EnsembleExplorerView } from '../render/EnsembleExplorerView';
import { DtwHeatmapView } from '../render/DtwHeatmapView';
import { AttributionPlusView } from '../render/AttributionPlusView';
import { LiveLab } from './LiveLab';

type Mode = 'explore' | 'live';

// map the manifest's real_or_synthetic lane to a human category (the CaseSelector groups by this)
const CATEGORY_KEY: Record<string, keyof ReturnType<typeof useT>['app']['cat']> = {
  'synthetic-analytic': 'analytic',
  'real-4tu': 'real',
  'field-pumping': 'field',
  'simulated-dfm': 'dfm',
  'synthetic-geodfn': 'dfn',
  'simulated-darts': 'darts',
  'benchmark-4tu': 'bench',
};

function wrap(label: string, node: React.ReactNode): React.ReactNode {
  return <ErrorBoundary label={label}>{node}</ErrorBoundary>;
}

// a readable case name from the slug (the CaseSelector shows the mono id + this friendly name)
function humanize(id: string): string {
  return id.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b([a-z])/g, (m) => m.toUpperCase());
}

// The workbench families for a given trace: Tabs (families) -> SubTabs (tools). Only families with a
// real tool for THIS trace are shown, so a DARTS/DFN case is not padded with empty study tabs.
function buildFamilies(trace: Trace, manifest: CaseManifest, t: ReturnType<typeof useT>): TabDef[] {
  const fam: TabDef[] = [];
  const tool = t.app.tool;

  if (isStudyTrace(trace)) {
    // Ensemble = the shape space of the whole ensemble
    const ensemble: SubTabDef[] = [
      { id: 'catalogue', label: tool.catalogue, content: wrap('catalogue', <CatalogueView trace={trace} />) },
    ];
    if (isStudyTraceV2(trace)) {
      ensemble.push({ id: 'explorer', label: tool.explorer, content: wrap('explorer', <EnsembleExplorerView trace={trace} />) });
      ensemble.push({ id: 'dtwmap', label: tool.dtwmap, content: wrap('dtwmap', <DtwHeatmapView trace={trace} />) });
    }
    if (isStudyTraceV2(trace) && trace.representations) {
      ensemble.push({ id: 'shape', label: tool.shape, content: wrap('shape', <RepresentationsView trace={trace} />) });
    }
    fam.push({ id: 'ensemble', label: t.app.fam.ensemble, content: <SubTabs tabs={ensemble} ariaLabel={t.app.fam.ensemble} /> });

    // Assignment = classify a curve + explain the labels (+ the P2e depth when baked)
    const assignment: SubTabDef[] = [
      { id: 'classify', label: tool.classify, content: wrap('classify', <ClassifyView trace={trace} />) },
      { id: 'attribution', label: tool.attribution, content: wrap('attribution', <AttributionView trace={trace} />) },
    ];
    const ap = isStudyTraceV2(trace) ? trace.attribution_plus : undefined;
    if (ap) {
      assignment.push({ id: 'attrplus', label: tool.attrplus, content: wrap('attrplus', <AttributionPlusView ap={ap} />) });
    }
    fam.push({ id: 'assignment', label: t.app.fam.assignment, content: <SubTabs ariaLabel={t.app.fam.assignment} tabs={assignment} /> });

    // Methods = the SOTA benchmarks computed on THIS ensemble (rich-method cases only)
    const mc = isStudyTraceV2(trace) ? trace.method_comparison : undefined;
    if (mc) {
      fam.push({
        id: 'methods', label: t.app.fam.methods,
        content: <SubTabs ariaLabel={t.app.fam.methods} tabs={[
          { id: 'agreement', label: tool.agreement, content: wrap('agreement', <MethodAgreementView mc={mc} />) },
        ]} />,
      });
    }

    // Physics = the simulated-transient block (DFM studies)
    if (isDfmTrace(trace)) {
      fam.push({
        id: 'physics', label: t.app.fam.physics,
        content: <SubTabs ariaLabel={t.app.fam.physics} tabs={[
          { id: 'sim', label: tool.sim, content: wrap('sim', <DfmView trace={trace} />) },
        ]} />,
      });
    }
  } else if (isDartsTrace(trace)) {
    fam.push({
      id: 'physics', label: t.app.fam.physics,
      content: <SubTabs ariaLabel={t.app.fam.physics} tabs={[
        { id: 'darts', label: tool.darts, content: wrap('darts', <DartsChart trace={trace} />) },
      ]} />,
    });
  } else if (isDfnTrace(trace)) {
    fam.push({
      id: 'physics', label: t.app.fam.physics,
      content: <SubTabs ariaLabel={t.app.fam.physics} tabs={[
        { id: 'network', label: tool.network, content: wrap('network', <DfnChart trace={trace} />) },
      ]} />,
    });
  }

  fam.push({ id: 'context', label: t.app.fam.context, content: wrap('context', <ContextView manifest={manifest} />) });
  return fam;
}

export function AppPage() {
  const t = useT();
  const lang = useShellLang();
  const [manifests, setManifests] = useState<Record<string, CaseManifest>>({});
  const [mode, setMode] = useState<Mode>('explore');
  // seed the selected case from the ?case= deep link so a shared URL opens that case (the CaseSelector
  // keeps the URL in sync thereafter); fall back to the first case once the index loads.
  const [sel, setSel] = useState(() => readCaseParam(window.location.search) ?? '');
  const [trace, setTrace] = useState<Trace | null>(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    loadIndex()
      .then(async (ix) => {
        const ms = await Promise.all(ix.cases.map((c) => loadManifest(c.case_id)));
        setManifests(Object.fromEntries(ms.map((m) => [m.case_id, m])));
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const cases: CaseDef[] = useMemo(
    () => Object.values(manifests)
      .map((m) => ({
        id: m.case_id, name: humanize(m.case_id),
        category: t.app.cat[CATEGORY_KEY[m.real_or_synthetic] ?? 'analytic'],
        expectedBand: m.expected_band,
      }))
      .sort((a, b) => (a.category + a.id).localeCompare(b.category + b.id)),
    [manifests, t],
  );

  useEffect(() => {
    if (cases.length && !cases.some((c) => c.id === sel)) setSel(cases[0].id);
  }, [cases, sel]);

  useEffect(() => {
    if (mode !== 'explore' || !sel || !manifests[sel]) return;
    loadTrace(manifests[sel].artifact.path).then(setTrace).catch((e) => setErr(String(e)));
  }, [sel, manifests, mode]);

  const manifest = manifests[sel];
  const families = useMemo(
    () => (trace && manifest ? buildFamilies(trace, manifest, t) : []),
    [trace, manifest, t],
  );

  const modes: Array<[Mode, string]> = [
    ['explore', t.app.mode.explore],
    ['live', t.app.mode.live],
  ];

  return (
    <div className="grid" style={{ gap: '1.25rem' }}>
      <div>
        <h1 style={{ marginBottom: '.25rem' }}>{t.app.title}</h1>
        <p className="muted" style={{ marginTop: 0 }}>{t.app.intro}</p>
      </div>
      {err && <div className="panel" style={{ borderColor: 'var(--bad)' }}>{t.common.error}: {err}</div>}

      {/* first-level MODE selector */}
      <div className="panel">
        <div className="tag" style={{ marginBottom: '.5rem' }}>{t.app.modeLabel}</div>
        <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
          {modes.map(([m, label]) => (
            <span key={m} className={`chip ${mode === m ? 'on' : ''}`} onClick={() => setMode(m)}>{label}</span>
          ))}
        </div>
        <p className="muted" style={{ fontSize: '.85rem', margin: '.6rem 0 0' }}>
          {mode === 'explore' ? t.app.mode.exploreHelp : t.app.mode.liveHelp}
        </p>
      </div>

      {mode === 'live' ? (
        <LiveLab />
      ) : (
        <>
          <div className="panel">
            <CaseSelector cases={cases} selectedId={sel} onSelect={setSel} lang={lang} deepLink="case" />
            {manifest && (
              <p className="readout" style={{ marginTop: '.7rem' }}>
                lane {manifest.lane} · engine {manifest.engine.package} {manifest.engine.version}
              </p>
            )}
          </div>

          <div className="panel">
            {families.length > 0
              ? <Tabs key={sel} tabs={families} ariaLabel={t.app.workbench} />
              : <p className="muted">{t.common.loading}</p>}
          </div>
        </>
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

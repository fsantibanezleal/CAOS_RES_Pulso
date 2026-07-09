// The App = a real workbench (ADR-0016, never meta-tabs). A first-level MODE selector
// (Explore a case / Live lab / Guided scenarios), then genuine domain views grouped into families
// (Ensemble / Assignment / Methods / Physics / Context) via the shared-shell Tabs + SubTabs. Every
// view runs on the committed artifact of the selected case. Case selection uses the shell CaseSelector
// (grouped by category, URL-synced); the tab chrome uses the shell Tabs/SubTabs (keyboard + ARIA).
import { useEffect, useMemo, useState } from 'react';
import { SubTabs, Tabs, readCaseParam, type SubTabDef, type TabDef } from '@fasl-work/caos-app-shell';
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
import { useLiveLab, LiveControls, LiveTools } from './LiveLab';

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

// a curated short name per case that ADDS meaning next to the mono id (never a de-slug of the id).
// Falls back to a light humanization only for an unmapped case.
const CASE_NAME: Record<string, string> = {
  CTRL_single_regime: 'Single-regime control', MIX04_homog_vs_dp: 'Homogeneous vs dual-porosity',
  WR01_baseline: 'Warren-Root baseline', WR02_depth_families: 'Depth-scaled families',
  WR03_timing_families: 'Transition-timing families', WR05_noisy: 'Noisy Warren-Root',
  FIELD_combined: 'Combined field campaigns', FIELD_horkheim: 'Horkheimer Insel aquifer',
  FIELD_lauswiesen: 'Lauswiesen aquifer', DFN06_sparse: 'Sparse fracture network',
  DFN07_dense: 'Dense fracture network', BENCH_A: 'Full corpus: dataset A',
  BENCH_B: 'Full corpus: dataset B', BENCH_C: 'Full corpus: dataset C',
  DARTS_homog_anchor: 'Homogeneous drawdown anchor', REAL_A_lowperm: '4TU dataset A (low perm)',
  REAL_B_midperm: '4TU dataset B (mid perm)', REAL_C_highperm: '4TU dataset C (high perm)',
  DFM01_geotypes: 'DFM GeoType study', DFM02_dense: 'DFM dense networks',
  DFM03_sparse: 'DFM sparse networks',
};
function caseName(id: string): string {
  return CASE_NAME[id] ?? id.replace(/_/g, ' ');
}

function wrap(label: string, node: React.ReactNode): React.ReactNode {
  return <ErrorBoundary label={label}>{node}</ErrorBoundary>;
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

  // cases grouped by category for the compact sidebar dropdown (a native <optgroup> select navigates
  // all 21 cases in one control instead of a 21-chip wall). Categories ordered real -> field -> DFM ->
  // analytic -> the rest, so measured data is first.
  const CAT_ORDER = ['real', 'field', 'dfm', 'darts', 'dfn', 'analytic', 'bench'];
  const groups = useMemo(() => {
    const by: Record<string, { id: string; name: string }[]> = {};
    for (const m of Object.values(manifests)) {
      const key = CATEGORY_KEY[m.real_or_synthetic] ?? 'analytic';
      (by[key] ??= []).push({ id: m.case_id, name: caseName(m.case_id) });
    }
    for (const k of Object.keys(by)) by[k].sort((a, b) => a.id.localeCompare(b.id));
    return CAT_ORDER.filter((k) => by[k]).map((k) => ({ key: k, label: t.app.cat[k as keyof typeof t.app.cat], cases: by[k] }));
  }, [manifests, t]);
  const allIds = useMemo(() => groups.flatMap((g) => g.cases.map((c) => c.id)), [groups]);

  useEffect(() => {
    if (allIds.length && !allIds.includes(sel)) setSel(allIds[0]);
  }, [allIds, sel]);

  // keep the ?case= deep link in sync so a shared URL reopens the case
  useEffect(() => {
    if (sel) {
      const u = new URL(window.location.href);
      u.searchParams.set('case', sel);
      window.history.replaceState(null, '', u.toString());
    }
  }, [sel]);

  useEffect(() => {
    if (mode !== 'explore' || !sel || !manifests[sel]) return;
    // clear the previous case's trace FIRST so the workbench families are rebuilt from the NEW trace,
    // not the stale one. Without this, switching to a case with a different family set (e.g. DFM study ->
    // DARTS: Physics/Context only) leaves the family Tabs pointed at a family that no longer exists -> blank.
    setTrace(null);
    let alive = true;
    loadTrace(manifests[sel].artifact.path).then((tr) => alive && setTrace(tr)).catch((e) => setErr(String(e)));
    return () => { alive = false; };
  }, [sel, manifests, mode]);

  const manifest = manifests[sel];
  const families = useMemo(
    () => (trace && manifest ? buildFamilies(trace, manifest, t) : []),
    [trace, manifest, t],
  );
  // the live-lab state lives here so its CONTROLS render in the sidebar and its TOOLS in the main area
  // (mirrors the RotorVitals rv-side pattern); the ONNX models only load once Live mode is opened.
  const lab = useLiveLab(mode === 'live');

  const modeChips = (
    <div className="mode-switch" role="tablist" aria-label={t.app.modeLabel}>
      {(['explore', 'live'] as Mode[]).map((m) => (
        <button key={m} role="tab" aria-selected={mode === m} className={`mode-btn ${mode === m ? 'on' : ''}`}
          onClick={() => setMode(m)}>{m === 'explore' ? t.app.mode.explore : t.app.mode.live}</button>
      ))}
    </div>
  );

  // ADR-0017 section 3 (mirroring the RotorVitals Tool): the App IS the workbench. `page-body` carries the
  // two-zone grid directly (no page-head eating vertical space): a control aside holding EVERY parameter
  // (mode + case picker + read-out in Explore, the live sliders in Live) and a workbench main that holds a
  // single Tabs of the domain tools. Switching case/mode remounts the Tabs so the first tab auto-selects.
  return (
    <div className="page-body pulso-layout">
      <aside className="pulso-side">
        {modeChips}
        {mode === 'explore' ? (
          <>
            <label className="side-field">
              <span className="side-label">{t.app.case}</span>
              <select value={sel} onChange={(e) => setSel(e.target.value)} aria-label={t.app.case}>
                {groups.map((g) => (
                  <optgroup key={g.key} label={g.label}>
                    {g.cases.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </optgroup>
                ))}
              </select>
            </label>
            {manifest && <CaseReadout manifest={manifest} t={t} />}
          </>
        ) : (
          <LiveControls lab={lab} />
        )}
      </aside>

      <div className="pulso-main">
        {err && <div className="panel" style={{ borderColor: 'var(--bad)', marginBottom: '1rem' }}>{t.common.error}: {err}</div>}
        {mode === 'live'
          ? <LiveTools lab={lab} />
          : families.length > 0
            ? <Tabs key={sel} tabs={families} ariaLabel={t.app.workbench} />
            : <p className="muted">{t.common.loading}</p>}
      </div>
    </div>
  );
}

// A compact live read-out of the selected case (ADR-0017 section 3.3): category, lane, and the headline
// metrics (K, silhouette, conformal coverage) pulled from the committed manifest.
function CaseReadout({ manifest, t }: { manifest: CaseManifest; t: ReturnType<typeof useT> }) {
  const metrics = manifest.metrics as Record<string, unknown>;
  const conf = (metrics.conformal ?? {}) as Record<string, number>;
  const num = (v: unknown) => (typeof v === 'number' ? v : undefined);
  const rows: Array<[string, string | undefined]> = [
    [t.app.ro.category, t.app.cat[CATEGORY_KEY[manifest.real_or_synthetic] ?? 'analytic']],
    [t.app.ro.lane, manifest.lane === 'live' ? t.app.laneLive : t.app.lanePrecompute],
    ['K', num(metrics.k)?.toString()],
    [t.common.silhouette, num(metrics.silhouette_train)?.toFixed(3)],
    [t.common.coverage, num(conf.empirical_coverage_test)?.toFixed(2)],
  ];
  return (
    <div className="side-readout">
      {rows.filter(([, v]) => v !== undefined).map(([k, v]) => (
        <div key={k} className="side-readout-row"><span>{k}</span><b>{v}</b></div>
      ))}
      {manifest.expected_band && <p className="muted" style={{ fontSize: '.8rem', marginTop: '.5rem' }}>{manifest.expected_band}</p>}
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

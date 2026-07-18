// The LIVE LAB — the real workbench: drag ω/λ/skin/noise, and every tool in the ladder recomputes
// LIVE on the tuned curve. Classical (Bourdet diagnostics) · SOTA (DTW-to-medoid) · novel (conformal)
// run in the TS engine; the LEARNED tools (1D-CNN, autoencoder, contrastive) run live via
// onnxruntime-web on the committed ONNX. No server, no replay — genuine in-browser compute.
import { useEffect, useMemo, useState } from 'react';
import { SubTabs, Tabs, type SubTabDef, type TabDef } from '@fasl-work/caos-app-shell';
import { useT } from '../i18n/useT';
import { generateResponse, preprocessForModels, warrenRootPd, homogeneousPd, bourdet } from '../engine/pta';
import {
  detectRegimes, fitTheis, fitWarrenRoot, secondLogDerivative, REGIME_COLORS, type RegimeKind,
} from '../engine/diagnostics';
import { conformalAssign, distancesToMedoids } from '../engine/dtw';
import { autoencode, classifyIncep, classifyPatchTST, embedAndRetrieve, getReference, loadDeep, type DeepReference } from '../engine/onnx';
import { ErrorBoundary } from '../components/ErrorBoundary';

const COLORS = ['#4f9cf9', '#f97b4f', '#41c98d', '#c94fd0', '#d8c14a'];

// The live-lab STATE + derived method ladder as a hook, so the App can render the CONTROLS in its left
// sidebar (ADR-0017 s3 / the RotorVitals rv-side pattern) and the TOOLS in the main area from one source.
export function useLiveLab(active = true) {
  const t = useT();
  const [omega, setOmega] = useState(0.05);
  const [logLam, setLogLam] = useState(-6);
  const [skin, setSkin] = useState(0);
  const [noise, setNoise] = useState(0.01);
  const [homog, setHomog] = useState(false);
  const [ref, setRef] = useState<DeepReference | null>(null);

  // only pull the ONNX models + reference once Live mode is actually opened, so the Explore landing
  // does not instantiate four inference sessions it never uses (no eager compute on the entry page).
  useEffect(() => {
    if (!active) return;
    loadDeep().then(() => setRef(getReference())).catch(() => setRef(null));
  }, [active]);

  const lam = Math.pow(10, logLam);
  const resp = useMemo(
    () => generateResponse(homog ? 1.0 : omega, lam, skin, noise, 1),
    [omega, lam, skin, noise, homog],
  );
  const model = useMemo(
    () => (ref ? preprocessForModels(resp.tD, resp.p, ref.n_points) : null),
    [resp, ref],
  );

  // the method ladder grouped by tier: Tabs (Classical / Shape / Learned) -> SubTabs (tools).
  const truth = { omega: homog ? 1 : omega, lam, skin, homog };
  const ready = !!(ref && model);
  const loading = <p className="muted">{t.live.loadingModels}</p>;
  const sub = (id: string, label: string, node: React.ReactNode): SubTabDef => ({
    id, label, content: <ErrorBoundary label={id}>{node}</ErrorBoundary>,
  });
  const ladder: TabDef[] = [
    {
      id: 'classical', label: t.live.tierClassical,
      content: <SubTabs ariaLabel={t.live.tierClassical} tabs={[
        sub('diag', t.live.m.diagnostics, <Diagnostics resp={resp} truth={truth} />),
      ]} />,
    },
    {
      id: 'shape', label: t.live.tierShape,
      content: <SubTabs ariaLabel={t.live.tierShape} tabs={[
        sub('dtw', t.live.m.dtw, ready ? <DtwView x={model!.x} ref={ref!} /> : loading),
        sub('conformal', t.live.m.conformal, ready ? <ConformalView x={model!.x} ref={ref!} /> : loading),
      ]} />,
    },
    {
      id: 'learned', label: t.live.tierLearned,
      content: <SubTabs ariaLabel={t.live.tierLearned} tabs={[
        sub('incep', t.live.m.inceptiontime, ready ? <ClassifierView x={model!.x} classify={classifyIncep} desc={t.live.incepDesc} acc={ref!.metrics.incep_test_accuracy} /> : loading),
        sub('patchtst', t.live.m.patchtst, ready ? <ClassifierView x={model!.x} classify={classifyPatchTST} desc={t.live.patchtstDesc} acc={ref!.metrics.patchtst_test_accuracy} /> : loading),
        sub('ae', t.live.m.autoencoder, ready ? <AeView x={model!.x} ref={ref!} /> : loading),
        sub('contrastive', t.live.m.contrastive, ready ? <ContrastiveView x={model!.x} ref={ref!} /> : loading),
      ]} />,
    },
  ];

  return { omega, setOmega, logLam, setLogLam, lam, skin, setSkin, noise, setNoise, homog, setHomog, ladder };
}

export type LiveLabHook = ReturnType<typeof useLiveLab>;

// The live controls, for the LEFT SIDEBAR (mirrors RotorVitals rv-side: the parametrization lives in the aside).
export function LiveControls({ lab }: { lab: LiveLabHook }) {
  const t = useT();
  const { omega, setOmega, logLam, setLogLam, lam, skin, setSkin, noise, setNoise, homog, setHomog } = lab;
  return (
    <div className="side-controls">
      <div className="side-label">{t.live.controls}</div>
      <Slider label={`ω = ${homog ? '1 (homog.)' : omega.toFixed(3)}`} min={0.005} max={0.5} step={0.005} value={omega} onChange={setOmega} disabled={homog} />
      <Slider label={`λ = ${lam.toExponential(1)}`} min={-9} max={-4} step={0.1} value={logLam} onChange={setLogLam} disabled={homog} />
      <Slider label={`skin = ${skin.toFixed(1)}`} min={0} max={5} step={0.5} value={skin} onChange={setSkin} />
      <Slider label={`noise = ${(noise * 100).toFixed(0)}%`} min={0} max={0.08} step={0.005} value={noise} onChange={setNoise} />
      <label className="side-check">
        <input type="checkbox" checked={homog} onChange={(e) => setHomog(e.target.checked)} />
        {t.live.homogeneous}
      </label>
    </div>
  );
}

// The method ladder (tier tabs -> tools), for the MAIN area.
export function LiveTools({ lab }: { lab: LiveLabHook }) {
  const t = useT();
  return (
    <div>
      <p className="muted" style={{ margin: '0 0 1rem' }}>{t.live.intro}</p>
      <Tabs tabs={lab.ladder} ariaLabel={t.live.ladder} />
    </div>
  );
}

function Slider({ label, min, max, step, value, onChange, disabled }: {
  label: string; min: number; max: number; step: number; value: number; onChange: (v: number) => void; disabled?: boolean;
}) {
  return (
    <label className="side-ctl" style={{ opacity: disabled ? 0.4 : 1 }}>
      {label}
      <input type="range" min={min} max={max} step={step} value={value} disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))} />
    </label>
  );
}

// ---------- classical (P2c): log-log Δp + p′ + p″, auto-detected flow regimes, live Warren-Root /
//            Theis fits that RECOVER the parameters from the curve ----------
const REGIME_LABEL: Record<RegimeKind, string> = {
  'wellbore-storage': 'wellbore storage', radial: 'radial (0.5)', linear: 'linear (½)',
  bilinear: 'bilinear (¼)', 'dual-porosity-transition': 'dual-porosity transition', boundary: 'boundary',
};

function Diagnostics({ resp, truth }: {
  resp: { tD: number[]; p: number[]; dp: number[] };
  truth: { omega: number; lam: number; skin: number; homog: boolean };
}) {
  const t = useT();
  const W = 860, H = 360, PAD = 46;
  // A denoised derivative for the interpretive layer (regimes + p″): the DISPLAYED p′ keeps the real
  // measurement noise, but regime detection and the curvature are read off a smoother derivative so
  // 1% pressure noise does not shatter them (standard practice: interpret the smoothed derivative).
  const dpSmooth = useMemo(() => bourdet(resp.tD, resp.p, 0.5), [resp]);
  const p2 = useMemo(() => secondLogDerivative(resp.tD, dpSmooth, 0.5), [resp, dpSmooth]);
  const regimes = useMemo(() => detectRegimes(resp.tD, dpSmooth), [resp, dpSmooth]);
  const wr = useMemo(() => fitWarrenRoot(resp.tD, resp.p), [resp]);
  const theis = useMemo(() => fitTheis(resp.tD, resp.p), [resp]);
  const wrFitCurve = useMemo(() => warrenRootPd(resp.tD, wr.omega, wr.lam), [resp, wr]);
  const theisFitCurve = useMemo(() => homogeneousPd(resp.tD, theis.skin), [resp, theis]);
  // Warren-Root fits the dual-porosity valley; Theis is the homogeneous baseline. The lower RMSE wins.
  const wrWins = wr.rmse <= theis.rmse;

  const lx = resp.tD.map((v) => Math.log10(v));
  // display the standard SMOOTHED Bourdet derivative (the interpretation curve; regimes + p″ are read
  // off it too). The raw noisy derivative plunges through the valley on a log axis; smoothing is the
  // standard practice, and the noise slider still shows as residual wiggle. Clamp the axis floor so a
  // stray low point cannot stretch the whole plot.
  const all = [...resp.p, ...dpSmooth].filter((v) => v > 0).map((v) => Math.log10(v));
  const yMin = Math.max(Math.min(...all), -2), yMax = Math.max(...all);
  const sx = (x: number) => PAD + ((x - lx[0]) / (lx[lx.length - 1] - lx[0])) * (W - 2 * PAD);
  // clamp the plotted value to the axis window so a near-zero derivative point stops at the floor
  // instead of shooting a spike past the frame (the valley genuinely dips; we bound it, not hide it).
  const sy = (y: number) => {
    const ly = Math.min(yMax, Math.max(yMin, Math.log10(Math.max(y, 1e-6))));
    return H - PAD - ((ly - yMin) / (yMax - yMin || 1)) * (H - 2 * PAD);
  };
  const path = (ys: number[]) => ys.map((y, i) => `${i === 0 ? 'M' : 'L'}${sx(lx[i]).toFixed(1)},${sy(y).toFixed(1)}`).join(' ');

  return (
    <div>
      <p className="muted">{t.live.diagDesc}</p>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ background: 'var(--bg-3)', borderRadius: 8 }} role="img" aria-label="diagnostic plot with detected flow regimes">
        {/* auto-detected flow-regime bands (behind the curves) */}
        {regimes.map((r, i) => (
          <rect key={i} x={sx(lx[r.iStart])} y={PAD} width={Math.max(0, sx(lx[r.iEnd]) - sx(lx[r.iStart]))}
            height={H - 2 * PAD} fill={REGIME_COLORS[r.kind]} fillOpacity={0.14} />
        ))}
        <line x1={PAD} y1={sy(0.5)} x2={W - PAD} y2={sy(0.5)} stroke="var(--fg-2)" strokeDasharray="4 4" />
        <text x={W - PAD - 130} y={sy(0.5) - 6} fill="var(--fg-2)" fontSize={11}>radial derivative plateau = 0.5</text>
        {/* the winning analytic fit, overlaid (dashed) to show the recovered response */}
        <path d={path(wrWins ? wrFitCurve : theisFitCurve)} fill="none" stroke="var(--fg-2)" strokeWidth={1.5} strokeDasharray="5 4" />
        <path d={path(resp.p)} fill="none" stroke="#4f9cf9" strokeWidth={2.5} />
        <path d={path(dpSmooth)} fill="none" stroke="#f97b4f" strokeWidth={2.2} />
        <text x={PAD} y={H - 14} fill="var(--fg-2)" fontSize={12}>log10 tD</text>
      </svg>

      <div style={{ display: 'flex', gap: '.5rem', marginTop: '.5rem', flexWrap: 'wrap' }}>
        <span className="readout" style={{ color: '#4f9cf9' }}>Δp (p_wD)</span>
        <span className="readout" style={{ color: '#f97b4f' }}>p′ (Bourdet, smoothed)</span>
        <span className="readout" style={{ color: 'var(--fg-2)' }}>{t.live.diag.bestFit}: {wrWins ? 'Warren-Root' : 'Theis'} (dashed)</span>
      </div>

      {/* p″ curvature in its own compact LINEAR panel (centred at 0), read off the smoothed derivative */}
      <div style={{ marginTop: '.7rem' }}>
        <span className="tag">p″ {t.live.diag.curvature}</span>
        <CurvaturePanel lx={lx} p2={p2} sx={sx} regimes={regimes} />
      </div>

      {/* detected regimes */}
      <div style={{ display: 'flex', gap: '.4rem', marginTop: '.6rem', flexWrap: 'wrap' }}>
        <span className="tag">{t.live.diag.detected}:</span>
        {regimes.length === 0 && <span className="muted">{t.live.diag.none}</span>}
        {regimes.map((r, i) => (
          <span key={i} className="badge" style={{ background: `color-mix(in srgb, ${REGIME_COLORS[r.kind]} 22%, transparent)`, color: REGIME_COLORS[r.kind] }}>
            {REGIME_LABEL[r.kind]}
          </span>
        ))}
      </div>

      {/* live parameter recovery: fitted vs true */}
      <h4 style={{ margin: '1rem 0 .3rem' }}>{t.live.diag.recovery}</h4>
      <p className="muted" style={{ fontSize: '.85em', marginTop: 0 }}>{t.live.diag.recoveryDesc}</p>
      <div className="scroll-x">
        <table>
          <thead>
            <tr><th>{t.live.diag.model}</th><th>{t.live.diag.recovered}</th><th>{t.live.diag.truth}</th><th>RMSE</th></tr>
          </thead>
          <tbody>
            <tr style={{ fontWeight: wrWins ? 700 : 400 }}>
              <td>Warren-Root (ω, λ)</td>
              <td className="tag">ω={wr.omega.toFixed(3)}, λ={wr.lam.toExponential(1)}</td>
              <td className="tag">{truth.homog ? 'n/a (homog.)' : `ω=${truth.omega.toFixed(3)}, λ=${truth.lam.toExponential(1)}`}</td>
              <td className="tag">{wr.rmse.toFixed(4)}</td>
            </tr>
            <tr style={{ fontWeight: !wrWins ? 700 : 400 }}>
              <td>Theis (skin)</td>
              <td className="tag">S={theis.skin.toFixed(2)}</td>
              <td className="tag">S={truth.skin.toFixed(2)}</td>
              <td className="tag">{theis.rmse.toFixed(4)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

// p″ curvature panel: a compact LINEAR symmetric-axis strip (p″ is near-zero and signed, so a shared
// log pressure axis would be meaningless). The zero line is drawn; the curve dips negative through a
// dual-porosity transition and peaks at regime changes.
function CurvaturePanel({ lx, p2, sx, regimes }: {
  lx: number[]; p2: number[]; sx: (x: number) => number; regimes: { iStart: number; iEnd: number; kind: RegimeKind }[];
}) {
  const W = 860, H = 120, PAD = 46;
  const amp = Math.max(1e-3, ...p2.map((v) => Math.abs(v)));
  const sy = (y: number) => H / 2 - (y / amp) * (H / 2 - 10);
  const path = p2.map((y, i) => `${i === 0 ? 'M' : 'L'}${sx(lx[i]).toFixed(1)},${sy(y).toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ background: 'var(--bg-3)', borderRadius: 8, marginTop: '.3rem' }} role="img" aria-label="second derivative curvature">
      {regimes.map((r, i) => (
        <rect key={i} x={sx(lx[r.iStart])} y={0} width={Math.max(0, sx(lx[r.iEnd]) - sx(lx[r.iStart]))}
          height={H} fill={REGIME_COLORS[r.kind]} fillOpacity={0.1} />
      ))}
      <line x1={PAD} y1={sy(0)} x2={W - PAD} y2={sy(0)} stroke="var(--fg-2)" strokeDasharray="3 3" strokeOpacity={0.5} />
      <path d={path} fill="none" stroke="#c94fd0" strokeWidth={1.8} />
    </svg>
  );
}

// ---------- SOTA: DTW distance to each baked medoid ----------
function DtwView({ x, ref }: { x: number[]; ref: DeepReference }) {
  const t = useT();
  const d = distancesToMedoids(x, ref.medoids, ref.dtw_window ?? 10);
  const nearest = d.indexOf(Math.min(...d));
  const max = Math.max(...d);
  return (
    <div>
      <p className="muted">{t.live.dtwDesc}</p>
      <span className="readout">{t.live.nearest}: <b style={{ color: COLORS[nearest % COLORS.length] }}>GT{nearest}</b></span>
      <table style={{ marginTop: '.6rem' }}>
        <thead><tr><th>GeoType</th><th>DTW distance</th></tr></thead>
        <tbody>
          {d.map((v, g) => (
            <tr key={g}>
              <td style={{ color: COLORS[g % COLORS.length] }}>GT{g}</td>
              <td><Bar frac={1 - v / max} color={COLORS[g % COLORS.length]} label={v.toFixed(3)} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------- novel: conformal p-values + prediction set + OOD (live) ----------
function ConformalView({ x, ref }: { x: number[]; ref: DeepReference }) {
  const t = useT();
  const [alpha, setAlpha] = useState(0.15);
  const d = distancesToMedoids(x, ref.medoids, ref.dtw_window ?? 10);
  const r = conformalAssign(d, ref.calibration_scores ?? {}, alpha);
  return (
    <div>
      <p className="muted">{t.live.conformalDesc}</p>
      <Slider label={`α = ${alpha.toFixed(2)} (coverage ${(1 - alpha).toFixed(2)})`} min={0.05} max={0.4} step={0.05} value={alpha} onChange={setAlpha} />
      <div style={{ display: 'flex', gap: '.5rem', margin: '.6rem 0', flexWrap: 'wrap' }}>
        <span className="readout">{t.live.set}: {r.set.length ? r.set.map((g) => `GT${g}`).join(', ') : '∅'}</span>
        {r.ood && <span className="badge bad">{t.live.ood}</span>}
      </div>
      <table>
        <thead><tr><th>GeoType</th><th>p-value</th><th>in set</th></tr></thead>
        <tbody>
          {r.pValues.map((p, g) => (
            <tr key={g}>
              <td style={{ color: COLORS[g % COLORS.length] }}>GT{g}</td>
              <td><Bar frac={p} color={COLORS[g % COLORS.length]} label={p.toFixed(3)} /></td>
              <td>{r.set.includes(g) ? '✓' : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------- learned: a GeoType classifier's class probabilities (ONNX live). Shared by the
//            InceptionTime (CNN) and PatchTST-lite (transformer) heads. ----------
function ClassifierView({ x, classify, desc, acc }: {
  x: number[]; classify: (c: number[]) => Promise<number[]>; desc: string; acc: number;
}) {
  const t = useT();
  const [p, setP] = useState<number[] | null>(null);
  useEffect(() => { classify(x).then(setP).catch(() => setP(null)); }, [x, classify]);
  if (!p) return <p className="muted">{t.common.loading}</p>;
  const top = p.indexOf(Math.max(...p));
  return (
    <div>
      <p className="muted">{desc}</p>
      <span className="readout">{t.live.predicted}: <b style={{ color: COLORS[top % COLORS.length] }}>GT{top}</b> ({(p[top] * 100).toFixed(0)}%) · {t.live.acc} {(acc * 100).toFixed(0)}%</span>
      <table style={{ marginTop: '.6rem' }}>
        <thead><tr><th>GeoType</th><th>{t.live.probability}</th></tr></thead>
        <tbody>{p.map((v, g) => (<tr key={g}><td style={{ color: COLORS[g % COLORS.length] }}>GT{g}</td><td><Bar frac={v} color={COLORS[g % COLORS.length]} label={(v * 100).toFixed(1) + '%'} /></td></tr>))}</tbody>
      </table>
    </div>
  );
}

// ---------- learned: autoencoder latent point + reconstruction anomaly (ONNX live) ----------
function AeView({ x, ref }: { x: number[]; ref: DeepReference }) {
  const t = useT();
  const [out, setOut] = useState<{ latent: number[]; reconError: number } | null>(null);
  useEffect(() => { autoencode(x).then(setOut).catch(() => setOut(null)); }, [x]);
  if (!out) return <p className="muted">{t.common.loading}</p>;
  const errs = ref.latent.map((_, i) => i); // baseline cloud size
  const anomaly = out.reconError;
  return (
    <div>
      <p className="muted">{t.live.aeDesc}</p>
      <div style={{ display: 'flex', gap: '.5rem', margin: '.5rem 0', flexWrap: 'wrap' }}>
        <span className="readout">{t.live.anomaly}: {anomaly.toFixed(3)}</span>
        <span className="readout">{t.live.latentDim}: {out.latent.length}</span>
      </div>
      <LatentScatter cloud={ref.latent} labels={ref.labels} point={out.latent} />
      <p className="muted" style={{ fontSize: '.8rem' }}>{t.live.latentNote} ({errs.length} {t.live.trainingCurves})</p>
    </div>
  );
}

// ---------- learned: contrastive embedding + nearest-neighbour retrieval (ONNX live) ----------
function ContrastiveView({ x, ref }: { x: number[]; ref: DeepReference }) {
  const t = useT();
  const [out, setOut] = useState<{ embedding: number[]; nnLabel: number; nnIndex: number } | null>(null);
  useEffect(() => { embedAndRetrieve(x).then(setOut).catch(() => setOut(null)); }, [x]);
  if (!out) return <p className="muted">{t.common.loading}</p>;
  return (
    <div>
      <p className="muted">{t.live.contrastiveDesc}</p>
      <span className="readout">{t.live.retrieved}: <b style={{ color: COLORS[out.nnLabel % COLORS.length] }}>GT{out.nnLabel}</b> · retrieval@1 {(ref.metrics.embed_retrieval_at1 * 100).toFixed(0)}%</span>
      <LatentScatter cloud={ref.embedding} labels={ref.labels} point={out.embedding} highlight={out.nnIndex} />
    </div>
  );
}

// PCA-free 2D projection (first two dims) of a high-D cloud + the live point.
function LatentScatter({ cloud, labels, point, highlight }: { cloud: number[][]; labels: number[]; point: number[]; highlight?: number }) {
  const W = 520, H = 360, PAD = 20;
  const xs = cloud.map((r) => r[0]).concat(point[0]);
  const ys = cloud.map((r) => r[1]).concat(point[1]);
  const xMin = Math.min(...xs), xMax = Math.max(...xs), yMin = Math.min(...ys), yMax = Math.max(...ys);
  const sx = (v: number) => PAD + ((v - xMin) / (xMax - xMin || 1)) * (W - 2 * PAD);
  const sy = (v: number) => H - PAD - ((v - yMin) / (yMax - yMin || 1)) * (H - 2 * PAD);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: 520, background: 'var(--bg-3)', borderRadius: 8 }} role="img" aria-label="latent space">
      {cloud.map((r, i) => (
        <circle key={i} cx={sx(r[0])} cy={sy(r[1])} r={i === highlight ? 5 : 2.2}
          fill={COLORS[labels[i] % COLORS.length]} fillOpacity={i === highlight ? 1 : 0.35}
          stroke={i === highlight ? '#fff' : 'none'} strokeWidth={1} />
      ))}
      <circle cx={sx(point[0])} cy={sy(point[1])} r={7} fill="#fff" stroke="#111" strokeWidth={2} />
      <text x={sx(point[0]) + 10} y={sy(point[1])} fill="var(--fg)" fontSize={12}>tuned curve</text>
    </svg>
  );
}

function Bar({ frac, color, label }: { frac: number; color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
      <div style={{ width: 140, height: 8, background: 'var(--bg-2)', borderRadius: 4 }}>
        <div style={{ width: `${Math.max(0, Math.min(100, frac * 100))}%`, height: 8, background: color, borderRadius: 4 }} />
      </div>
      <span className="tag">{label}</span>
    </div>
  );
}

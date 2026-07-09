// DTW distance heatmap (S2/P3): the committed cluster-ordered pairwise DTW matrix (uint8), rendered
// with a perceptually-uniform viridis colormap (rubric section 4 - never jet/rainbow). Rows/cols are
// ordered by GeoType so the clusters appear as dark (low-distance) blocks on the diagonal; cluster
// boundaries are drawn, and hovering reads the pair's distance + the two GeoTypes. Canvas2D (a single
// <=512x512 matrix does not need a WebGL context; the rubric reserves WebGL for the many-heatmap case).
import { useEffect, useMemo, useRef, useState } from 'react';
import type { StudyTraceV2 } from '../lib/contract.types';
import { useT } from '../i18n/useT';

// viridis anchors (perceptually uniform, CVD-safe); linear-interpolated to a 256 LUT.
const VIRIDIS: Array<[number, number, number]> = [
  [68, 1, 84], [72, 40, 120], [62, 74, 137], [49, 104, 142], [38, 130, 142],
  [31, 158, 137], [53, 183, 121], [110, 206, 88], [181, 222, 43], [253, 231, 37],
];
function viridis(t: number): [number, number, number] {
  const x = Math.min(1, Math.max(0, t)) * (VIRIDIS.length - 1);
  const i = Math.floor(x), f = x - i;
  const a = VIRIDIS[i], b = VIRIDIS[Math.min(i + 1, VIRIDIS.length - 1)];
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
}

const COLORS = ['var(--geo-0)', 'var(--geo-1)', 'var(--geo-2)', 'var(--geo-3)', 'var(--geo-4)'];

export function DtwHeatmapView({ trace }: { trace: StudyTraceV2 }) {
  const t = useT();
  const dtw = trace.dtw;
  const N = dtw.rows.length;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hover, setHover] = useState<{ i: number; j: number } | null>(null);

  // cluster boundary indices (where the ordered label changes) + per-cluster spans for the axis strips
  const bounds = useMemo(() => {
    const b: number[] = [];
    for (let i = 1; i < N; i++) if (dtw.order_labels[i] !== dtw.order_labels[i - 1]) b.push(i);
    return b;
  }, [dtw, N]);

  useEffect(() => {
    const cv = canvasRef.current;
    if (!cv || N === 0) return;
    cv.width = N; cv.height = N;
    const ctx = cv.getContext('2d')!;
    const img = ctx.createImageData(N, N);
    for (let i = 0; i < N; i++) {
      const row = dtw.rows[i];
      for (let j = 0; j < N; j++) {
        // invert so LOW distance (similar) is BRIGHT/yellow, high distance is dark-purple: reads as
        // "bright blocks = tight clusters". (viridis of 1 - d/255.)
        const [r, g, bl] = viridis(1 - row[j] / 255);
        const p = (i * N + j) * 4;
        img.data[p] = r; img.data[p + 1] = g; img.data[p + 2] = bl; img.data[p + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    // cluster boundary lines (drawn in matrix space, then the CSS scales the canvas up crisply)
    ctx.strokeStyle = 'rgba(255,255,255,0.7)';
    ctx.lineWidth = Math.max(0.5, N / 400);
    for (const b of bounds) {
      ctx.beginPath(); ctx.moveTo(b, 0); ctx.lineTo(b, N); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, b); ctx.lineTo(N, b); ctx.stroke();
    }
  }, [dtw, N, bounds]);

  const onMove = (e: React.MouseEvent) => {
    const cv = canvasRef.current!;
    const r = cv.getBoundingClientRect();
    const j = Math.floor(((e.clientX - r.left) / r.width) * N);
    const i = Math.floor(((e.clientY - r.top) / r.height) * N);
    setHover(i >= 0 && i < N && j >= 0 && j < N ? { i, j } : null);
  };

  const dist = hover ? (dtw.rows[hover.i][hover.j] / 255) * dtw.dmax : null;

  return (
    <div>
      <p className="muted">{t.app.dtwmap.desc}</p>
      <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap', margin: '.5rem 0', alignItems: 'center' }}>
        <span className="readout">{t.app.dtwmap.size}: {N}x{N}</span>
        <span className="readout">{t.app.dtwmap.dmax}: {dtw.dmax.toFixed(3)}</span>
        {dtw.note && dtw.note !== 'full' && <span className="tag">{dtw.note}</span>}
        {/* colorbar: bright(similar) -> dark(distant) */}
        <span className="tag" style={{ display: 'inline-flex', alignItems: 'center', gap: '.35rem' }}>
          {t.app.dtwmap.similar}
          <span style={{ width: 90, height: 10, borderRadius: 3, display: 'inline-block',
            background: 'linear-gradient(90deg, rgb(253,231,37), rgb(33,145,140), rgb(68,1,84))' }} />
          {t.app.dtwmap.distant}
        </span>
      </div>

      <div style={{ maxWidth: 460 }}>
        <canvas ref={canvasRef} onMouseMove={onMove} onMouseLeave={() => setHover(null)}
          role="img" aria-label={t.app.dtwmap.aria}
          style={{ width: '100%', imageRendering: 'pixelated', borderRadius: 8, cursor: 'crosshair', display: 'block' }} />
      </div>

      <div style={{ display: 'flex', gap: '.6rem', marginTop: '.5rem', flexWrap: 'wrap', minHeight: '1.4rem' }}>
        {hover && (
          <>
            <span className="readout">
              {t.app.dtwmap.pair}: <b style={{ color: COLORS[dtw.order_labels[hover.i] % COLORS.length] }}>GT{dtw.order_labels[hover.i]}</b>
              {' '}x{' '}
              <b style={{ color: COLORS[dtw.order_labels[hover.j] % COLORS.length] }}>GT{dtw.order_labels[hover.j]}</b>
            </span>
            <span className="readout">{t.app.dtwmap.distance}: {dist!.toFixed(3)}</span>
          </>
        )}
      </div>
      <p className="muted" style={{ fontSize: '.8em', marginTop: '.3rem' }}>{t.app.dtwmap.note}</p>
    </div>
  );
}

// ADR-0058 in-app architecture modal: tabbed, theme-aware SVG diagrams + bilingual text at depth.
import { useState } from 'react';
import { X } from 'lucide-react';
import { useT } from '../i18n/useT';

const TABS = ['t1', 't2', 't3', 't4'] as const;

export function ArchitectureModal({ onClose }: { onClose: () => void }) {
  const t = useT();
  const [tab, setTab] = useState<(typeof TABS)[number]>('t1');
  return (
    <div className="modal-back" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', padding: '1rem 1.25rem', borderBottom: '1px solid var(--border)' }}>
          <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{t.arch.title}</h2>
          <button className="icon-btn" style={{ marginLeft: 'auto' }} onClick={onClose} aria-label={t.arch.close}>
            <X size={18} />
          </button>
        </div>
        <div style={{ padding: '1rem 1.25rem' }}>
          <div className="tabs">
            {TABS.map((k) => (
              <span key={k} className={`tab ${tab === k ? 'on' : ''}`} onClick={() => setTab(k)}>
                {t.arch[k]}
              </span>
            ))}
          </div>
          <ArchDiagram which={tab} />
          <p className="muted" style={{ marginTop: '.75rem' }}>{t.arch[`p${tab.slice(1)}` as 'p1']}</p>
        </div>
      </div>
    </div>
  );
}

// Theme-aware SVGs (use currentColor + CSS vars so they invert with the theme).
function ArchDiagram({ which }: { which: string }) {
  const box = { fill: 'var(--bg-3)', stroke: 'var(--border)' };
  const accent = 'var(--accent)';
  const fg = 'var(--fg)';
  const fg2 = 'var(--fg-2)';
  if (which === 't1') {
    return (
      <svg viewBox="0 0 800 240" width="100%" role="img" aria-label="app diagram">
        <rect x="20" y="90" width="160" height="60" rx="8" {...box} />
        <text x="100" y="118" textAnchor="middle" fill={fg} fontSize="13">committed</text>
        <text x="100" y="136" textAnchor="middle" fill={fg2} fontSize="12">artifacts + manifest</text>
        <rect x="320" y="90" width="160" height="60" rx="8" fill="var(--accent)" opacity="0.15" stroke={accent} />
        <text x="400" y="118" textAnchor="middle" fill={fg} fontSize="13">React SPA</text>
        <text x="400" y="136" textAnchor="middle" fill={fg2} fontSize="12">replay (read-only)</text>
        <rect x="620" y="90" width="160" height="60" rx="8" {...box} />
        <text x="700" y="124" textAnchor="middle" fill={fg} fontSize="13">6 pages + workbench</text>
        <line x1="180" y1="120" x2="320" y2="120" stroke={accent} strokeWidth="2" markerEnd="url(#a)" />
        <line x1="480" y1="120" x2="620" y2="120" stroke={accent} strokeWidth="2" markerEnd="url(#a)" />
        <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill={accent} /></marker></defs>
      </svg>
    );
  }
  if (which === 't2') {
    const lanes = [['Offline', 'GeoDFN · open-DARTS · DTW · PAM · RF/SHAP', 'var(--geo-1)'], ['Live', 'numpy/scipy + pygeotypes (Pyodide)', 'var(--geo-2)'], ['Replay', 'committed trace + manifest', 'var(--geo-0)']];
    return (
      <svg viewBox="0 0 800 240" width="100%" role="img" aria-label="lanes diagram">
        {lanes.map((l, i) => (
          <g key={i}>
            <rect x="40" y={30 + i * 66} width="720" height="52" rx="8" fill="var(--bg-3)" stroke={l[2]} />
            <text x="60" y={52 + i * 66} fill={fg} fontSize="14" fontWeight="600">{l[0]}</text>
            <text x="60" y={70 + i * 66} fill={fg2} fontSize="12">{l[1]}</text>
          </g>
        ))}
      </svg>
    );
  }
  if (which === 't3') {
    const steps = ['GeoDFN', 'open-DARTS', 'preprocess', 'DTW k-medoids', 'conformal', 'RF/SHAP'];
    return (
      <svg viewBox="0 0 800 160" width="100%" role="img" aria-label="science flow">
        {steps.map((s, i) => (
          <g key={i}>
            <rect x={20 + i * 128} y="60" width="112" height="44" rx="7" {...box} />
            <text x={76 + i * 128} y="86" textAnchor="middle" fill={fg} fontSize="12">{s}</text>
            {i < steps.length - 1 && <line x1={132 + i * 128} y1="82" x2={148 + i * 128} y2="82" stroke={accent} strokeWidth="2" markerEnd="url(#b)" />}
          </g>
        ))}
        <defs><marker id="b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill={accent} /></marker></defs>
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 800 200" width="100%" role="img" aria-label="contracts">
      <rect x="40" y="40" width="300" height="54" rx="8" {...box} />
      <text x="190" y="64" textAnchor="middle" fill={fg} fontSize="13">Ingestion contract</text>
      <text x="190" y="82" textAnchor="middle" fill={fg2} fontSize="12">raw → pipeline (accept/reject)</text>
      <rect x="460" y="40" width="300" height="54" rx="8" fill="var(--accent)" opacity="0.15" stroke={accent} />
      <text x="610" y="64" textAnchor="middle" fill={fg} fontSize="13">Artifact contract</text>
      <text x="610" y="82" textAnchor="middle" fill={fg2} fontSize="12">pipeline → web (TS-mirrored)</text>
      <rect x="250" y="130" width="300" height="44" rx="8" {...box} />
      <text x="400" y="157" textAnchor="middle" fill={fg} fontSize="12">a drift on either fails the build</text>
    </svg>
  );
}

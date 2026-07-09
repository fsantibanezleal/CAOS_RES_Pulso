// The shared-shell configuration for Pulso (ADR-0016 / ADR-0058). One source of truth for the chrome:
// the shell renders the header (brand + six routes + GitHub/personal/portfolio + language + theme + the
// ⓘ architecture modal) and the FOOTER (name, version, "Developed by Felipe Santibanez-Leal",
// engine/data provenance + licenses, honest one-liner). The product version is single-sourced from
// package.json (below) so the footer and any in-app version read match the release tag.
import { Activity } from 'lucide-react';
import type { ArchitectureConfig, ShellConfig } from '@fasl-work/caos-app-shell';
import pkg from '../package.json';
import { ARCH_TABS } from './architecture';

export const VERSION = pkg.version; // single source of truth (== the git tag, e.g. 0.10.000)

const REPO = 'https://github.com/fsantibanezleal/CAOS_RES_Pulso';

const architecture: ArchitectureConfig = {
  title_en: 'Architecture / How it works',
  title_es: 'Arquitectura / Como funciona',
  tabs: ARCH_TABS,
};

// Bilingual footer provenance + honest disclaimer (ADR-0016 §2). Engines + licenses are stated; the
// disclaimer says how the app runs (offline-baked artifacts replayed + ONNX live in the browser).
export const shellConfig: ShellConfig = {
  product: { name: 'Pulso', mark: <Activity size={18} aria-hidden="true" /> },
  routes: [
    { path: '/', en: 'App', es: 'App' },
    { path: '/introduction', en: 'Introduction', es: 'Introduccion' },
    { path: '/methodology', en: 'Methodology', es: 'Metodologia' },
    { path: '/implementation', en: 'Implementation', es: 'Implementacion' },
    { path: '/experiments', en: 'Experiments', es: 'Experimentos' },
    { path: '/benchmark', en: 'Benchmark', es: 'Benchmark' },
  ],
  // github + Felipe's canonical personal/portfolio URLs (kept identical app-to-app per the shell standard),
  // so the header icon-links and the footer link row are complete, not just "Source on GitHub".
  links: {
    github: REPO,
    personal: 'https://fsantibanezleal.github.io',
    portfolio: 'https://fasl-work.com',
  },
  version: VERSION,
  architecture,
  footer: {
    // ADR-0016 s2: COMPACT one-wrapping-line footer. Provenance = engines (offline bake / live ONNX)
    // as one short clause; disclaimer = a single honest one-liner. NOT multi-sentence paragraphs (those
    // forced the footer into stacked blocks with orphaned separators, breaking the one-line rule).
    provenance: {
      en: 'Engines: GeoDFN + open-DARTS (offline) + onnxruntime-web (live ONNX)',
      es: 'Motores: GeoDFN + open-DARTS (offline) + onnxruntime-web (ONNX en vivo)',
    },
    disclaimer: {
      en: 'Offline-baked numbers, learned models live in-browser; no single method wins everywhere',
      es: 'Numeros pre-calculados offline, modelos aprendidos en vivo; ningun metodo gana en todo',
    },
  },
};

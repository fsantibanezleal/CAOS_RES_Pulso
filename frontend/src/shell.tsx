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
    provenance: {
      en: 'Engines: pygeotypes (Apache-2.0), GeoDFN (MIT), open-DARTS (GPL-3, offline), scikit-learn + SHAP, onnxruntime-web. Data: our GeoDFN + open-DARTS simulations, welltestpy field campaigns (MIT), community benchmark corpora.',
      es: 'Motores: pygeotypes (Apache-2.0), GeoDFN (MIT), open-DARTS (GPL-3, offline), scikit-learn + SHAP, onnxruntime-web. Datos: nuestras simulaciones GeoDFN + open-DARTS, campanas de campo welltestpy (MIT), corpus de referencia comunitarios.',
    },
    disclaimer: {
      en: 'Numbers come from committed offline artifacts; the learned models run live in-browser via onnxruntime-web. Honest scope: no single method wins everywhere.',
      es: 'Los numeros provienen de artefactos offline comprometidos; los modelos aprendidos corren en vivo en el navegador con onnxruntime-web. Alcance honesto: ningun metodo gana en todo.',
    },
  },
};

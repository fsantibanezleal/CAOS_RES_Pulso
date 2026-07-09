import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, Route, Routes } from 'react-router-dom';
import { AppShell, CitationsProvider, applyTheme, readTheme } from '@fasl-work/caos-app-shell';
import '@fasl-work/caos-app-shell/styles.css';
import './styles/theme.css';
import { shellConfig } from './shell';
import { CITATIONS } from './data/citations';
import { AppPage } from './pages/App';
import { Benchmark, Experiments, Implementation, Introduction, Methodology } from './pages/Prose';

// the shared shell owns theme + language state; set the theme pre-paint from the persisted choice
applyTheme(readTheme());

// ADR-0017 section 1.2: each page owns its `.page-body` root (centered, var(--maxw)); the shell chrome
// wraps them. ADR-0017 section 4.3: CitationsProvider mounted once, wrapping the shell.
function Root() {
  return (
    <HashRouter>
      <CitationsProvider items={CITATIONS}>
        <AppShell config={shellConfig}>
          <Routes>
            <Route path="/" element={<AppPage />} />
            <Route path="/introduction" element={<Introduction />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/implementation" element={<Implementation />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/benchmark" element={<Benchmark />} />
          </Routes>
        </AppShell>
      </CitationsProvider>
    </HashRouter>
  );
}

const el = document.getElementById('root');
if (el) createRoot(el).render(<StrictMode><Root /></StrictMode>);

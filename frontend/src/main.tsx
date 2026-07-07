import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, Route, Routes } from 'react-router-dom';
import { AppShell, applyTheme, readTheme } from '@fasl-work/caos-app-shell';
import '@fasl-work/caos-app-shell/styles.css';
import './styles/theme.css';
import { shellConfig } from './shell';
import { AppPage } from './pages/App';
import { Benchmark, Experiments, Implementation, Introduction, Methodology } from './pages/Prose';

// the shared shell owns theme + language state; set the theme pre-paint from the persisted choice
applyTheme(readTheme());

function Root() {
  return (
    <HashRouter>
      <AppShell config={shellConfig}>
        <main className="container" style={{ padding: '1.75rem 1.25rem 3rem' }}>
          <Routes>
            <Route path="/" element={<AppPage />} />
            <Route path="/introduction" element={<Introduction />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/implementation" element={<Implementation />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/benchmark" element={<Benchmark />} />
          </Routes>
        </main>
      </AppShell>
    </HashRouter>
  );
}

const el = document.getElementById('root');
if (el) createRoot(el).render(<StrictMode><Root /></StrictMode>);

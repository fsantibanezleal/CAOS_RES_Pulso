import { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, Route, Routes } from 'react-router-dom';
import './i18n';
import './styles/theme.css';
import { Header } from './components/Header';
import { ArchitectureModal } from './components/ArchitectureModal';
import { AppPage } from './pages/App';
import { Benchmark, Experiments, Implementation, Introduction, Methodology } from './pages/Prose';

function Root() {
  const [arch, setArch] = useState(false);
  return (
    <HashRouter>
      <Header onOpenArch={() => setArch(true)} />
      <main className="container" style={{ padding: '1.75rem 1.25rem 4rem' }}>
        <Routes>
          <Route path="/" element={<AppPage />} />
          <Route path="/introduction" element={<Introduction />} />
          <Route path="/methodology" element={<Methodology />} />
          <Route path="/implementation" element={<Implementation />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/benchmark" element={<Benchmark />} />
        </Routes>
      </main>
      {arch && <ArchitectureModal onClose={() => setArch(false)} />}
    </HashRouter>
  );
}

const el = document.getElementById('root');
if (el) createRoot(el).render(<StrictMode><Root /></StrictMode>);

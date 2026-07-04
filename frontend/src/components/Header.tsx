import { Github, Info, Languages, Moon, Sun } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useT } from '../i18n/useT';
import { useUI } from '../state/store';

export function Header({ onOpenArch }: { onOpenArch: () => void }) {
  const t = useT();
  const { theme, toggleTheme, lang, setLang } = useUI();
  const pages: Array<[string, string]> = [
    ['/', t.nav.app],
    ['/introduction', t.nav.introduction],
    ['/methodology', t.nav.methodology],
    ['/implementation', t.nav.implementation],
    ['/experiments', t.nav.experiments],
    ['/benchmark', t.nav.benchmark],
  ];
  return (
    <header className="hdr">
      <div className="container hdr-in">
        <span className="brand">
          <span className="dot" /> {t.brand}
        </span>
        <nav className="nav">
          {pages.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="hdr-tools">
          <button className="icon-btn" title={t.header.architecture} onClick={onOpenArch} aria-label={t.header.architecture}>
            <Info size={17} />
          </button>
          <button
            className="icon-btn"
            title={t.header.lang}
            onClick={() => setLang(lang === 'en' ? 'es' : 'en')}
            aria-label={t.header.lang}
          >
            <Languages size={17} />
            <span style={{ fontSize: 11, marginLeft: 2 }}>{lang.toUpperCase()}</span>
          </button>
          <button className="icon-btn" title={t.header.theme} onClick={toggleTheme} aria-label={t.header.theme}>
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>
          <a
            className="icon-btn"
            href="https://github.com/fsantibanezleal/CAOS_RES_FlowDNA"
            target="_blank"
            rel="noreferrer"
            title={t.header.github}
            aria-label={t.header.github}
          >
            <Github size={17} />
          </a>
        </div>
      </div>
    </header>
  );
}

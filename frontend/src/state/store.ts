// Global UI state (zustand): theme + language, persisted to localStorage. Kept tiny; the data
// selection lives in each page's local state (the App owns its source/case selectors).
import { create } from 'zustand';

type Theme = 'light' | 'dark';
type Lang = 'en' | 'es';

interface UIState {
  theme: Theme;
  lang: Lang;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  setLang: (l: Lang) => void;
}

const initialTheme = (): Theme => {
  const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('flowdna.theme') : null;
  return saved === 'light' ? 'light' : 'dark';
};
const initialLang = (): Lang => {
  const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('flowdna.lang') : null;
  return saved === 'es' ? 'es' : 'en';
};

const applyTheme = (t: Theme) => {
  if (typeof document !== 'undefined') document.documentElement.setAttribute('data-theme', t);
};

export const useUI = create<UIState>((set, get) => {
  applyTheme(initialTheme());
  return {
    theme: initialTheme(),
    lang: initialLang(),
    setTheme: (t) => {
      applyTheme(t);
      localStorage.setItem('flowdna.theme', t);
      set({ theme: t });
    },
    toggleTheme: () => get().setTheme(get().theme === 'dark' ? 'light' : 'dark'),
    setLang: (l) => {
      localStorage.setItem('flowdna.lang', l);
      set({ lang: l });
    },
  };
});

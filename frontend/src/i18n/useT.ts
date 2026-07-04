// Typed dict access for the current language (nested objects, full autocompletion) — simpler than
// string keys for deep prose content. Re-renders on language change via the zustand lang.
import { en, type Dict } from './en';
import { es } from './es';
import { useUI } from '../state/store';

export function useT(): Dict {
  const lang = useUI((s) => s.lang);
  return lang === 'es' ? es : en;
}

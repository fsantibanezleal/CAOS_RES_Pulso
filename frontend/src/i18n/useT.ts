// Typed dict access for the current language (nested objects, full autocompletion), simpler than
// string keys for deep prose content. The LANGUAGE is owned by the shared shell (useShellLang), so
// the shell's header toggle and the app content stay in lock-step from one source of truth.
import { useShellLang } from '@fasl-work/caos-app-shell';
import { en, type Dict } from './en';
import { es } from './es';

export function useT(): Dict {
  const lang = useShellLang();
  return lang === 'es' ? es : en;
}

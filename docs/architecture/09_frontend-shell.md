# 09 — The frontend shell (@fasl-work/caos-app-shell)

**Status:** adopted in v0.10.000 (rebuild phase P0.1). This replaced a hand-rolled header +
below-bar chrome that had **no footer** and a stale, invisible version.

## What the shell provides

Pulso's chrome is the shared **`@fasl-work/caos-app-shell`** package (ADR-0016 + ADR-0058), so the
header/footer/theme/language/architecture-modal are identical across the CAOS/Faena apps and a fix
lands in one place. Pulso does not hand-roll any of them.

- **Header** (`AppShell`): the product brand (name + pulse mark) + the six routes (App · Introduction
  · Methodology · Implementation · Experiments · Benchmark) + the icon links (GitHub, personal,
  portfolio) + the language toggle (EN default, ADR-0011) + the theme toggle (light/dark, ADR-0012) +
  the ⓘ **Architecture / How-it-works** button (ADR-0058).
- **Footer** (ADR-0016 §2): product name · "a CAOS research project" · **version** · "Developed by
  Felipe Santibanez-Leal" · engine/data **provenance + licenses** · an honest one-liner. It does not
  duplicate the header's personal/portfolio links.
- **Content primitives** for the deep pages: `Tabs`, `SubTabs`, `Equation`/`InlineMath`, `Callout`,
  `Figure`, and `CitationsProvider` + `Cite`/`Refs`/`ReferenceList` (used from phase P4 onward for
  graduate-level pages with inline citations and per-section reference lists).
- **State**: the shell OWNS theme + language (zustand + `data-theme`); the app reads the current
  language via `useShellLang`. See `Single source of truth` below.

## How Pulso wires it (`frontend/src`)

- `main.tsx` — sets the theme pre-paint (`applyTheme(readTheme())`), then wraps the `<Routes>` in
  `<AppShell config={shellConfig}>` inside a `HashRouter` (hash routing so deep links work on GitHub
  Pages without 404 tricks).
- `shell.tsx` — the `ShellConfig`: product name + mark, the six routes (bilingual labels), the repo
  link, the **version single-sourced from `package.json`** (`VERSION = pkg.version`, kept equal to the
  git release tag), the footer provenance + disclaimer (bilingual), and the architecture modal config.
- `architecture.ts` — the five ADR-0058 tabs (What Pulso is · The lanes · The web-app flow · The
  method ladder · The data contracts), each with bilingual body text and a themed SVG served from
  `public/svg/tech/`. NOTE: the SVG artwork is still the template placeholder in P0.1; the deep,
  hand-authored Pulso diagrams are authored in phase P4.
- `i18n/useT.ts` — reads `useShellLang()` so the shell's language toggle drives all app content.
- `index.html` — the product `<title>` + description + a pre-paint theme script (mirrors the shell's
  `caos.theme` localStorage key to avoid a flash).

## Single source of truth

- **Version**: `package.json` → `shell.tsx` `VERSION` → the footer. Bumped with each release tag.
- **Language**: the shell's `useShellLang` (localStorage `caos.lang`). The old app-local `useUI`
  zustand store and the i18next runtime init were removed; `i18n/{en,es}.ts` remain as the typed
  content dictionaries consumed via `useT`.
- **Theme**: the shell's theme store (localStorage `caos.theme`, `data-theme` attribute). `theme.css`
  keeps the Pulso design tokens (`--bg`, `--fg`, `--geo-*`, chips, gauges) keyed off `data-theme`.

## Verification

Screenshot-verified in **both themes** (light + dark), 0 console errors: the header, the footer
(name + v0.10.000 + Developed-by + provenance + licenses + honest one-liner), and the architecture
modal all render. Harness: `_CAOS_MANAGE/tools/visual-verify/pulso-shell.mjs`.

## What this is NOT (yet)

P0.1 adopts the shell only. The App workbench content, the ~22-method ladder, the rubric-compliant
visualizations, the graduate-level page content, and the deep architecture SVGs are later rebuild
phases (P2-P4). The chrome is correct now; the substance is built on top of it.

// Prebuild: copy the committed CONTRACT-2 artifacts (../data/derived) into the SPA's public/ so the static site
// replays them, and check the live-lane sources written from the fracpta package. Canonical copies live in ../data
// and ../data-pipeline, public/ is a build-time overlay (git-ignored).
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const PUB = join(HERE, 'public');

// 1) data/derived -> public/data (traces under <case>/trace.json + manifests/ subdir incl. index.json)
const derived = join(ROOT, 'data', 'derived');
if (existsSync(derived)) {
  mkdirSync(join(PUB, 'data'), { recursive: true });
  cpSync(derived, join(PUB, 'data'), { recursive: true });
  console.log('[copy-data] data/derived -> public/data');
} else {
  console.warn('[copy-data] no data/derived, run scripts/precompute first');
}

// 2) the optional Pyodide live lane reads public/pyodide/sources.json, written by
//    data-pipeline/export_live_sources.py from the installed fracpta package (committed with the bake).
if (!existsSync(join(PUB, 'pyodide', 'sources.json'))) {
  console.warn('[copy-data] no public/pyodide/sources.json, run data-pipeline/export_live_sources.py');
}

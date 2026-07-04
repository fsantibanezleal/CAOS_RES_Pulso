// Ties the CONTRACT 2 TS mirror to the REAL committed artifacts: the index, every manifest, and its
// trace must parse into the mirror types and pass shape checks. If the pipeline changes the schema
// without updating contract.types.ts, this test (and tsc) fail.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import type { CaseIndex, CaseManifest, Trace } from '../lib/contract.types';
import { isDartsTrace, isStudyTrace } from '../lib/contract.types';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const read = <T>(...p: string[]): T => JSON.parse(readFileSync(join(ROOT, 'data', 'derived', ...p), 'utf-8')) as T;

describe('CONTRACT 2 mirror matches the committed artifacts', () => {
  it('index -> every manifest -> trace parse into the mirror types and are consistent', () => {
    const idx = read<CaseIndex>('manifests', 'index.json');
    expect(idx.schema.startsWith('flowdna.index/')).toBe(true);
    expect(idx.cases.length).toBeGreaterThan(0);
    for (const entry of idx.cases) {
      const m = read<CaseManifest>('manifests', `${entry.case_id}.json`);
      expect(m.schema.startsWith('flowdna.manifest/')).toBe(true);
      expect(m.artifact.bytes).toBeGreaterThan(0);
      expect(['live', 'precompute']).toContain(m.lane);
      expect(m.engine.package).toBe('flowdnalab');
      const tr = read<Trace>(...m.artifact.path.split('/'));
      if (isStudyTrace(tr)) {
        expect(tr.medoids.length).toBe(tr.k);
        expect(tr.t_grid.length).toBeGreaterThan(0);
        expect(tr.medoids[0].length).toBe(tr.t_grid.length);
        expect(Object.keys(tr.calibration_scores).length).toBe(tr.k);
        expect(tr.summary.target).toBeGreaterThan(0);
      } else if (isDartsTrace(tr)) {
        expect(tr.tD.length).toBe(tr.pwD_sim.length);
        expect(tr.tD.length).toBe(tr.pwD_analytic.length);
        expect(tr.dpwD_sim.length).toBe(tr.tD.length);
        expect(typeof tr.validation.passed).toBe('boolean');
        expect(tr.validation.tol_rel_l2).toBeGreaterThan(0);
      } else {
        expect(tr.networks.length).toBeGreaterThan(0);
        expect(tr.descriptors.length).toBeGreaterThan(0);
        expect(tr.descriptor_names.length).toBe(tr.descriptors[0].length);
        expect(tr.transient_simulation).toContain('pending');
      }
    }
  });
});

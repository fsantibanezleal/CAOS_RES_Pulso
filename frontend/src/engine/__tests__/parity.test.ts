// TS live engine ↔ Python parity (the "live reproduces the offline" discipline). The TS Warren-Root
// / homogeneous responses must match pygeotypes.synthetic to <2e-3 relative.
import { describe, expect, it } from 'vitest';
import ref from './py_reference.json';
import { besselK0, homogeneousPd, warrenRootPd } from '../pta';
import { conformalAssign, dtwBanded } from '../dtw';

describe('TS analytic engine parity vs Python (pygeotypes.synthetic)', () => {
  it('Warren-Root pwD matches within 2e-3 relative', () => {
    const got = warrenRootPd(ref.tD, 0.05, 1e-6);
    got.forEach((v, i) => {
      const rel = Math.abs(v - ref.wr_005_1e6[i]) / Math.abs(ref.wr_005_1e6[i]);
      expect(rel).toBeLessThan(2e-3);
    });
  });

  it('homogeneous pwD matches within 2e-3 relative', () => {
    const got = homogeneousPd(ref.tD);
    got.forEach((v, i) => {
      const rel = Math.abs(v - ref.homog[i]) / Math.abs(ref.homog[i]);
      expect(rel).toBeLessThan(2e-3);
    });
  });

  it('besselK0 sanity (K0(1) ~ 0.4210)', () => {
    expect(Math.abs(besselK0(1) - 0.42102)).toBeLessThan(1e-4);
  });
});

describe('DTW + conformal (SOTA + novel) live primitives', () => {
  it('dtwBanded is zero on identical sequences and positive otherwise', () => {
    const a = [1, 2, 3, 4];
    expect(dtwBanded(a, a, 2)).toBe(0);
    expect(dtwBanded(a, [4, 3, 2, 1], 2)).toBeGreaterThan(0);
  });

  it('conformal returns a valid prediction set + OOD flag', () => {
    const cal = { '0': [0.1, 0.2, 0.3], '1': [1.0, 1.1, 1.2] };
    const r = conformalAssign([0.15, 1.05], cal, 0.2);
    expect(r.point).toBe(0);
    expect(r.pValues.length).toBe(2);
    expect(typeof r.ood).toBe('boolean');
  });
});

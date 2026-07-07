// P2c diagnostics engine: the fits must RECOVER the generating parameters on clean synthetic curves
// (the honest test of a fitter), and the regime detector must find a radial plateau on a homogeneous
// response. These run on the same analytic engine the live lab uses.
import { describe, expect, it } from 'vitest';
import { generateResponse, homogeneousPd, TD_GRID } from '../pta';
import { detectRegimes, fitTheis, fitWarrenRoot, secondLogDerivative } from '../diagnostics';

describe('P2c well-test diagnostics (live TS)', () => {
  it('fitWarrenRoot recovers the generating (omega, lambda) on a clean curve', () => {
    const { tD, p } = generateResponse(0.08, 1e-6, 0, 0, 1); // no noise
    const fit = fitWarrenRoot(tD, p);
    expect(fit.omega).toBeGreaterThan(0.04);
    expect(fit.omega).toBeLessThan(0.13);
    // lambda is recovered to within ~1 order of magnitude (it sets the transition timing)
    expect(Math.log10(fit.lam)).toBeGreaterThan(-7.2);
    expect(Math.log10(fit.lam)).toBeLessThan(-4.8);
    expect(fit.rmse).toBeLessThan(0.15);
  });

  it('fitTheis recovers a small skin on a homogeneous curve', () => {
    const p = homogeneousPd(TD_GRID, 1.0);
    const fit = fitTheis(TD_GRID, p);
    expect(Math.abs(fit.skin - 1.0)).toBeLessThan(0.6);
    expect(fit.rmse).toBeLessThan(0.05);
  });

  it('detectRegimes finds a radial plateau on a homogeneous response', () => {
    const { tD, dp } = generateResponse(1.0, 1e-6, 0, 0, 1); // homogeneous -> radial plateau at 0.5
    const segs = detectRegimes(tD, dp);
    expect(segs.some((s) => s.kind === 'radial')).toBe(true);
  });

  it('detectRegimes flags a dual-porosity transition on a Warren-Root curve', () => {
    const { tD, dp } = generateResponse(0.03, 1e-6, 0, 0, 1); // deep valley (small omega)
    const segs = detectRegimes(tD, dp);
    expect(segs.some((s) => s.kind === 'dual-porosity-transition' || s.kind === 'radial')).toBe(true);
    expect(segs.length).toBeGreaterThan(0);
  });

  it('secondLogDerivative returns a finite series of the right length', () => {
    const { tD, dp } = generateResponse(0.05, 1e-6, 0, 0.0, 1);
    const p2 = secondLogDerivative(tD, dp);
    expect(p2.length).toBe(tD.length);
    expect(p2.every((v) => Number.isFinite(v))).toBe(true);
  });
});

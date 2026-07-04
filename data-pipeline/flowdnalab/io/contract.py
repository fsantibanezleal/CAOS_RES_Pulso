"""CONTRACT 1 — ingestion (raw -> pipeline). The *bring-your-own-data* gate.

Two entry doors, each with an EXPLICIT outlier policy (reject / flag — never silent coercion):

1. **Curve sets** (`validate_curves`) — the real-data door. A pressure-transient record is a pair
   of arrays (t, Δp). Requirements per curve: strictly increasing t > 0, finite values, at least
   MIN_POINTS samples, at least MIN_DECADES of log-time span (the Bourdet derivative and DTW are
   meaningless on a shorter window). Suspicious-but-usable curves are FLAGGED (short span, heavy
   derivative sign-flipping = noise) and accepted; broken curves are REJECTED with a reason.
2. **Ensemble specs** (`validate_spec`) — the synthetic/analytic door. Parameter ranges must be
   physical (ω ∈ (0,1], λ > 0, noise bounded, fractions coherent) so a case cannot silently ask
   the engine for nonsense.

Documented for users in data/README.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .schema import EnsembleSpec

MIN_POINTS = 24
MIN_DECADES = 1.5
FLAG_DECADES = 2.0          # span in [MIN_DECADES, FLAG_DECADES) is accepted but flagged
FLAG_SIGN_FLIP_FRAC = 0.35  # fraction of first-difference sign flips above which a curve is flagged noisy


@dataclass
class ContractReport:
    accepted: list[Any]
    rejected: list[dict[str, Any]]
    flagged: list[dict[str, Any]]

    @property
    def ok(self) -> bool:
        return len(self.accepted) > 0

    def summary(self) -> str:
        return f"{len(self.accepted)} accepted, {len(self.rejected)} rejected, {len(self.flagged)} flagged"


def _finite(xs: list[float]) -> bool:
    return all(math.isfinite(float(x)) for x in xs)


def validate_curves(curves: list[dict[str, Any]]) -> ContractReport:
    """Apply CONTRACT 1 to raw curves: [{'curve_id', 't': [...], 'p': [...]}]. Pure; no I/O."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    flagged: list[dict[str, Any]] = []

    for i, row in enumerate(curves):
        cid = str(row.get("curve_id", f"curve{i}"))
        t = row.get("t")
        p = row.get("p")
        if not isinstance(t, (list, tuple)) or not isinstance(p, (list, tuple)) or len(t) != len(p):
            rejected.append({"row": i, "curve_id": cid, "reason": "t/p missing or of unequal length"})
            continue
        if len(t) < MIN_POINTS:
            rejected.append({"row": i, "curve_id": cid, "reason": f"only {len(t)} samples < {MIN_POINTS}"})
            continue
        if not (_finite(t) and _finite(p)):
            rejected.append({"row": i, "curve_id": cid, "reason": "NaN/Inf value"})
            continue
        tf = [float(x) for x in t]
        if tf[0] <= 0 or any(b <= a for a, b in zip(tf, tf[1:])):
            rejected.append({"row": i, "curve_id": cid, "reason": "t must be strictly increasing and > 0"})
            continue
        decades = math.log10(tf[-1] / tf[0])
        if decades < MIN_DECADES:
            rejected.append(
                {"row": i, "curve_id": cid, "reason": f"time span {decades:.2f} decades < {MIN_DECADES}"}
            )
            continue
        if decades < FLAG_DECADES:
            flagged.append({"curve_id": cid, "flag": f"short span: {decades:.2f} decades < {FLAG_DECADES}"})
        pf = [float(x) for x in p]
        # noise heuristic: sign flips of first differences, counting only MATERIAL differences
        # (>0.1% of the curve's range) — tiny early-time wiggles are not noise evidence
        rng_p = max(pf) - min(pf)
        thr = 1e-3 * rng_p if rng_p > 0 else 0.0
        diffs = [b - a for a, b in zip(pf, pf[1:])]
        material = [(a, b) for a, b in zip(diffs, diffs[1:]) if abs(a) > thr and abs(b) > thr]
        flips = sum(1 for a, b in material if a * b < 0)
        flip_frac = flips / max(1, len(material))
        if flip_frac > FLAG_SIGN_FLIP_FRAC:
            flagged.append({"curve_id": cid, "flag": f"noisy: {flip_frac:.0%} material sign flips"})
        accepted.append({"curve_id": cid, "t": tf, "p": pf})
    return ContractReport(accepted=accepted, rejected=rejected, flagged=flagged)


def validate_spec(spec: EnsembleSpec) -> ContractReport:
    """Apply CONTRACT 1 to an ensemble spec (the synthetic door). Rejects unphysical requests."""
    bad: list[str] = []
    flags: list[dict[str, Any]] = []
    if spec.n_curves < 12:
        bad.append(f"n_curves={spec.n_curves} < 12 (catalogue + conformal split needs more)")
    for name, (lo, hi) in (("omega_range", spec.omega_range), ("lam_range", spec.lam_range)):
        if not (0 < lo <= hi):
            bad.append(f"{name}=({lo:g},{hi:g}) must satisfy 0 < lo <= hi")
    if spec.omega_range[1] > 1.0:
        bad.append(f"omega_range max {spec.omega_range[1]:g} > 1 (storativity ratio is in (0,1])")
    if not (0.0 <= spec.noise_sd <= 0.5):
        bad.append(f"noise_sd={spec.noise_sd:g} out of [0, 0.5]")
    if not (0.0 <= spec.homogeneous_fraction <= 1.0):
        bad.append(f"homogeneous_fraction={spec.homogeneous_fraction:g} out of [0,1]")
    if spec.kind not in ("warren_root", "mixture"):
        bad.append(f"unknown kind {spec.kind!r}")
    if spec.derivative_order not in (0, 1, 2):
        bad.append("derivative_order must be 0, 1 or 2")
    if not (2 <= spec.k_min <= spec.k_max <= 12):
        bad.append(f"k range [{spec.k_min},{spec.k_max}] must satisfy 2 <= k_min <= k_max <= 12")
    if not (0.0 < spec.frac_cal < 0.5 and 0.0 < spec.frac_test < 0.5):
        bad.append("frac_cal and frac_test must be in (0, 0.5)")
    if not (0.0 < spec.alpha < 1.0):
        bad.append(f"alpha={spec.alpha:g} out of (0,1)")
    # conformal reachability: the calibration slice must allow empty sets at this alpha
    n_cal_per_class = spec.n_curves * spec.frac_cal / max(2, spec.k_min)
    if n_cal_per_class < (1.0 / spec.alpha - 1.0):
        flags.append(
            {
                "case_id": spec.case_id,
                "flag": (
                    f"~{n_cal_per_class:.0f} calibration curves/class < 1/alpha-1 = "
                    f"{1.0 / spec.alpha - 1.0:.0f}: out-of-catalogue verdicts unreachable at alpha={spec.alpha}"
                ),
            }
        )
    if bad:
        return ContractReport(accepted=[], rejected=[{"case_id": spec.case_id, "reason": "; ".join(bad)}],
                              flagged=flags)
    return ContractReport(accepted=[spec], rejected=[], flagged=flags)

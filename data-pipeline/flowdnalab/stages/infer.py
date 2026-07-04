"""Stage 4 — infer: conformally assign the held-out TEST curves against the trained catalogue.

This is exactly what the live lane does for a user's curve — run here offline over the test slice
so the committed artifact carries real, reproducible assignment examples (point prediction,
p-values, prediction set, out-of-catalogue verdicts).
"""
from __future__ import annotations

import numpy as np
from pygeotypes.assign import ConformalAssigner

from ..io.schema import EnsembleSpec


def run(assigner: ConformalAssigner, X_test: np.ndarray, spec: EnsembleSpec) -> list[dict]:
    out: list[dict] = []
    for i, x in enumerate(np.asarray(X_test, dtype=float)):
        r = assigner.predict(x, alpha=spec.alpha)
        d = r.to_dict()
        d["test_index"] = int(i)
        out.append(d)
    return out

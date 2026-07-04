"""CONTRACT 2 — artifact (pipeline -> web). The manifest is the authoritative, versioned record of a baked case:
its params, seed, engine+versions, the compact artifact pointer + byte size, the lane/gate verdict, flags from
CONTRACT 1, and the evaluation metrics. The web loads ONLY manifests + artifacts; frontend/src/lib/contract.types.ts
mirrors this schema so a drift fails the build. A flat index.json inventories every case (ADR-0057 default)."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .. import __version__

MANIFEST_SCHEMA = "flowdna.manifest/v1"
INDEX_SCHEMA = "flowdna.index/v1"


def _engine_block(extra_engines: dict[str, str] | None = None) -> dict:
    try:
        import pygeotypes
        pg_ver = pygeotypes.__version__
    except ImportError:  # pragma: no cover — pipeline venv always has it
        pg_ver = "unavailable"
    eng = {"package": "flowdnalab", "version": __version__, "pygeotypes": pg_ver}
    if extra_engines:
        eng.update(extra_engines)
    return eng


def build_case_manifest(
    *,
    case: Any,
    seed: int,
    artifact_rel: str,
    artifact_schema: str,
    trace_bytes: int,
    gate: dict,
    flags: list[dict],
    metrics: dict,
    extra_engines: dict[str, str] | None = None,
) -> dict:
    # Deterministic: a pure function of (params, seed). No wall-clock here (would dirty git on re-run) — the
    # lane/gate verdict + budgets carry the lane decision; live timing is measured in the browser, not committed.
    return {
        "schema": MANIFEST_SCHEMA,
        "case_id": case.id,
        "category": case.category,
        "real_or_synthetic": case.real_or_synthetic,
        "expected_band": case.expected_band,
        "engine": _engine_block(extra_engines),
        "params": asdict(case.spec),
        "seed": seed,
        "artifact": {"path": artifact_rel, "format": "json", "trace_schema": artifact_schema,
                     "bytes": trace_bytes},
        "lane": gate["lane"],
        "gate": gate,
        "flags": flags,
        "metrics": metrics,
    }


def build_index(entries: list[dict]) -> dict:
    """entries: [{case_id, category, manifest_path}] -> the flat authoritative inventory."""
    return {
        "schema": INDEX_SCHEMA,
        "engine_version": __version__,
        "n_cases": len(entries),
        "cases": sorted(entries, key=lambda e: e["case_id"]),
    }

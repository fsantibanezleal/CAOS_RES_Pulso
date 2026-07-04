"""Field-data path tests. The availability gate is tested WITHOUT the vault; the loader + bake are
skipped when the welltestpy campaigns are absent (CI / core-only envs), keeping the suite green."""
import json

import pytest

from flowdnalab import pipeline
from flowdnalab.cases.flowdna_cases import Case
from flowdnalab.io import field_data
from flowdnalab.io.schema import FieldDataSpec


def test_availability_is_honest_without_the_vault(tmp_path, monkeypatch):
    """With no field dir reachable, available() is False (so the suite + run_all skip field cases)."""
    monkeypatch.setenv("FLOWDNA_VAULT", str(tmp_path))  # empty -> no campaigns
    assert field_data.available() is False


@pytest.mark.skipif(not field_data.available(),
                    reason="welltestpy field campaigns not available (FLOWDNA_VAULT/field)")
class TestWithVault:
    @pytest.fixture(autouse=True)
    def _isolated_derived(self, tmp_path, monkeypatch):
        monkeypatch.setattr(pipeline, "DERIVED", tmp_path)
        monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "manifests")

    def test_loader_extracts_curves_and_descriptors(self):
        import numpy as np

        loaded = field_data.load_field(("horkheim", "lauswiesen"))
        assert loaded["n_available"] >= 30  # ~44 usable curves across both sites
        assert len(loaded["t"]) == len(loaded["p"]) == len(loaded["features"]) == len(loaded["ids"])
        assert loaded["feature_names"] == ["log_r", "log_Q", "site", "well_depth",
                                           "screen_size", "aquifer_depth"]
        feats = np.asarray(loaded["features"], dtype=float)
        assert np.all(np.isfinite(feats)), "descriptors must be NaN-free (imputed) for the RF gate"
        assert set(np.unique(feats[:, 2]).tolist()) <= {0.0, 1.0}  # site code
        for t in loaded["t"]:  # each curve is sorted, positive, finite time
            assert t[0] > 0 and np.all(np.diff(t) > 0)

    def test_field_case_bakes_an_aquifertype_catalogue(self):
        case = Case(
            "T_FIELD", "test: field", "field",
            FieldDataSpec(case_id="T_FIELD", sites=("horkheim", "lauswiesen"), k_max=4),
            "real field drawdown", "field-pumping",
        )
        m = pipeline._precompute_field(case, seed=3)
        assert m["real_or_synthetic"] == "field-pumping"
        assert m["artifact"]["trace_schema"].startswith("flowdna.trace/")
        trace = json.loads((pipeline.DERIVED / m["artifact"]["path"]).read_text(encoding="utf-8"))
        assert trace["preprocessing"]["derivative_order"] == 1  # raw drawdown -> Bourdet derivative
        assert len(trace["medoids"]) == m["metrics"]["k"]
        assert any("welltestpy field campaigns" in str(f) for f in m["flags"])

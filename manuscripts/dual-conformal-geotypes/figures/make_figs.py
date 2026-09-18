"""Deterministically generate the figures for the Pulso paper from the committed traces
(data/derived/<case>/trace.json). Every number is read from the JSON. Run with the figures
venv (matplotlib). Outputs vector PDFs next to this file."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DER = HERE.parents[2] / "data" / "derived"
BLUE, ORANGE, GREEN, PURPLE, GRAY, INK = "#2b6cb0", "#c05621", "#2f855a", "#6b46c1", "#718096", "#1a202c"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#4a5568", "axes.linewidth": 0.8})


def trace(case):
    return json.loads((DER / case / "trace.json").read_text(encoding="utf-8"))


# ---- Fig 1: silhouette per case, grouped by family (real transients cluster cleaner) ----
def fig_silhouette():
    groups = [
        ("Real 4TU", BLUE, ["REAL_A_lowperm", "REAL_B_midperm", "REAL_C_highperm"]),
        ("DFN/DFM", GREEN, ["DFM01_geotypes", "DFM02_dense", "DFM03_sparse"]),
        ("Hydrogeology", PURPLE, ["FIELD_horkheim", "FIELD_lauswiesen", "FIELD_combined"]),
        ("Analytic (WR/mix)", ORANGE, ["WR01_baseline", "WR02_depth_families", "WR03_timing_families", "WR05_noisy", "MIX04_homog_vs_dp"]),
    ]
    # Drawn at the printed column width (3.5 in) so the text prints at the sizes set here.
    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    x = 0; ticks = []; ticklab = []
    for name, col, cases in groups:
        for c in cases:
            try:
                s = trace(c).get("silhouette")
            except Exception:
                s = None
            if s is None:
                continue
            ax.bar(x, s, color=col, width=0.8, zorder=3)
            # Distinct tick labels: REAL_A/B/C and the three field sites are told apart.
            parts = c.split("_")
            lab = "_".join(parts[:2]) if c.startswith("REAL") else parts[1] if c.startswith("FIELD") else parts[0]
            ticks.append(x); ticklab.append(lab)
            x += 1
        x += 0.6
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=g[1], label=g[0]) for g in groups], fontsize=6.5, loc="upper right", ncol=2)
    ax.set_xticks(ticks); ax.set_xticklabels(ticklab, rotation=60, fontsize=6.5, ha="right")
    ax.tick_params(axis="y", labelsize=7)
    ax.set_ylabel("silhouette (clustering quality)", fontsize=7.5); ax.set_ylim(0, 0.95)
    fig.suptitle("Real transients cluster more cleanly than analytic families", fontsize=7.4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(HERE / "fig-silhouette.pdf"); plt.close(fig)


# ---- Fig 2: dual-representation vs shape-only conformal (the contribution) ----
def fig_dual():
    cases = ["WR01_baseline", "BENCH_A", "BENCH_B", "BENCH_C", "REAL_A_lowperm"]
    labels = ["WR01", "BENCH_A", "BENCH_B", "BENCH_C", "REAL_A"]
    cs, cd, ss, sd = [], [], [], []
    targets = set()
    for c in cases:
        d = trace(c); ap = d["attribution_plus"]["dual_conformal"]; summ = d["summary"]
        cs.append(ap["coverage_shape"]); cd.append(ap["coverage_dual"])
        ss.append(summ["mean_set_size"]); sd.append(ap["mean_set_dual"])
        # The reference line is the target coverage 1 - alpha stored in each trace (not hard-coded).
        tgt = round(1.0 - ap["alpha"], 6)
        assert abs(tgt - summ["target"]) < 1e-9, (c, tgt, summ["target"])
        targets.add(tgt)
    assert len(targets) == 1, targets          # one common target across the plotted cases
    target = targets.pop()
    # Drawn at the printed column width (3.5 in) so the text prints at the sizes set here; the
    # legend sits under the title, clear of the coverage bars.
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.5, 2.75))
    x = range(len(cases)); w = 0.38
    a1.bar([i - w / 2 for i in x], cs, w, color=GRAY, label="shape-only", zorder=3)
    a1.bar([i + w / 2 for i in x], cd, w, color=BLUE, label="dual", zorder=3)
    a1.axhline(target, color=INK, ls="--", lw=0.8, label=f"target {target:.2f}")
    a1.set_xticks(list(x)); a1.set_xticklabels(labels, rotation=45, fontsize=6.5, ha="right")
    a1.set_ylabel("marginal coverage", fontsize=7.5); a1.set_ylim(0, 1.0); a1.set_title("coverage", fontsize=7.5)
    a1.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    a2.bar([i - w / 2 for i in x], ss, w, color=GRAY, zorder=3)
    a2.bar([i + w / 2 for i in x], sd, w, color=BLUE, zorder=3)
    a2.set_xticks(list(x)); a2.set_xticklabels(labels, rotation=45, fontsize=6.5, ha="right")
    a2.set_ylabel("mean set size", fontsize=7.5); a2.set_title("tighter sets", fontsize=7.5)
    a2.set_yticks([0, 0.5, 1.0, 1.5])
    for a in (a1, a2):
        a.tick_params(axis="y", labelsize=7)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.suptitle("Dual conformal trades coverage for tighter,\nphysics-consistent sets", fontsize=7.6, y=0.99)
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, 0.875), ncol=3, fontsize=6.8, frameon=False)
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.2, top=0.72, wspace=0.55)
    fig.savefig(HERE / "fig-dual-conformal.pdf"); plt.close(fig)


# ---- Fig 3: the reproduced GeoType catalogue (member curves + medoids), a real case ----
def fig_catalogue(case="BENCH_C"):
    d = trace(case); t = d.get("t_grid"); mem = d["members"]
    curves = mem["curves"]; gt = mem["geotype"]; mi = d["embedding"]["medoid_idx"]
    x = t if (isinstance(t, list) and len(t) == len(curves[0])) else list(range(len(curves[0])))
    cols = {0: BLUE, 1: ORANGE}
    fig, ax = plt.subplots(figsize=(4.9, 3.0))
    step = max(1, len(curves) // 220)
    for i in range(0, len(curves), step):
        ax.plot(x, curves[i], color=cols.get(gt[i], GRAY), lw=0.5, alpha=0.18, zorder=2)
    for j, idx in enumerate(mi):
        ax.plot(x, curves[idx], color=cols.get(gt[idx], INK), lw=2.6, zorder=5, label=f"GeoType {gt[idx]} medoid")
    ax.set_xlabel("log dimensionless time"); ax.set_ylabel("Bourdet derivative (normalized)")
    ax.set_title(f"Reproduced GeoType catalogue ({case}): {len(set(gt))} flow-behaviour classes", fontsize=8.6)
    ax.legend(fontsize=7, loc="best")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "fig-catalogue.pdf"); plt.close(fig)


if __name__ == "__main__":
    fig_silhouette(); fig_dual(); fig_catalogue()
    print("figures written:", [p.name for p in sorted(HERE.glob("*.pdf"))])

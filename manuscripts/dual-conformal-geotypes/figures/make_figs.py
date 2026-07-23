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
    fig, ax = plt.subplots(figsize=(4.9, 3.0))
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
            ticks.append(x); ticklab.append(c.split("_")[0] if c.startswith(("REAL", "DFM", "FIELD", "WR", "MIX")) else c)
            x += 1
        x += 0.6
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=g[1], label=g[0]) for g in groups], fontsize=6.8, loc="upper right", ncol=2)
    ax.set_xticks(ticks); ax.set_xticklabels(ticklab, rotation=60, fontsize=6, ha="right")
    ax.set_ylabel("silhouette (clustering quality)"); ax.set_ylim(0, 0.95)
    ax.set_title("Real transients cluster more cleanly than analytic families", fontsize=8.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "fig-silhouette.pdf"); plt.close(fig)


# ---- Fig 2: dual-representation vs shape-only conformal (the contribution) ----
def fig_dual():
    cases = ["WR01_baseline", "BENCH_A", "BENCH_B", "BENCH_C", "REAL_A_lowperm"]
    labels = ["WR01", "BENCH_A", "BENCH_B", "BENCH_C", "REAL_A"]
    cs, cd, ss, sd = [], [], [], []
    for c in cases:
        d = trace(c); ap = d["attribution_plus"]["dual_conformal"]; summ = d["summary"]
        cs.append(ap["coverage_shape"]); cd.append(ap["coverage_dual"])
        ss.append(summ["mean_set_size"]); sd.append(ap["mean_set_dual"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(5.0, 2.9))
    x = range(len(cases)); w = 0.38
    a1.bar([i - w / 2 for i in x], cs, w, color=GRAY, label="shape-only", zorder=3)
    a1.bar([i + w / 2 for i in x], cd, w, color=BLUE, label="dual", zorder=3)
    a1.axhline(0.9, color=INK, ls="--", lw=0.8)
    a1.set_xticks(list(x)); a1.set_xticklabels(labels, rotation=45, fontsize=6.5, ha="right")
    a1.set_ylabel("marginal coverage"); a1.set_ylim(0, 1.0); a1.set_title("coverage", fontsize=8.5); a1.legend(fontsize=6.8)
    a2.bar([i - w / 2 for i in x], ss, w, color=GRAY, zorder=3)
    a2.bar([i + w / 2 for i in x], sd, w, color=BLUE, zorder=3)
    a2.set_xticks(list(x)); a2.set_xticklabels(labels, rotation=45, fontsize=6.5, ha="right")
    a2.set_ylabel("mean set size"); a2.set_title("tighter sets", fontsize=8.5)
    for a in (a1, a2):
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.suptitle("Dual conformal trades coverage for tighter, physics-consistent sets", fontsize=8.6)
    fig.tight_layout(rect=[0, 0, 1, 0.94]); fig.savefig(HERE / "fig-dual-conformal.pdf"); plt.close(fig)


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

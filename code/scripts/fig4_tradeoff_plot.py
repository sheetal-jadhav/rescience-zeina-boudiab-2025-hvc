"""Plot the Fig 4 burst-size/duration trade-off from the RA-capacitance runs.
Inputs: results/random_tight.jsonl (200 calibration runs, Cm 20 pF), results/fig4_cm_network_grid.jsonl
(Cm 14-18 pF grid, 2 seeds), results/robust_seeds.jsonl (final config, 50 seeds),
results/fig4_cm16_confirm.jsonl (Cm 16, 10 seeds).
Run from code/: ../.venv/bin/python -I scripts/fig4_tradeoff_plot.py -> figures/article_fig4_tradeoff.png"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = Path(__file__).resolve().parents[2] / "results"
FIG = Path(__file__).resolve().parents[2] / "figures"


def load(name):
    return [json.loads(l) for l in open(R / name)]


def main():
    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 3.8))
    cal = [l["score"] for l in load("random_tight.jsonl")
           if "error" not in l.get("score", {}) and l["score"].get("ra_in_order")]
    a.scatter([s["ra_spikes"] for s in cal], [s["ra_dur"] for s in cal], s=8, c="0.75",
              label="Cm 20 pF, 200 random configs")
    grid = {}
    for l in load("fig4_cm_network_grid.jsonl"):
        grid.setdefault(l["variant"], []).append(l["score"])
    cms = sorted({float(v.split("_")[0][2:]) for v in grid})
    cmap = plt.get_cmap("viridis")
    for v, S in grid.items():
        cm = float(v.split("_")[0][2:])
        a.scatter(np.mean([s["ra_spikes"] for s in S]), np.mean([s["ra_dur"] for s in S]), s=22,
                  color=cmap((cm - cms[0]) / (cms[-1] - cms[0])), edgecolor="none")
    for cm in cms:
        a.scatter([], [], s=22, color=cmap((cm - cms[0]) / (cms[-1] - cms[0])), label=f"Cm {cm:.0f} pF")
    for name, mk, lab in (("robust_seeds.jsonl", "s", "final config (Cm 20), 50 seeds"),
                          ("fig4_cm16_confirm.jsonl", "D", "Cm 16, gSK 12.5, gA 14, 10 seeds")):
        S = [l["score"] for l in load(name)]
        x = [s["ra_spikes"] for s in S]; y = [s["ra_dur"] for s in S]
        a.errorbar(np.mean(x), np.mean(y), xerr=np.std(x), yerr=np.std(y), fmt=mk, color="k",
                   ms=6, mfc="w", label=lab, zorder=5)
    a.errorbar(4.76, 8.12, xerr=0.48, yerr=0.89, fmt="*", color="crimson", ms=12,
               label="original Fig 4", zorder=6)
    a.set_xlabel("spikes per burst"); a.set_ylabel("burst duration (ms)")
    a.set_xlim(2.2, 7.2); a.set_ylim(4, 16)
    a.legend(fontsize=6.5, loc="upper left", frameon=False)
    a.set_title("A  Burst size and duration move together", fontsize=9, loc="left")

    rows = []
    for v, S in grid.items():
        rows.append((float(v.split("_")[0][2:]), np.mean([s["link_ms"] for s in S]),
                     np.mean([s["ra_ok"] for s in S])))
    rows = np.array(rows)
    for cm in cms:
        m = rows[:, 0] == cm
        b.scatter(rows[m, 1], rows[m, 2], s=22, color=cmap((cm - cms[0]) / (cms[-1] - cms[0])))
    base = load("robust_seeds.jsonl")
    b.scatter(np.mean([l["score"]["link_ms"] for l in base]), np.mean([l["score"]["ra_ok"] for l in base]),
              marker="s", color="k", facecolor="w", s=40, label="final config (Cm 20)")
    c16 = load("fig4_cm16_confirm.jsonl")
    b.scatter(np.mean([l["score"]["link_ms"] for l in c16]), np.mean([l["score"]["ra_ok"] for l in c16]),
              marker="D", color="k", facecolor="w", s=40, label="Cm 16 (10 seeds)")
    b.axvline(1.4, color="crimson", ls="--", lw=1); b.text(1.41, 5, "original raster\n~1.4 ms", color="crimson", fontsize=7)
    b.set_xlabel("delay between neighbouring RA bursts (ms)")
    b.set_ylabel("RA meeting the burst criterion (of 120)")
    b.legend(fontsize=6.5, frameon=False, loc="lower right")
    b.set_title("B  Shorter delays cost criterion-meeting bursts", fontsize=9, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "article_fig4_tradeoff.png", dpi=200)


if __name__ == "__main__":
    main()

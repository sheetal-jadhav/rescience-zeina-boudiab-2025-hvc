"""Article Fig 4 (cf. original Fig 4): the 120 HVC_RA in chain order after the start pulse, an
enlargement of two successive neurons with the delay between their first spikes, and the burst
statistics of this network against the original's mean +- SD.

Final configuration (configs/final.json, Cm 20 pF), seed 0, start pulse 500 pA x 10 ms (I-07).
Run from code/: ../.venv/bin/python -I scripts/fig4_article.py -> figures/replication_fig4.png
"""
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("HVC_CONFIG", "configs/final.json")
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from calibrate_random import to_kwargs  # noqa: E402
from phase1_seeds import CONFIG  # noqa: E402
from hvcnet.analysis import bursts  # noqa: E402
from hvcnet.evaluate import score, simulate  # noqa: E402

RED = (0.85, 0.0, 0.0)
ORIG = {"spikes": (4.76, 0.48), "dur": (8.12, 0.89)}
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "mathtext.default": "regular"})


def main(seed=0, pair=(30, 31)):
    net, r, sp = simulate(seed=seed, **to_kwargs(CONFIG))
    s = score(net, sp)
    t, V = r["t"], r["V"]
    chain = [int(j) for j in net.chain_order()]
    firsts = np.array([sp[j][0] for j in chain])
    t0, t1 = 45.0, np.ceil((firsts[-1] + 20) / 10) * 10
    win = (t >= t0) & (t <= t1)

    fig = plt.figure(figsize=(7.2, 7.6))
    ax = fig.add_axes([0.06, 0.06, 0.52, 0.89])
    gap, vs = 3.0, 0.036                        # row spacing; mV -> rows (100 mV ~ 1.2 rows)
    base = -gap * np.arange(len(chain))
    for k, j in enumerate(chain):
        ax.plot(t[win], (V[win, j] - V[win, j][0]) * vs + base[k], color=RED, lw=0.4)
    for k in (1, 30, 60, 90, 120):
        ax.text(t0 - 2, base[k - 1], str(k), ha="right", va="center", fontsize=7)
    ax.text(t0 - 14, base[59], r"HVC$_{RA}$ (chain order)", rotation=90, ha="center", va="center")
    ybar = base[-1] - 6
    ax.plot([t1 - 10, t1], [ybar, ybar], "k", lw=1.2)          # 10 ms, as original Fig 4
    ax.text(t1 - 5, ybar - 1.5, "10 ms", ha="center", va="top", fontsize=7)
    ax.set_xlim(t0 - 3, t1 + 2); ax.set_ylim(ybar - 6, base[0] + 6)
    ax.axis("off")
    ax.text(-0.08, 1.0, "A", transform=ax.transAxes, fontweight="bold", fontsize=11)

    # box around the enlarged pair
    a, b = (chain[p - 1] for p in pair)
    bx0, bx1 = sp[a][0] - 3, sp[b][-1] + 3
    by0, by1 = base[pair[1] - 1] - 1.5, base[pair[0] - 1] + 5
    ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fill=False, lw=0.7, ec="k"))

    # B: enlargement
    ins = fig.add_axes([0.64, 0.56, 0.34, 0.36])
    w = (t > sp[a][0] - 6) & (t < sp[b][-1] + 12)
    off = 110.0
    ins.plot(t[w], V[w, a] + off, color=RED, lw=0.9)
    ins.plot(t[w], V[w, b], color=RED, lw=0.9)
    ins.text(t[w][0], V[w, a][0] + off + 6, rf"HVC$_{{RA}}^{{{pair[0]}}}$", fontsize=8, va="bottom")
    ins.text(t[w][0], V[w, b][0] + 6, rf"HVC$_{{RA}}^{{{pair[1]}}}$", fontsize=8, va="bottom")
    d = sp[b][0] - sp[a][0]
    for x in (sp[a][0], sp[b][0]):
        ins.axvline(x, color="0.5", lw=0.6, ls=":")
    ya = V[w, b].min() - 8
    ins.annotate("", xy=(sp[b][0], ya), xytext=(sp[a][0], ya),
                 arrowprops=dict(arrowstyle="<->", lw=0.8, shrinkA=0, shrinkB=0))
    ins.text(sp[b][0] + 1, ya, f"{d:.1f} ms", ha="left", va="center", fontsize=8)
    # scale bars as in the original inset: 25 mV (vertical) and 10 ms (horizontal), L-shaped
    xs = t[w][-1] - 10
    ys = V[w, b].min() + 45
    ins.plot([xs, xs], [ys, ys + 25], "k", lw=1)
    ins.plot([xs, xs + 10], [ys, ys], "k", lw=1)
    ins.text(xs + 0.6, ys + 12.5, "25 mV", ha="left", va="center", fontsize=7)
    ins.text(xs + 5, ys - 3, "10 ms", ha="center", va="top", fontsize=7)
    ins.set_xlim(t[w][0], t[w][-1] + 2)
    ins.axis("off")
    ins.text(-0.02, 1.02, "B", transform=ins.transAxes, fontweight="bold", fontsize=11)
    ax.text(bx1 + 1.5, by1, "B", fontweight="bold", fontsize=8, va="top")

    # C: burst statistics of this network vs the original
    B = [bb for j in chain for bb in bursts(sp[j])]
    n_sp = np.array([len(bb) for bb in B]); dur = np.array([bb[-1] - bb[0] for bb in B])
    for i, (vals, key, lab, bins) in enumerate((
            (n_sp, "spikes", "spikes per burst", np.arange(1.5, 7.5, 1.0)),
            (dur, "dur", "burst duration (ms)", np.arange(4, 14.01, 0.5)))):
        c = fig.add_axes([0.66 + i * 0.18, 0.12, 0.14, 0.3])
        m, sd = ORIG[key]
        c.axvspan(m - sd, m + sd, color="0.88", lw=0)
        c.axvline(m, color="k", lw=0.8, ls="--")
        c.hist(vals, bins=bins, color=RED, alpha=0.85, edgecolor="w", lw=0.4)
        c.axvline(vals.mean(), color=RED, lw=1.2)
        c.set_xlabel(lab)
        c.spines[["top", "right"]].set_visible(False)
        c.set_title(f"{vals.mean():.2f} ± {vals.std():.2f}" if key == "spikes"
                    else f"{vals.mean():.1f} ± {vals.std():.1f} ms", fontsize=7.5, color=RED)
        if i == 0:
            c.set_ylabel("bursts")
            c.text(-0.45, 1.12, "C", transform=c.transAxes, fontweight="bold", fontsize=11)
    fig.text(0.66, 0.035, "red: this network (120 HVC$_{RA}$); dashed line and grey band:\n"
             "original Fig 4 (mean ± SD)", fontsize=6.5, va="top")

    out = ROOT / "figures" / "replication_fig4.png"
    fig.savefig(out, dpi=250)
    print(out, f"delay {d:.2f} ms;", {k: s[k] for k in ("ra_spikes", "ra_dur", "ra_ok", "link_ms")})


if __name__ == "__main__":
    main()

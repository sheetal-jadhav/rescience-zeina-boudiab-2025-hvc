"""Replication figures laid out like the original Figures 2 and 4-13 of Bou Diab et al. (2025):
stacked voltage traces without axes, panel letters, neuron labels HVC_class^index in the
original colours (HVC_RA red, HVC_X blue, HVC_INT black), perturbation labels such as
'g_A (↑)', and scale bars. Neuron indices: RA by chain position, X and INT by index within
their class (1-based); they refer to our network instance, not the original's.

Run after run_final.sh and fig12.py. Writes figures/replication_figN.png."""

import json, os, sys
from multiprocessing import Pool
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("HVC_CONFIG", "configs/final.json")
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from calibrate_random import RANGES, to_kwargs
from phase1_seeds import CONFIG
from hvcnet.evaluate import simulate
from hvcnet.network import AMPA, GABA, build
from hvcnet.params import INT, RA, X

FIG, RES = ROOT / "figures", ROOT / "results"
RED, BLUE, BLACK = (1, 0, 0), (0, 0, 1), (0, 0, 0)
COLOR = {RA: RED, X: BLUE, INT: BLACK}
CLS = {RA: "RA", X: "X", INT: "INT"}
KW = to_kwargs(CONFIG)
T0, T1 = 40.0, 340.0          # display window (ms)
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "mathtext.default": "regular"})


# ---------------------------------------------------------------- drawing helpers
def name(cls, idx):
    return rf"HVC$_{{{CLS[cls]}}}^{{{idx}}}$"


def letter(ax, s):
    ax.text(-0.02, 1.02, s, transform=ax.transAxes, fontweight="bold", fontsize=12, va="bottom")


def stack(ax, t, traces, colors, spacing, lw=0.5, thick=(), vscale=1.0):
    """Stacked voltage traces, first at the top; vscale compresses voltage (1 = mV).
    Returns the y baseline of each trace."""
    win = (t >= T0) & (t <= T1)
    base = []
    for i, (v, c) in enumerate(zip(traces, colors)):
        y0 = -i * spacing
        ax.plot(t[win], (v[win] - v[win][0]) * vscale + y0, color=c, lw=1.6 if i in thick else lw)
        base.append(y0)
    ax.set_xlim(T0, T1 + 5)
    ax.axis("off")
    return base


def scalebar(ax, ms=10, mv=None, x=None, y=None):
    x = T1 - ms if x is None else x
    y = ax.get_ylim()[0] if y is None else y
    ax.plot([x, x + ms], [y, y], "k", lw=1.2)
    ax.text(x + ms / 2, y, f"{ms} ms", ha="center", va="top", fontsize=7)
    if mv:
        ax.plot([x, x], [y, y + mv], "k", lw=1.2)
        ax.text(x - 1, y + mv / 2, f"{mv} mV", ha="right", va="center", fontsize=7)


def ra_stack(ax, net, r, n=120, mark=None, label_rows=(1, 30, 60, 90, 120)):
    chain = net.chain_order()[:n]
    thick = [list(chain).index(mark)] if mark is not None and mark in chain else []
    # original style: each burst about one row tall (100 mV -> ~1.2 rows)
    base = stack(ax, r["t"], [r["V"][:, j] for j in chain], [RED] * len(chain), 3.0, thick=thick,
                 lw=0.45, vscale=0.036)
    for k in label_rows:
        if k <= len(chain):
            ax.text(T0 - 3, base[k - 1], str(k), ha="right", va="center", fontsize=7)
    return chain, base


def class_index(net, j):
    for cls, grp in ((RA, net.chain_order()), (X, net.x), (INT, net.int_)):
        if j in set(int(v) for v in grp):
            return cls, list(int(v) for v in grp).index(j) + 1
    raise KeyError(j)


def save(fig, n):
    out = FIG / f"replication_fig{n}.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(out)


# ---------------------------------------------------------------- simulations
def sim(args):
    seed, per = args
    net, r, sp = simulate(seed=seed, per_neuron=per, **KW)
    return net, {"t": r["t"], "V": r["V"]}, sp


def load(fname):
    return [json.loads(l) for l in open(RES / fname)]


def pick(fname, name):
    """Example for a perturbation: prefer a run whose break is at (or right after) the
    perturbed neuron / its targets; otherwise the first run. Returns (idx, broke)."""
    runs = [x for x in load(fname) if x["name"] == name and x["seed"] == 0]
    broke = [x for x in runs if x["break_pos"] is not None]
    x = (broke or runs)[0]
    return x["idx"], bool(broke)


# ---------------------------------------------------------------- figures
def fig2():
    import fig2_pairs
    res = fig2_pairs.panels(switches=KW["switches"])
    titles = {"A": ("RA -> INT -> X", [(2, BLUE, "HVC$_X$"), (0, RED, "HVC$_{RA}$")], 100),
              "B": ("RA -> INT", [(1, BLACK, "HVC$_{INT}$"), (0, RED, "HVC$_{RA}$")], 50),
              "C": ("INT -> X (pulses)", [(1, BLUE, "HVC$_X$"), (0, BLACK, "HVC$_{INT}$")], 200),
              "D": ("INT -> X (500 ms step)", [(1, BLUE, "HVC$_X$"), (0, BLACK, "HVC$_{INT}$")], 200),
              "E": ("X -> INT", [(1, BLACK, "HVC$_{INT}$"), (0, BLUE, "HVC$_X$")], 100)}
    fig, axs = plt.subplots(5, 1, figsize=(4, 11))
    for ax, (key, (r, _)) in zip(axs, res.items()):
        L = key.split()[0]
        _, traces, ms = titles[L]
        for k, (idx, col, lab) in enumerate(traces):
            v = r["V"][:, idx]
            off = -k * 120
            ax.plot(r["t"], v - v[0] + off, color=col, lw=0.9)
            ax.text(r["t"][0] - 5, off, lab, ha="right", va="center", fontsize=8, color=col)
        ax.axis("off"); letter(ax, f"{L}2")
        x = r["t"][-1] + 0.04 * r["t"][-1]
        y = ax.get_ylim()[0]
        ax.set_xlim(r["t"][0] - 0.02 * r["t"][-1], x + ms * 1.2)
        ax.plot([x, x + ms], [y, y], "k"); ax.text(x + ms / 2, y, f"{ms} ms", ha="center", va="top", fontsize=7)
        ax.plot([x, x], [y, y + 20], "k"); ax.text(x - 2, y + 10, "20 mV", ha="right", va="center", fontsize=7)
    fig.suptitle("Model simulations", y=1.0)
    fig.tight_layout()
    save(fig, 2)


def fig4(base):
    net, r, sp = base
    fig = plt.figure(figsize=(9, 9))
    ax = fig.add_axes([0.06, 0.04, 0.6, 0.92])
    chain, yb = ra_stack(ax, net, r)
    scalebar(ax, 10)
    # inset: two successive RA neurons (positions 30, 31) and their delay, as in the original
    j1, j2 = chain[29], chain[30]
    ax.plot([sp[j1][0] - 2, sp[j1][-1] + 2, sp[j1][-1] + 2, sp[j1][0] - 2, sp[j1][0] - 2],
            [yb[29] + 4, yb[29] + 4, yb[30] - 2, yb[30] - 2, yb[29] + 4], color="k", lw=0.6)
    ins = fig.add_axes([0.7, 0.45, 0.28, 0.25])
    t = r["t"]; w = (t > sp[j1][0] - 8) & (t < sp[j2][-1] + 15)
    ins.plot(t[w], r["V"][w, j1] + 100, color=RED, lw=0.9)
    ins.plot(t[w], r["V"][w, j2], color=RED, lw=0.9)
    d = sp[j2][0] - sp[j1][0]
    ins.annotate("", xy=(sp[j2][0], -90), xytext=(sp[j1][0], -90), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ins.text((sp[j1][0] + sp[j2][0]) / 2, -100, f"{d:.1f} ms", ha="center", va="top", fontsize=8)
    ins.plot([t[w][-1] - 10, t[w][-1]], [-60, -60], "k", lw=1)
    ins.text(t[w][-1] - 5, -63, "10 ms", ha="center", va="top", fontsize=7)
    ins.plot([t[w][-1] - 10, t[w][-1] - 10], [-60, -35], "k", lw=1)
    ins.text(t[w][-1] - 11, -47, "25 mV", ha="right", va="center", fontsize=7)
    ins.axis("off")
    save(fig, 4)


def fig5():
    import fig5_delay
    fig, axs = plt.subplots(1, 2, figsize=(9, 5))
    panels = (("A", "Effect of g$_{AMPA}$ on delay", [(10.0, 10.0), (12.0, 10.0)], "g$_{AMPA}$"),
              ("B", "Effect of g$_A$ on delay", [(10.0, 10.0), (10.0, 13.0)], "g$_A$"))
    for ax, (L, ylab, pairs, sym) in zip(axs, panels):
        rr = [fig5_delay.pair(g, gA) for g, gA in pairs]
        t = rr[0]["t"]; w = (t > 18) & (t < 60)
        ax.plot(t[w], rr[0]["V"][w, 0] + 130, "k", lw=0.9, label="Presynaptic HVC$_{RA}$")
        for res, col, (g, gA) in zip(rr, (RED, BLUE), pairs):
            val = g if sym.startswith("g$_{AMPA") else gA
            ax.plot(t[w], res["V"][w, 1], color=col, lw=0.9,
                    label=f"Postsynaptic HVC$_{{RA}}$, {sym} = {val:.0f} nS")
        pre_peak = fig5_delay.peaks(t, rr[0]["V"][:, 0])[0]
        for k, (res, col) in enumerate(zip(rr, (RED, BLUE))):
            post_peak = fig5_delay.peaks(t, res["V"][:, 1])[0]
            y = 195 + 8 * k
            ax.plot([pre_peak, post_peak], [y, y], color=col, lw=3)
            ax.text(post_peak + 0.5, y, f"{post_peak - pre_peak:.1f} ms", va="center", fontsize=7, color=col)
        ax.axis("off"); letter(ax, L)
        ax.text(17, 40, ylab, rotation=90, ha="right", va="center", fontsize=11, fontweight="bold")
        ax.plot([55, 60], [-100, -100], "k"); ax.text(57.5, -103, "5 ms", ha="center", va="top", fontsize=7)
        ax.plot([55, 55], [-100, -80], "k"); ax.text(54.5, -90, "20 mV", ha="right", va="center", fontsize=7)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), frameon=False, fontsize=8)
    save(fig, 5)


def perturbed_stack(ax, run, mark_ra, label, extra=()):
    net, r, sp = run
    chain, yb = ra_stack(ax, net, r, mark=mark_ra)
    if mark_ra is not None:
        pos = list(chain).index(mark_ra)
        ax.text(T1 + 6, yb[pos], name(RA, pos + 1), color=RED, fontsize=9, va="center")
    y = yb[-1] - 12
    for j in extra:
        cls, k = class_index(net, j)
        v = r["V"][:, j]; win = (r["t"] >= T0) & (r["t"] <= T1)
        ax.plot(r["t"][win], (v[win] - v[win][0]) * 0.15 + y, color=COLOR[cls], lw=0.6)
        ax.text(T0 - 3, y, name(cls, k), color=COLOR[cls], ha="right", va="center", fontsize=9)
        y -= 22
    ax.text((T0 + T1) / 2, y + 2, label, ha="center", va="top", fontsize=11,
            color=COLOR[class_index(net, extra[-1])[0]] if extra else RED)
    scalebar(ax, 10, y=y + 6)


def fig6(runs, picks):
    fig, axs = plt.subplots(1, 2, figsize=(10, 8))
    for ax, L, key, lab in ((axs[0], "A", "6A", "g$_A$ (↑)"), (axs[1], "B", "6B", "g$_{SK}$ (↑)")):
        idx, broke, factor = picks[key]
        perturbed_stack(ax, runs[key], idx, f"{lab}  ×{factor:g}" + ("" if broke else "  (no break)"))
        letter(ax, L)
    save(fig, 6)


def fig7(base):
    net, r, sp = base
    fig, axs = plt.subplots(2, 1, figsize=(7, 9))
    for ax, L, grp, col in ((axs[0], "A", net.int_[:10], BLACK), (axs[1], "B", net.x[:10], BLUE)):
        stack(ax, r["t"], [r["V"][:, j] for j in grp], [col] * 10, 110)
        ax.text(T0 - 6, -5 * 110, "Membrane Potential (mV)", rotation=90, ha="right", va="center")
        letter(ax, L)
    scalebar(axs[1], 10, 40)
    save(fig, 7)


def fig8(base):
    net, r, sp = base
    syn = net.synapses
    # interneuron with the most presynaptic RA+X partners
    best = max((int(j) for j in net.int_), key=lambda j: np.sum((syn.post == j) & (syn.kind == AMPA)))
    pre = syn.pre[(syn.post == best) & (syn.kind == AMPA)]
    ras = sorted([int(p) for p in pre if net.cells.types[p] == RA], key=lambda j: sp[j][0] if len(sp[j]) else 1e9)
    xs = [int(p) for p in pre if net.cells.types[p] == X]
    order = ras + xs + [best]
    fig, ax = plt.subplots(figsize=(8, 1 + 0.8 * len(order)))
    yb = stack(ax, r["t"], [r["V"][:, j] for j in order], [COLOR[net.cells.types[j]] for j in order], 110)
    for j, y in zip(order, yb):
        cls, k = class_index(net, j)
        ax.text(T0 - 3, y, name(cls, k), color=COLOR[cls], ha="right", va="center", fontsize=9)
    ax.text(T0 - 40, yb[len(yb) // 2], "Membrane Potential (mV)", rotation=90, ha="right", va="center")
    scalebar(ax, 10, 20)
    save(fig, 8)


def fig9(runs, picks):
    fig, axs = plt.subplots(1, 2, figsize=(10, 9))
    for ax, L, key, lab in ((axs[0], "A", "9A", "g$_{CaT}$ (↑)"), (axs[1], "B", "9B", "g$_H$ (↑)")):
        idx, broke, factor = picks[key]
        net, r, sp = runs[key]
        syn = net.synapses
        targets = set(syn.post[(syn.pre == idx) & (syn.kind == GABA)].tolist())
        bp = next((j for j in net.chain_order() if j in targets and not len(sp[j])), None)
        perturbed_stack(ax, runs[key], bp, f"{lab}  ×{factor:g}" + ("" if broke else "  (no break)"), extra=[idx])
        letter(ax, L)
    save(fig, 9)


def fig10(base):
    net, r, sp = base
    syn = net.synapses
    xs = [int(x) for x in net.x if np.any((syn.post == x) & (syn.kind == GABA))]
    xj = max(xs, key=lambda j: len(sp[j]))
    ints = [int(i) for i in syn.pre[(syn.post == xj) & (syn.kind == GABA)]]
    fig, axs = plt.subplots(2, 1, figsize=(8, 7))
    order = ints + [xj]
    yb = stack(axs[0], r["t"], [r["V"][:, j] for j in order], [COLOR[net.cells.types[j]] for j in order], 110)
    for j, y in zip(order, yb):
        cls, k = class_index(net, j)
        axs[0].text(T0 - 3, y, name(cls, k), color=COLOR[cls], ha="right", va="center", fontsize=9)
    letter(axs[0], "A")
    # B: overlay on a 60 ms window around the first X spike (cf. original zoom panels)
    late = [x for x in sp[xj] if x > 70.0]
    tx = late[0] if late else 150.0
    w = (r["t"] > tx - 45) & (r["t"] < tx + 15)
    for j in order:
        axs[1].plot(r["t"][w], r["V"][w, j], color=COLOR[net.cells.types[j]], lw=0.8)
    axs[1].axis("off"); letter(axs[1], "B")
    axs[1].plot([tx + 5, tx + 15], [-100, -100], "k"); axs[1].text(tx + 10, -103, "10 ms", ha="center", va="top", fontsize=7)
    axs[1].plot([tx + 5, tx + 5], [-100, -60], "k"); axs[1].text(tx + 4, -80, "40 mV", ha="right", va="center", fontsize=7)
    save(fig, 10)


def fig11(runs, picks):
    fig, axs = plt.subplots(1, 3, figsize=(14, 9))
    for ax, L, key, lab in ((axs[0], "A", "11A", "g$_H$ (↑)"), (axs[1], "B", "11B", "g$_{CaT}$ (↑)"),
                            (axs[2], "C", "11C", "g$_{SK}$ (↓)")):
        idx, broke, factor = picks[key]
        net, r, sp = runs[key]
        syn = net.synapses
        ints = syn.post[(syn.pre == idx) & (syn.kind == AMPA)]
        it = int(max(ints, key=lambda j: len(sp[j]))) if len(ints) else None
        txt = f"{lab}  " + (f"×{factor:g}" if key != "11C" else "= 0") + ("" if broke else "  (no break)")
        perturbed_stack(ax, runs[key], None, txt, extra=([it] if it is not None else []) + [idx])
        letter(ax, L)
    save(fig, 11)


def fig12(example):
    net, r, sp = example
    fig = plt.figure(figsize=(11, 7))
    a = fig.add_axes([0.03, 0.05, 0.45, 0.9]); ra_stack(a, net, r); letter(a, "A"); scalebar(a, 10)
    b = fig.add_axes([0.55, 0.62, 0.43, 0.33]); stack(b, r["t"], [r["V"][:, j] for j in net.int_[:3]], [BLACK] * 3, 110)
    b.text(T0 - 5, -110, "HVC$_{INT}$", rotation=90, ha="right", va="center", fontsize=10); letter(b, "B")
    c = fig.add_axes([0.55, 0.05, 0.43, 0.5]); stack(c, r["t"], [r["V"][:, j] for j in net.x[:5]], [BLUE] * 5, 110)
    c.text(T0 - 5, -220, "HVC$_X$", rotation=90, ha="right", va="center", fontsize=10, color=BLUE); letter(c, "C")
    scalebar(c, 10, 40)
    save(fig, 12)


def fig13():
    data = load("robust_fig13.jsonl")
    # 'accurate' judged on HVC_RA only (X/INT criteria are never met; see text)
    ok = lambda s: "error" not in s and s["ra_fired"] == 120 and s["ra_in_order"] and s["ra_ok"] >= 0.75 * 120
    ionic = [("gA@RA", "HVC$_{RA}$", "g$_A$", BLACK), ("gSK@RA", "HVC$_{RA}$", "g$_{SK}$", (0, 0.45, 0.85)),
             ("gSK@X", "HVC$_X$", "g$_{SK}$", (0, 0.45, 0.85)), ("gH@INT", "HVC$_{INT}$", "g$_H$", (0, 0.65, 0.3)),
             ("gH@X", "HVC$_X$", "g$_H$", (0, 0.65, 0.3)), ("gCaT@INT", "HVC$_{INT}$", "g$_{CaT}$", RED),
             ("gCaT@X", "HVC$_X$", "g$_{CaT}$", RED)]
    synap = [("g_RA_RA", "HVC$_{RA}$\nto\nHVC$_{RA}$", RED), ("g_RA_INT", "HVC$_{RA}$\nto\nHVC$_{INT}$", RED),
             ("g_X_INT", "HVC$_X$\nto\nHVC$_{INT}$", RED), ("g_INT_X", "HVC$_{INT}$\nto\nHVC$_X$", BLACK),
             ("g_INT_RA", "HVC$_{INT}$\nto\nHVC$_{RA}$", BLACK)]
    fig, axs = plt.subplots(2, 1, figsize=(9, 9))
    for ax, L, items in ((axs[0], "A", [(k, lab, c) for k, lab, _, c in ionic]), (axs[1], "B", synap)):
        for i, (key, lab, col) in enumerate(items, 1):
            runs = [x for x in data if x["tag"] == f"fig13:{key}"]
            # a tested value counts as allowed only if every seed passes
            values = sorted({x["point"][key] for x in runs})
            good = [v for v in values if all(ok(x["score"]) for x in runs if x["point"][key] == v)]
            bad = [v for v in values if v not in good]
            lo, hi = RANGES[key]
            ax.add_patch(plt.Rectangle((i - 0.3, lo), 0.6, hi - lo, color=(0.75, 0.8, 0.95), alpha=0.7, lw=0))
            ax.scatter([i] * len(bad), bad, s=14, facecolor="none", edgecolor="0.55", lw=0.8)
            ax.scatter([i] * len(good), good, s=18, color=col)
        ax.set_xticks(range(1, len(items) + 1))
        ax.set_xticklabels([lab for _, lab, *_ in items], fontsize=8)
        ax.set_ylabel("nS"); letter(ax, L)
    from matplotlib.lines import Line2D
    axs[0].legend(handles=[Line2D([], [], marker="o", ls="", color=c, label=l) for l, c in
                           (("g$_A$", BLACK), ("g$_{SK}$", (0, 0.45, 0.85)), ("g$_H$", (0, 0.65, 0.3)), ("g$_{CaT}$", RED))]
                  + [plt.Rectangle((0, 0), 1, 1, color=(0.75, 0.8, 0.95), label="original range"),
                     Line2D([], [], marker="o", ls="", mfc="none", mec="0.6", label="tested, rejected")],
                  fontsize=7, loc="upper right")
    axs[1].legend(handles=[Line2D([], [], marker="o", ls="", color=c, label=l) for l, c in
                           (("g$_{AMPA}$", RED), ("g$_{GABA}$", BLACK))], fontsize=7, loc="upper right")
    save(fig, 13)


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    fu = "fig6_9_11_followup.jsonl"
    picks = {}
    for key, fname, name_, factor in (("6A", fu, "fig6A_RA_gA_x20", 20), ("6B", fu, "fig6B_RA_gSK_x15", 15),
                                      ("9A", "fig6_9_11.jsonl", "fig9A_INT_gCaT_x10", 10),
                                      ("9B", "fig6_9_11.jsonl", "fig9B_INT_gH_x10", 10),
                                      ("11A", "fig6_9_11.jsonl", "fig11A_X_gH_x10", 10),
                                      ("11B", "fig6_9_11.jsonl", "fig11B_X_gCaT_x15", 15),
                                      ("11C", "fig6_9_11.jsonl", "fig11C_X_gSK_0", 0)):
        idx, broke = pick(fname, name_)
        picks[key] = (idx, broke, factor)
    attr = {"6A": "gA", "6B": "gSK", "9A": "gCaT", "9B": "gH", "11A": "gH", "11B": "gCaT", "11C": "gSK"}
    jobs = {"base": (0, None)}
    for key, (idx, _, factor) in picks.items():
        jobs[key] = (0, {attr[key]: {idx: ("set", 0.0) if key == "11C" else ("mul", float(factor))}})
    f12 = load("fig12.jsonl")
    ex = next((x for x in f12 if not (x["score"]["ra_fired"] == 120 and x["score"]["ra_in_order"])), f12[0])
    with Pool(8) as pool:
        out = dict(zip(jobs, pool.map(sim, list(jobs.values()))))
    # Fig 6 follow-up perturbations were run with INT->RA at 5 nS; redo those two to match
    for key in ("6A", "6B"):
        kw = dict(KW); kw["spec"] = to_kwargs(dict(CONFIG, g_INT_RA=5.0))["spec"]
        idx, _, factor = picks[key]
        net, r, sp = simulate(seed=0, per_neuron={attr[key]: {idx: ("mul", float(factor))}}, **kw)
        out[key] = (net, {"t": r["t"], "V": r["V"]}, sp)
    base = out["base"]
    fig2(); fig4(base); fig5(); fig6(out, picks); fig7(base); fig8(base); fig9(out, picks)
    fig10(base); fig11(out, picks)
    # rebuild the Fig 12 example with the same per-neuron X draws as fig12.job (same RNG order)
    k = ex["run"]
    rng = np.random.default_rng(12000 + k)
    net = build(KW["spec"], seed=ex["seed"])
    per = {a: {int(i): ("set", float(rng.uniform(*RANGES[f"{a}@X"]))) for i in np.where(net.cells.types == X)[0]}
           for a in ("gCaT", "gSK", "gH")}
    fig12(sim((ex["seed"], per)))
    fig13()

"""Article figures from results/*.jsonl (final configuration, accurate tolerances).

Run after run_final.sh. Writes figures/article_*.png and prints the numbers quoted in the text.
"""

import collections, json, os, sys
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
from hvcnet.analysis import burst_stats, spike_times
from hvcnet.evaluate import score, simulate
from hvcnet.network import AMPA, GABA, build

RES, FIG = ROOT / "results", ROOT / "figures"
load = lambda name: [json.loads(l) for l in open(RES / name)]


def ok_chain(s):
    return "error" not in s and s["ra_fired"] == 120 and s["ra_in_order"]


def fig_sequence():
    net, r, sp = simulate(seed=0, **to_kwargs(CONFIG))
    chain = net.chain_order()
    seeds = [x["score"] for x in load("robust_seeds.jsonl")]
    fig = plt.figure(figsize=(10, 7))
    gs = fig.add_gridspec(3, 3, height_ratios=[4, 1, 1])
    ax = fig.add_subplot(gs[0, :2])
    for i, j in enumerate(chain):
        ax.plot(sp[j], np.full(len(sp[j]), i), "|", color="crimson", ms=2.5)
    ax.set_ylabel("HVC$_{RA}$ (chain order)"); ax.set_title("A  seed 0")
    for row, grp, col, lab in ((1, net.x, "royalblue", "HVC$_X$"), (2, net.int_, "k", "HVC$_{INT}$")):
        a = fig.add_subplot(gs[row, :2], sharex=ax)
        for i, j in enumerate(grp):
            a.plot(sp[j], np.full(len(sp[j]), i), "|", color=col, ms=2)
        a.set_ylabel(lab)
    a.set_xlabel("time (ms)")
    for k, (key, lab, paper) in enumerate((("ra_spikes", "spikes / burst", 4.76),
                                            ("ra_dur", "burst duration (ms)", 8.12))):
        b = fig.add_subplot(gs[k, 2]) if k == 0 else fig.add_subplot(gs[1:, 2])
        v = [s[key] for s in seeds]
        b.hist(v, bins=12, color="gray"); b.axvline(paper, color="crimson", ls="--", label="original")
        b.set_xlabel(lab); b.legend(fontsize=7)
    fig.suptitle(f"Sequence propagation (Fig 4): {sum(ok_chain(s) for s in seeds)}/{len(seeds)} "
                 "networks propagate through all 120 HVC$_{RA}$ in order")
    fig.tight_layout(); fig.savefig(FIG / "article_fig4_sequence.png", dpi=150)
    m = lambda k: (np.mean([s[k] for s in seeds]), np.std([s[k] for s in seeds]))
    print("FIG4", {k: m(k) for k in ("ra_spikes", "ra_dur", "ra_ok", "link_ms", "x_ok",
                                      "x_silent", "int_spikes_med")})
    return net, r, sp


def fig_x_int(net, r, sp):
    """Example HVC_X and an interneuron presynaptic to it (cf. original Fig 10)."""
    syn = net.synapses
    cand = [int(x) for x in net.x if np.any((syn.post == x) & (syn.kind == GABA))]
    xj = max(cand, key=lambda j: len(sp[j]))
    ints = syn.pre[(syn.post == xj) & (syn.kind == GABA)]
    fig, axs = plt.subplots(len(ints) + 1, 1, figsize=(9, 2 + 1.4 * len(ints)), sharex=True)
    for a, j in zip(axs, list(ints) + [xj]):
        a.plot(r["t"], r["V"][:, j], lw=0.7, color="k" if j in ints else "royalblue")
        a.set_ylabel(("INT " if j in ints else "X ") + str(int(j)))
    axs[-1].set_xlabel("time (ms)")
    fig.suptitle("HVC$_X$ and its presynaptic interneuron(s): single rebound spikes, not bursts "
                 "(cf. original Figs 7B, 10)")
    fig.tight_layout(); fig.savefig(FIG / "article_fig10_x_int.png", dpi=150)


def fig_perturbations():
    nets = {}
    rows = []
    for fname, label, cfg in (("fig6_9_11.jsonl", "INT$\\to$RA as configured", CONFIG),
                              ("fig6_9_11_followup.jsonl", "INT$\\to$RA = 5 nS", dict(CONFIG, g_INT_RA=5.0))):
        G = collections.defaultdict(list)
        for x in load(fname):
            if x["name"] != "baseline":
                G[x["name"]].append(x["break_pos"] is not None)
        for name, v in G.items():
            rows.append((label, name, np.mean(v), len(v)))
    names = sorted({r[1] for r in rows}, key=lambda n: (int(n[3:].split("_")[0].rstrip("ABC")), n))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    w = 0.4
    for k, label in enumerate(("INT$\\to$RA as configured", "INT$\\to$RA = 5 nS")):
        vals = [next((r[2] for r in rows if r[0] == label and r[1] == n), np.nan) for n in names]
        ax.bar(np.arange(len(names)) + (k - 0.5) * w, vals, w, label=label)
    ax.set_xticks(range(len(names))); ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("fraction of runs where the chain breaks"); ax.set_ylim(0, 1.05)
    ax.set_title("Single-neuron perturbations (original Figs 6, 9, 11 each show one break)")
    ax.legend(); fig.tight_layout(); fig.savefig(FIG / "article_fig6_9_11_perturbations.png", dpi=150)
    for r_ in rows:
        print("PERT", r_)


def fig_ranges():
    G = collections.defaultdict(list)
    for x in load("robust_fig13.jsonl"):
        key = x["tag"].split(":", 1)[1]
        G[key].append((x["point"][key], ok_chain(x["score"]),
                       x["score"].get("ra_ok", np.nan) / 120 if "error" not in x["score"] else 0))
    keys = list(RANGES)
    fig, axs = plt.subplots(3, 4, figsize=(13, 8))
    for ax, key in zip(axs.flat, keys):
        v = sorted(G[key])
        xs = sorted({a for a, _, _ in v})
        chain = [np.mean([c for a, c, _ in v if a == x]) for x in xs]
        raok = [np.mean([o for a, _, o in v if a == x]) for x in xs]
        lo, hi = RANGES[key]
        ax.axvspan(lo, hi, color="0.88", label="published range")
        ax.plot(xs, chain, "o-k", label="chain complete")
        ax.plot(xs, raok, "s--", color="crimson", label="RA criterion")
        ax.set_title(key, fontsize=9); ax.set_ylim(-0.05, 1.05)
        print("FIG13", key, [(round(x, 2), round(c, 2), round(o, 2)) for x, c, o in zip(xs, chain, raok)])
    axs.flat[0].legend(fontsize=7)
    fig.suptitle("Fig 13: one conductance varied at a time (others at the final configuration)")
    fig.tight_layout(); fig.savefig(FIG / "article_fig13_ranges.png", dpi=150)


def fig_numerics():
    sol = load("robust_solver.jsonl")
    ref = {x["seed"]: np.array([np.nan if v is None else v for v in x["firsts"]])
           for x in sol if x["method"] == "rk45_1e-6"}
    meths = ("rk45_1e-3", "rk4_0.025", "rk4_0.01")
    fig, axs = plt.subplots(1, 3, figsize=(13, 4))
    for m in meths:
        for x in sol:
            if x["method"] == m:
                f = np.array([np.nan if v is None else v for v in x["firsts"]])
                axs[0].plot(np.abs(f - ref[x["seed"]]), lw=0.8,
                            color={"rk45_1e-3": "crimson", "rk4_0.025": "orange", "rk4_0.01": "green"}[m],
                            label=m if x["seed"] == 0 else None)
    axs[0].set_xlabel("chain position"); axs[0].set_ylabel("|Δ first-spike time| vs RK45 1e-6 (ms)")
    axs[0].set_yscale("symlog", linthresh=0.01); axs[0].legend(fontsize=7)
    allm = ("rk45_1e-3", "rk45_1e-6", "rk4_0.025", "rk4_0.01")
    du = [[x["score"]["ra_dur"] for x in sol if x["method"] == m] for m in allm]
    axs[1].boxplot(du, labels=allm); axs[1].set_ylabel("RA burst duration (ms)")
    axs[1].axhline(8.12, color="crimson", ls="--", lw=0.8); axs[1].tick_params(axis="x", rotation=30)
    nz = load("robust_noise.jsonl")
    sig = sorted({x["sigma"] for x in nz})
    axs[2].plot(sig, [np.mean([ok_chain(x["score"]) for x in nz if x["sigma"] == s]) for s in sig], "o-k", label="chain complete")
    axs[2].plot(sig, [np.mean([x["score"]["ra_ok"] / 120 for x in nz if x["sigma"] == s]) for s in sig], "s--", color="crimson", label="RA criterion")
    axs[2].set_xscale("symlog", linthresh=5); axs[2].set_xlabel("noise σ (pA·ms$^{1/2}$)"); axs[2].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "article_numerics_noise.png", dpi=150)
    for m in allm:
        S = [x["score"] for x in sol if x["method"] == m]
        print("SOLVER", m, {k: round(float(np.mean([s[k] for s in S])), 3) for k in ("ra_spikes", "ra_dur", "ra_ok", "link_ms")})
    for s in sig:
        S = [x["score"] for x in nz if x["sigma"] == s]
        print("NOISE", s, sum(ok_chain(x) for x in S), "/", len(S), round(float(np.mean([x["ra_ok"] for x in S])), 1))


def summaries():
    for fname in ("robust_pern.jsonl", "robust_noX.jsonl"):
        S = [x["score"] for x in load(fname)]
        print("SUMMARY", fname, "chain", sum(ok_chain(s) for s in S), "/", len(S),
              {k: round(float(np.nanmean([s[k] for s in S])), 2) for k in ("ra_ok", "ra_spikes", "ra_dur", "int_spikes_med")})


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    net, r, sp = fig_sequence()
    fig_x_int(net, r, sp)
    fig_perturbations()
    fig_ranges()
    fig_numerics()
    summaries()

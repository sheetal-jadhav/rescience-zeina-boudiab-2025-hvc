"""Fig 5: delay between successive RA bursts vs gAMPA (A) and gA (B), two-cell RA -> RA.

Paper values: (A) gAMPA 10 vs 12 nS with gA fixed; (B) gA 10 vs 13 nS with gAMPA 10 nS.
Delay = first-spike peak (pre) to first-spike peak (post), as in the Fig 5 bars. The
presynaptic RA is driven like the network's first neuron (500 pA, 10 ms). Besides the paper's
two values per panel, both parameters are swept to give full curves."""

import json, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from calibrate_random import to_kwargs
from phase1_seeds import CONFIG
from hvcnet import RA, Cells, Model, Synapses, pulses, run_rk45, settle

KW = to_kwargs(CONFIG)
RA_GA, RA_GSK = CONFIG["gA@RA"], CONFIG["gSK@RA"]


def peaks(t, v, thr=0.0):
    up = np.where((v[:-1] < thr) & (v[1:] >= thr))[0]
    out = []
    for i in up:
        j = i + np.argmax(v[i:i + 100])   # 1 ms window at dt 0.01
        out.append(t[j])
    return np.array(out)


def pair(g_ampa, gA_post, gA_pre=RA_GA):
    cells = Cells([RA, RA])
    cells.gA[:] = [gA_pre, gA_post]
    cells.gSK[:] = RA_GSK
    m = Model(cells, Synapses([0], [1], [g_ampa], [0]), switches=KW["switches"])
    y0 = settle(m, m.initial_state(), 500.0)
    m.stimulus = pulses(2, [(0, 20.0, 30.0, 500.0)])
    r = run_rk45(m, y0, 90.0, dt_out=0.01, max_step=0.05, rtol=1e-6, atol=1e-9)
    pre, post = (peaks(r["t"], r["V"][:, k]) for k in (0, 1))
    delay = post[0] - pre[0] if len(pre) and len(post) else np.nan
    return {"g_ampa": g_ampa, "gA_post": gA_post, "pre_spikes": len(pre),
            "post_spikes": len(post), "delay_ms": delay, "t": r["t"], "V": r["V"]}


def main():
    out_dir = HERE.parents[1]
    res = {"A": [pair(g, 10.0) for g in (10.0, 12.0)],
           "B": [pair(10.0, gA) for gA in (10.0, 13.0)],
           "sweep_gAMPA": [pair(g, 10.0) for g in np.arange(6.0, 36.0, 2.0)],
           "sweep_gA": [pair(10.0, gA) for gA in np.arange(1.0, 15.5, 1.0)]}

    fig, axs = plt.subplots(2, 2, figsize=(10, 7))
    for ax, key, lab in ((axs[0, 0], "A", "gAMPA"), (axs[0, 1], "B", "gA")):
        for r, c in zip(res[key], ("red", "blue")):
            ax.plot(r["t"], r["V"][:, 1], c, lw=0.9,
                    label=f"post, {lab}={r['g_ampa'] if key == 'A' else r['gA_post']:.0f} nS: "
                          f"delay {r['delay_ms']:.2f} ms, {r['post_spikes']} spikes")
        ax.plot(res[key][0]["t"], res[key][0]["V"][:, 0] + 120, "k", lw=0.8, label="pre (+120 mV)")
        ax.set_xlim(15, 60); ax.legend(fontsize=7); ax.set_title(f"Fig 5{key}")
    for ax, key, xk, xl in ((axs[1, 0], "sweep_gAMPA", "g_ampa", "gAMPA (nS), gA=10"),
                            (axs[1, 1], "sweep_gA", "gA_post", "postsynaptic gA (nS), gAMPA=10")):
        x = [r[xk] for r in res[key]]
        ax.plot(x, [r["delay_ms"] for r in res[key]], "o-k")
        ax.set_xlabel(xl); ax.set_ylabel("delay (ms)")
        ax2 = ax.twinx(); ax2.plot(x, [r["post_spikes"] for r in res[key]], "s--", color="gray")
        ax2.set_ylabel("post spikes", color="gray")
    fig.tight_layout()
    fig.savefig(out_dir / "figures/phase1_fig5_delay.png", dpi=100)

    summary = {k: [{kk: (None if isinstance(vv, float) and np.isnan(vv) else vv)
                    for kk, vv in r.items() if kk not in ("t", "V")} for r in v]
               for k, v in res.items()}
    json.dump(summary, open(out_dir / "results/fig5_delay.json", "w"), indent=1, default=float)
    for k in ("A", "B"):
        for r in summary[k]:
            print(k, r)


if __name__ == "__main__":
    main()

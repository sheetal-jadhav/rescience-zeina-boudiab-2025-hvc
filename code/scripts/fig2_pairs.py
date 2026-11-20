"""Phase-1 Fig 2: paired/triplet recordings of Mooney & Prather (2005) as in Bou Diab Fig 2.

Protocols from the Fig 2 legend: 10 ms, 0.5 nA pulses (A, B, C, E) or a 500 ms, 0.5 nA step (D).
Pulse timing is read off the figure (spacing ~100 ms in A/E, ~150 ms in C, ~60 ms in B).
Synaptic conductances: the network defaults (the paper doesn't give pair values; I-06).
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hvcnet import INT, RA, X, Cells, Model, Synapses, pulses, run_rk45, settle
from hvcnet.network import AMPA, GABA
from hvcnet.params import SYNAPSE_G

AMP, DUR = 500.0, 10.0


def circuit(types, edges, stim, t_end, g=SYNAPSE_G, switches=None):
    names = {RA: "RA", X: "X", INT: "INT"}
    pre, post, gg, kind = [], [], [], []
    for a, b in edges:
        pre.append(a); post.append(b)
        gg.append(g[(names[types[a]], names[types[b]])])
        kind.append(GABA if types[a] == INT else AMPA)
    kw = {"switches": switches} if switches else {}
    m = Model(Cells(types), Synapses(pre, post, gg, kind), **kw)
    y0 = settle(m, m.initial_state(), 800.0)
    m.stimulus = pulses(len(types), stim)
    return run_rk45(m, y0, t_end, dt_out=0.05, max_step=0.1, rtol=1e-6, atol=1e-9)


def panels(switches=None):
    train = lambda idx, t0, n, isi: [(idx, t0 + k * isi, t0 + k * isi + DUR, AMP) for k in range(n)]
    return {
        "A  RA -> INT -> X": (circuit([RA, INT, X], [(0, 1), (1, 2)], train(0, 50, 4, 100), 450,
                                      switches=switches), [2, 0]),
        "B  RA -> INT": (circuit([RA, INT], [(0, 1)], train(0, 30, 2, 60), 160,
                                 switches=switches), [1, 0]),
        "C  INT -> X (pulses)": (circuit([INT, X], [(0, 1)], train(0, 100, 4, 150), 900,
                                         switches=switches), [1, 0]),
        "D  INT -> X (500 ms step)": (circuit([INT, X], [(0, 1)], [(0, 200, 700, AMP)], 1000,
                                              switches=switches), [1, 0]),
        "E  X -> INT": (circuit([X, INT], [(0, 1)], train(0, 50, 4, 100), 450,
                                switches=switches), [1, 0]),
    }


def main(out="../figures/phase1_fig2_pairs.png"):
    res = panels()
    fig, axs = plt.subplots(len(res), 1, figsize=(7, 13))
    for ax, (title, (r, order)) in zip(axs, res.items()):
        post, pre = order
        v_post = r["V"][:, post]
        ax.plot(r["t"], v_post - v_post[0] + 20, "C0", lw=1, label="postsynaptic (offset)")
        ax.plot(r["t"], r["V"][:, pre], "k", lw=0.8, label="stimulated")
        rest = r["V"][0, post]
        ax.set_title(f"{title}: post rest {rest:.1f} mV, max deflection "
                     f"{np.ptp(v_post[r['t'] > 20]):.1f} mV", fontsize=9)
    axs[-1].set_xlabel("time (ms)")
    fig.tight_layout()
    fig.savefig(out, dpi=100)
    print(out)


if __name__ == "__main__":
    main()

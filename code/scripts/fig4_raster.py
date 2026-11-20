"""Phase-1 Fig 4-style raster: HVC(RA) in chain order, plus X and INT (seed and duration as args)."""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hvcnet import Model, pulses, run_rk45, settle
from hvcnet.analysis import burst_stats, spike_times
from hvcnet.network import build


def main(seed=0, t_end=400.0, out="../figures/phase1_fig4_raster.png"):
    net = build(seed=seed)
    m = Model(net.cells, net.synapses)
    y0 = settle(m, m.initial_state(), 500.0)
    m.stimulus = pulses(net.cells.N, [(net.first_ra, 50.0, 60.0, 500.0)])   # I-07 [ours]
    r = run_rk45(m, y0, t_end)
    sp = spike_times(r["t"], r["V"])
    chain = net.chain_order()
    counts, durs = burst_stats([sp[j] for j in chain])

    fig, axs = plt.subplots(3, 1, figsize=(9, 9), sharex=True,
                            gridspec_kw={"height_ratios": [4, 1, 1]})
    for row, groups, color in ((0, chain, "crimson"), (1, net.x, "royalblue"), (2, net.int_, "k")):
        for i, j in enumerate(groups):
            axs[row].plot(sp[j], np.full(len(sp[j]), i), "|", color=color, ms=3)
    axs[0].set_ylabel("HVC(RA), chain order")
    axs[1].set_ylabel("HVC(X)")
    axs[2].set_ylabel("HVC(INT)")
    axs[2].set_xlabel("time (ms)")
    axs[0].set_title(f"Phase 1 (text only), seed {seed}: RA bursts {counts.mean():.2f}±{counts.std():.2f} "
                     f"spikes, {durs.mean():.1f}±{durs.std():.1f} ms")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(out)


if __name__ == "__main__":
    main(*(float(a) if i else int(a) for i, a in enumerate(sys.argv[1:3])))

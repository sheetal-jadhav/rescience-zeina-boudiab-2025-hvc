"""Fig 2 as connected pairs/triplets, with synaptic conductances calibrated to the original
model column (Bou Diab et al. calibrated Fig 2 "by eye"; the values are not reported, I-19/I-23).

Targets, measured from the original Fig 2 model column with its scale bars (issues log, I-24):
  C2  INT->X  X IPSP ~4.0 mV per INT spike            -> fitted g_INT->X
  E2  X->INT  INT fires once per X spike               -> g_X->INT = middle of the one-spike range
  A2  RA->INT INT fires once per RA spike (needed for the disynaptic X IPSP)
                                                       -> g_RA->INT = middle of the one-spike range
  B2  RA->INT first INT EPSP ~6.5 mV, subthreshold     -> fitted g_RA->INT (a different pair; Mooney
                                                          & Prather saw both sub- and suprathreshold
                                                          RA->INT pairs, their Fig 4A)
  Not fitted (predictions): A2 X IPSP (~4.7 mV) and D2 X hyperpolarisation (~4.7-5 mV), both
  from the C2 value of g_INT->X; B2's spike on the second pulse.

Presynaptic stimulus, two protocols (as in fig2_single_cells.py): stated 0.5 nA, and the Mooney &
Prather procedure (one spike per pulse: RA 150, INT 250, X 500 pA; D2 145 pA for 820 ms).
-> figures/replication_fig2_pairs.png ; numbers printed.
Run from code/:  ../.venv/bin/python -I scripts/fig2_pairs_mp.py
"""
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hvcnet import INT, RA, X  # noqa: E402
from hvcnet.params import SYNAPSE_G  # noqa: E402
import fig2_pairs as fp  # noqa: E402  (circuit(): cells + AMPA/GABA synapses, settled, RK45 1e-6/1e-9)

warnings.filterwarnings("ignore", category=RuntimeWarning)
FIG = Path(__file__).resolve().parents[2] / "figures"
COL = {RA: "#d62728", X: "#1f4fd6", INT: "k"}
NAME = {RA: "HVC$_{RA}$", X: "HVC$_X$", INT: "HVC$_{INT}$"}

# Calibrated pair conductances (nS); network values in SYNAPSE_G for comparison
G_INT_X = 10.0      # C2: X IPSP 4.0 mV (0.40 mV/nS, linear over 0.5-12 nS)
G_X_INT = 11.0      # E2: one INT spike per X spike for 6.5-16 nS (2 spikes from 18 nS)
G_RA_INT_A = 25.0   # A2: one INT spike per RA spike for 16-35 nS (0 below 16, 2 from 45)
G_RA_INT_B = 7.4    # B2: INT EPSP 6.5 mV (0.88 mV/nS), subthreshold

STATED = {RA: 500.0, INT: 500.0, X: 500.0}
MP = {RA: 150.0, INT: 250.0, X: 500.0}


def g(**kw):
    d = dict(SYNAPSE_G)
    for k, v in kw.items():
        d[tuple(k.split("_"))] = v
    return d


def train(idx, t0, n, isi, amp):
    return [(idx, t0 + k * isi, t0 + k * isi + 10.0, amp) for k in range(n)]


def panels(amp, step):
    """(label, types, edges, stim, t_end, g, (post index, pre index), (time bar, post mV, pre mV))"""
    return [
        ("A2", [RA, INT, X], [(0, 1), (1, 2)], train(0, 50, 4, 100, amp[RA]), 450,
         g(RA_INT=G_RA_INT_A, INT_X=G_INT_X), (2, 0), (100, 10, 45)),
        ("B2", [RA, INT], [(0, 1)], train(0, 30, 2, 115, amp[RA]), 210,
         g(RA_INT=G_RA_INT_B), (1, 0), (50, 20, 20)),
        ("C2", [INT, X], [(0, 1)], train(0, 100, 4, 190, amp[INT]), 950,
         g(INT_X=G_INT_X), (1, 0), (200, 4, 40)),
        ("D2", [INT, X], [(0, 1)], [(0, 200, 200 + step[1], step[0])], 300 + step[1],
         g(INT_X=G_INT_X), (1, 0), (200, 4, 30)),
        ("E2", [X, INT], [(0, 1)], train(0, 50, 4, 100, amp[X]), 450,
         g(X_INT=G_X_INT), (1, 0), (100, 40, 40)),
    ]


def spikes(t, V):
    return t[1:][(V[:-1] < 0) & (V[1:] >= 0)]


def measure(lab, r, stim, post, pre):
    t = r["t"]; Vpo = r["V"][:, post]; Vpr = r["V"][:, pre]
    spr = spikes(t, Vpr); spo = spikes(t, Vpo)
    if lab == "D2":
        a, b = stim[0][1], stim[0][2]
        base = np.interp(a, t, Vpo); w = (t > a + 100) & (t < b)
        return (f"pre {((spr >= a) & (spr < b)).sum()} spikes ({((spr >= a) & (spr < b)).sum() / (b - a) * 1e3:.0f} Hz); "
                f"post mean {np.mean(Vpo[w]) - base:+.2f} mV, {((spo >= a) & (spo < b)).sum()} post spikes in step")
    pre_n, post_n, amps = [], [], []
    for _, a, b, _ in stim:
        w = (t >= a) & (t < a + 70); base = np.interp(a, t, Vpo)
        pre_n.append(int(((spr >= a) & (spr < a + 70)).sum()))
        post_n.append(int(((spo >= a) & (spo < a + 70)).sum()))
        amps.append(Vpo[w].max() - base if lab in ("B2", "E2") else Vpo[w].min() - base)
    return (f"pre spikes/pulse {pre_n}; post spikes/pulse {post_n}; "
            f"post PSP {np.round(amps, 2).tolist()} mV")


def draw(ax, t, Vpost, Vpre, cpost, cpre, bars):
    """Two traces stacked as in the original: each scaled to its own vertical bar (1 bar = 1 unit)."""
    ms, mv_post, mv_pre = bars
    yp = (Vpost - Vpost[0]) / mv_post
    yq = (Vpre - Vpre[0]) / mv_pre
    CLIP = 3.0                                     # post trace cut at 3 scale bars above rest
    yp_shown = np.minimum(yp, CLIP)
    top = yq.max() + 0.5 - yp_shown.min()          # post trace's lowest point sits above pre's peak
    ax.plot(t, yp_shown + top, color=cpost, lw=0.9)
    if yp.max() > CLIP:
        i = np.argmax(yp)
        ax.text(t[i], CLIP + top, " (spike truncated)", fontsize=6, color=cpost, va="bottom")
    ax.plot(t, yq, color=cpre, lw=0.9)
    x0 = t[-1] + 0.03 * t[-1]
    ax.plot([x0, x0], [0.3, 1.3], "k", lw=1.1)
    ax.text(x0 + 0.01 * t[-1], 0.8, f"{mv_post}, {mv_pre} mV" if mv_post != mv_pre else f"{mv_pre} mV",
            fontsize=6.5, va="center")
    ax.plot([x0 - ms, x0], [-0.4, -0.4], "k", lw=1.1)
    ax.text(x0 - ms / 2, -0.5, f"{ms} ms", ha="center", va="top", fontsize=6.5)
    ax.set_xlim(t[0], x0 + 0.2 * t[-1]); ax.axis("off")


def main():
    cols = [("Stated 0.5 nA", STATED, (500.0, 500.0)), ("Mooney & Prather procedure", MP, (145.0, 820.0))]
    fig, axs = plt.subplots(5, 2, figsize=(9, 12))
    print("Calibrated g (nS): INT->X %.1f, X->INT %.1f, RA->INT %.1f (A2) / %.1f (B2); network: %s"
          % (G_INT_X, G_X_INT, G_RA_INT_A, G_RA_INT_B, SYNAPSE_G))
    for c, (title, amp, step) in enumerate(cols):
        print(f"\n== {title}")
        for k, (lab, types, edges, stim, t_end, gg, (post, pre), bars) in enumerate(panels(amp, step)):
            r = fp.circuit(types, edges, stim, t_end, g=gg)
            m = measure(lab, r, stim, post, pre)
            print(f"{lab}: {m}")
            ax = axs[k, c]
            draw(ax, r["t"], r["V"][:, post], r["V"][:, pre], COL[types[post]], COL[types[pre]], bars)
            ax.set_title(f"{lab}  {NAME[types[pre]]} -> {NAME[types[post]]}"
                         + (f"   ({title})" if k == 0 else ""), fontsize=8, loc="left")
    fig.suptitle("Fig 2 pairs, calibrated synapses: stated stimulus vs Mooney & Prather procedure",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "replication_fig2_pairs.png", dpi=200)


if __name__ == "__main__":
    main()

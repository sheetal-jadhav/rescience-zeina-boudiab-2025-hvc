"""Fig 2 as single cells (no synapses): each panel's *stimulated* cell alone, our model (code/hvcnet).

figures/replication_fig2_single.png, two columns:
  Stated protocol (left): the currents Bou Diab et al. state for the model, 0.5 nA (10 ms pulses in
    A, B, C, E; a 500 ms step in D).
  Mooney & Prather protocol (right): their Methods say "current amplitudes and/or the resting
    membrane potential of the trigger cell were adjusted to elicit only a single action potential
    per pulse". Pulse amplitude = middle of our cell's one-spike range (RA 110-200 -> 150 pA;
    INT 130-370 -> 250 pA; X >= 190 -> 500 pA, unchanged). D2 step: 145 pA for 820 ms, the
    amplitude giving the original D2's ~60 Hz (50 spikes) over its drawn duration (~820 ms; the
    text says 500 ms). Holding current alone cannot give RA one spike at 0.5 nA (0 to -60 pA: always
    3 spikes), so amplitude is the adjusted quantity.
Pulse spacing is read off the original panels (A 100, B 115, C 190, E 100 ms).

figures/fig2_code_protocols.png: the authors' Fig 2 code protocols (Figure 2 Source Code 1-4):
X +150 pA, X -120 pA, RA +200 pA, INT +75 pA steps, exactly as in their files (their initial
conditions, no settling); left our cells, right their cells (Python port in
fig2_cell_excitability.py, which includes I_KNa and I_NaP).
Run from code/:  ../.venv/bin/python -I scripts/fig2_single_cells.py
"""
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hvcnet import INT, RA, X, Cells, Model, pulses, run_rk45, settle  # noqa: E402
import fig2_cell_excitability as port  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)  # exp overflow in the steep s-gate
FIG = Path(__file__).resolve().parents[2] / "figures"
AMP, DUR = 500.0, 10.0
COL = {RA: "#d62728", X: "#1f4fd6", INT: "k"}
NAME = {RA: "HVC$_{RA}$", X: "HVC$_X$", INT: "HVC$_{INT}$"}

# Their Fig 2 code cells (Source Code 1 = X, 2 = X variant, 3 = RA, 4 = INT)
THEIR = {
    1: dict(port.COMMON, gNa=450, gK=50, gSK=6, gKNa=40, gCaT=2.65, gH=4, gA=5, C=100, kr=0.3,
            V0=-70.6, rs_factor=1.0),
    2: dict(port.COMMON, gNa=450, gK=1700, gSK=1, gKNa=40, gCaT=2.65, gH=4, gA=5, C=100, kr=0.3,
            V0=-67.5, rs_factor=1.0),
    3: port.THEIR_RA,
    4: port.THEIR_INT,
}
THEIR_OF = {RA: 3, INT: 4, X: 1}


def ours(ctype, stim, t_end):
    m = Model(Cells([ctype]))
    y0 = settle(m, m.initial_state(), 800.0)
    m.stimulus = pulses(1, [(0, a, b, amp) for a, b, amp in stim])
    r = run_rk45(m, y0, t_end, dt_out=0.05, max_step=0.1, rtol=1e-6, atol=1e-9)
    return r["t"], r["V"][:, 0]


def theirs(P, stim, t_end, settle_ms=800.0):
    """Piecewise RK45 (RelTol 1e-6, AbsTol 1e-9) so pulse edges are hit exactly.
    settle_ms=0 reproduces their files (fixed initial conditions from t = 0)."""
    x = [P["V0"], 0.0002, 0.01, 0.05, 0.0, 0.103, 7.09, 0.03, 0.03, 0.1]
    if settle_ms:
        x = solve_ivp(port.rhs, (0, settle_ms), x, args=(P, 0.0), rtol=1e-6, atol=1e-9).y[:, -1]
    edges = sorted({0.0, t_end, *[v for a, b, _ in stim for v in (a, b)]})
    ts, Vs = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        I = sum(amp for s0, s1, amp in stim if s0 <= a and b <= s1)
        s = solve_ivp(port.rhs, (a, b), x, args=(P, I), rtol=1e-6, atol=1e-9, max_step=0.05,
                      dense_output=False)
        ts.append(s.t); Vs.append(s.y[0]); x = s.y[:, -1]
    return np.concatenate(ts), np.concatenate(Vs)


def spikes(t, V):
    return t[1:][(V[:-1] < 0) & (V[1:] >= 0)]


def draw(ax, t, V, color, ms, mv, title=None):
    ax.plot(t, V, color=color, lw=0.8)
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=8, loc="left")
    x0 = t[-1] - ms
    y0 = np.nanmin(V) - 5
    ax.plot([x0, x0 + ms], [y0, y0], "k", lw=1.2)
    ax.plot([x0 + ms, x0 + ms], [y0, y0 + mv], "k", lw=1.2)
    ax.text(x0 + ms / 2, y0 - 2, f"{ms} ms", ha="center", va="top", fontsize=6.5)
    ax.text(x0 + ms, y0 + mv / 2, f" {mv} mV", ha="left", va="center", fontsize=6.5)


def train(t0, n, isi, amp=AMP):
    return [(t0 + k * isi, t0 + k * isi + DUR, amp) for k in range(n)]


# Mooney & Prather protocol amplitudes (pA): middle of our cell's one-spike range for a 10 ms pulse
MP_AMP = {RA: 150.0, INT: 250.0, X: 500.0}
MP_STEP = (145.0, 820.0)   # D2: amplitude giving the original's ~60 Hz, over its drawn ~820 ms

# Panel: (label, cell, stated stimulus, M&P stimulus, t_end, time bar ms, voltage bar mV as in the
# original panel). Pulse spacing as read off the original panels.
PAPER = [("A2", RA, train(50, 4, 100), train(50, 4, 100, MP_AMP[RA]), 450, 100, 45),
         ("B2", RA, train(30, 2, 115), train(30, 2, 115, MP_AMP[RA]), 210, 50, 20),
         ("C2", INT, train(100, 4, 190), train(100, 4, 190, MP_AMP[INT]), 950, 200, 40),
         ("D2", INT, [(200, 700, AMP)], [(200, 200 + MP_STEP[1], MP_STEP[0])], 1150, 200, 30),
         ("E2", X, train(50, 4, 100), train(50, 4, 100, MP_AMP[X]), 450, 100, 40)]
# Their files: (source code no., our cell type, stimulus, t_end)
CODE = [(1, X, [(160, 645, 150.0)], 800),
        (2, X, [(170, 870, -120.0)], 1500),
        (3, RA, [(160, 575, 200.0)], 750),
        (4, INT, [(170, 870, 75.0)], 1500)]


def count(t, V, stim):
    """Spikes per pulse (pulses) or firing rate (one long step)."""
    sp = spikes(t, V)
    if len(stim) == 1 and stim[0][1] - stim[0][0] > 50:
        a, b, _ = stim[0]
        n = ((sp >= a) & (sp < b)).sum()
        return f"{n} spikes ({n / (b - a) * 1000:.0f} Hz)"
    per = [int(((sp >= a) & (sp < b + 15)).sum()) for a, b, _ in stim]
    return f"{per} per pulse"


def main():
    rows = []
    fig, axs = plt.subplots(len(PAPER), 2, figsize=(8, 10))
    for (lab, ct, stim, stim_mp, t_end, ms, mv), (a0, a1) in zip(PAPER, axs):
        t, V = ours(ct, stim, t_end)
        t2, V2 = ours(ct, stim_mp, t_end)
        amp_mp = stim_mp[0][2]
        draw(a0, t, V, COL[ct], ms, mv, f"{lab}  {NAME[ct]}, stated 500 pA: {count(t, V, stim)}")
        draw(a1, t2, V2, COL[ct], ms, mv,
             f"{lab}  {NAME[ct]}, M&P protocol {amp_mp:.0f} pA: {count(t2, V2, stim_mp)}")
        rows.append((lab, NAME[ct], count(t, V, stim), count(t2, V2, stim_mp)))
    fig.suptitle("Fig 2, stimulated cells alone (our model): stated protocol vs "
                 "Mooney & Prather protocol", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "replication_fig2_single.png", dpi=200)

    fig, axs = plt.subplots(len(CODE), 2, figsize=(8, 8))
    for (no, ct, stim, t_end), (a0, a1) in zip(CODE, axs):
        amp = stim[0][2]
        t, V = ours(ct, stim, t_end)
        t2, V2 = theirs(THEIR[no], stim, t_end, settle_ms=0.0)
        draw(a0, t, V, COL[ct], 100, 20, f"Our {NAME[ct]}, {amp:+.0f} pA: {count(t, V, stim)}")
        draw(a1, t2, V2, COL[ct], 100, 20,
             f"Their Source Code {no}, {amp:+.0f} pA: {count(t2, V2, stim)}")
        rows.append((f"Code {no}", f"{NAME[ct]} {amp:+.0f} pA", count(t, V, stim), count(t2, V2, stim)))
    fig.suptitle("The authors' Fig 2 code protocols: our cells vs their cells", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_code_protocols.png", dpi=200)

    print(f"{'panel':8s} {'cell':22s} {'stated 0.5 nA / our cell':28s} M&P protocol / their cell")
    for r in rows:
        print(f"{r[0]:8s} {r[1]:22s} {r[2]:28s} {r[3]}")


if __name__ == "__main__":
    main()

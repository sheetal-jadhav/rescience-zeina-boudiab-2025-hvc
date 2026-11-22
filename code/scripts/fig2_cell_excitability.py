"""Why do our Fig 2 cells fire more than the original's at the published 0.5 nA?

Faithful Python port of the authors' single-cell Fig 2 code (Figure 2 Source Code 3 = HVC_RA,
Source Code 4 = HVC_INT; Daou et al. 2013 equations incl. I_KNa and I_NaP), solved with RK45 at
their tolerances (RelTol 1e-6, AbsTol 1e-9). We then swap their parameters, one at a time, for
ours (code/hvcnet/params.py) and remove I_KNa / I_NaP, and count spikes at 500 pA.

Run from code/:  ../.venv/bin/python -I scripts/fig2_cell_excitability.py
"""
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

COMMON = dict(VL=-70, VK=-90, VNa=50, VH=-30, gL=2, gNap=1, gCa=19,
              taunbar=10, tauhpbar=1000, taue=20, tauh=1, taurs=1500, taur0=200, taur1=87.5,
              Ca_ex=2.5, RTF=26.7, thetam=-35, thetan=-30, thetas=-20, thetamp=-40, thetahp=-48,
              thetaa=-20, thetae=-60, thetarf=-105, thetars=-105, thetaaT=-65, thetab=0.4,
              thetarT=-67, thetarrT=68, sigmam=-5, sigman=-5, sigmas=-0.05, sigmamp=-6, sigmahp=6,
              sigmaa=-10, sigmae=5, sigmarf=5, sigmars=25, sigmaaT=-7.8, sigmab=-0.1, sigmarT=2,
              sigmarrT=2.2, f=0.1, eps=0.0015, kCa=0.3, bCa=0.1, ks=0.5, Rpump=0.0008, Kp=15,
              prf=100, alphaNa=0.0001, Naeq=8)
# Source Code 3 (RA) and 4 (INT): parameters, initial V, and the XPP factor on drs (INT only)
THEIR_RA = dict(COMMON, gNa=300, gK=400, gSK=27, gKNa=1000, gH=1, gA=150, gCaT=0.55, C=20, kr=0.95,
                V0=-80.14, rs_factor=1.0)
THEIR_INT = dict(COMMON, gNa=800, gK=1700, gSK=1, gKNa=1, gCaT=1.05, gH=4, gA=1, C=75, kr=0.01,
                 V0=-62.14, rs_factor=3.0)
# Ours (code/hvcnet/params.py), no I_KNa or I_NaP in the published model
OUR_RA = dict(gNa=300, gK=150, gA=9, gSK=11, gCaT=0, gH=0, C=20, gKNa=0, gNap=0)
OUR_INT = dict(gNa=800, gK=1200, gA=0, gSK=0, gCaT=1.3, gH=3, C=75, kr=0.01, gKNa=0, gNap=0)


def logi(z, th, sg):
    return 1.0 / (1.0 + np.exp((z - th) / sg))


def rhs(t, x, P, I):
    V, n, h, e, rT, Ca, Na, rf, rs, hp = x
    iCaL = P["gCa"] * logi(V, P["thetas"], P["sigmas"]) ** 2 * V * (P["Ca_ex"] / (1 - np.exp(2 * V / P["RTF"])))
    aT = logi(V, P["thetaaT"], P["sigmaaT"])
    bT = 1 / (1 + np.exp((rT - P["thetab"]) / P["sigmab"])) - 1 / (1 + np.exp(-P["thetab"] / P["sigmab"]))
    rTinf = 1 / (1 + np.exp((V - P["thetarT"]) / P["sigmarT"]))
    taurT = P["taur0"] + P["taur1"] / (1 + np.exp((V - P["thetarrT"]) / P["sigmarrT"]))
    iCaT = P["gCaT"] * aT ** 3 * bT ** 3 * V * (P["Ca_ex"] / (1 - np.exp(2 * V / P["RTF"])))
    iNap = P["gNap"] * logi(V, P["thetamp"], P["sigmamp"]) * hp * (V - P["VNa"])
    tauhp = P["tauhpbar"] / np.cosh((V - P["thetahp"]) / (2 * P["sigmahp"]))
    iL = P["gL"] * (V - P["VL"])
    taun = P["taunbar"] / np.cosh((V - P["thetan"]) / (2 * P["sigman"]))
    iK = P["gK"] * n ** 4 * (V - P["VK"])
    ah = 0.128 * np.exp(-(V + 50) / 18); bh = 4 / (1 + np.exp(-(V + 27) / 5))
    iNa = P["gNa"] * logi(V, P["thetam"], P["sigmam"]) ** 3 * h * (V - P["VNa"])
    iA = P["gA"] * logi(V, P["thetaa"], P["sigmaa"]) * e * (V - P["VK"])
    iSK = P["gSK"] * Ca ** 2 / (Ca ** 2 + P["ks"] ** 2) * (V - P["VK"])
    phi = lambda z: z ** 3 / (z ** 3 + P["Kp"] ** 3)
    iKNa = P["gKNa"] * 0.37 / (1 + (38.7 / Na) ** 3.5) * (V - P["VK"])
    taurf = P["prf"] / (-7.4 * (V + 70) / (np.exp(-(V + 70) / 0.8) - 1) + 65 * np.exp(-(V + 56) / 23))
    iH = P["gH"] * (P["kr"] * rf + (1 - P["kr"]) * rs) * (V - P["VH"])
    return [(-iL - iK - iNa - iCaL - iCaT - iA - iSK - iKNa - iH - iNap + I) / P["C"],
            (logi(V, P["thetan"], P["sigman"]) - n) / taun,
            (ah / (ah + bh) - h) / P["tauh"],
            (logi(V, P["thetae"], P["sigmae"]) - e) / P["taue"],
            (rTinf - rT) / taurT,
            -P["f"] * (P["eps"] * (iCaL + iCaT) + P["kCa"] * (Ca - P["bCa"])),
            -P["alphaNa"] * (iNa + iNap) - 3 * P["Rpump"] * (phi(Na) - phi(P["Naeq"])),
            (1 / (1 + np.exp((V - P["thetarf"]) / P["sigmarf"])) - rf) / taurf,
            P["rs_factor"] * (1 / (1 + np.exp((V - P["thetars"]) / P["sigmars"])) - rs) / P["taurs"],
            (logi(V, P["thetahp"], P["sigmahp"]) - hp) / tauhp]


def run(P, amp, t_on, t_off, t_end, settle=1000.0):
    """Settle with no input (the authors' code starts from fixed ICs; we settle so every variant
    starts at its own rest), then solve piecewise so the pulse edges are hit exactly."""
    x = [P["V0"], 0.0002, 0.01, 0.05, 0.0, 0.103, 7.09, 0.03, 0.03, 0.1]
    x = solve_ivp(rhs, (0, settle), x, args=(P, 0.0), method="RK45", rtol=1e-6, atol=1e-9).y[:, -1]
    ts, Vs = [], []
    for a, b, I in ((0, t_on, 0.0), (t_on, t_off, amp), (t_off, t_end, 0.0)):
        s = solve_ivp(rhs, (a, b), x, args=(P, I), method="RK45", rtol=1e-6, atol=1e-9, max_step=0.05)
        ts.append(s.t); Vs.append(s.y[0]); x = s.y[:, -1]
    t, V = np.concatenate(ts), np.concatenate(Vs)
    up = t[1:][(V[:-1] < 0) & (V[1:] >= 0)]
    return up, V[np.searchsorted(t, t_on) - 1]


def variants(base, ours, keys):
    out = [("their cell (Source Code)", base)]
    out += [("  without I_KNa", dict(base, gKNa=0)), ("  without I_NaP", dict(base, gNap=0)),
            ("  without I_KNa and I_NaP", dict(base, gKNa=0, gNap=0))]
    for k in keys:
        out.append((f"  {k}: {base[k]} -> ours {ours[k]}", dict(base, **{k: ours[k]})))
    out.append(("all of ours (no I_KNa/I_NaP)", dict(base, **ours)))
    return out


def main():
    print("HVC_RA, 500 pA x 10 ms pulse (Fig 2 A2/B2): spikes per pulse")
    for lab, P in variants(THEIR_RA, OUR_RA, ["gA", "gK", "gSK", "gCaT", "gH"]):
        sp, vr = run(P, 500.0, 100.0, 110.0, 250.0)
        print(f"  {lab:38s} {len(sp):2d} spikes   (rest {vr:6.1f} mV)")
    print("\nHVC_INT, 500 pA x 500 ms step (Fig 2 D2): firing rate")
    for lab, P in variants(THEIR_INT, OUR_INT, ["gK", "gA", "gSK", "gCaT", "gH"]):
        sp, vr = run(P, 500.0, 100.0, 600.0, 700.0)
        n = ((sp >= 100) & (sp < 600)).sum()
        print(f"  {lab:38s} {n / 0.5:5.0f} Hz   (rest {vr:6.1f} mV)")
    print("\nHVC_INT, their own Source Code 4 current (75 pA step):")
    sp, _ = run(THEIR_INT, 75.0, 100.0, 600.0, 700.0)
    print(f"  their cell: {((sp >= 100) & (sp < 600)).sum() / 0.5:.0f} Hz")


if __name__ == "__main__":
    main()

"""Can the full Daou et al. 2013 HVC(X) cell fire Bou Diab's fast rebound bursts?

Test of the hypothesis that Bou Diab et al. ran the network with Daou 2013's complete cell
models (including I_NaP and I_KNa, which the paper says it removed) rather than the reduced
cells of their eqs 1-3. Parameters and equations are read directly from Daou 2013's published
XPP files (reference/daou2013-published-code/, gitignored), so nothing is retyped.

Target (Bou Diab Fig 10): HVC(X) rebound bursts of ~4-9 spikes within ~10-20 ms (~500 Hz).
Our reduced X cell is rate-limited to ~160 Hz.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "reference" / "daou2013-published-code"
OUT = ROOT / "results" / "daou13_xcell.jsonl"


def read_ode(name):
    text = (CODE / name).read_text()
    p = {k: float(v) for k, v in re.findall(r"^par (\w+)=([-\d.eE]+)", text, re.M)}
    init = dict(re.findall(r"(\w+)=([-\d.]+)", re.search(r"^init (.*)$", text, re.M).group(1)))
    p["rs_factor"] = 3.0 if re.search(r"rs'=3\*", text) else 1.0
    # phirT is declared in the .ode files but not used in rT' (it is used in the .m files)
    p["use_phirT"] = 0.0
    return p, {k: float(v) for k, v in init.items()}


def rhs_factory(p, iapp):
    def rhs(t, y):
        V, n, h, e, rT, Ca, Na, rf, rs, hp = y
        Vc = np.clip(V, -150, 100)
        sinf = 1 / (1 + np.exp((Vc - p["thetas"]) / p["sigmas"]))
        ghk = Vc * (p["Ca_ex"] / (1 - np.exp(2 * Vc / p["RTF"]))) if abs(Vc) > 1e-6 else -p["Ca_ex"] * p["RTF"] / 2
        iCaL = p["gCa"] * sinf**2 * ghk
        aTinf = 1 / (1 + np.exp((Vc - p["thetaaT"]) / p["sigmaaT"]))
        bTinf = 1 / (1 + np.exp((rT - p["thetab"]) / p["sigmab"])) - 1 / (1 + np.exp(-p["thetab"] / p["sigmab"]))
        rTinf = 1 / (1 + np.exp((Vc - p["thetarT"]) / p["sigmarT"]))
        taurT = p["taur0"] + p["taur1"] / (1 + np.exp((Vc - p["thetarrT"]) / p["sigmarrT"]))
        iCaT = p["gCaT"] * aTinf**3 * bTinf**3 * ghk
        mpinf = 1 / (1 + np.exp((Vc - p["thetamp"]) / p["sigmamp"]))
        hpinf = 1 / (1 + np.exp((Vc - p["thetahp"]) / p["sigmahp"]))
        tauhp = p["tauhpbar"] / np.cosh((Vc - p["thetahp"]) / (2 * p["sigmahp"]))
        iNap = p["gNap"] * mpinf * hp * (V - p["VNa"])
        iL = p["gL"] * (V - p["VL"])
        ninf = 1 / (1 + np.exp((Vc - p["thetan"]) / p["sigman"]))
        taun = p["taunbar"] / np.cosh((Vc - p["thetan"]) / (2 * p["sigman"]))
        iK = p["gK"] * n**4 * (V - p["VK"])
        minf = 1 / (1 + np.exp((Vc - p["thetam"]) / p["sigmam"]))
        ah = 0.128 * np.exp(-(Vc + 50) / 18)
        bh = 4 / (1 + np.exp(-(Vc + 27) / 5))
        iNa = p["gNa"] * minf**3 * h * (V - p["VNa"])
        ainf = 1 / (1 + np.exp((Vc - p["thetaa"]) / p["sigmaa"]))
        einf = 1 / (1 + np.exp((Vc - p["thetae"]) / p["sigmae"]))
        iA = p["gA"] * ainf * e * (V - p["VK"])
        iSK = p["gSK"] * Ca**2 / (Ca**2 + p["ks"] ** 2) * (V - p["VK"])
        Nap = max(Na, 1e-6)
        winf = 0.37 / (1 + (38.7 / Nap) ** 3.5)
        iKNa = p["gKNa"] * winf * (V - p["VK"])
        phi = lambda x: x**3 / (x**3 + p["Kp"] ** 3)
        rfinf = 1 / (1 + np.exp((Vc - p["thetarf"]) / p["sigmarf"]))
        x = Vc + 70
        lin = 7.4 * 0.8 if abs(x) < 1e-6 else -7.4 * x / (np.exp(-x / 0.8) - 1)
        taurf = p["prf"] / (lin + 65 * np.exp(-(Vc + 56) / 23))
        rsinf = 1 / (1 + np.exp((Vc - p["thetars"]) / p["sigmars"]))
        iH = p["gH"] * (p["kr"] * rf + (1 - p["kr"]) * rs) * (V - p["VH"])
        phirT = p["phirT"] if p["use_phirT"] else 1.0
        dV = (-iL - iK - iNa - iCaL - iCaT - iA - iSK - iKNa - iH - iNap + iapp(t)) / p["C"]
        return [dV, (ninf - n) / taun, (ah / (ah + bh) - h) / p["tauh"], (einf - e) / p["taue"],
                phirT * (rTinf - rT) / taurT, -p["f"] * (p["eps"] * (iCaL + iCaT) + p["kCa"] * (Ca - p["bCa"])),
                -p["alphaNa"] * (iNa + iNap) - 3 * p["Rpump"] * (phi(Nap) - phi(p["Naeq"])),
                (rfinf - rf) / taurf, p["rs_factor"] * (rsinf - rs) / p["taurs"], (hpinf - hp) / tauhp]
    return rhs


def run(p, init, amp, t_on, t_off, t_end):
    iapp = lambda t: amp if t_on < t < t_off else 0.0
    y0 = [init["V"], init["n"], init["h"], init["e"], 0.0, init["Cai"], init["Nai"],
          init["rf"], init["rs"], init["hp"]]
    sol = solve_ivp(rhs_factory(p, iapp), (0, t_end), y0, method="RK45", rtol=1e-6, atol=1e-9,
                    max_step=0.05, dense_output=True)
    t = np.arange(0, t_end, 0.01)
    return t, sol.sol(t)[0]


def spikes(t, V):
    i = np.where((V[:-1] < 0) & (V[1:] >= 0))[0]
    return t[i]


def describe(t, V, t_on, t_off, rebound):
    sp = spikes(t, V)
    win = sp[(sp > t_off) & (sp < t_off + 150)] if rebound else sp[(sp > t_on) & (sp < t_off)]
    isi = np.diff(win)
    burst = 1 + int(np.argmax(np.append(isi, 99) > 10)) if len(win) else 0
    return {"n_spikes": int(len(win)), "first_burst_spikes": burst,
            "max_rate_hz": float(1000 / isi.min()) if len(isi) else 0.0,
            "first_isi_ms": float(isi[0]) if len(isi) else None,
            "spike_times": [round(float(s), 2) for s in win[:12]]}


CASES = [
    # name, file, overrides, amp (pA), on, off, end, rebound?
    ("Fig4 X depolarising step (as published)", "Figure_4.ode", {}, None, None, None, 800, False),
    ("Fig4 X, 400 pA step (max rate)", "Figure_4.ode", {"iAp": 400}, None, None, None, 800, False),
    ("Fig7 X rebound (as published, gK 1700)", "Figure_7.ode", {}, None, None, None, 1500, True),
    ("Fig7 X rebound with gK 50 (Fig4 value)", "Figure_7.ode", {"gK": 50}, None, None, None, 1500, True),
    ("Fig7 X rebound with gK 80 (BD Table 1)", "Figure_7.ode", {"gK": 80}, None, None, None, 1500, True),
    ("Fig4 X, 50 ms -120 pA (IPSP-like) rebound", "Figure_4.ode", {}, -120, 200, 250, 600, True),
    ("Fig4 X, 50 ms -300 pA rebound", "Figure_4.ode", {}, -300, 200, 250, 600, True),
    ("Reduced (BD-like): Fig7, gK 80, no NaP/KNa", "Figure_7.ode", {"gK": 80, "gNap": 0, "gKNa": 0}, None, None, None, 1500, True),
]

if __name__ == "__main__":
    rows = []
    for name, f, ov, amp, on, off, end, reb in CASES:
        p, init = read_ode(f)
        p.update(ov)
        amp = p["iAp"] if amp is None else amp
        on = p["from"] if on is None else on
        off = p["to"] if off is None else off
        t, V = run(p, init, amp, on, off, end)
        r = {"case": name, "file": f, "overrides": ov, "amp": amp, "on": on, "off": off,
             **describe(t, V, on, off, reb)}
        rows.append(r)
        print(json.dumps(r), flush=True)
        np.save(ROOT / "results" / f"daou13_xcell_{len(rows)}.npy", np.vstack([t[::10], V[::10]]))
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

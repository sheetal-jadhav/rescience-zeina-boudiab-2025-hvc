"""What sets the within-burst spike interval of HVC_RA in the chain? (Fig 4: 4.76 spikes in 8.12 ms,
i.e. ~2.2 ms between spikes; ours ~3.93 spikes in 8.61 ms, ~2.9 ms.)

A 15-neuron RA chain with the final configuration's RA cells (gA, gSK) and RA->RA synapse, kicked as
in the network (500 pA x 10 ms into RA1); no INT or X. Bursts of RA 6-15 (after the chain settles)
are scored. One setting is changed at a time.
Run from code/:  ../.venv/bin/python -I scripts/fig4_burst_isi.py  -> results/fig4_burst_isi.jsonl
"""
import json
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from hvcnet import RA, Cells, Model, Synapses, pulses, run_rk45, settle  # noqa: E402
from hvcnet.network import AMPA  # noqa: E402
from hvcnet.params import Gating, Switches  # noqa: E402

CFG = json.load(open(HERE.parent / "configs/final.json"))
N = 15
BASE_SW = dict(bT_exponent=CFG["sw_bT_exponent"], alpha_h_offset=CFG["sw_alpha_h_offset"])


def chain(cell=None, gating=None, switches=None, g_rara=CFG["g_RA_RA"], kick=500.0):
    c = Cells([RA] * N)
    c.gA[:] = CFG["gA@RA"]; c.gSK[:] = CFG["gSK@RA"]
    for k, v in (cell or {}).items():
        getattr(c, k)[:] = v
    syn = Synapses(list(range(N - 1)), list(range(1, N)), [g_rara] * (N - 1), [AMPA] * (N - 1))
    m = Model(c, syn, gating=replace(Gating(), **(gating or {})),
              switches=replace(Switches(), **dict(BASE_SW, **(switches or {}))))
    y0 = settle(m, m.initial_state(), 500.0)
    m.stimulus = pulses(N, [(0, 50.0, 60.0, kick)])
    r = run_rk45(m, y0, 50.0 + 6.0 * N + 60.0, dt_out=0.02, max_step=0.05, rtol=1e-6, atol=1e-9)
    t, V = r["t"], r["V"]
    out = []
    for j in range(5, N):
        s = t[1:][(V[:-1, j] < 0) & (V[1:, j] >= 0)]
        if len(s):
            out.append((len(s), s[-1] - s[0], np.diff(s).mean() if len(s) > 1 else np.nan))
    if len(out) < N - 5:
        return {"propagates": False}
    a = np.array(out)
    return {"propagates": True, "spikes": float(a[:, 0].mean()), "dur": float(a[:, 1].mean()),
            "isi": float(np.nanmean(a[:, 2]))}


VARIANTS = [("baseline", {})]
VARIANTS += [(f"tau_n {v}", {"gating": {"tau_n": v}}) for v in (7.5, 5.0, 3.0)]
VARIANTS += [(f"tau_h {v}", {"gating": {"tau_h": v}}) for v in (0.5, 2.0)]
VARIANTS += [(f"Cm {v}", {"cell": {"Cm": v}}) for v in (15.0, 10.0)]
VARIANTS += [(f"gK {v}", {"cell": {"gK": v}}) for v in (250.0, 400.0)]
VARIANTS += [(f"gNa {v}", {"cell": {"gNa": v}}) for v in (400.0, 600.0)]
VARIANTS += [("alpha_h_offset 50 [Daou13 code]", {"switches": {"alpha_h_offset": 50.0}}),
             ("RTF 26.7 [Daou13 code]", {"switches": {"RTF": 26.7}}),
             ("tau_n constant 10 [BD eq]", {"switches": {"tau_n_voltage_dependent": False}})]


def job(v):
    name, kw = v
    try:
        return dict(name=name, **chain(**kw))
    except Exception as e:
        return {"name": name, "error": repr(e)}


def main():
    with Pool(8) as p:
        rows = p.map(job, VARIANTS)
    out = HERE.parents[1] / "results" / "fig4_burst_isi.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"{'variant':34s} spikes  dur(ms)  ISI(ms)")
    for r in rows:
        if r.get("propagates"):
            print(f"{r['name']:34s} {r['spikes']:5.2f}  {r['dur']:6.2f}   {r['isi']:5.2f}")
        else:
            print(f"{r['name']:34s} {'no propagation' if 'error' not in r else r['error']}")
    print(f"{'original Fig 4':34s}  4.76    8.12    ~2.2")


if __name__ == "__main__":
    main()

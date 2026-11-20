"""Fig 13 range sweeps and robustness checks on the frozen Phase-1 configuration.

Usage: robustness.py <part>   with part in {fig13, pern, seeds, solver, noise, noX}
Each part appends JSON lines to results/robust_<part>.jsonl.

fig13  one conductance at a time over 9 values spanning [lo/2, 1.5*hi] of its published range
       (Fig 13); 2 seeds. The paper's 'accurate network' needs X/INT criteria we can't meet,
       so here 'accurate' is judged on RA only (chain complete, RA criterion).
pern   per-neuron random conductances within the Fig 13 ranges for RA (gA, gSK) and INT
       (gH, gCaT); X stays population-level, as in the paper's Methods. 16 seeds.
seeds  frozen config on 50 seeds (headline Fig 4 statistics).
solver RK45 rtol 1e-3 (MATLAB default) vs rtol 1e-6/atol 1e-9 (tolerances in the authors'
       single-cell code) vs fixed-step RK4 at 0.025 and 0.01 ms; 4 seeds; first-spike times kept.
noise  additive white-noise current, sigma in pA*ms^0.5, fixed-step RK4 0.01 ms (our reading of
       'sigma*xi(t)'; units unreported, I-08); 4 seeds.
noX    Reviewer-2 ablation: HVC(X) disconnected (X->INT = 0 and INT->X = 0); 16 seeds.
"""

import json, sys, time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np
from calibrate_random import RANGES, to_kwargs
from phase1_seeds import CONFIG
from hvcnet.analysis import spike_times
from hvcnet.evaluate import score, simulate
from hvcnet.model import Model, pulses
from hvcnet.network import build
from hvcnet.params import INT, RA
from hvcnet.sim import run_rk4, run_rk45, settle

OUT = HERE.parents[1] / "results"


def clean(d):
    return {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in d.items()}


def firsts(net, sp):
    return [float(sp[j][0]) if len(sp[j]) else None for j in net.chain_order()]


def job_point(args):
    tag, point, seed, extra = args
    t0 = time.time()
    try:
        net, r, sp = simulate(seed=seed, **to_kwargs(point), **(extra or {}))
        s = clean(score(net, sp))
    except Exception as e:
        s = {"error": repr(e)}
    return {"tag": tag, "point": point, "seed": seed, "score": s, "sec": round(time.time() - t0, 1)}


def job_pern(seed):
    kw = to_kwargs(CONFIG)
    net = build(kw["spec"], seed=seed)
    rng = np.random.default_rng(5000 + seed)
    per = {}
    for attr, typ in (("gA", RA), ("gSK", RA), ("gH", INT), ("gCaT", INT)):
        lo, hi = RANGES[f"{attr}@{'RA' if typ == RA else 'INT'}"]
        idx = np.where(net.cells.types == typ)[0]
        per[attr] = {int(i): ("set", float(rng.uniform(lo, hi))) for i in idx}
    net2, r, sp = simulate(seed=seed, per_neuron=per, **kw)
    return {"tag": "pern", "seed": seed, "score": clean(score(net2, sp))}


def _model(seed, point=CONFIG):
    kw = to_kwargs(point)
    net = build(kw["spec"], seed=seed)
    m = Model(net.cells, net.synapses, switches=kw["switches"])
    y0 = settle(m, m.initial_state(), 500.0)
    m.stimulus = pulses(net.cells.N, [(net.first_ra, 50.0, 60.0, 500.0)])
    return net, m, y0


def job_solver(args):
    method, seed = args
    net, m, y0 = _model(seed)
    t0 = time.time()
    if method == "rk45_1e-3":
        r = run_rk45(m, y0, 400.0)
    elif method == "rk45_1e-6":
        r = run_rk45(m, y0, 400.0, rtol=1e-6, atol=1e-9)
    elif method == "rk4_0.025":
        r = run_rk4(m, y0, 400.0, dt=0.025)
    else:
        r = run_rk4(m, y0, 400.0, dt=0.01)
    sp = spike_times(r["t"], r["V"])
    return {"tag": "solver", "method": method, "seed": seed, "sec": round(time.time() - t0, 1),
            "score": clean(score(net, sp)), "firsts": firsts(net, sp)}


def job_noise(args):
    sigma, seed = args
    net, m, y0 = _model(seed)
    m.noise_pA = sigma
    r = run_rk4(m, y0, 400.0, dt=0.01, rng=np.random.default_rng(seed))
    sp = spike_times(r["t"], r["V"])
    return {"tag": "noise", "sigma": sigma, "seed": seed, "score": clean(score(net, sp))}


def fig13_jobs():
    jobs = []
    for key, (lo, hi) in RANGES.items():
        for v in np.linspace(lo / 2, hi * 1.5, 9):
            p = dict(CONFIG, **{key: round(float(v), 3)})
            jobs += [(f"fig13:{key}", p, s, None) for s in (0, 1)]
    return jobs


if __name__ == "__main__":
    part = sys.argv[1]
    out = OUT / f"robust_{part}.jsonl"
    with Pool(8) as pool, open(out, "w") as f:
        if part == "fig13":
            it = pool.imap_unordered(job_point, fig13_jobs())
        elif part == "pern":
            it = pool.imap_unordered(job_pern, range(16))
        elif part == "seeds":
            it = pool.imap_unordered(job_point, [("seeds", CONFIG, s, None) for s in range(50)])
        elif part == "solver":
            it = pool.imap_unordered(job_solver, [(m, s) for m in ("rk45_1e-3", "rk45_1e-6",
                                     "rk4_0.025", "rk4_0.01") for s in range(4)])
        elif part == "noise":
            it = pool.imap_unordered(job_noise, [(sg, s) for sg in (0, 5, 10, 20, 40, 80, 160)
                                                 for s in range(4)])
        elif part == "noX":
            p = dict(CONFIG, g_X_INT=0.0, g_INT_X=0.0)
            it = pool.imap_unordered(job_point, [("noX", p, s, None) for s in range(16)])
        for res in it:
            f.write(json.dumps(res) + "\n"); f.flush()
    print(out)

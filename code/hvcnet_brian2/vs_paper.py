"""Brian2 implementation scored against the original paper's quantitative claims.

Parts (same protocols and random draws as the SciPy scripts):
  seeds  50 wiring seeds (Fig 4 statistics; robustness.py seeds)
  noX    HVC(X) disconnected, 16 seeds (robustness.py noX)
  fig12  HVC(X) gCaT, gSK, gH drawn per neuron, 100 runs (fig12.py)
Writes results/brian2_<part>.jsonl.
"""
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
os.environ.setdefault("HVC_CONFIG", str(CODE / "configs" / "final.json"))
sys.path.insert(0, str(CODE / "scripts")); sys.path.insert(0, str(CODE))
import numpy as np  # noqa: E402
from calibrate_random import RANGES, to_kwargs  # noqa: E402
from phase1_seeds import CONFIG  # noqa: E402

import hvcnet_brian2 as hb  # noqa: E402
from hvcnet.evaluate import score  # noqa: E402
from hvcnet.network import build  # noqa: E402
from hvcnet.params import X  # noqa: E402

RESULTS = CODE.parent / "results"


def _clean(s):
    return {a: (float(b) if isinstance(b, (np.floating, np.integer)) else b) for a, b in s.items()}


def job(args):
    part, k = args
    point = dict(CONFIG, g_X_INT=0.0, g_INT_X=0.0) if part == "noX" else CONFIG
    kw = to_kwargs(point)
    per, seed = None, k
    if part == "fig12":
        seed = k % 10                 # as fig12.py: 10 networks x 10 conductance draws
        net = build(kw["spec"], seed=seed)
        rng = np.random.default_rng(12000 + k)
        per = {}
        for attr in ("gCaT", "gSK", "gH"):
            lo, hi = RANGES[f"{attr}@X"]
            per[attr] = {int(i): ("set", float(rng.uniform(lo, hi)))
                         for i in np.where(net.cells.types == X)[0]}
    net, sp = hb.simulate(seed=seed, per_neuron=per, dt=0.01, **kw)
    return {"part": part, "run": k, "seed": seed, "score": _clean(score(net, sp))}


if __name__ == "__main__":
    parts = sys.argv[1:] or ["seeds", "noX", "fig12"]
    n = {"seeds": 50, "noX": 16, "fig12": 100}
    job(("seeds", 0))                 # compile the Cython code once before forking workers
    with Pool(6) as pool:
        for part in parts:
            rows = list(pool.imap_unordered(job, [(part, k) for k in range(n[part])]))
            rows.sort(key=lambda r: r["run"])
            (RESULTS / f"brian2_{part}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            print(part, "done", flush=True)

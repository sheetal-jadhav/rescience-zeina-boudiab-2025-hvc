"""Fig 12: HVC_X maximal conductances (gCaT, gSK, gH) drawn per neuron within the Fig 13A ranges,
100 simulations (original: 41% unaffected, 59% disrupted). Writes results/fig12.jsonl.

'Disrupted' in the original includes unrealistic X/INT firing, which our model shows in every
run (X criterion never met), so we report the RA-based measures separately: chain broken, and
fraction of RA meeting the burst criterion."""

import json, os, sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("HVC_CONFIG", "configs/final.json")
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np
from calibrate_random import RANGES, to_kwargs
from phase1_seeds import CONFIG
from hvcnet.evaluate import score, simulate
from hvcnet.network import build
from hvcnet.params import X

N_RUNS = 100


def job(k):
    kw = to_kwargs(CONFIG)
    seed = k % 10                     # 10 network instances x 10 conductance draws
    net = build(kw["spec"], seed=seed)
    rng = np.random.default_rng(12000 + k)
    per = {}
    for attr in ("gCaT", "gSK", "gH"):
        lo, hi = RANGES[f"{attr}@X"]
        per[attr] = {int(i): ("set", float(rng.uniform(lo, hi))) for i in np.where(net.cells.types == X)[0]}
    net2, r, sp = simulate(seed=seed, per_neuron=per, **kw)
    s = score(net2, sp)
    return {"run": k, "seed": seed, "score": {a: (float(b) if isinstance(b, (np.floating, np.integer)) else b)
                                               for a, b in s.items()}}


if __name__ == "__main__":
    out = HERE.parents[1] / "results/fig12.jsonl"
    with Pool(8) as pool, open(out, "w") as f:
        for res in pool.imap_unordered(job, range(N_RUNS)):
            f.write(json.dumps(res) + "\n"); f.flush()
    print(out)

"""Cross-simulator check: hvcnet (SciPy RK45, rtol 1e-6) vs hvcnet_brian2 (Brian2 RK4).

Same networks (seeds 0-4), final configuration, same protocol. For each run: the paper's
scores, and spike-by-spike timing differences for neurons with equal spike counts.
Writes results/compare_brian2.jsonl.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1]))
from calibrate_random import to_kwargs  # noqa: E402
from phase1_seeds import CONFIG  # noqa: E402  (configs/final.json via HVC_CONFIG)

import hvcnet_brian2 as hb  # noqa: E402
from hvcnet.evaluate import score, simulate  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "results" / "compare_brian2.jsonl"


def compare(net, ref, other):
    same = [i for i in range(len(ref)) if len(ref[i]) == len(other[i])]
    d = np.concatenate([np.abs(ref[i] - other[i]) for i in same if len(ref[i])] or [np.zeros(0)])
    chain = net.chain_order()
    first = np.array([abs(ref[j][0] - other[j][0]) for j in chain if len(ref[j]) and len(other[j])])
    by_class = {}
    for name, idx in (("ra", net.ra), ("x", net.x), ("int", net.int_)):
        by_class[name] = {"same_count": int(sum(len(ref[i]) == len(other[i]) for i in idx)),
                          "n": int(len(idx)),
                          "spikes_ref": int(sum(len(ref[i]) for i in idx)),
                          "spikes_other": int(sum(len(other[i]) for i in idx))}
    return {"max_dt_ms": float(d.max()) if len(d) else None,
            "median_dt_ms": float(np.median(d)) if len(d) else None,
            "ra_first_spike_max_dt_ms": float(first.max()),
            "ra_first_spike_mean_dt_ms": float(first.mean()),
            "by_class": by_class}


def clean(d):
    return {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in d.items()}


if __name__ == "__main__":
    kw = to_kwargs(CONFIG)
    rows = []
    for seed in range(5):
        t = time.time()
        net, _, sp_ref = simulate(seed=seed, **kw)
        t_ref = time.time() - t
        row = {"seed": seed, "scipy": {"sec": round(t_ref, 1), **clean(score(net, sp_ref))}}
        for dt in (0.01, 0.025):
            t = time.time()
            net_b, sp_b = hb.simulate(seed=seed, dt=dt, **kw)
            row[f"brian2_dt{dt}"] = {"sec": round(time.time() - t, 1), **clean(score(net_b, sp_b)),
                                     "vs_scipy": compare(net, sp_ref, sp_b)}
        rows.append(row)
        print(json.dumps(row), flush=True)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print("COMPARE_DONE")

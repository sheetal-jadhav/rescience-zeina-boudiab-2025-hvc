"""Random search inside the Fig 13 ranges (plus equation switches); one JSON line per run.

Every sampled value lies inside the published allowed range, so a good point is a valid
instance of the paper's model rather than a re-fit."""

import json, sys, time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from hvcnet.evaluate import score, simulate
from hvcnet.params import INT, RA, X, NetworkSpec, SYNAPSE_G, Switches, with_switches

RANGES = {  # [BD-F13] (nS)
    "gA@RA": (1.0, 14.0), "gSK@RA": (9.0, 12.5),
    "gSK@X": (1.0, 3.0), "gH@X": (1.5, 7.5), "gCaT@X": (1.0, 9.0),
    "gH@INT": (1.0, 5.0), "gCaT@INT": (1.0, 2.0),
    "g_RA_RA": (29.0, 31.0), "g_RA_INT": (10.0, 45.0), "g_X_INT": (2.0, 31.0),
    "g_INT_X": (6.0, 42.0), "g_INT_RA": (2.0, 5.0),
}
CHOICES = {"sw_bT_exponent": [2, 3], "sw_alpha_h_offset": [15.0, 50.0]}
TYPES = {"RA": RA, "X": X, "INT": INT}


def to_kwargs(point):
    """Translate a flat parameter point into simulate() keyword arguments."""
    g, overrides, sw, gating, kin = dict(SYNAPSE_G), {}, {}, {}, {}
    for k, v in point.items():
        if k.startswith("gt_"):
            gating[k[3:]] = v
        elif k.startswith("kin_"):
            kin[k[4:]] = v
        elif k.startswith("g_"):
            a, b = k[2:].split("_")
            g[(a, b)] = v
        elif k.startswith("sw_"):
            sw[k[3:]] = v
        else:
            name, typ = k.split("@")
            overrides.setdefault(name, {})[TYPES[typ]] = v
    return dict(spec=NetworkSpec(g=g), overrides=overrides, switches=with_switches(**sw),
                gating=gating, kinetics=kin)


def run(point, seed=0):
    t0 = time.time()
    try:
        net, r, sp = simulate(seed=seed, **to_kwargs(point))
        s = score(net, sp)
    except Exception as e:
        s = {"error": repr(e)}
    s = {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in s.items()}
    return {"point": point, "seed": seed, "score": s, "sec": round(time.time() - t0, 1)}


def sample(rng, n):
    for _ in range(n):
        p = {k: round(float(rng.uniform(*lo_hi)), 3) for k, lo_hi in RANGES.items()}
        p.update({k: v[rng.integers(len(v))] for k, v in CHOICES.items()})
        yield {k: (int(v) if isinstance(v, np.integer) else v) for k, v in p.items()}


if __name__ == "__main__":
    n, out, rng_seed = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    points = list(sample(np.random.default_rng(rng_seed), n))
    with Pool(8) as pool, open(out, "a") as f:
        for res in pool.imap_unordered(run, points):
            f.write(json.dumps(res) + "\n"); f.flush()

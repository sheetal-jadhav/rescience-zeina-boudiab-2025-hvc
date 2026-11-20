"""Grid search within the Fig 13 ranges; writes one JSON line per run to results/."""

import itertools, json, sys, time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from hvcnet.evaluate import score, simulate
from hvcnet.params import INT, RA, X, NetworkSpec, SYNAPSE_G


def run(point):
    over = {k: v for k, v in point.items() if not k.startswith("g_")}
    g = dict(SYNAPSE_G)
    for k, v in point.items():
        if k.startswith("g_"):
            a, b = k[2:].split("_")
            g[(a, b)] = v
    overrides = {}
    for key, val in over.items():
        name, typ = key.split("@")
        overrides.setdefault(name, {})[{"RA": RA, "X": X, "INT": INT}[typ]] = val
    t0 = time.time()
    try:
        net, r, sp = simulate(NetworkSpec(g=g), seed=point.get("seed", 0) if False else 0,
                              overrides=overrides)
        s = score(net, sp)
    except Exception as e:  # keep the sweep going; record the failure
        s = {"error": repr(e)}
    s = {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in s.items()}
    return {"point": point, "score": s, "sec": round(time.time() - t0, 1)}


def main(grid_json, out):
    grid = json.loads(grid_json)
    keys = list(grid)
    points = [dict(zip(keys, vals)) for vals in itertools.product(*grid.values())]
    with Pool(8) as pool, open(out, "a") as f:
        for res in pool.imap_unordered(run, points):
            f.write(json.dumps(res) + "\n"); f.flush()
    print(out, len(points))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

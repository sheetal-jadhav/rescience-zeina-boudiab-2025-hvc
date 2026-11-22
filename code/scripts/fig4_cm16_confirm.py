"""Confirmation on 10 seeds of the best full-network grid point. Fig 4 burst statistics with a smaller RA capacitance (Cm unreported, I-01; Daou13 20 pF) and RA adaptation retuned inside the Fig 13 ranges, chosen on the RA chain (fig4_cm_grid.py).

Variants on the frozen final configuration (configs/final.json), 10 seeds each:
  base       start pulse 500 pA x 10 ms into RA1 (I-07), network synapses from final.json
  kick150    start pulse 150 pA x 10 ms (the M&P one-spike amplitude for our RA cell)
  fig2syn    Fig 2 fitted synapses in the network: RA->INT 25, X->INT 11, INT->X 10 nS
  fig2syn_B  as fig2syn but RA->INT 7.4 nS (the subthreshold B2 pair)
  both       fig2syn + kick150
RA->RA and INT->RA are not constrained by Fig 2 and keep their final.json values.
Original Fig 4: 4.76 +- 0.48 spikes per burst, 8.12 +- 0.89 ms.
Run from code/: HVC_CONFIG=configs/final.json ../.venv/bin/python -I scripts/fig4_mp_test.py
-> results/fig4_cm16_confirm.jsonl
"""
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from hvcnet.evaluate import score, simulate  # noqa: E402
from calibrate_random import to_kwargs  # noqa: E402

CONFIG = {k: v for k, v in json.load(open(HERE.parent / "configs/final.json")).items()
          if not k.startswith("_")}
VARIANTS = {"Cm16_gSK12.5_gA14": ({"Cm@RA": 16.0, "gSK@RA": 12.5, "gA@RA": 14.0}, (50.0, 60.0, 500.0))}
OUT = HERE.parents[1] / "results" / "fig4_cm16_confirm.jsonl"


def job(args):
    name, seed = args
    change, kick = VARIANTS[name]
    t0 = time.time()
    try:
        net, r, sp = simulate(seed=seed, kick=kick, **to_kwargs(dict(CONFIG, **change)))
        s = {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
             for k, v in score(net, sp).items()}
    except Exception as e:  # keep going; report the error
        s = {"error": repr(e)}
    return {"variant": name, "seed": seed, "score": s, "sec": round(time.time() - t0, 1)}


def main(n_seeds=10):
    jobs = [(v, s) for v in VARIANTS for s in range(n_seeds)]
    with Pool(os.cpu_count()) as pool, open(OUT, "w") as f:
        for res in pool.imap_unordered(job, jobs):
            f.write(json.dumps(res) + "\n"); f.flush()
            sc = res["score"]
            print(res["variant"], res["seed"], sc.get("ra_spikes"), sc.get("ra_dur"),
                  sc.get("ra_fired"), flush=True)
    rows = [json.loads(l) for l in open(OUT)]
    print("\nvariant     spikes/burst      duration (ms)    RA fired   in order   n")
    for v in VARIANTS:
        R = [r["score"] for r in rows if r["variant"] == v and "error" not in r["score"]]
        sp = np.array([r["ra_spikes"] for r in R]); du = np.array([r["ra_dur"] for r in R])
        print(f"{v:10s}  {sp.mean():.2f} +- {sp.std():.2f}    {du.mean():.2f} +- {du.std():.2f}"
              f"     {np.mean([r['ra_fired'] for r in R]):.0f}      "
              f"{sum(r['ra_in_order'] for r in R)}/{len(R)}    {len(R)}")
    print("original    4.76 +- 0.48      8.12 +- 0.89")


if __name__ == "__main__":
    main()

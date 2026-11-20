"""Follow-up to fig6_9_11.py: same protocol with INT->RA at the top of its published range
(5 nS instead of the frozen 2.01 nS) and larger RA gA/gSK factors (the Fig 6A factor is unreported)."""

import json, sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fig6_9_11 as base
from phase1_seeds import CONFIG

base.CONFIG = dict(CONFIG, g_INT_RA=5.0)
base.SEEDS = (0,)
base.PERTURBATIONS = {
    "fig6A_RA_gA_x5": ("RA", "gA", "mul", 5.0),
    "fig6A_RA_gA_x10": ("RA", "gA", "mul", 10.0),
    "fig6A_RA_gA_x20": ("RA", "gA", "mul", 20.0),
    "fig6B_RA_gSK_x15": ("RA", "gSK", "mul", 15.0),
    "fig6B_RA_gSK_x60": ("RA", "gSK", "mul", 60.0),
    "fig9A_INT_gCaT_x10": ("INT", "gCaT", "mul", 10.0),
    "fig9B_INT_gH_x10": ("INT", "gH", "mul", 10.0),
    "fig11A_X_gH_x10": ("X", "gH", "mul", 10.0),
    "fig11B_X_gCaT_x15": ("X", "gCaT", "mul", 15.0),
    "fig11C_X_gSK_0": ("X", "gSK", "set", 0.0),
}

if __name__ == "__main__":
    from calibrate_random import to_kwargs
    from hvcnet.network import build
    jobs = [("baseline", s, None) for s in base.SEEDS]
    for s in base.SEEDS:
        tg = base.targets(build(to_kwargs(base.CONFIG)["spec"], seed=s), s)
        for name, (cls, *_r) in base.PERTURBATIONS.items():
            jobs += [(name, s, i) for i in tg[cls]]
    out = HERE.parents[1] / "results/fig6_9_11_followup.jsonl"
    with Pool(8) as pool, open(out, "w") as f:
        for res in pool.imap_unordered(base.job, jobs):
            f.write(json.dumps(res) + "\n"); f.flush()
    print(out, len(jobs))

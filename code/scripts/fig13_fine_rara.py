"""Fine RA->RA sweep (28-31 nS in 0.25 nS steps, 2 seeds), appended to robust_fig13.jsonl
under the same tag: the coarse 4-nS grid of robustness.py fig13 straddles the narrow window."""

import json, os, sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("HVC_CONFIG", "configs/final.json")
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np
from phase1_seeds import CONFIG
from robustness import job_point

if __name__ == "__main__":
    jobs = [("fig13:g_RA_RA", dict(CONFIG, g_RA_RA=round(float(v), 3)), s, None)
            for v in np.arange(28.0, 31.01, 0.25) for s in (0, 1)]
    with Pool(8) as pool, open(HERE.parents[1] / "results/robust_fig13.jsonl", "a") as f:
        for res in pool.imap_unordered(job_point, jobs):
            f.write(json.dumps(res) + "\n")
    print(len(jobs))

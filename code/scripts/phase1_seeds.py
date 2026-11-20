"""Phase-1 configuration evaluated over wiring seeds; writes results/phase1_seeds.jsonl."""

import json, sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from calibrate_random import run

CONFIG = {k: v for k, v in json.load(open(HERE.parent / "configs/phase1.json")).items()
          if not k.startswith("_")}

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    out = HERE.parents[1] / "results/phase1_seeds.jsonl"
    with Pool(8) as pool, open(out, "w") as f:
        for res in pool.starmap(run, [(CONFIG, s) for s in range(n)]):
            f.write(json.dumps(res) + "\n")
    print(out)

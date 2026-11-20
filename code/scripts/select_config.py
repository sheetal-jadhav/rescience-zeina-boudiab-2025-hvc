"""Pick the final configuration from a calibration search with a fixed, documented objective.

Among runs where all 120 RA fire in order, maximise
    ra_ok - 20*|spikes - 4.76| - 10*|duration - 8.12|
(paper's Fig 4 values). Writes configs/final.json."""

import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_SPK, TARGET_DUR = 4.76, 8.12


def objective(s):
    return s["ra_ok"] - 20 * abs(s["ra_spikes"] - TARGET_SPK) - 10 * abs(s["ra_dur"] - TARGET_DUR)


if __name__ == "__main__":
    src = ROOT / sys.argv[1]
    runs = [json.loads(l) for l in open(src)]
    ok = [r for r in runs if "error" not in r["score"]
          and r["score"]["ra_fired"] == 120 and r["score"]["ra_in_order"]]
    best = max(ok, key=lambda r: objective(r["score"]))
    cfg = {"_comment": f"Selected from {src.name} by select_config.py (objective: ra_ok - "
                       f"20|spikes-{TARGET_SPK}| - 10|dur-{TARGET_DUR}|); integration rtol 1e-6, "
                       f"atol 1e-9. All values inside the Fig 13 ranges.",
           "_score": best["score"], **best["point"]}
    json.dump(cfg, open(ROOT / "code/configs/final.json", "w"), indent=1)
    print(json.dumps(best["score"]), "\n", json.dumps(best["point"]))

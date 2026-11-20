"""Phase-1 config evaluated with the equation forms found in the authors' single-cell code
(alpha_h +50, theta_aT -65, RTF 26.7, bT^3, voltage-dependent tau_n; phi_rT unused)."""

import json, sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from calibrate_random import run
from phase1_seeds import CONFIG

CODE_FORMS = {"sw_alpha_h_offset": 50.0, "sw_theta_aT": -65.0, "sw_RTF": 26.7, "sw_bT_exponent": 3}

if __name__ == "__main__":
    cfg = dict(CONFIG, **CODE_FORMS)
    out = HERE.parents[1] / "results/phase2_codeforms_seeds.jsonl"
    with Pool(8) as pool, open(out, "w") as f:
        for res in pool.starmap(run, [(cfg, s) for s in range(16)]):
            f.write(json.dumps(res) + "\n")
    print(out)

"""Exploratory 'minimal sufficient change' study (NOT part of the replication proper).

One hypothesis at a time on the frozen Phase-1 configuration; each value is labelled with
how far it lies from the published value or range. Writes results/minimal_change.jsonl."""

import json, sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from calibrate_random import run
from phase1_seeds import CONFIG

SEEDS = range(4)
TAU_R0, TAU_R1 = 200.0, 87.5

SWEEPS = {
    "baseline": [{}],
    # H1: faster ICaT de-inactivation (scale both rT time-constant terms)
    "H1_tau_rT_scale": [{"gt_tau_r0": TAU_R0 * f, "gt_tau_r1": TAU_R1 * f, "_x": f}
                        for f in (0.5, 0.25, 0.1, 0.05)],
    # H2: more negative HVC(X) rest via a constant bias current (pA)
    "H2_X_bias_pA": [{"Ibias@X": b, "_x": b} for b in (-25.0, -50.0, -100.0, -150.0)],
    # H3: stronger drive onto interneurons (published RA->INT range 10-45 nS)
    "H3_RA_INT_nS": [{"g_RA_INT": g, "_x": g} for g in (60.0, 90.0, 135.0)],
    # H4a: stronger inhibition onto X (published INT->X range 6-42 nS)
    "H4a_INT_X_nS": [{"g_INT_X": g, "_x": g} for g in (60.0, 120.0, 240.0)],
    # H4b: longer GABA-A decay (published ad = 0.18 /ms, i.e. 5.6 ms)
    "H4b_gaba_decay_ms": [{"kin_ad_gaba": 1.0 / t, "_x": t} for t in (11.0, 22.0, 44.0)],
}

if __name__ == "__main__":
    jobs = []
    for name, points in SWEEPS.items():
        for p in points:
            x = p.get("_x")
            cfg = dict(CONFIG, **{k: v for k, v in p.items() if not k.startswith("_")})
            jobs += [(name, x, cfg, s) for s in SEEDS]
    out = HERE.parents[1] / "results/minimal_change.jsonl"

    def tag(args):
        return args

    with Pool(8) as pool, open(out, "w") as f:
        for (name, x, cfg, s), res in zip(jobs, pool.starmap(run, [(c, s) for _, _, c, s in jobs])):
            res.update({"hypothesis": name, "x": x})
            f.write(json.dumps(res) + "\n")
    print(out, len(jobs))

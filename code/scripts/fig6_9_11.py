"""Figs 6, 9, 11: single-neuron intrinsic perturbations that break the RA sequence.

The paper shows one hand-picked example per perturbation. Here each perturbation is applied to
N_TARGETS randomly chosen neurons of the relevant class in each of SEEDS networks, and we
report how often the chain breaks and whether the break follows the paper's mechanism:
  RA (Fig 6):  the perturbed RA loses its burst, so the chain stops there.
  INT (Fig 9): the perturbed INT fires more and a RA it inhibits loses its burst.
  X (Fig 11):  the perturbed X fires more, the INTs it excites fire more, and a RA they
               inhibit loses its burst.
Multipliers are the paper's (Fig 6B, 9, 11 legends). The Fig 6A gA increase isn't reported
(T-10), so a range of factors is tested."""

import json, sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np
from calibrate_random import to_kwargs
from phase1_seeds import CONFIG
from hvcnet.analysis import bursts
from hvcnet.evaluate import simulate
from hvcnet.network import AMPA, GABA, build

SEEDS = (0, 1)
N_TARGETS = 8
PERTURBATIONS = {
    "fig6A_RA_gA_x1.5": ("RA", "gA", "mul", 1.5),
    "fig6A_RA_gA_x2": ("RA", "gA", "mul", 2.0),
    "fig6A_RA_gA_x3": ("RA", "gA", "mul", 3.0),
    "fig6B_RA_gSK_x15": ("RA", "gSK", "mul", 15.0),
    "fig9A_INT_gCaT_x10": ("INT", "gCaT", "mul", 10.0),
    "fig9B_INT_gH_x10": ("INT", "gH", "mul", 10.0),
    "fig11A_X_gH_x10": ("X", "gH", "mul", 10.0),
    "fig11B_X_gCaT_x15": ("X", "gCaT", "mul", 15.0),
    "fig11C_X_gSK_0": ("X", "gSK", "set", 0.0),
}


def chain_break(net, sp):
    """Chain position of the first RA that doesn't fire in order (None if the chain completes)."""
    chain = net.chain_order()
    last = -np.inf
    for pos, j in enumerate(chain):
        if not len(sp[j]) or sp[j][0] <= last:
            return pos
        last = sp[j][0]
    return None


def targets(net, seed):
    rng = np.random.default_rng(1000 + seed)
    chain = net.chain_order()
    return {"RA": rng.choice(chain[5:-5], N_TARGETS, replace=False),
            "INT": rng.choice(net.int_, N_TARGETS, replace=False),
            "X": rng.choice(net.x, N_TARGETS, replace=False)}


def job(args):
    name, seed, idx = args
    kw = to_kwargs(CONFIG)
    if name == "baseline":
        net, r, sp = simulate(seed=seed, **kw)
    else:
        cls, attr, op, val = PERTURBATIONS[name]
        net, r, sp = simulate(seed=seed, per_neuron={attr: {int(idx): (op, val)}}, **kw)
    return {"name": name, "seed": seed, "idx": None if idx is None else int(idx),
            "spikes": [len(s) for s in sp], "first": [float(s[0]) if len(s) else None for s in sp],
            "bursts": [len(bursts(s, min_spikes=1)) for s in sp],
            "break_pos": chain_break(net, sp)}


if __name__ == "__main__":
    jobs = [("baseline", s, None) for s in SEEDS]
    for s in SEEDS:
        tg = targets(build(to_kwargs(CONFIG)["spec"], seed=s), s)
        for name, (cls, *_rest) in PERTURBATIONS.items():
            jobs += [(name, s, i) for i in tg[cls]]
    out = HERE.parents[1] / "results/fig6_9_11.jsonl"
    with Pool(8) as pool, open(out, "w") as f:
        for res in pool.imap_unordered(job, jobs):
            f.write(json.dumps(res) + "\n"); f.flush()
    print(out, len(jobs))

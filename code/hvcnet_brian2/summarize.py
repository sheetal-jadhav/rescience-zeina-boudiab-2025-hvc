"""Table: original paper vs SciPy (hvcnet) vs Brian2 (hvcnet_brian2), from results/*.jsonl.
Writes results/brian2_vs_paper.md."""
import json
from pathlib import Path

import numpy as np

RES = Path(__file__).resolve().parents[2] / "results"


def load(name):
    p = RES / name
    return [json.loads(l)["score"] for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def ms(rows, key):
    v = np.array([r[key] for r in rows], dtype=float)
    return f"{np.nanmean(v):.2f} ± {np.nanstd(v):.2f}" if len(v) else "n/a"


def chain(rows):
    return f"{sum(r['ra_fired'] == 120 and r['ra_in_order'] for r in rows)}/{len(rows)}" if rows else "n/a"


def broken(rows):
    return f"{sum(not (r['ra_fired'] == 120 and r['ra_in_order']) for r in rows)}/{len(rows)}" if rows else "n/a"


def x_ok(rows):
    return f"{sum(r['x_ok'] for r in rows)}/{50 * len(rows)}" if rows else "n/a"


def med(rows, key):
    return f"{np.median([r[key] for r in rows]):.1f}" if rows else "n/a"


sp, b2 = load("robust_seeds.jsonl"), load("brian2_seeds.jsonl")
spx, b2x = load("robust_noX.jsonl"), load("brian2_noX.jsonl")
sp12, b212 = load("fig12.jsonl"), load("brian2_fig12.jsonl")
rows = [
    ("Fig 4: chain completes, in order", "yes", chain(sp), chain(b2)),
    ("Fig 4: HVC(RA) spikes per burst", "4.76 ± 0.48", ms(sp, "ra_spikes"), ms(b2, "ra_spikes")),
    ("Fig 4: HVC(RA) burst duration (ms)", "8.12 ± 0.89", ms(sp, "ra_dur"), ms(b2, "ra_dur")),
    ("HVC(RA) meeting the burst criterion (of 120)", "120", ms(sp, "ra_ok"), ms(b2, "ra_ok")),
    ("Figs 7B/10: HVC(X) meeting the 1-4 bursts, 4-9 spikes criterion", "all", x_ok(sp), x_ok(b2)),
    ("HVC(X) spikes per burst (median)", "4-9", med(sp, "x_spb_med"), med(b2, "x_spb_med")),
    ("Figs 7A/8: interneuron spikes per 400 ms (median)", "dense", med(sp, "int_spikes_med"), med(b2, "int_spikes_med")),
    ("HVC(X) removed: chain completes", "not tested", chain(spx), chain(b2x)),
    ("Fig 12: per-neuron HVC(X) variation, chain broken", "59/100 disrupted", broken(sp12), broken(b212)),
]
table = ["| Measure | Original paper | SciPy (hvcnet) | Brian2 (hvcnet_brian2) |", "|---|---|---|---|"]
table += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
note = (f"\nNetworks: {len(sp)} / {len(b2)} wiring seeds (Fig 4 rows), {len(spx)} / {len(b2x)} without "
        f"HVC(X), {len(sp12)} / {len(b212)} Fig 12 runs (SciPy / Brian2). Mean ± SD across networks.\n")
out = "\n".join(table) + "\n" + note
(RES / "brian2_vs_paper.md").write_text(out)
print(out)

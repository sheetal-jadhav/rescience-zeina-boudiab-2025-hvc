"""Grid over RA capacitance (Cm, not reported: I-01) and RA adaptation (gSK, gA, within Fig 13
ranges) on the 15-neuron RA chain of fig4_burst_isi.py. Target: Fig 4, 4.76 spikes in 8.12 ms.
Run from code/: ../.venv/bin/python -I scripts/fig4_cm_grid.py -> results/fig4_cm_grid.json"""
import itertools
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fig4_burst_isi as f  # noqa: E402

GRID = list(itertools.product([11.0, 12.0, 13.0, 14.0], [9.0, 10.5, 12.0, 12.5], [1.0, 5.0, 10.0, 14.0]))


def job(p):
    cm, gsk, ga = p
    try:
        r = f.chain(cell={"Cm": cm, "gSK": gsk, "gA": ga})
    except Exception as e:
        r = {"propagates": False, "error": repr(e)}
    return [cm, gsk, ga, r]


if __name__ == "__main__":
    with Pool(8) as P:
        res = P.map(job, GRID)
    json.dump(res, open(HERE.parents[1] / "results/fig4_cm_grid.json", "w"))
    ok = [x for x in res if x[3].get("propagates")]
    ok.sort(key=lambda x: abs(x[3]["spikes"] - 4.76) + 0.5 * abs(x[3]["dur"] - 8.12))
    print(f"{len(ok)}/{len(res)} propagate\nCm   gSK   gA    spikes  dur    ISI")
    for a, b, c, r in ok[:14]:
        print(f"{a:4} {b:5} {c:5}   {r['spikes']:.2f}  {r['dur']:5.2f}  {r['isi']:.2f}")

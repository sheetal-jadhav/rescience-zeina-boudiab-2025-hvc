#!/bin/sh
# Brian2 implementation: test, cross-check against the SciPy implementation, and score against
# the original paper. Run from anywhere; results go to results/.
#   1-2 min   test (small network, two time steps)
#   ~10 min   compare_scipy.py: 5 networks, SciPy RK45 vs Brian2 RK4 at dt 0.01 and 0.025 ms
#   ~20 min   vs_paper.py: 50 networks (Fig 4), 16 without HVC(X), 100 for Fig 12 (6 processes)
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${PYTHON:-$ROOT/.venv/bin/python}"
"$PY" -m pytest -q "$ROOT/code/tests/test_brian2.py"
"$PY" "$ROOT/code/hvcnet_brian2/compare_scipy.py"
"$PY" "$ROOT/code/hvcnet_brian2/vs_paper.py"
"$PY" "$ROOT/code/hvcnet_brian2/summarize.py"

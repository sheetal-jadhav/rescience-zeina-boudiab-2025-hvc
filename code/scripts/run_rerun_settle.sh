#!/bin/sh
# Rerun every article result after making the settling step use tight tolerances
# (2026-11-21). The configuration (configs/final.json) is kept as selected.
set -e
cd "$(dirname "$0")/.."
PY=../.venv/bin/python
export HVC_CONFIG=configs/final.json
date; $PY -I hvcnet_brian2/compare_scipy.py 2>&1 | grep -v "WARNING\|INFO"
for part in seeds noX pern solver noise fig13; do date; echo "== robustness $part"; $PY -I scripts/robustness.py $part; done
for s in fig6_9_11 fig6_9_11_followup fig5_delay fig2_pairs fig12 fig13_fine_rara; do date; echo "== $s"; $PY -I scripts/$s.py; done
$PY -I scripts/article_figures.py && $PY -I scripts/make_figures.py
date; echo RERUN_DONE

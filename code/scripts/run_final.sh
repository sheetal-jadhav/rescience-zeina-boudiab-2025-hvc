#!/bin/sh
# Full article pipeline at accurate tolerances (rtol 1e-6, atol 1e-9).
set -e
cd "$(dirname "$0")/.."
PY=../.venv/bin/python
$PY -I scripts/calibrate_random.py 200 ../results/random_tight.jsonl 1
$PY -I scripts/select_config.py results/random_tight.jsonl
export HVC_CONFIG=configs/final.json
for part in seeds noX pern solver noise fig13; do $PY -I scripts/robustness.py $part; done
$PY -I scripts/fig6_9_11.py
$PY -I scripts/fig6_9_11_followup.py
$PY -I scripts/fig5_delay.py
echo PIPELINE_DONE

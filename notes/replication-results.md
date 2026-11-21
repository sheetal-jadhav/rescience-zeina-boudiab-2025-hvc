# Replication results by figure (final; feeds the article)

**Setup:**
- configuration `code/configs/final.json`, chosen by `select_config.py` from 200 runs within the
  Fig 13 ranges
- RK45 with rtol 1e-6, atol 1e-9
- 400 ms runs, kick 500 pA × 10 ms into RA1
- figures in `figures/replication_figN.png`, laid out like the original Fig N
- earlier loose-tolerance results kept as `results/*_rtol1e-3.*`

| Fig | Original | Replication | Verdict |
|---|---|---|---|
| 2 | Pair responses match Mooney & Prather (2-5 mV PSPs, subthreshold) | With network-strength synapses, PSPs are 10-12 mV and suprathreshold. Pair conductances not reported; supplied "Fig 2" code is single-neuron | **Not reproduced** (pair conductances unknown) |
| 4 | All 120 RA fire once, in order; 4.76 ± 0.48 spikes, 8.12 ± 0.89 ms | **50/50 networks** propagate in order; 3.93 ± 0.12 spikes, 8.61 ± 0.35 ms; 115/120 RA meet the criterion; 1.96 ms per link | **Reproduced** (≈0.8 fewer spikes per burst) |
| 5 | ↑gAMPA shortens the delay and adds spikes; ↑gA lengthens it (~3.4 → 7 ms bars) | 10 → 12 nS: 5.6 → 4.6 ms, 1 → 2 spikes. gA 10 → 13: 5.6 → 5.8 ms. The Fig 5A legend contradicts its own text | **Direction reproduced, magnitude not** (gA effect ~15× smaller) |
| 6 | ↑gA or gSK ×15 in one RA silences it and breaks the chain | Configured INT->RA: 0/16 breaks (gA ×1.5-3, gSK ×15). With INT->RA 5 nS: gA ×20 and gSK ×60 break 8/8 at the perturbed RA; gA ≤ ×10 breaks 0/8; gSK ×15 breaks 1/8 (four neurons downstream) | **Mechanism reproduced only with much larger perturbations** |
| 7 | INT dense bursts; X 1-4 rebound bursts of 4-9 spikes | INT sparse (median 8 spikes / 400 ms); X single spikes, 27 ± 2 of 50 silent, 0/50 meet the criterion | **Not reproduced** |
| 8 | INT bursts aligned to its RA/X inputs; dense when inputs coincide | INT spikes aligned to its RA inputs (1-3 spikes each) but no dense bursts | **Partly** (alignment yes, density no) |
| 9 | INT gCaT ×10 or gH ×10 → dense INT firing silences a target RA, breaking the chain | The perturbed INT fires more, but 0/24 breaks (both INT->RA levels) | **Not reproduced** |
| 10 | X escapes INT inhibition with multi-spike rebound bursts | X single rebound spikes | **Not reproduced** |
| 11 | X gH ×10, gCaT ×15 or gSK = 0 → X->INT->RA breaks the chain | X fires more (e.g. gH ×10: regular spiking), but 0/24 breaks | **Not reproduced** |
| 12 | Per-neuron X conductance variation: 59/100 runs disrupted | 0/100 runs break the chain; RA criterion 113.5/120 on average; X/INT unrealistic in every run (as at baseline) | **Not reproduced** (the RA chain is insensitive to X) |
| 13 | Allowed ranges (narrowest: RA->RA ~29-31 nS, INT->RA ~2-5 nS) | RA->RA allowed **28.0-30.5 nS** (agrees with the original's narrow window). gSK@RA ≥ ~11.6 (upper part of 9-12.5). gA@RA ≥ ~5.6 (upper part of 1-14). All X/INT intrinsic and other synaptic values pass across and beyond their ranges, including INT->RA 1-7.5 nS | **RA->RA window reproduced**; the other ranges are wider, because the RA chain doesn't depend on X/INT |

## Robustness (not in the original)
- **Solver:** with MATLAB-default tolerances (RK45 1e-3/1e-6), first-spike times deviate by up to
  ~8 ms along the chain and bursts lengthen (10.9 vs 8.6 ms). The RA criterion drops from 115 to
  44/120. RK4 at 0.025 and 0.01 ms agrees with tight RK45 to within 0.4 and 0.03 ms.
- **Noise** (additive, σ in pA·ms^½, RK4 0.01 ms):
  - σ ≤ 10: no effect
  - σ = 20: RA criterion 89/120
  - σ = 40: 51/120
  - σ = 80: 9/120 (chain still complete)
  - σ = 160: chain breaks 4/4
- **Per-neuron RA/INT conductances within the published ranges:** the chain completes 16/16, but
  only 7/120 RA meet the criterion (5.6 spikes, 14 ms), because most of the published gSK@RA
  range is below the ~11.6 nS threshold.
- **HVC(X) removed** (eLife Reviewer 2's question): the chain completes 16/16 with the RA
  criterion at 115/120. The sequence doesn't need HVC(X) in this model.

## Overall
1. The RA sequence (Fig 4) and the narrow RA->RA window (Fig 13) reproduce from the text.
2. The X and INT phenotypes (Figs 7, 8, 10) don't, and neither does any result that depends on
   them (Figs 9, 11, 12). In the reproduced model the chain is far more robust to single-neuron
   perturbations than reported.
3. Results depend strongly on solver tolerance.
4. The supplied code doesn't implement the network (Phase 2), so the cause of the X/INT
   discrepancy can't be established without the authors.

**Updated 2026-11-21** after the settling-tolerance fix (rerun of all results; see issues log).

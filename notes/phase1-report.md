# Phase 1 report: reproduction from text only

Closed 2026-11-20. Git tag `phase1-complete`.

## Sources used
- Bou Diab, Chammas & Daou 2025 (eLife): text, appendix and figures
- Daou et al. 2013 (J Neurophysiol): paper, plus that paper's own published code (Bertram lab
  site). This is the cited predecessor model, not Bou Diab's code.
- Destexhe, Mainen & Sejnowski 1994: synaptic reversal potentials only

**Not used:** Bou Diab's supplementary code. It was downloaded on 2026-11-20 into
`original-code-DO-NOT-OPEN-UNTIL-PHASE-2/` and left unopened. SHA-256 checksums at closing:

```
3db9cc2809cea935d771b27224a034306051a10271852fa5bad350c496fc295b  elife-105526-code1.zip
460f3027cbeb7baf10fbafa9a0aa47f0217fd0bba1e4dece463b0f0f8617f9bb  elife-105526-code2.zip
12b490f54b14c20063cfe89bed6e1e2ed5d6fe384cc2f8d22ce9402b597bd1c1  elife-105526-code3.zip
70f3a18b72c7e1a354b8abf9eee4fa6ca354a307e741b1374b42ef1dfd77bc99  elife-105526-fig2-code1.zip
1579923ed5d3ead1368135ffbaad3dc87fe0851e61fbf2ffeab23e958de4ecee  elife-105526-fig2-code2.zip
6012f6d7bd45c6e0691623c223b8d88ce599a9bc12b6b443f0fec2de4dcfd64f  elife-105526-fig2-code3.zip
56ffb13b644ba7a051a3fa9796ff9f334fcd34240de1c6127a586663e38f3263  elife-105526-fig2-code4.zip
```

## Frozen Phase-1 configuration
`code/configs/phase1.json`. All values are inside the Fig 13 ranges.
- **Switches:** bT exponent 3 [Daou13], αh +15 [text], τn voltage-dependent [Daou13]
- **Other fixed choices:** see `notes/issues-log.md`
- **Start input:** 500 pA for 10 ms into RA1
- **Solver:** RK45, rtol 1e-3, atol 1e-6

## Results over 16 wiring seeds (`results/phase1_seeds.jsonl`)

| Quantity | Paper | Phase 1 (mean ± SD across seeds) | Verdict |
|---|---|---|---|
| RA propagate through the full chain, in order | yes | **16/16 seeds** | **Reproduced** |
| RA spikes per burst | 4.76 ± 0.48 | 3.97 ± 0.11 | Close (within the 3-6 criterion) |
| RA burst duration | 8.12 ± 0.89 ms | 9.17 ± 0.38 ms | Close (≤ 10 ms criterion met on average) |
| RA meeting the paper's criterion (one burst, 3-6 spikes, ≤ 10 ms) | all ("desired" network) | 89.9 ± 7.1 / 120 | Partly |
| Delay per chain link | ~1.4 ms (Fig 4 slope); "5 ms" (Fig 4 inset) | 2.09 ± 0.01 ms | Not comparable (paper inconsistent, I-18) |
| X: 1-4 bursts of 4-9 spikes | yes (Figs 7B, 10) | **0/50 X meet it**; median 1 spike per "burst"; 12.3 ± 1.8 X silent | **Not reproduced** |
| INT dense bursting throughout song | yes (Fig 7A: bursts of 5-30 spikes at very high rate) | median 23.7 spikes per 400 ms | **Not reproduced** (too sparse) |
| Fig 2 pair calibration (Mooney & Prather PSPs 2-5 mV, subthreshold) | Fig 2 | With network-strength synapses: IPSPs 10-12 mV; RA->INT and X->INT drive spikes | **Not reproduced**; pair conductances not given (new issue I-19) |

**Calibration search behind this:** 290 runs within the Fig 13 ranges (grid, random search,
capacitance scan).
- RA behaviour is reproducible inside the published ranges.
- The X rebound-burst phenotype was never obtained anywhere in them.

**Mechanistic hypothesis:** the ICaT availability gate rT has τ ≈ 287.5 ms at all
physiological voltages, so brief network IPSPs can't de-inactivate it. The isolated X does
fire a ~10-spike rebound after 500 ms of inhibition (Fig 2D protocol), which supports this.

## New issues found in Phase 1
- **I-17:** the Fig 5A legend contradicts the text on the direction of the gAMPA effect.
- **I-18:** the Fig 4 inset "5 ms" doesn't match the raster slope (~1.4 ms).
- **I-19 (new):** Fig 2 must use pair conductances far below the network (Fig 13B) values to
  get Mooney & Prather's 2-5 mV PSPs. These pair values aren't reported.
- **D-06:** with the text's constant τn = 10 ms, spikes are ~10 ms wide and RA can't burst.
  The voltage-dependent τn of Daou 2013 is required.
- **D-01 … D-08:** the Bou Diab text and Daou 2013 conflict (see the issues log). Two of these
  are printed errors shared by both papers (αh in the code, the rs∞ sign).

## Questions for Phase 2 (in priority order)
1. Why do X fire multi-spike rebound bursts in the original? Check: T-current equations and
   constants (rT kinetics, θrrT sign, φrT), X resting potential, X->INT and INT->X wiring and
   strengths.
2. Why are INT so much more active? Check: RA->INT, X->INT counts and strengths, INT intrinsic
   parameters and initial state.
3. The default values of every variable conductance (I-05, I-06), Cm (I-01), the start input
   (I-07), noise (I-08), tolerances and seeds (I-09).
4. Which of the printed-equation forms (D-01 … D-07, T-04) does the code use?
5. The Fig 2 pair conductances (I-19).

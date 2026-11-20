# Replication results by figure (living document; feeds the article)

Configuration: `code/configs/phase1.json` unless noted. All runs are logged in `results/`.

| Fig | Paper | Our result | Verdict |
|---|---|---|---|
| 2 | Paired PSPs match Mooney & Prather (2-5 mV, subthreshold) | With network-strength synapses, PSPs are 10-12 mV and suprathreshold. Pair conductances aren't reported, and the supplied "Fig 2" code is single-neuron (Daou 2013 ports). | **Not reproducible as published** (I-19, I-15) |
| 4 | 120 RA fire once each, in order; 4.76 ± 0.48 spikes, 8.12 ± 0.89 ms | 16/16 seeds propagate in order; 3.97 ± 0.11 spikes, 9.17 ± 0.38 ms | **Reproduced** (burst size slightly smaller) |
| 5 | gAMPA 10 → 12 nS shortens the delay and adds spikes; gA 10 → 13 nS lengthens the delay (bars ~3.4 → ~7 ms) and removes spikes; post burst ~6 spikes | gAMPA 10 → 12: 5.56 → 4.61 ms, 1 → 2 spikes. gA 10 → 13: 5.56 → 5.78 ms, spikes unchanged. Full sweeps: delay falls monotonically with gAMPA (7.4 → 1.6 ms over 8-34 nS) and rises weakly with gA (5.1 → 6.0 ms over 1-15 nS). Post burst 1-2 spikes at 10-12 nS (4 spikes at ~30 nS, the network value). | **Qualitative directions reproduced (as stated in the text); magnitudes not.** The Fig 5A legend contradicts the text (I-17). |
| 6 | Raising gA (factor unreported) or gSK ×15 in one RA silences it and breaks the chain | Frozen config (INT->RA 2.01 nS): no break up to gA ×3, gSK ×15 (1/16). With INT->RA 5 nS (top of range): gA ×20 and gSK ×60 break the chain at the perturbed RA in 8/8; gSK ×15 breaks 6/8, but only 1/6 at the perturbed cell. | **Mechanism reproduced at larger factors**; the paper's ×15 isn't sufficient by itself |
| 7, 8, 10 | INT dense bursting; X 1-4 rebound bursts of 4-9 spikes | INT too sparse; X single spikes (0/50 meet the criterion), robust across 290 calibration runs and every equation form in the supplied code | **Not reproduced** |
| 9 | INT gCaT ×10 or gH ×10 makes that INT fire densely and silences a target RA, breaking the chain | The perturbed INT fires +6 to +18 spikes, but the chain breaks 0/16 (INT->RA 2 nS) and 0/8 (INT->RA 5 nS) | **Not reproduced** (effect on the INT yes, on the chain no) |
| 11 | X gH ×10, gCaT ×15, or gSK = 0 makes the X -> INT -> RA path break the chain | X fires +5 to +10 spikes. Breaks 0/16 at 2 nS. At 5 nS: gCaT ×15 2/8, gSK = 0 1/8, gH ×10 0/8. | **Largely not reproduced** |
| 12 | Varying X conductances per neuron: 59/100 runs disrupted | not run (depends on the X phenotype, which isn't reproduced) | pending |
| 13 | Allowed ranges | Used as search bounds. Within them, RA is reproducible, X/INT not. | pending (formal range search) |

**Overall:** the RA chain is reproducible and **more robust than the paper reports**. The
paper's single-neuron perturbations (Figs 9, 11) don't break it within the published inhibitory
range. This is consistent with the X/INT phenotypes not being reproduced: in the paper, those
breaks run through dense INT firing.

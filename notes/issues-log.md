# Issues log: Bou Diab et al. 2025

Status: `OPEN`, then resolved as `[Daou13]`, `[code]` or `[our choice]`. Every
entry ends up in the article's "Reproducibility notes" table.

## Missing values (gaps)
| ID | Item | Status |
|---|---|---|
| I-01 | Membrane capacitance Cm | OPEN → Daou13 |
| I-02 | Ca_ex, F, R, T (temperature) for the GHK Ca currents | OPEN → Daou13 |
| I-03 | kr (fast fraction of IH) | OPEN → Daou13 |
| I-04 | V_AMPA, V_GABA-A reversal potentials | OPEN → Daou13 / Destexhe 1994 |
| I-05 | Default (non-varied) values of gA, gSK, gH, gCaT; only Fig 13 ranges given | OPEN |
| I-06 | Default synaptic conductances per connection type; only Fig 13B ranges given | OPEN |
| I-07 | Start input to RA1: amplitude, duration, noise | OPEN |
| I-08 | Noise σ: units ("% of mean synaptic conductance" applied as a current); on or off in the main figures | OPEN |
| I-09 | Integrator tolerances (ode45 RelTol/AbsTol), initial conditions, run length, random seeds | OPEN |
| I-10 | How the totals of 120/50/50 are enforced when per-MC counts are random (20 × U(3,10) has mean 130) | OPEN |
| I-11 | INT inputs: split between own-MC and other-MC RA (3-8 total) | OPEN |
| I-12 | Spike/burst detection definitions used for the 3-6 spikes, ≤ 10 ms and 4-9 spikes criteria | OPEN |
| I-13 | ODE counts per cell (6/8/7) don't map uniquely onto the listed state variables (e.g. is [Ca] integrated in INT, which has no ISK?) | OPEN → Daou13 |

## Apparent typos in the printed equations
| ID | Location | As printed | Likely intended | Status |
|---|---|---|---|---|
| T-01 | Eq 9 | dx/dt = (x∞(V) − **V**)/τx | (x∞ − x)/τx | OPEN |
| T-02 | Eq 17 | rT∞ uses θaT, σaT | θrT, σrT (both listed in Table 1 but otherwise unused) | OPEN |
| T-03 | Eq 21 | + kCa([Ca] − bCa) | − kCa([Ca] − bCa) (as printed, Ca grows without bound) | OPEN |
| T-04 | Synapse [T] | 1/(1 + exp((Vpre − VT)/Kp)) | 1/(1 + exp(−(Vpre − VT)/Kp)) (Destexhe 1994); as printed, transmitter is released at rest | OPEN |
| T-05 | Eq 26 | d rs/**ds** | d rs/dt | OPEN |
| T-06 | Eq 7, 13 | GHK term Ca_ex/(1 − e^{2FV/RT}) without a V factor | probably V·Ca_ex/(1 − e^{2FV/RT}); check Daou13 | OPEN |
| T-07 | Table 1 | VCa = −85 mV; never used with GHK | remove, or the source used an Ohmic Ca current? | OPEN |
| T-08 | Table 1 | τhp = 1000 ms; no equation uses it | ? | OPEN |
| T-09 | Table 1 | σs = −0.05 mV (extremely steep s∞) | maybe −5? check Daou13 | OPEN |
| T-10 | Fig 6 legend | "gSK from 15-fold nS"; the gA increase value is missing | not determinable from the text | OPEN |

## Internal inconsistencies
| ID | Item | Status |
|---|---|---|
| I-14 | Fig 5 uses RA->RA gAMPA = 10 and 12 nS, but Fig 13B gives the allowed RA->RA range as ~29-31. Different units/normalisation, or a 2-cell test outside network conditions? | OPEN |
| I-15 | Methods: code "will be made available … on ModelDB". The data-availability statement says code is provided for Figs 2 and 4-12. The supplement holds 3 network files plus 4 Fig 2 files; Fig 13 code is absent. | noted |
| I-16 | Fig 13 axes have no units | OPEN |

## Resolution pass 1: Daou et al. 2013 (2026-11-20)

Sources: Daou 2013 paper PDF (Bertram lab site, `reference/papers/`) and Daou 2013's
**own published code** (`reference/daou2013-published-code/`, from
math.fsu.edu/~bertram/software/birdsong/JNP_13). This is the cited predecessor model, not Bou
Diab's code, so the Phase-1 independence protocol still holds. Tags: `[Daou13]` = paper text,
`[Daou13-code]` = their code.

**Phase-1 rule:**
1. Use Bou Diab's text when it is complete and physically sensible.
2. Otherwise use Daou 2013's text.
3. Otherwise use Daou 2013's code.
4. Every alternative is kept as a switch in `hvcnet/params.py` and tested for sensitivity.

| ID | Resolution |
|---|---|
| I-01 Cm | **RA 20 pF, X 100 pF, INT 75 pF** [Daou13 Table 2]. Caveat: Bou Diab retuned gK (RA 150 vs 400, X 80 vs 50, INT 1200 vs 1700) and gA/gSK, so they may also have changed Cm. Not determinable from the text. |
| I-02 | **Ca_ex = 2.5 mM** [Daou13]. T: the paper says 25 °C/298 K (RT/F = 25.7 mV); the code uses **RTF = 26.7 mV** (~37 °C). Default 25.7 mV (text); 26.7 is a switch. |
| I-03 kr | **X 0.3, INT 0.01** (RA 0.95, unused because Bou Diab's RA has no IH) [Daou13 Table 2] |
| I-04 | Not in Daou13. V_AMPA = 0 mV, V_GABA = −80 mV from Destexhe, Mainen & Sejnowski 1994 [our choice, cited] |
| I-13 | Bou Diab's ODE counts can't be matched exactly; we integrate a uniform state per cell (unused gates are harmless) [our choice] |
| T-01 | Confirmed typo: dx/dt = (x∞ − x)/τx [Daou13 eq 8] |
| T-02 | Confirmed typo: rT∞ uses θrT = −67, σrT = 2 [Daou13 eq 17, code]. τrT uses θrrT = 68, σrrT = 2.2 [Daou13-code] |
| T-03 | Confirmed typo: d[Ca]/dt = **−f[ε(ICaL + ICaT) + kCa([Ca] − bCa)]** [Daou13 eq 21, code] |
| T-05 | Confirmed typo: d/dt |
| T-06 | Confirmed: the GHK currents include a **V factor**: g·x·**V**·Ca_ex/(1 − e^{2V/RTF}) [Daou13 eqs 6 and 13, code] |
| T-07 | VCa is unused (GHK) |
| T-08 | τhp belongs to I_Nap, which Bou Diab dropped. Unused. |
| T-09 | σs = −0.05 matches Daou13 Table 1 and the XPP code. Daou's Fig-3 plotting script uses −1. Default −0.05. |

**New discrepancies found (Bou Diab text vs Daou13):**
| ID | Item | Phase-1 default | Alternative switch |
|---|---|---|---|
| D-01 | αh: both papers print exp((V+15)/−18); **Daou's code uses exp(−(V+50)/18)** | text (+15) | code (+50) |
| D-02 | rs∞: both papers print 1/(1 + exp(−(V−θrs)/σrs)), which makes Ih activate with depolarisation (unphysical); **the code has no minus sign** | **code (corrected)** | none |
| D-03 | bT exponent: Bou Diab 2, Daou paper and code 3 | Bou Diab (2) | 3 |
| D-04 | θaT: Bou Diab −64 mV, Daou −65 mV | Bou Diab (−64) | −65 |
| D-05 | σaT: Bou Diab +7.8 (gives an inactivation-shaped curve for an activation gate), Daou −7.8 | **−7.8 (corrected)** | none |
| D-06 | τn: Bou Diab constant 10 ms; Daou τ̄n/cosh((V−θn)/(2σn)) | Bou Diab (constant) | cosh |
| D-07 | φrT = 0.2 multiplies drT/dt in Daou's MATLAB code only (not the XPP code, not either paper) | none (1.0) | 0.2 |
| D-08 | Bou Diab dropped I_Nap and I_KNa (present in Daou13), and RA has no IH/ICaT, INT no IA/ISK (eqs 1-3) | follow Bou Diab | none |

The Bou Diab Phase-1 values remain open: the default gA/gSK/gH/gCaT values (I-05; Fig 13
medians used), the synaptic defaults (I-06; Fig 13B medians used), the start input (I-07),
noise (I-08) and the solver settings (I-09; MATLAB ode45 defaults RelTol 1e-3, AbsTol 1e-6
used).

## Phase-1 build notes (2026-11-20)

| ID | Item | Decision / status |
|---|---|---|
| D-06 (revised) | With BD's constant τn = 10 ms, every spike is ~10 ms wide and HVC(RA) can't burst (one spike per neuron, unlike BD Figs 2, 4 and 5 and Daou13). | **Default switched to the Daou13 voltage-dependent τn** (evidence-based); the constant is kept as a switch |
| D-01 (evidence) | αh +50 [Daou13-code] lowers X spike peaks to ~17 mV; +15 gives ~43 mV (single cell, constant τn) | keep +15 |
| I-17 | **Fig 5A legend vs text:** the text says raising gAMPA (10 -> 12 nS) *shortens* the delay, but in the figure the 10 nS trace (red) has the *shorter* delay bar (~3.4 ms vs ~7 ms) | OPEN |
| I-18 | **Fig 4:** the inset labels the delay between neighbours "5 ms", but the raster slope is ~1.4 ms per row (75 rows in ~107 ms at the 10 ms scale bar). The whole RA sequence (~170 ms) is drawn under a full song spectrogram. | OPEN |
| I-07 | Start input: 500 pA for 10 ms into RA1 (the Fig 2 protocol) | [ours] |
| num | Gating rates use V clipped to [-150, 100] mV so adaptive-solver trial stages can't produce inf/nan; currents use raw V | [ours]; check against fixed-step RK4 |

**First network result (seed 0, all defaults, RK45 rtol 1e-3):**
- 120/120 RA fire, in chain order
- one burst each, **4.78 ± 0.71 spikes** (paper 4.76 ± 0.48)
- burst duration 11.9 ± 2.5 ms (paper 8.12 ± 0.89)
- ~2.1 ms per link (paper Fig 4 ~1.4 ms)
- X: 0-12 bursts per neuron (paper 1-4); 0/50 meet the X criterion
- INT: dense firing (median ~40 spikes / 1 s)

Next: calibrate within the Fig-13 ranges (X gH/gCaT/gSK, INT->X, X->INT) for the X criterion, and the RA burst width.

## Calibration round 1 (2026-11-20)

- **Grid** (81 runs): X gCaT, gH, gSK × INT->X, within the Fig 13 ranges → `results/grid_x1.jsonl`
- **Random search** (200 runs): all 12 adjustable values uniform within the Fig 13 ranges, plus
  switches D-01 and D-03 → `results/random1.jsonl`. 0 errors; 199/200 propagate through all 120
  RA in order.
- **Capacitance scan** (9 runs): X Cm 100/50/25 pF × INT Cm 75/37.5/18.75 pF (Cm is a BD gap,
  I-01) → `code/scripts/cm_scan.py`

| Finding | Detail |
|---|---|
| **RA: reproducible within ranges** | Up to 104-111/120 RA meet the paper's criterion (one burst, 3-6 spikes, ≤ 10 ms). Burst duration is driven by gSK@RA (r = −0.77), gA@RA (−0.41) and g_RA_RA (+0.46). Example: gA 12.8, gSK 12.0 → 3.95 spikes, 9.1 ms, 2.1 ms per link. |
| **X: NOT reproducible within ranges** | In all 290 runs the median HVC(X) "burst" is **1 spike** (paper: 1-4 bursts of 4-9 spikes; Fig 7B, Fig 10). 0-3/50 X meet the criterion at best; 11-24 X stay silent. Unchanged by Cm, bT exponent or αh. |
| **INT firing too sparse** | Median 14-25 spikes per 400 ms (up to ~80 with Cm/4) vs Fig 7A bursts of 5-30 spikes at very high rate. Main driver: g_RA_INT (r = +0.82). |
| **Mechanistic reading** | The T-current availability gate rT has τ ≈ τr0 + τr1 = 287.5 ms at all physiological V (θrrT = +68 mV puts the sigmoid in saturation). At X rest (−62.5 mV) rT ≈ 0.1, so bT ≈ 0.03. The brief (~5-20 ms) IPSPs in the network can't de-inactivate ICaT, so X rebounds with one spike. Daou13's slice data (long current steps) don't test this regime. |
| **Candidate causes (to test)** | (1) sign of θrrT (Terman 2002 convention), (2) φrT, (3) X resting potential (more negative rest → rT available), (4) θaT −64/−65, (5) RTF, (6) INT drive structure, (7) a difference only the original code can reveal (Phase 2) |

## Phase 2 (2026-11-20): see `notes/phase2-report.md`
- **I-15 (upgraded, major):** the supplementary "network" code is a non-functional scaffold
  (no X, no RA<->INT synapses, placeholder INT). The "ODE file used in all simulations" is
  Daou 2013's single-neuron file, unchanged. The "Figure 2" code is ported Daou 2013
  single-neuron XPP files with no synapses. No figure from Figs 2 or 4-13 can be generated from
  the supplement.
- **Code settles (single cell):** D-02, D-03 (3), D-05, D-06 (cosh), D-07 (φrT unused), RTF
  26.7, T-03, T-06. **Code contradicts the text:** D-01 (+50), D-04 (−65), the presence of
  I_Nap/I_KNa, RA gK/gA values, RA gCaT.
- **Everything network-level remains OPEN**: not determinable from the published material.

## Search for the network code elsewhere (2026-11-20)
None found. Searched:
- ModelDB (API search "HVC": no Bou Diab/Daou network model)
- GitHub: repo search ("HVC network Daou", "Bou Diab HVC", "zebra finch HVC model"); the
  `daoulab` account's 3 repos (none HVC); `rbertram/birdsong`, which is Ross et al. 2017
  eNeuro, a 3-neuron network, not this paper
- Zenodo, Figshare, OSF
- bioRxiv preprint v1 (2024-11-17) and v2 (2025-08-22): both say "Source codes … will be made
  available online at our lab's website as well as on ModelDB"
- Daou lab website `sites.aub.edu.lb/daoulab/software/` (only SongSeq, the 2012 song-analysis
  tool)
- A web search

## Exploratory: minimal-sufficient-change study (2026-11-20; NOT replication)
`code/scripts/minimal_change.py` → `results/minimal_change.jsonl` (72 runs, 4 seeds each, Phase-1
config, one change at a time).

**Result: no single change produces HVC(X) bursts**, even far outside the published values.
The median spikes per X burst stays at 1 throughout.
- **H1, T-current recovery 2-20× faster:** single spikes, then silence.
- **H2, X bias current −25 to −150 pA:** single spikes, then silence.
- **H3, RA->INT 60-135 nS (range ≤ 45):** INT doubles to 48 spikes but X is unchanged.
- **H4a, INT->X 60-240 nS (range ≤ 42):** X unchanged.
- **H4b, GABA decay 11-44 ms (published 5.6):** X unchanged; RA chain degrades.

**The RA chain survives all of them** (71/72 runs).

**Interpretation:** the limit is the X *cell* model, not network drive. With BD/Daou X
parameters (gK 80 nS, no I_KNa), X can't fire above ~160 Hz (f-I test), whereas Fig 10 shows
X rebound bursts of ~5 spikes in ~10 ms (~500 Hz). The published X burst phenotype implies an
X cell different from the one specified in the text plus Daou 2013. Next: single-cell X
rebound tests (which intrinsic parameters allow high-frequency rebound bursts).

## Test: full Daou 2013 HVC(X) cell (2026-11-21)
Question: did Bou Diab run the network with Daou 2013's complete cells (with I_NaP, I_KNa)?
`code/scripts/daou13_xcell.py` reads parameters straight from Daou 2013's XPP files
(`results/daou13_xcell.jsonl`).

| Case | Spikes | Max rate |
|---|---|---|
| Figure_4.ode, +150 pA (as published) | 12 in 485 ms | 37 Hz |
| Figure_4.ode, +400 pA | 33 | 102 Hz |
| Figure_7.ode rebound, −120 pA 700 ms (as published, gK 1700) | 4 | 60 Hz |
| same, gK 50 / gK 80 | 8 / 7 | 86 / 83 Hz |
| Figure_4.ode, 50 ms −120 or −300 pA (IPSP-like) | 0 | none |
| Reduced (no NaP/KNa, gK 80) rebound | 7 | 78 Hz |

**Result: the full Daou 2013 X cell can't fire Bou Diab's rebound bursts either** (Fig 10:
~5 spikes in ~10 ms, ~500 Hz). Its maximum is ~100 Hz, and brief inhibition gives no rebound.
I_NaP/I_KNa barely matter. So "they used the 2013 cells unchanged" doesn't explain Figs 7B/10.
The X phenotype in the paper needs parameters that appear in neither paper nor either code base.

## Full re-read of the paper, including reviews and author response (2026-11-21)
New or sharpened items (reported as open in the article):
- **I-13 sharpened:** the ODE counts (RA 6, X 8, INT 7) vs eqs 1-3 (5, 7, 7) imply one extra
  state each in RA and X. That fits RA with I_CaT (rT; Daou13 RA gCaT 0.55) and X with I_A (e;
  Daou13 X gA 5). INT matches. This can't explain X bursting (I_A lowers excitability).
- **I-20:** conductance heterogeneity is contradictory. Results: "maximal conductances … for
  each model neuron … are all selected randomly". Methods: manually chosen defaults, varied at
  the population and single-neuron level, and X shared.
- **I-21:** the author response says the noise is on in the main simulations ("our model does,
  in fact, include a stochastic current") and that the start input goes to "a small HVC(RA)"
  group of one microcircuit. The Results say only HVC(RA)1.
- **I-22:** HVC(X) homogeneity is justified by Daou & Margoliash 2020 (Nat Commun 11:1964). The
  X parameters may come from those fits, not Daou 2013. No public code or parameter table found.
- **I-23:** the Fig 2 synaptic calibration was done by eye from published figures (author
  response), so there is no objective to reproduce.
- **Minor:** Fig 7B says X fire "2-4" bursts, while Methods and Discussion say 1-4. The Fig 10
  text says "HVCX1" for HVCX3.
- **For our Discussion:** the reviewers asked whether removing HVC(X) changes propagation, and
  the authors didn't test it. Our no-X run answers it: no effect. The eLife assessment calls the
  work "incomplete".


## Second implementation in Brian2, and a settling-tolerance fix (2026-11-21)
- **`code/hvcnet_brian2/`:** the same model, rewritten in Brian2 2.11 equation syntax with units
  (RK4, Cython code generation). Shared with `hvcnet`: parameter dataclasses and network wiring
  only. Test: `code/tests/test_brian2.py`.
- **Found by the cross-check:** `sim.settle()` ran the 500 ms pre-stimulus settling at SciPy's
  default tolerance (rtol 1e-3), not 1e-6. HVC(X) and interneurons that fire spontaneously keep
  firing while settling, so their spike times at the start of each run depended on that
  tolerance. On the 20-neuron test network:
  - with loose settling, 3/20 neurons had different spike counts in Brian2, by up to 6.8 ms,
    and the difference didn't shrink with Brian2's dt;
  - with tight settling, 20/20 counts match, and the maximum timing difference is 0.35 ms at
    dt 0.01 and 0.19 ms at dt 0.005 (first-order convergence).
- **Fix:** `settle()` now defaults to rtol 1e-6, atol 1e-9. All article results were rerun with
  `code/scripts/run_rerun_settle.sh`. The configuration `configs/final.json` was kept as
  selected; its calibration ran with the old settling.
- **Cross-check on full networks (5 seeds, `results/compare_brian2.jsonl`):** the chain propagates
  in all runs. Burst statistics agree in 4/5 seeds. For seed 1, Brian2 converges with dt to
  3.41 spikes per burst, against SciPy's 3.94.
- **Cause: chaos, not a coding difference.**
  - Isolated X and INT cells agree to within 0.03 ms in both codes.
  - During settling, 100/220 neurons fire spontaneously (an X <-> INT loop). The two codes match
    spike for spike until ~190 ms, when an X rebound spike amplifies a 0.02 ms input difference
    to 0.4 ms.
  - Perturbing only the SciPy initial voltages by 1e-9 mV reproduces Brian2's outcomes exactly
    (3.30 or 3.41 spikes per burst; ~100/220 neurons keep their spike counts).
  - So individual X/INT spike trains, and per-seed RA burst statistics in such networks, are
    not reproducible spike for spike. Comparisons must be statistical, across seeds
    (`code/scripts/brian2_vs_paper.py`).

## Fig 2 as single cells: stated protocol vs Mooney & Prather protocol (2026-11-22)
- **I-24:** at the stimulus the paper states for the *model* (0.5 nA: 10 ms pulses; a 500 ms step
  in D2; "same values used as by Mooney and Prather"), our stimulated cells fire more than the
  original model column of Fig 2:
  - RA: 3 spikes per pulse (original 1); INT: 2 per pulse (original 1); X: 1 (original 1).
  - D2 INT: 89 spikes, 178 Hz (original: 50 spikes over ~820 ms, ~60 Hz, measured from the
    figure; the drawn step lasts ~820 ms, not the stated 500 ms).
- **Not a bug, and not I_KNa** (`code/scripts/fig2_cell_excitability.py`, a Python port of the
  authors' Figure 2 Source Code 3-4, validated: with our parameters it gives our 3 spikes and
  ~180 Hz):
  - their own INT cell fires 176 Hz at 0.5 nA, like ours; no INT parameter changes this;
  - their own RA cell (Daou13 values, gA 150) does not fire at all to 0.5 nA x 10 ms (peaks at
    -43 mV); removing I_KNa / I_NaP changes nothing; gA alone decides: 3 spikes for gA 9-40
    (published range 1-14), 1 spike only near gA 80-90;
  - so neither the published parameters nor the supplied code produce the published Fig 2 at
    the stated current.
- **Mooney & Prather (2005) Methods:** "brief (~10 ms) depolarizing current pulses (+0.5 to 1
  nA)", and "current amplitudes and/or the resting membrane potential of the trigger cell were
  adjusted to elicit only a single action potential per pulse"; long steps "0.5 s at +0.5 nA".
- **Holding current alone does not work for RA:** 0 to -60 pA (rest -74 to -98 mV): always 3
  spikes at 0.5 nA. INT reaches 1 spike at -80 pA (rest -88 mV; M&P's C1 INT is at -85 mV).
- **Decision (user, 2026-11-22): report both protocols** (`code/scripts/fig2_single_cells.py`,
  `figures/replication_fig2_single.png`):
  - *Stated:* 0.5 nA throughout -> not reproduced (numbers above).
  - *M&P procedure* [ours]: pulse amplitude = middle of our cell's one-spike range for a 10 ms
    pulse (RA 110-200 -> 150 pA; INT 130-370 -> 250 pA; X >= 190 -> 500 pA unchanged); D2 step
    145 pA for 820 ms (gives the figure's ~60 Hz). -> RA 1 spike + after-depolarization, INT 1,
    X 1, D2 49 spikes at 60 Hz: matches the original model column. Below the 0.5-1 nA range,
    which we attribute to our cells' higher input resistance (RA: 20 pF, 2 nS leak at rest).
  - Pulse spacing corrected to the original panels: A 100, B 115 (was 60), C 190 (was 150),
    E 100 ms.
- **Also measured from the original model column (for the later pair calibration, I-19/I-23):**
  A2 X IPSP ~4.7 mV; B2 first INT EPSP ~6.5 mV, subthreshold, spike on the second; C2 X IPSP
  ~4 mV; D2 X ~4.7-5 mV below rest; E2 INT spikes once per X spike.
- **Their code's own protocols** (`figures/fig2_code_protocols.png`): INT +75 pA identical (31 Hz
  both); X +150 pA: ours 54 Hz vs 25 Hz (their X has gK 50, gSK 6, gKNa 40); RA +200 pA: ours
  82 Hz vs their delayed 10 Hz (gA). Source Code 2 (X, -120 pA) uses gK 1700, gSK 1 (INT values).

## Fig 2 pairs with calibrated synapses (2026-11-22; `code/scripts/fig2_pairs_mp.py`)
- Paper: "we connected one HVC(RA) neuron to excite one HVC(INT) ... connected with one HVC(X) via
  a GABA current"; "synaptic parameters were calibrated" (by eye, I-23; values not reported, I-19).
- **Fitted to the original model column** (presynaptic cell under the M&P procedure; settled cells):
  - INT->X **10 nS** (network 21): C2 X IPSP 4.1 mV (target 4.0; 0.40 mV/nS, linear).
  - X->INT **11 nS** (network 21): one INT spike per X spike for 6.5-16 nS; 2 spikes from 18 nS.
  - RA->INT **25 nS** for A2 (one INT spike per RA spike for 16-35 nS) and **7.4 nS** for B2
    (EPSP 6.6 mV, target 6.5, subthreshold). Two values because A2 needs a suprathreshold and B2
    a subthreshold RA->INT pair; Mooney & Prather report both kinds (their Fig 4A).
- **Predictions (not fitted), M&P procedure:** A2 X IPSP 3.7-4.2 mV (target ~4.7, ~20% low);
  D2 X held -5.2 mV with a ripple at each INT spike (target 4.7-5 mV, ripple as in original).
- **Not reproduced:** B2's spike on the second pulse (identical pulses on a settled cell give
  identical subthreshold EPSPs; starting unsettled, as their code does, makes INT fire on the
  *first* pulse instead); D2: X fires one rebound spike 66 ms after the step (original: none in
  the ~100 ms drawn); C2: no post-spike depolarising hump in INT.
- **Stated 0.5 nA with the same synapses:** RA bursts of 3 -> A2 X IPSPs ~6 mV; B2 INT fires on
  every pulse; C2 X IPSP 6.4 mV (2 INT spikes); D2 X -10.5 mV and a 5-spike rebound burst.
- Figure: `figures/replication_fig2_pairs.png` (left stated, right M&P), replaces the single-cell
  figure in the article. Each trace has its own scale bar as in the original.

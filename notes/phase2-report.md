# Phase 2 report: comparison with the authors' supplementary code

Opened 2026-11-20, after tag `phase1-complete`. The archives matched the SHA-256 checksums
recorded in `phase1-report.md`. The code was read only; no part of it was run or copied into
`hvcnet`.

## What the supplement contains

| File (as published) | Paper's description | What it actually is |
|---|---|---|
| `Figures 412 Source Code 1.m` (`N1DE_refactored`) | "connects all neurons in the network via the corresponding ionic currents" | A **refactoring scaffold**, not the published network: **no HVC(X) neurons**; one linear RA chain 1→2→…→N (no microcircuits, no random sampling); **no RA→INT or INT→RA/X synapses**. The INT block is labelled "scaffold (illustrative; extend similarly)", with "placeholder" h∞ and zeroed rT/rf/rs derivatives ("copy real kinetics from your legacy code"). There is no driver script, no `ode45` call and no network-construction code. |
| `Figures 412 Source Code 2.m` (`build_params_template`) | "builds the template of projecting neurons as well as interneurons" | A parameter template marked "example placeholders!" and "fill properly". Its values contradict the paper: C_RA = 75, gK_RA = 1700, gNa_RA = 800, gSK_RA = 1, gA_RA = 1, VT = −20, AMPA ar/ad = 1.5/0.8, GABA ar/ad = 1.0/0.6, Ca_ex = 2, RTF = 25. |
| `Figures 412 Source Code 3.m` (`DiffEquations`) | "the differential equations file … called in all simulations" | **Byte-for-byte identical to Daou et al. 2013's `DiffEquations.m`** (Bertram lab, JNP_13): a single neuron with I_Nap and I_KNa, which the paper says it excluded (eqs 1-3). No synapses. |
| `Figure 2 Source Code 1-4.m` | "underlying ODEs and parameters" for the Fig 2 neurons | **Single neurons under current steps, ported from Daou 2013's XPP files.** Source Code 1 matches `Figure_4.ode` (X: iAp 150 pA, window 160-645 ms, same inits). The others are RA (C 20, gK 400, gA 150, gKNa 1000) and INT (C 75, gK 1700) sets close to Daou 2013 Table 2. **No synapses, so none can produce Fig 2's paired recordings.** |

**Conclusion:** none of the supplementary code can generate Figs 2 or 4-13 as published. The
data-availability claim ("Source codes have been provided for Figures 2, 4-12") is not met.

## Gaps the code does settle (single-neuron context only), tagged `[code]`

| Issue | Code value | Phase-1 choice | Agreement |
|---|---|---|---|
| D-01 αh | exp(−(V+50)/18) | +15 (text) | differs |
| D-02 rs∞ | no minus sign | no minus sign | agrees |
| D-03 bT exponent | 3 | 3 (frozen config) | agrees |
| D-04 θaT | −65 | −64 (text) | differs |
| D-05 σaT | −7.8 | −7.8 | agrees |
| D-06 τn | voltage-dependent (cosh) | voltage-dependent | agrees |
| D-07 φrT | parameter 0.2 present but **not applied** to drT/dt in the Fig 2 code | 1.0 | agrees |
| I-02 RT/F | 26.7 mV | 25.69 mV | differs |
| T-03 Ca equation | −f[ε(ICaL+ICaT) + kCa(Ca−bCa)] | same | agrees |
| T-06 GHK V factor | present | present | agrees |
| ode45 tolerances (Fig 2 code) | RelTol 1e-6, AbsTol 1e-9 | 1e-3 / 1e-6 (MATLAB defaults) | differs (network unknown) |

**Not settled (the code doesn't contain them):** the network Cm and conductances in the
paper's model (I-01, I-05, I-06), the synapse model and reversal potentials (I-04, T-04), the
network construction (I-10, I-11), the start input (I-07), noise (I-08), seeds (I-09) and the
Fig 2 pair conductances (I-19).

**New contradiction between code and paper:** the single-cell code includes I_Nap and I_KNa and
uses Daou 2013's gK/gA (e.g. RA gK 400, gA 150), whereas the paper's eqs 1-3 omit those currents
and its Table 1 gives RA gK 150. The RA code also has gCaT 0.55, but eq 1 has no ICaT in RA.

## Test: Phase-1 network with the code's equation forms
`code/scripts/phase2_codeforms.py`: αh +50, θaT −65, RTF 26.7, bT³, 16 seeds, otherwise the
frozen Phase-1 configuration (`results/phase2_codeforms_seeds.jsonl`).

| | Phase 1 (text forms) | Code forms |
|---|---|---|
| Full RA chain in order | 16/16 | 16/16 |
| RA meeting the criterion | 89.9/120 | 79.1/120 |
| RA spikes / burst, duration | 3.97, 9.17 ms | 3.69, 8.78 ms |
| X meeting the criterion | 0/50 | 0/50 (median 1 spike per burst) |
| INT median spikes / 400 ms | 23.7 | 20.9 |

The HVC(RA) result is **robust to every equation form** on record. The HVC(X) and INT
phenotypes are **reproduced under none of them**.

## Status for the article
- Reproduced: sequence propagation (Fig 4) and RA burst statistics, from text plus Daou 2013.
- Not reproduced: the HVC(X) rebound bursts (Figs 7B, 10), dense INT bursting (Figs 7A, 8),
  and the Fig 2 pair calibration. The supplied code can't help, because it doesn't implement
  the network.
- The network-level gaps can't be settled from the published material.

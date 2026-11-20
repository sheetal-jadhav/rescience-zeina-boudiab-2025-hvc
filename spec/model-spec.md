# Model specification extracted from Bou Diab et al. 2025 (Phase 1, from text)

**Source tags**
- `[eq N]`: appendix equation N
- `[T1]`: Appendix 1 Table 1
- `[M]`: Methods text
- `[R]`: Results text
- `[F13]`: read off Fig 13 box plots
- `[F5]`: Fig 5 legend
- `[Daou13]`: to be filled from Daou et al. 2013
- `[GAP]`: not given anywhere; see `notes/issues-log.md`
- `[TYPO?]`: as printed, but probably wrong; see the issues log

## 1. Neurons (single compartment, Hodgkin-Huxley type)

Membrane equations [eq 1-3]:

```
Cm dV_RA/dt  = -IL - IK - INa - ICaL - IA  - ISK                 (6 ODEs per cell)
Cm dV_X/dt   = -IL - IK - INa - ICaL - ICaT - ISK - IH          (8 ODEs)
Cm dV_INT/dt = -IL - IK - INa - ICaL - ICaT - IH                (7 ODEs)
```
- Plus one ODE per incoming synapse.
- Cm: **[GAP]**. Conductances are in nS, so Cm is presumably in pF → [Daou13].

ODE counts, as stated in [M], and the state variables they imply:
- **RA (6):** V, n, h, e (IA inactivation), [Ca], and one more. [GAP] whether it's a gating
  variable or Ca.
- **X (8):** V, n, h, rT, [Ca], rf, rs, and one more.
- **INT (7):** V, n, h, rT, rf, rs, [Ca]. INT has no ISK, so [Ca] may not be integrated → [GAP].
- Check all three counts against Daou13.

### Currents
| Current | Form | Notes |
|---|---|---|
| IL | gL (V − VL) | [eq 4 text] |
| IK | gK n⁴ (V − VK) | [eq 4] |
| INa | gNa m∞³(V) h (V − VNa) | [eq 5]; m is instantaneous |
| IA | gA a∞(V) e (V − VK) | [eq 6]; RA only |
| ICaL | gCa s∞²(V) · Ca_ex / (1 − exp(2FV/RT)) | [eq 7]. GHK form **without the usual V factor** [TYPO?] → check Daou13. Ca_ex, F, R, T: [GAP] |
| ICaT | gCaT aT∞³(V) bT∞²(rT) · Ca_ex / (1 − exp(2FV/RT)) | [eq 13]; X and INT |
| ISK | gSK k∞([Ca]) (V − VK) | [eq 19]; RA and X |
| IH | gH [kr rf + (1 − kr) rs] (V − Vh) | [eq 22]; X and INT. kr: [GAP] |

### Gating
- x∞(V) = 1 / (1 + exp((V − θx)/σx)) for x = m, a, s, and for n and e [eq 8].
- dx/dt = (x∞(V) − x)/τx for x = n, h, e [eq 9]. **As printed it reads (x∞ − V)/τx** [TYPO?].
- h∞ = αh/(αh + βh), with αh = 0.128 exp((V + 15)/−18) and βh = 4/(1 + exp((V + 27)/−5))
  [eq 10-12].
  - Only h∞ is given. Is h relaxed with τh = 1 ms [T1]? Table 1 has τh = 1 ms, so presumably
    yes.
- aT∞(V) = 1/(1 + exp((V − θaT)/σaT)) [eq 14].
- bT∞(rT) = 1/(1 + exp((rT − θb)/σb)) − 1/(1 + exp(−θb/σb)) [eq 15].
- drT/dt = (rT∞(V) − rT)/τrT(V) [eq 16].
  - rT∞(V) = 1/(1 + exp((V − θaT)/σaT)) [eq 17]: **reuses the aT parameters**, although T1 lists
    θrT = −67 and σrT = 2 [TYPO?]. Likely intended: (V − θrT)/σrT.
  - τrT(V) = τr0 + τr1/(1 + exp((V − θrrT)/σrrT)) [eq 18].
- k∞([Ca]) = [Ca]²/([Ca]² + ks²) [eq 20].
- d[Ca]/dt = −f ε (ICaL + ICaT) **+** kCa ([Ca] − bCa) [eq 21]. **The sign of the clearance
  term makes it unstable** [TYPO?]; presumably −kCa ([Ca] − bCa).
- IH fast component: drf/dt = (rf∞ − rf)/τrf(V); rf∞ = 1/(1 + exp((V − θrf)/σrf));
  τrf(V) = prf / ( −7.4(V + 70)/(exp((V + 70)/−0.8) − 1) + 65 exp((V + 56)/−23) ) [eq 23-25].
- IH slow component: d rs/**ds** [TYPO: dt] = (rs∞ − rs)/τrs; rs∞ = 1/(1 + exp(−(V − θrs)/σrs))
  [eq 26-27]. Note the opposite sign convention from rf∞.

### Fixed parameters [T1]
| Param | Value | Param | Value |
|---|---|---|---|
| VL | −70 mV | θaT | −64 mV |
| VK | −90 mV | θb | 0.4 mV (dimensionless, since rT is unitless) |
| VNa | 50 mV | θrT | −67 mV (unused as printed) |
| VCa | −85 mV (unused: GHK form) [TYPO?] | θrrT | 68 mV (sign? see log) |
| VH | −30 mV | σm | −5 mV |
| gL | 2 nS | σn | −5 mV |
| gCa (L-type) | 19 nS | σs | −0.05 mV [TYPO? very steep] |
| τn | 10 ms | σa | −10 mV |
| τhp | 1000 ms (**not used in any equation**) | σe | 5 mV |
| τe | 20 ms | σrf | 5 mV |
| τh | 1 ms | σrs | 25 mV |
| τrs | 1500 ms | σaT | 7.8 mV |
| τr0 | 200 ms | σb | −0.1 |
| τr1 | 87.5 ms | σrT | 2 mV (unused as printed) |
| θm | −35 mV | σrrT | 2.2 mV |
| θn | −30 mV | f | 0.1 |
| θs | −20 mV | ε | 0.0015 µM pA⁻¹ ms⁻¹ |
| θa | −20 mV | kCa | 0.3 ms⁻¹ |
| θe | −60 mV | bCa | 0.1 µM |
| θrf | −105 mV | ks | 0.5 µM |
| θrs | −105 mV | prf | 100 |
| gNa RA / X / INT | 300 / 450 / 800 nS | gK RA / X / INT | 150 / 80 / 1200 nS |

- **Missing [GAP]:** Cm, Ca_ex, F, R, T, kr, V_AMPA, V_GABA.
- **gA, gSK, gH, gCaT defaults:** given only as Fig 13 ranges (below).
- **θh, σh:** not needed (h∞ is given explicitly).

### Variable conductances: allowed ranges [F13A] (nS assumed; the axis has no units)
- **HVC(RA):** gA ~1-14 (median ~9); gSK ~9-12.5 (median ~11)
- **HVC(X):** gSK ~1-3 (median ~2); gH ~1.5-7.5 (median ~4.5); gCaT ~1-9 (median ~4)
- **HVC(INT):** gH ~1-5 (median ~3); gCaT ~1-2 (median ~1.3)
- **Defaults** ("manually selected", [M]): [GAP]. Start from the medians.
- HVC(X) share one value per conductance across the population [M]. RA and INT values vary
  per neuron, randomly, within these ranges [M, R].
- Fig 5 uses gA 10 and 13 nS in a 2-neuron test, which is consistent with the range.

## 2. Synapses [Appendix, after Destexhe 1994]
```
I_syn = ḡ s (V_post − V_rev)
[T]   = Tmax / (1 + exp((V_pre − VT)/Kp))      [TYPO?] Destexhe has −(V_pre − VT)/Kp
ds/dt = ar [T](1 − s) − ad s
Tmax = 1, Kp = 5, VT = 2
GABA-A: ar = 5,   ad = 0.18
AMPA:   ar = 1.1, ad = 0.19
```
- V_AMPA and V_GABA: [GAP]. Destexhe uses 0 mV and about −80 mV.
- One s variable per synapse ("every synaptic current … added a new ODE", [M]).
- **Synaptic conductance ranges [F13B]:**
  - RA->RA AMPA ~29-31 (very narrow)
  - RA->INT AMPA ~10-45
  - X->INT AMPA ~2-31
  - INT->X GABA ~6-42
  - INT->RA GABA ~2-5 (narrow)
- **Fig 5 uses RA->RA gAMPA = 10 and 12 nS**, outside the F13B range → see issue I-14.
- No NMDA and no GABA-B [M].

## 3. Network construction [R, Fig 3]
1. Pools: 120 RA, 50 INT, 50 X. 20 microcircuits (MCs) in order.
2. Assign RA to MCs: each MC gets a random 3-10, each neuron in exactly one MC.
   - **[GAP]:** 20 × U(3,10) has mean 130 ≠ 120. How is the total kept at 120? Possibly the last
     MC takes the remainder, or draws are redrawn.
   - Same issue for INT and X: 1-4 per MC, mean 50, matching 50 only on average.
3. Within each MC: random order RA1→RA2→…→RAm, connected by AMPA.
4. Last RA of MC i → first RA of MC i+1 (AMPA).
5. Each INT gets a random 3-8 AMPA inputs from RA in its own MC **and** in other MCs. [GAP]: the
   split between own and other MCs.
6. Each INT sends a random 2-4 GABA synapses to RA in **any MC except its own**.
7. Each X → a random 1-3 INT in its own MC (AMPA).
8. Each INT → a random 1-2 X in its own MC (GABA).
9. Start: "a stochastic DC input" to RA1 of MC1 only. Amplitude, duration and noise: [GAP].
   Fig 2 used 0.5 nA for 10 ms.
10. Noise: I_noise = σ ξ(t) into every neuron. σ is "1-5% of the mean synaptic conductance"
    (a unit mismatch, current vs conductance) [GAP]. Is noise on in the main figures? [GAP]
11. Initial conditions, simulation length, seed: [GAP].
12. Solver: MATLAB ode45; tolerances [GAP]. Temperature fixed; value [GAP] (needed in the GHK
    RT/F).

## 4. Acceptance criteria for "desired network activity" [M] (used for Figs 12-13)
- **HVC(RA):** one burst per run, 3-6 spikes, burst ≤ 10 ms, spikes riding on a plateau.
- **HVC(X):** 1-4 bursts, 4-9 spikes per burst, mostly rebound after inhibition.
- **HVC(INT):** tonic firing with bursts throughout.
- **Intrinsic properties:** resting potential within the Daou13 ranges; X and INT show a sag
  and rebound after inhibition; INT spikes undershoot rest.
- **Note:** Fig 4 reports RA bursts of 8.12 ± 0.89 ms with **4.76 ± 0.48 spikes**, and the
  Discussion says "3-6 spikes, ~10 ms". These are consistent.
- **Spike detection threshold:** [GAP]. Choose 0 mV and report it.

## 5. Per-figure protocols
- **Fig 2:** pairs and triplets.
  - RA(0.5 nA, 10 ms pulses) → INT (AMPA) → X (GABA).
  - INT pulses (10 ms × 4, 0.5 nA) or 500 ms of DC at 0.5 nA → X.
  - X pulses → INT.
  - Pulse count and intervals: read off the figure.
- **Fig 5:** 2 RA neurons. gAMPA 10 vs 12 nS with gA fixed; gA 10 vs 13 nS with gAMPA = 10.
  Measure the first-spike-peak delay.
- **Fig 6:** gA up, and gSK up 15× ("from 15-fold nS", garbled legend [TYPO?]), in one RA.
- **Fig 9:** INT gCaT ×10; INT gH ×10.
- **Fig 11:** X gH ×10; X gCaT ×15; X gSK = 0.
- **Fig 12:** 100 runs with X gCaT, gSK and gH drawn per neuron within the F13A ranges. Expect
  41% normal, 59% disrupted.
- **Fig 13:** a range-expansion search around the defaults: "increased or decreased randomly up
  until the point that the network ceased to be accurate". The algorithm is underspecified;
  re-implement it and document our version.

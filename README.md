# [Re] Biophysical network modeling of sequence propagation in HVC

Independent replication of **Bou Diab Z, Chammas M, Daou A (2025). Biophysical network modeling
of temporal and stereotyped sequence propagation of neural activity in the premotor nucleus
HVC. eLife 14:RP105526. doi:10.7554/eLife.105526**. The target journal is
[ReScience C](https://rescience.github.io/).

Decision taken 2026-11-20. Background and alternatives considered:
`../input/ideas/hvc-rescience-candidates.md` and `../input/ideas/hvc-model-claims-check.md`.

## Independence protocol (ReScience reviewers will ask about this)

- **Phase 1, from text:** build everything from the paper text, its appendix, its figures and
  the papers it cites (mainly Daou et al. 2013). Don't open the original code. Every value used
  gets a source tag in `spec/model-spec.md`.
- **Phase 2, from code:** only after Phase 1 figures exist, unzip
  `original-code-DO-NOT-OPEN-UNTIL-PHASE-2/` and use it to settle the gaps logged in
  `notes/issues-log.md`. Tag each value taken from it `[code]`, and report every Phase-1 vs
  Phase-2 difference.
- Keep this order in the git history: commit at the end of each phase.

## Tooling

- **Python 3 + NumPy + SciPy.** The main integrator is `scipy.integrate.solve_ivp(method="RK45")`.
  That is the same Dormand-Prince 4(5) pair as MATLAB `ode45`, so solver differences can be
  tested cleanly. A fixed-step RK4 (0.01 and 0.025 ms) is used as a check.
- One vectorised right-hand side for the whole network (~2000 state variables). Brian2 is a
  possible later port if speed is a problem.
- `requirements.txt` pins versions; `make figN` regenerates each figure.

## Target figures

| Fig | What | Type of target |
|---|---|---|
| 2 | Paired-neuron calibration vs Mooney & Prather 2005 (RA->INT dPSP, RA->INT->X iPSP, INT->X iPSP and sag, X->INT dPSP) | qualitative waveform |
| 4 | Raster of 120 HVC(RA): one burst each, in order; burst 8.12 ± 0.89 ms, 4.76 ± 0.48 spikes | **quantitative** |
| 5 | RA->RA delay vs gAMPA (10 -> 12 nS) and vs gA (10 -> 13 nS) | **quantitative** |
| 6 | Raising gA or gSK in one HVC(RA) breaks the chain | qualitative, plus a threshold to find |
| 7-8, 10 | INT dense bursting; X makes 1-4 rebound bursts (4-9 spikes per burst) | **quantitative criteria** (Methods) |
| 9, 11 | Raising INT gCaT/gH (×10) or X gH (×10) / gCaT (×15), or setting X gSK = 0, breaks the chain | qualitative |
| 12 | Varying X conductances individually: 59/100 runs disrupted | **quantitative** |
| 13 | Allowed ranges for gA, gSK, gH, gCaT and the synaptic conductances | **quantitative** (needs the paper's acceptance criteria) |
| - | Noise σ up to 1-5% harmless, larger values disrupt | qualitative |

## Status

- [x] Paper read in full; equations and parameters extracted -> `spec/model-spec.md`
- [x] Gaps, typos and inconsistencies logged -> `notes/issues-log.md` (26 items: 13 gaps, 10 apparent typos, 3 inconsistencies)
- [x] Original figures saved -> `reference/original-figures/`
- [x] Original code downloaded and **left unopened** in a separate folder
- [x] Daou 2013 paper and its published code obtained (Bertram lab site).
- [x] `code/hvcnet` library: params (source-tagged, with switches), model, network, sim
      (RK45 and RK4), analysis. 8 tests pass (`../.venv/bin/python -m pytest code/tests`).
- [x] First network run: 120/120 RA fire in order, 4.78 ± 0.71 spikes per burst (paper
      4.76 ± 0.48). Raster: `figures/phase1_fig4_raster.png`.
- [x] Calibration round 1 (290 runs within the Fig 13 ranges): RA reproduced; X rebound bursts
      and dense INT not reproduced
- [x] **Phase 1 closed (2026-11-20), tag `phase1-complete`.** Report: `notes/phase1-report.md`
- [ ] **User:** decide whether to `git init` this folder and create a public GitHub repo.
      ReScience requires a public repo at submission.
- [ ] Phase 1 week 1: single cells (Fig 2)
- [ ] Phase 1 weeks 2-3: network (Figs 4-11)
- [ ] Phase 1 week 4: Figs 12-13, then commit
- [x] **Phase 2 closed (2026-11-20), tag `phase2-complete`:** the supplementary code doesn't implement
      the network (scaffold + Daou 2013 single-cell files). Report: `notes/phase2-report.md`
- [x] Figs 5, 6, 9, 11 run → `notes/replication-results.md` (per-figure verdicts)
- [x] Final pipeline at accurate tolerances: all figures (2, 4-13) in the original layout, robustness, Fig 12;
      article draft filled (`article/content.tex`), results in `notes/replication-results.md`
- [ ] Robustness and ablation
- [ ] Article (ReScience C LaTeX template)

# [Re] Biophysical network modeling of sequence propagation in HVC

Independent replication, for [ReScience C](https://rescience.github.io/), of **Bou Diab Z,
Chammas M, Daou A (2025). Biophysical network modeling of temporal and stereotyped sequence
propagation of neural activity in the premotor nucleus HVC. eLife 14:RP105526.
doi:10.7554/eLife.105526**.

Author: Sheetal Jadhav (Independent Researcher, ORCID
[0000-0001-6942-7748](https://orcid.org/0000-0001-6942-7748)).

**Result in one line:** the HVC(RA) chain reproduces. The HVC(X) rebound bursts, dense
interneuron firing, Fig 2 calibration and the fragility results (Figs 6, 9, 11, 12) do not
reproduce from the published description. See `notes/replication-results.md` and the article
in `article/`.

## Repository layout

- `code/hvcnet/`: the model library (cells, synapses, network builder, RK45/RK4 integrators,
  analysis)
- `code/hvcnet_brian2/`: an independent second implementation of the same model in Brian2,
  with its own README, requirements and `run_all.sh` (optional; see below)
- `code/scripts/`: one script per experiment or figure
- `code/configs/`: the frozen Phase-1 configuration and the final configuration
- `code/tests/`: unit tests (`pytest`)
- `results/`: raw results (JSON lines) of every run in the article. Files suffixed
  `_rtol1e-3` are earlier runs at MATLAB-default tolerance; files suffixed `_BUG_default_params`
  are superseded runs kept for transparency.
- `figures/`: all figures. `replication_figN.png` matches original Fig N.
- `spec/model-spec.md`: every equation and parameter, with its source
- `notes/`:
  - `issues-log.md`: all gaps, typos, discrepancies and choices
  - `phase1-report.md`, `phase2-report.md`
  - `replication-results.md`: per-figure verdicts
- `article/`: ReScience C LaTeX source
- `LICENSE`: MIT (code)

The original article's PDF, figures and supplementary code, and Daou et al. (2013)'s code, are
not redistributed here. Get them from the publishers.

## Reproducing

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest code/tests        # 8 tests (+1 if Brian2 is installed)
sh code/scripts/run_final.sh                 # calibration, robustness, Figs 5, 6, 9, 11 (hours)
cd code && ../.venv/bin/python -I scripts/fig12.py && ../.venv/bin/python -I scripts/fig13_fine_rara.py
../.venv/bin/python -I scripts/fig2_pairs.py && ../.venv/bin/python -I scripts/article_figures.py
# Fig 2 (article version): stated 0.5 nA vs the Mooney & Prather one-spike procedure
../.venv/bin/python -I scripts/fig2_pairs_mp.py         # pairs with fitted synapses (article Fig 2)
../.venv/bin/python -I scripts/fig2_single_cells.py     # stimulated cells alone; authors' code protocols
../.venv/bin/python -I scripts/fig2_cell_excitability.py  # port of the authors' Fig 2 cell code
# Fig 4 burst statistics: start pulse, Fig 2 synapses, RA capacitance (sensitivity, not adopted)
../.venv/bin/python -I scripts/fig4_mp_test.py && ../.venv/bin/python -I scripts/fig4_burst_isi.py
../.venv/bin/python -I scripts/fig4_cm_grid.py && ../.venv/bin/python -I scripts/fig4_cm_network.py
../.venv/bin/python -I scripts/fig4_cm_network_grid.py && ../.venv/bin/python -I scripts/fig4_cm16_confirm.py
../.venv/bin/python -I scripts/fig4_tradeoff_plot.py
../.venv/bin/python -I scripts/make_figures.py
../.venv/bin/python -I scripts/daou13_xcell.py   # needs Daou 2013 XPP files in reference/
```

**Brian2 implementation (optional):** see `code/hvcnet_brian2/README.md`.

```sh
.venv/bin/pip install -r code/hvcnet_brian2/requirements.txt
sh code/hvcnet_brian2/run_all.sh             # test, cross-check, scored against the paper (~30 min)
```

## Independence protocol 

- **Phase 1, from text:** build everything from the paper text, its appendix, its figures and
  the papers it cites (mainly Daou et al. 2013). Don't open the original code. Every value used
  gets a source tag in `spec/model-spec.md`.
- **Phase 2, from code:** only after Phase 1 figures exist, unzip
  `original-code-DO-NOT-OPEN-UNTIL-PHASE-2/` and use it to settle the gaps logged in
  `notes/issues-log.md`. Tag each value taken from it `[code]`, and report every Phase-1 vs
  Phase-2 difference.
- Each phase was closed by a git tag (`phase1-complete`, `phase2-complete`) before the next began.

## Tooling

- **Python 3 + NumPy + SciPy.** The main integrator is `scipy.integrate.solve_ivp(method="RK45")`.
  That is the same Dormand-Prince 4(5) pair as MATLAB `ode45`, so solver differences can be
  tested cleanly. A fixed-step RK4 (0.01 and 0.025 ms) is used as a check.
- One vectorised right-hand side for the whole network (~2000 state variables).
- A second implementation in Brian2 (`code/hvcnet_brian2/`) cross-checks the first.
- `requirements.txt` pins versions.

## Target figures

| Original Fig | What | Type of target |
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


# Brian2 implementation

A second, independent implementation of the Bou Diab, Chammas & Daou (2025) HVC network model,
written in [Brian2](https://brian2.readthedocs.io). The equations are rewritten in Brian2's
equation syntax, with units, from the same specification (`spec/model-spec.md`) and corrections
(`notes/issues-log.md`) as the main SciPy implementation (`code/hvcnet/`).

The two implementations share only data: the parameter values (`hvcnet/params.py`) and the
network wiring (`hvcnet.evaluate.configure`). That way both simulate exactly the same networks.

## Install and run

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/pip install -r code/hvcnet_brian2/requirements.txt   # includes the main requirements
sh code/hvcnet_brian2/run_all.sh                                # test, cross-check, vs paper (~30 min)
```

The steps can also be run one at a time:

| Command | What it does | Output |
|---|---|---|
| `.venv/bin/python -m pytest code/tests/test_brian2.py` | small network: identical spike counts in both codes; timing error shrinks with dt | pass/fail |
| `.venv/bin/python code/hvcnet_brian2/compare_scipy.py` | 5 networks, SciPy RK45 (rtol 1e-6) vs Brian2 RK4 (dt 0.01 and 0.025 ms) | `results/compare_brian2.jsonl` |
| `.venv/bin/python code/hvcnet_brian2/vs_paper.py` | the paper's quantitative tests: 50 networks (Fig 4), 16 without HVC(X), 100 runs for Fig 12 | `results/brian2_{seeds,noX,fig12}.jsonl` |
| `.venv/bin/python code/hvcnet_brian2/summarize.py` | table: original paper vs SciPy vs Brian2 | `results/brian2_vs_paper.md` |

**Compiler:** Brian2 generates and compiles C code when a C compiler is available (Xcode
Command Line Tools on macOS: `xcode-select --install`; `gcc` on Linux). A full network run then
takes ~15 s at dt 0.01 ms. Without a compiler, Brian2 falls back to pure NumPy. That gives
identical spike times (checked on the test network) but is about 15× slower: ~2.5 min for the
20-neuron test. The full `run_all.sh` is impractical that way, so install a compiler first.

**Use from Python:**

```python
import hvcnet_brian2 as hb        # with code/ on sys.path
net, spikes = hb.simulate(seed=0, dt=0.01)   # spikes[i]: spike times (ms) of neuron i
```

`simulate()` takes the same arguments as `hvcnet.evaluate.simulate()`: `spec`, `seed`,
`overrides`, `switches`, `per_neuron`, `kick`, `t_end`.

## Numerical differences from the SciPy implementation

- Brian2 uses fixed-step RK4 (default dt 0.01 ms); the SciPy code uses adaptive RK45.
- Brian2 updates synapses and neurons in separate sub-steps, so synaptic currents are held fixed
  within a step. The error is first order in dt.
- A spike time is the first time step with V > 0 mV. The SciPy code samples V every 0.025 ms.
- The A-type K⁺ inactivation gate is called `ea`, because Brian2 reserves `e`.

## What the cross-check shows

- **Single cells** (isolated HVC(X) and interneurons, 1.5 s) agree to within 0.03 ms.
- **Small networks:** every neuron has the same spike count in both codes. Timing differences
  shrink from 0.35 ms (dt 0.01) to 0.19 ms (dt 0.005).
- **Full networks:** some network instances are chaotic. Spontaneously firing HVC(X) and
  interneurons form a loop that amplifies tiny differences. In one such network, perturbing the
  SciPy initial voltages by 1e-9 mV changes the result as much as switching to Brian2 does.
  Spike-for-spike agreement is therefore impossible in those networks, and the codes are compared
  statistically across many networks (`summarize.py`).
- The cross-check also found that the SciPy code's pre-stimulus settling ran at a loose
  tolerance. This is now fixed (`notes/issues-log.md`).

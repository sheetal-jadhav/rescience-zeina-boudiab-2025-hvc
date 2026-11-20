"""Score one network simulation against the paper's acceptance criteria (Methods,
'Desired network activity') and the Fig 4 numbers."""

from dataclasses import replace

import numpy as np

from .analysis import bursts, burst_stats, ra_criteria, spike_times, x_criteria
from .model import Model, pulses
from .network import build
from .params import Gating, NetworkSpec, Switches, SynapseKinetics
from .sim import run_rk45, settle


def simulate(spec=NetworkSpec(), seed=0, overrides=None, switches=Switches(), t_end=400.0,
             kick=(50.0, 60.0, 500.0), rtol=1e-3, gating=None, kinetics=None, per_neuron=None):
    """Build, settle, kick RA1 and run. `overrides` maps Cells attribute -> {type: value};
    `gating`/`kinetics` are field overrides for Gating/SynapseKinetics (exploratory only).
    `per_neuron` maps Cells attribute -> {neuron index: ("set"|"mul", value)} (Figs 6/9/11)."""
    net = build(spec, seed=seed)
    if kinetics:
        s = net.synapses
        net.synapses = type(s)(s.pre, s.post, s.g, s.kind, replace(SynapseKinetics(), **kinetics))
    for name, per_type in (overrides or {}).items():
        arr = getattr(net.cells, name)
        for typ, val in per_type.items():
            arr[net.cells.types == typ] = val
    for name, per_idx in (per_neuron or {}).items():
        arr = getattr(net.cells, name)
        for idx, (op, val) in per_idx.items():
            arr[idx] = arr[idx] * val if op == "mul" else val
    m = Model(net.cells, net.synapses, gating=replace(Gating(), **(gating or {})),
              switches=switches)
    y0 = settle(m, m.initial_state(), 500.0)
    m.stimulus = pulses(net.cells.N, [(net.first_ra, *kick)])
    r = run_rk45(m, y0, t_end, rtol=rtol)
    return net, r, spike_times(r["t"], r["V"])


def score(net, sp):
    chain = net.chain_order()
    ra = [sp[j] for j in chain]
    firsts = np.array([s[0] if len(s) else np.nan for s in ra])
    fired = np.isfinite(firsts)
    counts, durs = burst_stats(ra)
    xs = [sp[j] for j in net.x]
    x_nb = np.array([len(bursts(s, min_spikes=1)) for s in xs])
    x_spb = np.array([len(b) for s in xs for b in bursts(s, min_spikes=1)])
    ints = np.array([len(sp[j]) for j in net.int_])
    order_ok = bool(fired.all() and np.all(np.diff(firsts) > 0))
    link = np.diff(firsts).mean() if fired.all() else np.nan
    return {
        "ra_fired": int(fired.sum()),
        "ra_in_order": order_ok,
        "ra_ok": int(ra_criteria(ra).sum()),
        "ra_spikes": counts.mean() if len(counts) else np.nan,
        "ra_dur": durs.mean() if len(durs) else np.nan,
        "ra_dur_sd": durs.std() if len(durs) else np.nan,
        "link_ms": link,
        "x_ok": int(x_criteria(xs).sum()),
        "x_silent": int((x_nb == 0).sum()),
        "x_bursts_med": float(np.median(x_nb)),
        "x_bursts_max": int(x_nb.max()),
        "x_spb_med": float(np.median(x_spb)) if len(x_spb) else np.nan,
        "int_spikes_med": float(np.median(ints)),
    }

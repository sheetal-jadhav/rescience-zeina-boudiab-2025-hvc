import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hvcnet import INT, RA, X, Cells, Model, pulses, run_rk45, settle
from hvcnet.analysis import burst_stats, spike_times
from hvcnet.model import _ghk, _tau_rf
from hvcnet.network import AMPA, GABA, build
from hvcnet.params import NetworkSpec


def test_ghk_continuous_at_zero():
    V = np.array([-1e-4, 0.0, 1e-4])
    out = _ghk(V, 25.69, 2.5)
    assert np.allclose(out, -0.5 * 25.69 * 2.5, rtol=1e-3)


def test_tau_rf_finite_at_minus_70():
    V = np.array([-70.0 - 1e-3, -70.0, -70.0 + 1e-3])
    tau = _tau_rf(V, 100.0)
    assert np.all(np.isfinite(tau)) and np.ptp(tau) < 1e-3 * tau.mean()


@pytest.mark.parametrize("typ,rest", [(RA, -73.75), (X, -62.54), (INT, -62.05)])
def test_resting_potentials_stable(typ, rest):
    m = Model(Cells([typ]))
    y = settle(m, m.initial_state(), 1500.0)
    assert abs(y[0] - rest) < 0.5


def test_ra_fires_for_depolarising_step():
    m = Model(Cells([RA]))
    y0 = settle(m, m.initial_state(), 500.0)
    m.stimulus = pulses(1, [(0, 50.0, 250.0, 200.0)])
    r = run_rk45(m, y0, 300.0)
    assert len(spike_times(r["t"], r["V"])[0]) > 3


def test_network_construction_rules():
    spec = NetworkSpec()
    for seed in range(5):
        net = build(spec, seed=seed)
        assert [len(g) for g in (net.ra, net.x, net.int_)] == [120, 50, 50]
        assert len(net.mc_ra) == 20
        assert all(spec.ra_per_mc[0] <= len(g) <= spec.ra_per_mc[1] for g in net.mc_ra)
        assert all(spec.int_per_mc[0] <= len(g) <= spec.int_per_mc[1] for g in net.mc_int)
        assert sorted(np.concatenate(net.mc_ra)) == list(net.ra)

        mc = {}
        for kind, groups in (("ra", net.mc_ra), ("x", net.mc_x), ("int", net.mc_int)):
            for i, g in enumerate(groups):
                for j in g:
                    mc[int(j)] = i
        types = net.cells.types
        s = net.synapses
        for a, b, k in zip(s.pre, s.post, s.kind):
            ta, tb = types[a], types[b]
            if ta == INT and tb == RA:
                assert k == GABA and mc[a] != mc[b]
            elif ta == INT and tb == X:
                assert k == GABA and mc[a] == mc[b]
            elif ta == X:
                assert tb == INT and k == AMPA and mc[a] == mc[b]
            elif ta == RA:
                assert tb in (RA, INT) and k == AMPA
            else:
                pytest.fail(f"unexpected synapse {ta}->{tb}")
        n_ra_ra = np.sum((types[s.pre] == RA) & (types[s.post] == RA))
        assert n_ra_ra == 119


def test_sequence_propagates_in_order():
    net = build(seed=0)
    m = Model(net.cells, net.synapses)
    y0 = settle(m, m.initial_state(), 300.0)
    m.stimulus = pulses(net.cells.N, [(net.first_ra, 20.0, 30.0, 500.0)])
    r = run_rk45(m, y0, 120.0)
    sp = spike_times(r["t"], r["V"])
    chain = net.chain_order()[:20]
    firsts = [sp[j][0] for j in chain]
    assert np.all(np.diff(firsts) > 0)
    counts, _ = burst_stats([sp[j] for j in chain])
    assert len(counts) == 20 and 3 <= counts.mean() <= 7

"""The Brian2 implementation reproduces the SciPy one on a small network."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# optional: pip install -r code/hvcnet_brian2/requirements.txt
hb = pytest.importorskip("hvcnet_brian2", exc_type=ImportError)
from hvcnet.evaluate import simulate
from hvcnet.params import NetworkSpec

SMALL = NetworkSpec(n_ra=12, n_int=4, n_x=4, n_mc=2, ra_per_mc=(5, 7), int_per_mc=(2, 2),
                    x_per_mc=(2, 2))


def _max_dt(ref, other):
    assert all(len(a) == len(b) for a, b in zip(ref, other))  # identical spike counts
    return max(np.max(np.abs(a - b)) for a, b in zip(ref, other) if len(a))


def test_brian2_matches_scipy_small_network():
    net, _, ref = simulate(SMALL, seed=1, t_end=150.0)
    assert all(len(ref[j]) for j in net.chain_order())  # the chain propagates
    err = [_max_dt(ref, hb.simulate(SMALL, seed=1, t_end=150.0, dt=dt)[1]) for dt in (0.01, 0.005)]
    # RK4 with operator-split synapses is first order: halving dt roughly halves the error
    assert err[1] < 0.7 * err[0] and err[1] < 0.25  # ms

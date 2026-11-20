"""Bou Diab et al. (2025) network construction (Results, 'Network organization' and
'Synaptic connectivity'; Fig 3).

Choices the paper leaves open are marked [ours] and listed in notes/issues-log.md.
"""

from dataclasses import dataclass

import numpy as np

from .model import Cells, Synapses
from .params import INT, RA, X, NetworkSpec

AMPA, GABA = 0, 1


def _counts(rng, total, lo, hi, n_mc, max_tries=100_000):
    """Per-microcircuit counts uniform in [lo, hi] that sum to `total` [ours, I-10]:
    rejection sampling, so each accepted draw is uniform over valid count vectors."""
    for _ in range(max_tries):
        c = rng.integers(lo, hi + 1, size=n_mc)
        if c.sum() == total:
            return c
    raise ValueError(f"cannot split {total} into {n_mc} groups of {lo}-{hi}")


def _split(rng, ids, counts):
    perm = rng.permutation(ids)
    return np.split(perm, np.cumsum(counts)[:-1])


@dataclass
class Network:
    cells: Cells
    synapses: Synapses
    mc_ra: list       # per microcircuit, RA indices in chain order
    mc_int: list
    mc_x: list
    ra: np.ndarray    # global indices by class
    x: np.ndarray
    int_: np.ndarray

    @property
    def first_ra(self):
        return int(self.mc_ra[0][0])

    def chain_order(self):
        return np.concatenate(self.mc_ra)


def build(spec=NetworkSpec(), seed=0):
    rng = np.random.default_rng(seed)
    ra = np.arange(spec.n_ra)
    x = spec.n_ra + np.arange(spec.n_x)
    int_ = spec.n_ra + spec.n_x + np.arange(spec.n_int)
    types = np.r_[np.full(spec.n_ra, RA), np.full(spec.n_x, X), np.full(spec.n_int, INT)]

    mc_ra = _split(rng, ra, _counts(rng, spec.n_ra, *spec.ra_per_mc, spec.n_mc))
    mc_int = _split(rng, int_, _counts(rng, spec.n_int, *spec.int_per_mc, spec.n_mc))
    mc_x = _split(rng, x, _counts(rng, spec.n_x, *spec.x_per_mc, spec.n_mc))
    mc_of = {int(j): i for i, grp in enumerate(mc_ra) for j in grp}

    pre, post, g, kind = [], [], [], []

    def add(a, b, gg, k):
        pre.append(int(a)); post.append(int(b)); g.append(gg); kind.append(k)

    # RA chain within each MC (already in random order), then last of MC i -> first of MC i+1
    for i, grp in enumerate(mc_ra):
        for a, b in zip(grp[:-1], grp[1:]):
            add(a, b, spec.g[("RA", "RA")], AMPA)
        if i + 1 < len(mc_ra):
            add(grp[-1], mc_ra[i + 1][0], spec.g[("RA", "RA")], AMPA)

    for i, ints in enumerate(mc_int):
        others = np.concatenate([grp for k, grp in enumerate(mc_ra) if k != i])
        for j in ints:
            # RA -> INT: 3-8 inputs drawn from the whole RA pool [ours, I-11]
            for a in rng.choice(ra, rng.integers(*spec.ra_to_int_in, endpoint=True), replace=False):
                add(a, j, spec.g[("RA", "INT")], AMPA)
            # INT -> RA: 2-4 outputs to RA in any MC except its own
            for b in rng.choice(others, rng.integers(*spec.int_to_ra_out, endpoint=True), replace=False):
                add(j, b, spec.g[("INT", "RA")], GABA)
            # INT -> X: 1-2 outputs to X in its own MC
            xs = mc_x[i]
            n_out = min(len(xs), rng.integers(*spec.int_to_x_out, endpoint=True))
            for b in rng.choice(xs, n_out, replace=False):
                add(j, b, spec.g[("INT", "X")], GABA)
        # X -> INT: 1-3 outputs to INT in its own MC
        for a in mc_x[i]:
            n_out = min(len(ints), rng.integers(*spec.x_to_int_out, endpoint=True))
            for b in rng.choice(ints, n_out, replace=False):
                add(a, b, spec.g[("X", "INT")], AMPA)

    return Network(Cells(types), Synapses(pre, post, g, kind), mc_ra, mc_int, mc_x, ra, x, int_)

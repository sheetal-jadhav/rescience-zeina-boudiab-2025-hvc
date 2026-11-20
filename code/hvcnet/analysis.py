"""Spike and burst detection and the paper's acceptance criteria (Methods, 'Desired network
activity'). Thresholds are our choices (issues log I-12) and are reported in the article."""

import numpy as np

SPIKE_THRESHOLD = 0.0      # mV, upward crossing
BURST_ISI = 10.0           # ms, spikes closer than this belong to one burst


def spike_times(t, V, threshold=SPIKE_THRESHOLD):
    """List of spike-time arrays, one per neuron (V has shape [time, neuron])."""
    above = V >= threshold
    up = ~above[:-1] & above[1:]
    return [t[1:][up[:, j]] for j in range(V.shape[1])]


def bursts(spikes, max_isi=BURST_ISI, min_spikes=2):
    """Group a spike train into bursts; returns a list of spike-time arrays."""
    if len(spikes) == 0:
        return []
    groups = np.split(spikes, np.where(np.diff(spikes) > max_isi)[0] + 1)
    return [g for g in groups if len(g) >= min_spikes]


def burst_stats(spike_lists):
    """Per-burst spike counts and durations (first to last spike) pooled over neurons."""
    counts, durs = [], []
    for s in spike_lists:
        for b in bursts(s):
            counts.append(len(b))
            durs.append(b[-1] - b[0])
    return np.array(counts), np.array(durs)


def first_spike_order(spike_lists):
    """Neuron indices sorted by first spike time (neurons that never spike are dropped)."""
    firsts = [(s[0], j) for j, s in enumerate(spike_lists) if len(s)]
    return [j for _, j in sorted(firsts)]


def ra_criteria(spike_lists):
    """Each RA fires exactly one burst of 3-6 spikes lasting <= 10 ms [BD Methods]."""
    ok = []
    for s in spike_lists:
        b = bursts(s, min_spikes=1)
        ok.append(len(b) == 1 and 3 <= len(b[0]) <= 6 and b[0][-1] - b[0][0] <= 10.0)
    return np.array(ok)


def x_criteria(spike_lists):
    """Each X fires 1-4 bursts, each with 4-9 spikes [BD Methods]."""
    ok = []
    for s in spike_lists:
        b = bursts(s, min_spikes=1)
        ok.append(1 <= len(b) <= 4 and all(4 <= len(g) <= 9 for g in b))
    return np.array(ok)

"""Single-compartment HVC neurons and kinetic synapses as one vectorised ODE system.

State layout for N neurons and E synapses:
    [V, n, h, e, rT, Ca, rf, rs] each of length N, then s of length E.
Every neuron integrates the same gates; a current whose conductance is zero has no effect,
which keeps the right-hand side branch-free (issues log I-13).
"""

import numpy as np

from .params import CELL_TYPES, Gating, Switches, SynapseKinetics

N_GATES = 8
V_CLIP = (-150.0, 100.0)
V_, N_, H_, E_, RT_, CA_, RF_, RS_ = range(N_GATES)


def _sig(V, theta, sigma):
    # clip so very steep gates (sigma_s = -0.05) saturate without overflow warnings
    return 1.0 / (1.0 + np.exp(np.clip((V - theta) / sigma, -500.0, 500.0)))


def _tau_rf(V, prf):
    """Ih fast time constant [BD eq 25]; the 0/0 at V = -70 mV is replaced by its limit 5.92."""
    x = V + 70.0
    small = np.abs(x) < 1e-6
    safe = np.where(small, 1.0, x)
    term = np.where(small, 7.4 * 0.8, -7.4 * safe / (np.exp(-safe / 0.8) - 1.0))
    return prf / (term + 65.0 * np.exp(-(V + 56.0) / 23.0))


def _ghk(V, RTF, Ca_ex):
    """V * Ca_ex / (1 - exp(2V/RTF)), with its V -> 0 limit (-RTF/2 * Ca_ex)."""
    z = 2.0 * V / RTF
    small = np.abs(z) < 1e-6
    safe = np.where(small, 1.0, z)
    out = V * Ca_ex / (1.0 - np.exp(safe))
    return np.where(small, -0.5 * RTF * Ca_ex, out)


class Cells:
    """Per-neuron parameter arrays built from cell-type labels."""

    def __init__(self, types, overrides=None):
        self.types = np.asarray(types, dtype=int)
        self.N = len(self.types)
        for name in ("Cm", "gNa", "gK", "gL", "gCaL", "gA", "gSK", "gCaT", "gH", "kr"):
            setattr(self, name, np.array([getattr(CELL_TYPES[t], name) for t in self.types]))
        self.Ibias = np.zeros(self.N)  # constant injected current (pA); 0 in the published model
        for name, values in (overrides or {}).items():
            getattr(self, name)[:] = values


class Synapses:
    """Edge list: pre, post, maximal conductance, and AMPA (0) or GABA-A (1) kind."""

    def __init__(self, pre, post, g, kind, kin=SynapseKinetics()):
        self.pre = np.asarray(pre, dtype=int)
        self.post = np.asarray(post, dtype=int)
        self.g = np.asarray(g, dtype=float)
        self.kind = np.asarray(kind, dtype=int)
        self.E = len(self.pre)
        gaba = self.kind == 1
        self.ar = np.where(gaba, kin.ar_gaba, kin.ar_ampa)
        self.ad = np.where(gaba, kin.ad_gaba, kin.ad_ampa)
        self.Erev = np.where(gaba, kin.E_gaba, kin.E_ampa)
        self.kin = kin

    @classmethod
    def empty(cls):
        return cls([], [], [], [])


class Model:
    def __init__(self, cells, synapses=None, gating=Gating(), switches=Switches(), stimulus=None):
        self.c = cells
        self.syn = synapses if synapses is not None else Synapses.empty()
        self.p = gating
        self.sw = switches
        self.stimulus = stimulus        # callable t -> pA array of length N, or None
        self.noise_pA = 0.0             # only used by fixed-step Euler-Maruyama (I-08)
        self.size = N_GATES * cells.N + self.syn.E

    def currents(self, V, n, h, e, rT, Ca, rf, rs):
        """Ionic currents in pA (positive = outward)."""
        p, sw, c = self.p, self.sw, self.c
        m_inf = _sig(V, p.theta_m, p.sigma_m)
        ghk = _ghk(V, sw.RTF, p.Ca_ex)
        bT = _sig(rT, p.theta_b, p.sigma_b) - 1.0 / (1.0 + np.exp(-p.theta_b / p.sigma_b))
        return {
            "L": c.gL * (V - p.VL),
            "K": c.gK * n**4 * (V - p.VK),
            "Na": c.gNa * m_inf**3 * h * (V - p.VNa),
            "CaL": c.gCaL * _sig(V, p.theta_s, p.sigma_s) ** 2 * ghk,
            "A": c.gA * _sig(V, p.theta_a, p.sigma_a) * e * (V - p.VK),
            "SK": c.gSK * Ca**2 / (Ca**2 + p.ks**2) * (V - p.VK),
            "CaT": c.gCaT * _sig(V, sw.theta_aT, p.sigma_aT) ** 3 * bT**sw.bT_exponent * ghk,
            "H": c.gH * (c.kr * rf + (1.0 - c.kr) * rs) * (V - p.VH),
        }

    def rhs(self, t, y):
        # exp overflow far from threshold only saturates a gate to 0 or 1
        with np.errstate(over="ignore"):
            return self._rhs(t, y)

    def _rhs(self, t, y):
        N, p, sw = self.c.N, self.p, self.sw
        V, n, h, e, rT, Ca, rf, rs = y[: N_GATES * N].reshape(N_GATES, N)
        I = self.currents(V, n, h, e, rT, Ca, rf, rs)
        # Rates and steady states see V clipped to a physiological range, so trial stages of
        # the adaptive solver with extreme V cannot produce inf/nan gates. Currents use raw V.
        V = np.clip(V, V_CLIP[0], V_CLIP[1])
        I_ion = sum(I.values())

        I_syn = np.zeros(N)
        ds = np.empty(0)
        if self.syn.E:
            syn, kin = self.syn, self.syn.kin
            s = y[N_GATES * N:]
            T = kin.Tmax / (1.0 + np.exp(-(V[syn.pre] - kin.VT) / kin.Kp))
            ds = syn.ar * T * (1.0 - s) - syn.ad * s
            I_syn = np.bincount(syn.post, syn.g * s * (V[syn.post] - syn.Erev), minlength=N)

        I_app = self.stimulus(t) if self.stimulus is not None else 0.0

        if sw.tau_n_voltage_dependent:
            tau_n = p.tau_n / np.cosh((V - p.theta_n) / (2.0 * p.sigma_n))
        else:
            tau_n = p.tau_n
        a_h = 0.128 * np.exp(-(V + sw.alpha_h_offset) / 18.0)
        b_h = 4.0 / (1.0 + np.exp(-(V + 27.0) / 5.0))
        tau_rT = p.tau_r0 + p.tau_r1 / (1.0 + np.exp((V - p.theta_rrT) / p.sigma_rrT))
        tau_rf = _tau_rf(V, p.prf)

        dy = np.empty_like(y)
        d = dy[: N_GATES * N].reshape(N_GATES, N)
        d[V_] = (-I_ion - I_syn + I_app + self.c.Ibias) / self.c.Cm
        d[N_] = (_sig(V, p.theta_n, p.sigma_n) - n) / tau_n
        d[H_] = (a_h / (a_h + b_h) - h) / p.tau_h
        d[E_] = (_sig(V, p.theta_e, p.sigma_e) - e) / p.tau_e
        d[RT_] = sw.phi_rT * (_sig(V, p.theta_rT, p.sigma_rT) - rT) / tau_rT
        d[CA_] = -p.f * (p.eps * (I["CaL"] + I["CaT"]) + p.kCa * (Ca - p.bCa))
        d[RF_] = (_sig(V, p.theta_rf, p.sigma_rf) - rf) / tau_rf
        d[RS_] = (_sig(V, p.theta_rs, p.sigma_rs) - rs) / p.tau_rs   # D-02: code sign
        dy[N_GATES * N:] = ds
        return dy

    def initial_state(self, V0=-70.0):
        """Gates at their steady state for V0; synapses closed."""
        N, p, sw = self.c.N, self.p, self.sw
        V = np.full(N, V0)
        a_h = 0.128 * np.exp(-(V + sw.alpha_h_offset) / 18.0)
        b_h = 4.0 / (1.0 + np.exp(-(V + 27.0) / 5.0))
        y = np.zeros(self.size)
        g = y[: N_GATES * N].reshape(N_GATES, N)
        g[V_] = V
        g[N_] = _sig(V, p.theta_n, p.sigma_n)
        g[H_] = a_h / (a_h + b_h)
        g[E_] = _sig(V, p.theta_e, p.sigma_e)
        g[RT_] = _sig(V, p.theta_rT, p.sigma_rT)
        g[CA_] = p.bCa
        g[RF_] = _sig(V, p.theta_rf, p.sigma_rf)
        g[RS_] = _sig(V, p.theta_rs, p.sigma_rs)
        return y

    def voltages(self, y):
        return y[: self.c.N]


def pulses(N, specs):
    """Stimulus from (neuron indices, t_on, t_off, amplitude pA) tuples."""
    specs = [(np.atleast_1d(idx), t0, t1, amp) for idx, t0, t1, amp in specs]

    def stim(t):
        I = np.zeros(N)
        for idx, t0, t1, amp in specs:
            if t0 <= t < t1:
                I[idx] += amp
        return I

    stim.breakpoints = sorted({t for _, t0, t1, _ in specs for t in (t0, t1)})
    return stim

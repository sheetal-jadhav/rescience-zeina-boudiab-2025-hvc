"""Second, independent implementation of the Bou Diab et al. (2025) HVC model in Brian2.

The equations are rewritten here in Brian2's equation syntax, with units, from the same
specification as `hvcnet.model` (spec/model-spec.md and the corrections in notes/issues-log.md).
Only data are shared with `hvcnet`: the parameter dataclasses and the network wiring
(`hvcnet.evaluate.configure`), so that both simulators run exactly the same network.

The I_A inactivation gate is called `ea` (Brian2 reserves `e`).

Numerical differences from `hvcnet`:
- fixed-step RK4 (default dt = 0.01 ms) instead of adaptive RK45;
- Brian2 updates synapses and neurons in separate steps, so synaptic currents are held fixed
  within each RK4 step (operator splitting);
- spike times are the first time step with V > 0 mV, not an interpolated crossing.
"""

from dataclasses import replace

import re

import numpy as np
import setuptools  # noqa: F401  provides `distutils`, which Brian2 imports, on Python >= 3.12
import brian2 as b2
from brian2 import mV, ms, nS, pA, pF

from hvcnet.evaluate import configure
from hvcnet.network import GABA
from hvcnet.params import Gating, NetworkSpec, Switches

NEURON_EQS = """
dv/dt = (-(IL + IK + INa + ICaL + IA + ISK + ICaT + IH) - Iampa - Igaba + Iapp) / Cm : volt
dn/dt = (sig(vc, theta_n, sigma_n) - n) / tau_n : 1
dh/dt = (h_inf - h) / tau_h : 1
dea/dt = (sig(vc, theta_e, sigma_e) - ea) / tau_e : 1
drT/dt = phi_rT * (sig(vc, theta_rT, sigma_rT) - rT) / tau_rT : 1
dCa/dt = -f * (eps * (ICaL + ICaT) + kCa * (Ca - bCa)) : 1
drf/dt = (sig(vc, theta_rf, sigma_rf) - rf) / tau_rf : 1
drs/dt = (sig(vc, theta_rs, sigma_rs) - rs) / tau_rs : 1

vc = clip(v, -150*mV, 100*mV) : volt
ghk = -0.5 * RTF * Ca_ex / exprel(2 * v / RTF) : volt
IL = gL * (v - VL) : amp
IK = gK * n**4 * (v - VK) : amp
INa = gNa * sig(v, theta_m, sigma_m)**3 * h * (v - VNa) : amp
ICaL = gCaL * sig(v, theta_s, sigma_s)**2 * ghk : amp
IA = gA * sig(v, theta_a, sigma_a) * ea * (v - VK) : amp
ISK = gSK * Ca**2 / (Ca**2 + ks**2) * (v - VK) : amp
bT = 1 / (1 + exp((rT - theta_b) / sigma_b)) - 1 / (1 + exp(-theta_b / sigma_b)) : 1
ICaT = gCaT * sig(v, theta_aT, sigma_aT)**3 * bT**bT_exp * ghk : amp
IH = gH * (kr * rf + (1 - kr) * rs) * (v - VH) : amp

tau_n = tau_nbar / (cosh((vc - theta_n) / (2 * sigma_n)) * tau_n_vdep + (1 - tau_n_vdep)) : second
a_h = 0.128 * exp(-(vc / mV + ah_off) / 18) : 1
b_h = 4 / (1 + exp(-(vc / mV + 27) / 5)) : 1
h_inf = a_h / (a_h + b_h) : 1
tau_rT = tau_r0 + tau_r1 / (1 + exp((vc - theta_rrT) / sigma_rrT)) : second
tau_rf = prf * ms / (7.4 * 0.8 / exprel(-(vc / mV + 70) / 0.8) + 65 * exp(-(vc / mV + 56) / 23)) : second

Iampa : amp
Igaba : amp
Iapp : amp
Cm : farad (constant)
gNa : siemens (constant)
gK : siemens (constant)
gL : siemens (constant)
gCaL : siemens (constant)
gA : siemens (constant)
gSK : siemens (constant)
gCaT : siemens (constant)
gH : siemens (constant)
kr : 1 (constant)
"""

SYNAPSE_EQS = """
g_syn : siemens (constant)
ds/dt = ar * T * (1 - s) - ad * s : 1 (clock-driven)
T = Tmax / (1 + exp(-(vc_pre - VT) / Kp)) : 1
{target}_post = g_syn * s * (vc_post - Erev) : amp (summed)
"""

def _expand(eqs):
    """Write sig(x, th, s) out as a clipped logistic (hvcnet.model._sig) in plain Brian2 syntax."""
    return re.sub(r"sig\(([^,()]+), ([^,()]+), ([^,()]+)\)",
                  r"(1 / (1 + exp(clip((\1 - \2) / \3, -500, 500))))", eqs)


def _namespace(p, sw, kin):
    return dict(
        VL=p.VL * mV, VK=p.VK * mV, VNa=p.VNa * mV, VH=p.VH * mV, Ca_ex=p.Ca_ex,
        RTF=sw.RTF * mV,
        theta_m=p.theta_m * mV, sigma_m=p.sigma_m * mV,
        theta_n=p.theta_n * mV, sigma_n=p.sigma_n * mV, tau_nbar=p.tau_n * ms,
        tau_n_vdep=1.0 if sw.tau_n_voltage_dependent else 0.0,
        tau_h=p.tau_h * ms, ah_off=sw.alpha_h_offset,
        theta_s=p.theta_s * mV, sigma_s=p.sigma_s * mV,
        theta_a=p.theta_a * mV, sigma_a=p.sigma_a * mV,
        theta_e=p.theta_e * mV, sigma_e=p.sigma_e * mV, tau_e=p.tau_e * ms,
        theta_aT=sw.theta_aT * mV, sigma_aT=p.sigma_aT * mV,
        theta_b=p.theta_b, sigma_b=p.sigma_b, bT_exp=sw.bT_exponent,
        theta_rT=p.theta_rT * mV, sigma_rT=p.sigma_rT * mV, phi_rT=sw.phi_rT,
        theta_rrT=p.theta_rrT * mV, sigma_rrT=p.sigma_rrT * mV,
        tau_r0=p.tau_r0 * ms, tau_r1=p.tau_r1 * ms,
        f=p.f, eps=p.eps / (pA * ms), kCa=p.kCa / ms, bCa=p.bCa, ks=p.ks,
        theta_rf=p.theta_rf * mV, sigma_rf=p.sigma_rf * mV, prf=p.prf,
        theta_rs=p.theta_rs * mV, sigma_rs=p.sigma_rs * mV, tau_rs=p.tau_rs * ms,
        Tmax=kin.Tmax, VT=kin.VT * mV, Kp=kin.Kp * mV,
    )


def simulate(spec=NetworkSpec(), seed=0, overrides=None, switches=Switches(), t_end=400.0,
             kick=(50.0, 60.0, 500.0), t_settle=500.0, dt=0.01, gating=None, kinetics=None,
             per_neuron=None, target="cython"):
    """Same protocol as hvcnet.evaluate.simulate: settle, pulse into RA1, run t_end (ms).
    Returns (net, spikes) with spikes[i] an array of spike times (ms, from the end of settling)."""
    b2.start_scope()
    b2.prefs.codegen.target = target
    b2.defaultclock.dt = dt * ms
    net = configure(spec, seed, overrides, kinetics, per_neuron)
    c, syn = net.cells, net.synapses
    p = replace(Gating(), **(gating or {}))
    ns = _namespace(p, switches, syn.kin)

    G = b2.NeuronGroup(c.N, _expand(NEURON_EQS), threshold="v > 0*mV", refractory="v > 0*mV",
                       method="rk4", namespace=ns)
    for name in ("gNa", "gK", "gL", "gCaL", "gA", "gSK", "gCaT", "gH"):
        setattr(G, name, getattr(c, name) * nS)
    G.Cm = c.Cm * pF
    G.kr = c.kr
    # resting initial state as in hvcnet: V = -70 mV, gates at steady state, Ca = bCa
    G.v = -70 * mV
    G.n = _expand("sig(v, theta_n, sigma_n)")
    G.h = "h_inf"
    G.ea = _expand("sig(v, theta_e, sigma_e)")
    G.rT = _expand("sig(v, theta_rT, sigma_rT)")
    G.Ca = p.bCa
    G.rf = _expand("sig(v, theta_rf, sigma_rf)")
    G.rs = _expand("sig(v, theta_rs, sigma_rs)")

    groups = [G]
    for kind, target_var, ar, ad, E in (
            (0, "Iampa", syn.kin.ar_ampa, syn.kin.ad_ampa, syn.kin.E_ampa),
            (GABA, "Igaba", syn.kin.ar_gaba, syn.kin.ad_gaba, syn.kin.E_gaba)):
        sel = syn.kind == kind
        if not sel.any():
            continue
        S = b2.Synapses(G, G, SYNAPSE_EQS.format(target=target_var), method="rk4",
                        namespace=dict(ns, ar=ar / ms, ad=ad / ms, Erev=E * mV))
        S.connect(i=syn.pre[sel], j=syn.post[sel])
        S.g_syn = syn.g[sel] * nS
        S.s = 0
        groups.append(S)

    mon = b2.SpikeMonitor(G)
    network = b2.Network(*groups, mon)
    network.run(t_settle * ms)
    t0 = network.t / ms
    t_on, t_off, amp = kick
    network.run(t_on * ms)
    G.Iapp[net.first_ra] = amp * pA
    network.run((t_off - t_on) * ms)
    G.Iapp[net.first_ra] = 0 * pA
    network.run((t_end - t_off) * ms)

    trains = mon.spike_trains()
    spikes = [np.asarray(trains[i] / ms) - t0 for i in range(c.N)]
    spikes = [s[s >= 0] for s in spikes]
    return net, spikes

"""Model parameters for the Bou Diab, Chammas & Daou (2025) HVC network.

Units: mV, ms, nS, pF, pA; intracellular Ca in uM; Ca_ex in mM (as in Daou et al. 2013).

Every value carries a source tag (see notes/issues-log.md):
  [BD-T1]  Bou Diab Appendix 1 Table 1      [BD-eq]   Bou Diab appendix equations
  [BD-F13] read off Bou Diab Fig 13 (median) [BD-text] Bou Diab Results/Methods text
  [Daou13] Daou et al. 2013 paper            [Daou13-code] Daou et al. 2013 published code
  [Dx94]   Destexhe, Mainen & Sejnowski 1994 [ours]    our choice, documented
"""

from dataclasses import dataclass, field, replace

RA, X, INT = 0, 1, 2
TYPE_NAMES = {RA: "RA", X: "X", INT: "INT"}


@dataclass(frozen=True)
class Switches:
    """Alternatives for ambiguous or conflicting equations (issues log D-01..D-07, I-02)."""

    alpha_h_offset: float = 15.0   # D-01: 15 [BD-eq, Daou13] vs 50 [Daou13-code]
    bT_exponent: int = 2           # D-03: 2 [BD-eq] vs 3 [Daou13]
    theta_aT: float = -64.0        # D-04: -64 [BD-T1] vs -65 [Daou13]
    # D-06: constant [BD-eq] vs cosh [Daou13]. Constant 10 ms gives ~10-ms-wide spikes, unlike
    # every trace in BD Figs 2/5 and Daou13, so the Daou13 form is the default.
    tau_n_voltage_dependent: bool = True
    phi_rT: float = 1.0            # D-07: 1.0 [BD, Daou13 papers] vs 0.2 [Daou13 MATLAB code]
    RTF: float = 25.69             # I-02: 298 K [Daou13] vs 26.7 mV [Daou13-code]


@dataclass(frozen=True)
class Gating:
    """Fixed gating and calcium constants [BD-T1 unless noted]."""

    VL: float = -70.0
    VK: float = -90.0
    VNa: float = 50.0
    VH: float = -30.0
    Ca_ex: float = 2.5             # mM [Daou13]
    theta_m: float = -35.0; sigma_m: float = -5.0
    theta_n: float = -30.0; sigma_n: float = -5.0; tau_n: float = 10.0
    tau_h: float = 1.0
    theta_s: float = -20.0; sigma_s: float = -0.05
    theta_a: float = -20.0; sigma_a: float = -10.0
    theta_e: float = -60.0; sigma_e: float = 5.0; tau_e: float = 20.0
    sigma_aT: float = -7.8         # D-05: sign corrected from BD-T1 (+7.8) [Daou13]
    theta_b: float = 0.4; sigma_b: float = -0.1
    theta_rT: float = -67.0; sigma_rT: float = 2.0      # T-02 [Daou13]
    theta_rrT: float = 68.0; sigma_rrT: float = 2.2     # [Daou13-code]
    tau_r0: float = 200.0; tau_r1: float = 87.5
    f: float = 0.1
    eps: float = 0.0015            # uM / (pA ms)
    kCa: float = 0.3               # 1/ms
    bCa: float = 0.1               # uM
    ks: float = 0.5                # uM
    theta_rf: float = -105.0; sigma_rf: float = 5.0; prf: float = 100.0
    theta_rs: float = -105.0; sigma_rs: float = 25.0; tau_rs: float = 1500.0


@dataclass(frozen=True)
class CellType:
    """Per-class conductances (nS) and capacitance (pF). A zero conductance removes a current."""

    Cm: float
    gNa: float
    gK: float
    gL: float = 2.0                # [BD-T1]
    gCaL: float = 19.0             # [BD-T1]
    gA: float = 0.0
    gSK: float = 0.0
    gCaT: float = 0.0
    gH: float = 0.0
    kr: float = 0.0


# gNa, gK [BD-T1]; Cm, kr [Daou13 Table 2]; gA, gSK, gCaT, gH [BD-F13 medians] (I-05)
CELL_TYPES = {
    RA: CellType(Cm=20.0, gNa=300.0, gK=150.0, gA=9.0, gSK=11.0),
    X: CellType(Cm=100.0, gNa=450.0, gK=80.0, gSK=2.0, gCaT=4.0, gH=4.5, kr=0.3),
    INT: CellType(Cm=75.0, gNa=800.0, gK=1200.0, gCaT=1.3, gH=3.0, kr=0.01),
}

# Allowed ranges read off Fig 13A (nS) [BD-F13], used for per-neuron variation (Figs 12-13)
CONDUCTANCE_RANGES = {
    RA: {"gA": (1.0, 14.0), "gSK": (9.0, 12.5)},
    X: {"gSK": (1.0, 3.0), "gH": (1.5, 7.5), "gCaT": (1.0, 9.0)},
    INT: {"gH": (1.0, 5.0), "gCaT": (1.0, 2.0)},
}


@dataclass(frozen=True)
class SynapseKinetics:
    """Destexhe et al. (1994) kinetic synapse [BD-eq]; release sign corrected (T-04)."""

    Tmax: float = 1.0
    Kp: float = 5.0
    VT: float = 2.0
    ar_ampa: float = 1.1; ad_ampa: float = 0.19
    ar_gaba: float = 5.0; ad_gaba: float = 0.18
    E_ampa: float = 0.0            # I-04 [Dx94]
    E_gaba: float = -80.0          # I-04 [Dx94]


# Default synaptic conductances (nS): Fig 13B medians [BD-F13] (I-06)
SYNAPSE_G = {
    ("RA", "RA"): 30.0,
    ("RA", "INT"): 27.0,
    ("X", "INT"): 21.0,
    ("INT", "X"): 21.0,
    ("INT", "RA"): 3.5,
}


@dataclass(frozen=True)
class NetworkSpec:
    """Bou Diab network construction rules [BD-text, Fig 3]."""

    n_ra: int = 120
    n_int: int = 50
    n_x: int = 50
    n_mc: int = 20
    ra_per_mc: tuple = (3, 10)
    int_per_mc: tuple = (1, 4)
    x_per_mc: tuple = (1, 4)
    ra_to_int_in: tuple = (3, 8)   # inputs per INT, from the whole RA pool (I-11)
    int_to_ra_out: tuple = (2, 4)  # outputs per INT, to RA in other MCs only
    x_to_int_out: tuple = (1, 3)   # within own MC
    int_to_x_out: tuple = (1, 2)   # within own MC
    g: dict = field(default_factory=lambda: dict(SYNAPSE_G))


def with_switches(**kwargs):
    return replace(Switches(), **kwargs)

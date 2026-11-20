"""hvcnet: biophysical HVC network models (Bou Diab et al. 2025 replication)."""

from .params import RA, X, INT, Switches, with_switches
from .model import Cells, Synapses, Model, pulses
from .sim import run_rk45, run_rk4, settle

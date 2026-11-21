"""Integrators that record membrane potentials on a fixed output grid.

`run_rk45` steps scipy's Dormand-Prince RK45 (the method of MATLAB ode45) and samples its
dense output, so the full state is never stored. Stimulus on/off times are hit exactly by
restarting the solver there. `run_rk4` is a fixed-step reference, optionally with additive
current noise (Euler-Maruyama on V).
"""

import numpy as np
from scipy.integrate import RK45


def _grid(t0, t1, dt_out):
    return np.arange(t0, t1 + 0.5 * dt_out, dt_out)


def run_rk45(model, y0, t_end, dt_out=0.025, rtol=1e-3, atol=1e-6, max_step=np.inf):
    """Defaults rtol=1e-3, atol=1e-6 are the MATLAB ode45 defaults (issues log I-09)."""
    t_out = _grid(0.0, t_end, dt_out)
    V_out = np.empty((len(t_out), model.c.N))
    breaks = [b for b in getattr(model.stimulus, "breakpoints", []) if 0.0 < b < t_end]
    edges = [0.0] + breaks + [t_end]
    y, k, n_steps = np.asarray(y0, float), 0, 0
    for a, b in zip(edges[:-1], edges[1:]):
        solver = RK45(model.rhs, a, y, b, rtol=rtol, atol=atol, max_step=max_step)
        while k < len(t_out) and t_out[k] <= a + 1e-12:
            V_out[k] = model.voltages(y)
            k += 1
        while solver.status == "running":
            solver.step()
            n_steps += 1
            if solver.status == "failed":
                raise RuntimeError(f"RK45 failed at t={solver.t:.3f} ms")
            hi = np.searchsorted(t_out, solver.t, side="right")
            if hi > k:
                dense = solver.dense_output()
                V_out[k:hi] = dense(t_out[k:hi])[: model.c.N].T
                k = hi
        y = solver.y
    return {"t": t_out, "V": V_out, "y_end": y, "n_steps": n_steps}


def run_rk4(model, y0, t_end, dt=0.01, dt_out=0.025, rng=None):
    """Classic RK4. If model.noise_pA > 0, adds sigma*sqrt(dt)*xi/Cm to V after each step."""
    n_steps = int(round(t_end / dt))
    every = max(1, int(round(dt_out / dt)))
    t_out = np.arange(0, n_steps + 1, every) * dt
    V_out = np.empty((len(t_out), model.c.N))
    rng = rng or np.random.default_rng(0)
    y = np.asarray(y0, float).copy()
    f, k = model.rhs, 0
    for i in range(n_steps + 1):
        if i % every == 0:
            V_out[k] = model.voltages(y)
            k += 1
        if i == n_steps:
            break
        t = i * dt
        k1 = f(t, y)
        k2 = f(t + dt / 2, y + dt / 2 * k1)
        k3 = f(t + dt / 2, y + dt / 2 * k2)
        k4 = f(t + dt, y + dt * k3)
        y += dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        if model.noise_pA:
            y[: model.c.N] += model.noise_pA * np.sqrt(dt) * rng.standard_normal(model.c.N) / model.c.Cm
    return {"t": t_out, "V": V_out, "y_end": y, "n_steps": n_steps}


def settle(model, y0, t_settle=1000.0, rtol=1e-6, atol=1e-9):
    """Run without stimulus so slow gates (rs, rT, Ca) reach rest; returns the end state.
    Tight tolerances by default: spontaneously firing HVC(X) and interneurons keep firing while
    settling, and their phase at the end depends on the tolerance (found by the Brian2 check)."""
    stim, model.stimulus = model.stimulus, None
    try:
        return run_rk45(model, y0, t_settle, dt_out=t_settle, rtol=rtol, atol=atol)["y_end"]
    finally:
        model.stimulus = stim

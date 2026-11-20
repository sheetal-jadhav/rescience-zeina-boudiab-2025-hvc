import sys, itertools
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
from multiprocessing import Pool
from calibrate_random import run

BASE = {'gA@RA': 12.776, 'gSK@RA': 12.016, 'gSK@X': 2.843, 'gH@X': 7.11, 'gCaT@X': 5.719,
        'gH@INT': 3.009, 'gCaT@INT': 1.038, 'g_RA_RA': 29.205, 'g_RA_INT': 28.337,
        'g_X_INT': 26.824, 'g_INT_X': 21.575, 'g_INT_RA': 2.011, 'sw_bT_exponent': 3,
        'sw_alpha_h_offset': 15.0}

if __name__ == "__main__":
    pts = []
    for cx, ci in itertools.product([100.0, 50.0, 25.0], [75.0, 37.5, 18.75]):
        p = dict(BASE); p["Cm@X"] = cx; p["Cm@INT"] = ci; pts.append(p)
    with Pool(8) as pool:
        for r in pool.imap(run, pts):
            s, p = r["score"], r["point"]
            print(f"Cm X {p['Cm@X']:6.1f} INT {p['Cm@INT']:6.2f} | fired {s.get('ra_fired')} "
                  f"order {s.get('ra_in_order')} ra_ok {s.get('ra_ok')} | x_ok {s.get('x_ok')} "
                  f"spb {s.get('x_spb_med')} nb {s.get('x_bursts_med')} silent {s.get('x_silent')} "
                  f"| int {s.get('int_spikes_med')} {s.get('error', '')}", flush=True)

"""Slew-rate investigation: which simulation setting and interpolation measure the slew rate most accurately?

Reproduces the method comparison of the work log / report (reference designs of the TAs, references.csv):
- ground truth: the transient with a fixed 0.1 ns maximum time step, linear interpolation
- methods: the 50 ns testbench grid (linear and spline crossings), a smaller fixed maximum step, ngspice's own step
  control (.options trtol / reltol), forced breakpoints, a two-pass run, and combinations
- per method: SR of the first rising and falling edge, error vs the ground truth, ngspice time (median of N runs),
  Python time, and the extra minutes for a 5000-simulation run
- a plot of the rising and falling edge (ground truth, 50 ns samples, linear vs spline, trtol time points)

Only COPIES of TwoStage.cir are simulated (in the output folder); the testbench itself is not changed.
Run from CAD/:
    python analysis/sr_investigation.py                     # Design 1, 10 runs per method, + plot
    python analysis/sr_investigation.py --design "Design 3" --runs 3 --no-plot
Results go to no_backup/sr_investigation/ (method table as CSV, plot as PNG).
"""
import argparse
import os
import re
import sys
import time

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

sys.path.insert(0, os.getcwd())
from ngspice_interface import dut_testbench  # noqa: E402

YAML_PATH = os.path.join('ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')
NETLIST = os.path.join('ngspice_interface', 'files', 'input_netlists', 'TwoStage.cir')
VDD = 1.2  # .param VDD of the testbench
# the input pulse rises 0.5-1.0 us and falls 5.5-6.0 us: the output edges follow within a few hundred ns
INPUT_EDGE_WINDOWS = [(0.5e-6, 1.5e-6), (5.5e-6, 6.5e-6)]


# ---------- netlist variants (scratch copies) ----------

def netlist_variant(tran='tran 50n 30u', options='', extra=''):
    """The testbench text with another tran line, extra .options and/or extra elements (before .control)."""
    text = re.sub(r'^tran .*$', tran, open(NETLIST).read(), flags=re.M)
    text = re.sub(r'^\.options .*\n', '', text, flags=re.M)  # start from ngspice's defaults
    insert = ''.join(line + '\n' for line in [options, extra] if line)
    return text.replace('.control', insert + '.control', 1)


def breakpoint_source(windows, spacing):
    """A dummy PWL source on its own node: every PWL corner is a breakpoint, so ngspice must put a time point
    there. Alternating 0 / 1 uV makes every point a real corner. Not connected to the opamp."""
    points, k = [(0.0, 0.0)], 0
    for t_start, t_stop in windows:
        for t in np.arange(t_start, t_stop, spacing):
            if t > points[-1][0]:
                k += 1
                points.append((t, 1e-6 * (k % 2)))
    lines = ['vbp bp 0 PWL(']
    for i in range(0, len(points), 8):
        lines.append('+ ' + ' '.join(f'{t:.6e} {v:.1e}' for t, v in points[i:i + 8]))
    lines += ['+ )', 'rbp bp 0 1k']
    return '\n'.join(lines)


# ---------- measurement (rising and falling edge, linear or spline crossings) ----------

def levels(v):
    """10 % / 90 % levels of the swing, with the floor / cap of find_slew_rate."""
    v_low, v_high = v.min(), v.max()
    v_10 = max(v_low + 0.1 * (v_high - v_low), 0.1 * VDD)
    v_90 = min(v_low + 0.9 * (v_high - v_low), 0.9 * VDD)
    return v_10, v_90


def crossing_time(t, v, i, level, method):
    """Time where v crosses `level` inside the sample interval i -> i+1."""
    if method == 'linear':
        if v[i] < v[i + 1]:
            return np.interp(level, [v[i], v[i + 1]], [t[i], t[i + 1]])
        return np.interp(level, [v[i + 1], v[i]], [t[i + 1], t[i]])
    lo, hi = max(i - 2, 0), min(i + 4, len(t))  # spline through 3 samples on each side of the interval
    spline = CubicSpline(t[lo:hi], v[lo:hi])
    return brentq(lambda x: spline(x) - level, t[i], t[i + 1])


def first_crossing(t, v, level, rising, method, after=-np.inf):
    """(time, sample index) of the first crossing after `after`, or (None, None)."""
    if after is None:
        return None, None
    for i in range(len(v) - 1):
        if t[i + 1] <= after:
            continue
        if (rising and v[i] < level <= v[i + 1]) or (not rising and v[i] > level >= v[i + 1]):
            return crossing_time(t, v, i, level, method), i
    return None, None


def edge_slew_rates(t, v, method):
    """SR (V/us) of the first rising edge and the following falling edge; NaN if an edge is missing."""
    v_10, v_90 = levels(v)
    r_10, _ = first_crossing(t, v, v_10, True, method)
    r_90, _ = first_crossing(t, v, v_90, True, method, after=r_10)
    f_90, _ = first_crossing(t, v, v_90, False, method, after=r_90)
    f_10, _ = first_crossing(t, v, v_10, False, method, after=f_90)
    rise = (v_90 - v_10) / (r_90 - r_10) * 1e-6 if r_90 is not None else np.nan
    fall = (v_90 - v_10) / (f_10 - f_90) * 1e-6 if f_10 is not None else np.nan
    return rise, fall, (r_10, r_90, f_90, f_10)


def spline_overshoot(t, v):
    """Largest excursion (V) of the 6-sample splines beyond their samples, around the four crossings."""
    worst = 0.0
    v_10, v_90 = levels(v)
    for level, rising in [(v_10, True), (v_90, True), (v_90, False), (v_10, False)]:
        _, i = first_crossing(t, v, level, rising, 'linear')
        if i is None:
            continue
        lo, hi = max(i - 2, 0), min(i + 4, len(t))
        fine = np.linspace(t[lo], t[hi - 1], 400)
        s = CubicSpline(t[lo:hi], v[lo:hi])(fine)
        worst = max(worst, s.max() - v[lo:hi].max(), v[lo:hi].min() - s.min())
    return worst


# ---------- simulation ----------

def simulate(text, label, design, folder, n_runs):
    """Simulate one netlist variant n_runs times; returns time, v(net6), median ngspice time, parse time."""
    path = os.path.join(folder, f'{label}.cir')
    with open(path, 'w') as f:
        f.write(text)
    dut = dut_testbench.DUT(YAML_PATH)
    dut.netlist_path = path
    dut.output_netlists_folder = dut.output_files_folder = dut.logs_folder = folder
    dut.sim_timeout = 600.0  # the 0.1 ns ground truth takes ~40 s, longer than the testbench's 20 s timeout
    netlist = dut.create_new_netlist(design, process='TT', temp_pvt=27, vdd=VDD)
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        assert dut.simulate(netlist) == 0, label
        times.append(time.perf_counter() - start)
    start = time.perf_counter()
    assert dut.parse_outputs(), label
    return dut.time.copy(), dut.vout_tran.copy(), float(np.median(times)), time.perf_counter() - start


def reference_design(name):
    ref = pd.read_csv('references.csv').set_index('Attribute').drop(columns='Unit')
    return {row[len('param_'):]: (int(ref.loc[row, name]) if row.startswith('param_m') else float(ref.loc[row, name]))
            for row in ref.index if row.startswith('param_')}


def compare_methods(design, folder, n_runs):
    """The method table for one design (first row = ground truth)."""
    rows, waves = [], {}

    def run(label, text, interp='linear', runs=n_runs, extra_time=0.0, note=''):
        t, v, t_ngspice, t_parse = simulate(text, re.sub(r'\W+', '_', label), design, folder, runs)
        start = time.perf_counter()
        rise, fall, marks = edge_slew_rates(t, v, interp)
        t_python = t_parse + time.perf_counter() - start
        waves[label] = (t, v)
        rows.append(dict(method=label, sr_rise=rise, sr_fall=fall, t_ngspice=t_ngspice + extra_time,
                         t_python=t_python, points=len(t), note=note,
                         spline_overshoot_mV=spline_overshoot(t, v) * 1e3 if interp == 'spline' else np.nan))
        return marks

    run('ground truth (tmax 0.1 ns)', netlist_variant('tran 50n 30u 0 0.1n'), runs=max(1, n_runs // 5))
    marks_a = run('a. 50 ns grid', netlist_variant())
    run('b. 50 ns grid + spline', netlist_variant(), 'spline')
    for tmax in ['5n', '1n']:
        run(f'c. tmax {tmax}', netlist_variant(f'tran 50n 30u 0 {tmax}'))
    for opts in ['trtol=1', 'trtol=0.5', 'trtol=0.2', 'trtol=0.1', 'reltol=1e-4', 'trtol=1 reltol=1e-4', 'reltol=1e-5']:
        run(f'd1. {opts}', netlist_variant(options=f'.options {opts}'))
    for spacing in [1e-9, 2e-9]:
        run(f'd2. breakpoints {spacing * 1e9:.0f} ns in input-edge windows',
            netlist_variant(extra=breakpoint_source(INPUT_EDGE_WINDOWS, spacing)))
    # two-pass: the coarse run (a) locates the output edges, a second full run forces points only there
    r_10, r_90, f_90, f_10 = marks_a
    margin = 150e-9
    windows = [(r_10 - margin, r_90 + margin), (f_90 - margin, f_10 + margin)]
    t_pass1 = rows[1]['t_ngspice']
    for spacing in [1e-9, 0.5e-9]:
        run(f'd3. two-pass, {spacing * 1e9:g} ns points at the edges', netlist_variant(extra=breakpoint_source(windows, spacing)),
            extra_time=t_pass1, note='ngspice time includes pass 1')
    run('d4. breakpoints 1 ns + method=gear', netlist_variant(options='.options method=gear',
                                                               extra=breakpoint_source(INPUT_EDGE_WINDOWS, 1e-9)))
    run('e. trtol=1 + spline', netlist_variant(options='.options trtol=1'), 'spline')
    run('e. breakpoints 2 ns + spline', netlist_variant(extra=breakpoint_source(INPUT_EDGE_WINDOWS, 2e-9)), 'spline')
    run('e. tmax 5n + spline', netlist_variant('tran 50n 30u 0 5n'), 'spline')
    run('e. trtol=0.1 + tran 50n 5.5u', netlist_variant('tran 50n 5.5u', options='.options trtol=0.1'),
        note='rising edge only')
    run('f. tran 2n 5.5u', netlist_variant('tran 2n 5.5u'), note='rising edge only')

    table = pd.DataFrame(rows)
    truth = table.iloc[0]
    base = table.iloc[1]  # a. 50 ns grid
    table['err_rise_%'] = (table.sr_rise / truth.sr_rise - 1) * 100
    table['err_fall_%'] = (table.sr_fall / truth.sr_fall - 1) * 100
    table['extra_min_per_5000'] = (table.t_ngspice + table.t_python - base.t_ngspice - base.t_python) * 5000 / 60
    return table, waves


def plot_edges(waves, filename):
    """Rising and falling edge: ground truth, 50 ns samples (linear), 6-sample splines, trtol=0.1 time points."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    gt_t, gt_v = waves['ground truth (tmax 0.1 ns)']
    a_t, a_v = waves['a. 50 ns grid']
    w_t, w_v = waves['d1. trtol=0.1']
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    for ax, (t0, t1), rising, title in [(axes[0], (0.60e-6, 0.95e-6), True, 'rising edge'),
                                        (axes[1], (5.55e-6, 6.25e-6), False, 'falling edge')]:
        m = (gt_t >= t0) & (gt_t <= t1)
        ax.plot(gt_t[m] * 1e9, gt_v[m], color='black', lw=2.2, label='ground truth (tmax 0.1 ns)')
        m = (a_t >= t0 - 50e-9) & (a_t <= t1 + 50e-9)
        ax.plot(a_t[m] * 1e9, a_v[m], 'o-', color='tab:orange', ms=6, lw=1.2, label='50 ns grid: samples + linear')
        for k, level in enumerate(levels(a_v)):
            _, i = first_crossing(a_t, a_v, level, rising, 'linear', after=t0)
            if i is None or a_t[i] > t1:
                continue
            lo, hi = max(i - 2, 0), min(i + 4, len(a_t))
            fine = np.linspace(a_t[lo], a_t[hi - 1], 300)
            keep = (fine >= t0 - 50e-9) & (fine <= t1 + 50e-9)
            ax.plot(fine[keep] * 1e9, CubicSpline(a_t[lo:hi], a_v[lo:hi])(fine[keep]), color='tab:green', ls='--',
                    lw=1.5, label='50 ns grid: spline (6-sample window)' if k == 0 else None)
        m = (w_t >= t0) & (w_t <= t1)
        ax.plot(w_t[m] * 1e9, w_v[m], '.', color='tab:blue', ms=4, label='trtol=0.1: time points (adaptive)')
        for level, name in zip(levels(gt_v), ['10 %', '90 %']):
            ax.axhline(level, color='gray', lw=0.9, ls=':')
            ax.text(t1 * 1e9, level, f' {name} (truth)', va='center', fontsize=8, color='gray')
        ax.axhline(levels(a_v)[1], color='tab:orange', lw=0.9, ls=':')
        ax.text(t1 * 1e9, levels(a_v)[1] + 0.03, ' 90 % (50 ns grid)', va='center', fontsize=8, color='tab:orange')
        ax.set_xlim(t0 * 1e9, t1 * 1e9 + 60)
        ax.set_ylim(-0.25, 1.45)
        ax.set_xlabel('time (ns)')
        ax.set_title(f'Reference Design 1, {title}')
    axes[0].set_ylabel('v(net6) (V)')
    axes[0].legend(fontsize=8, loc='upper left')
    fig.tight_layout()
    fig.savefig(filename, dpi=130)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--design', default='Design 1', help='column of references.csv')
    parser.add_argument('--runs', type=int, default=10, help='ngspice runs per method (median time)')
    parser.add_argument('--out', default=os.path.join('no_backup', 'sr_investigation'))
    parser.add_argument('--no-plot', action='store_true')
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    table, waves = compare_methods(reference_design(args.design), args.out, args.runs)
    name = args.design.replace(' ', '_')
    table.to_csv(os.path.join(args.out, f'sr_methods_{name}.csv'), index=False)
    pd.set_option('display.width', 250)
    print(table[['method', 'sr_rise', 'sr_fall', 'err_rise_%', 'err_fall_%', 't_ngspice', 't_python',
                 'extra_min_per_5000', 'spline_overshoot_mV', 'note']].round(3).to_string(index=False))
    if not args.no_plot:
        plot_edges(waves, os.path.join(args.out, f'sr_methods_{name}.png'))
        print('plot:', os.path.join(args.out, f'sr_methods_{name}.png'))

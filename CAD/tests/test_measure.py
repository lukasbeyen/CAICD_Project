"""Tests for ngspice_interface/dut_testbench.py: the metric calculations.

Synthetic data with known answers checks the math of each measurement; four real designs are compared
with ngspice's own meas, and the TAs' five reference designs with their measured values.
Run from CAD/ (the course code builds its paths from os.getcwd()).
"""
import os
import re
import subprocess

import numpy as np
import pandas as pd
import pytest
import yaml
from scipy.optimize import brentq

from ngspice_interface import dut_testbench

YAML_PATH = os.path.join('ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')
REFERENCES = 'references.csv'  # TA reference designs: one column per design; rows param_*, action_*, spec_*, norm_*, reward

# same frequency grid as the netlist's "ac dec 10 1 1T"
FREQ = np.logspace(0, 12, 121)
VDD = 1.2  # supply of the testbench (.param VDD in TwoStage.cir), for the synthetic slew-rate signals

# a mid-range design on the TwoStage.yaml grid (W, L in m, Cc in F, Rc in ohm)
MID_DESIGN = {}
for dev in ['p1', 'n1', 'p3', 'n3', 'n4', 'n5']:
    MID_DESIGN['m' + dev] = 13
    MID_DESIGN['w' + dev] = 1.5e-06
    MID_DESIGN['l' + dev] = 1.35e-07
MID_DESIGN['cap'] = 5.0e-12
MID_DESIGN['res'] = 5000.0

# real designs for the comparison with ngspice's own measurements; the last two come from a
# scan of 40 random designs on the TwoStage.yaml grid (seed 0)
REAL_DESIGNS = {
    'mid_range': MID_DESIGN,
    'low_cc': dict(MID_DESIGN, cap=0.5e-12),  # PM ~ 40 deg: non-dominant pole close to the UGBW
    'high_gain': dict(mp1=12, wp1=1.25e-06, lp1=1.35e-07, mn1=11, wn1=1.0e-06, ln1=1.35e-07,
                      mp3=13, wp3=3.0e-06, lp3=1.8e-07, mn3=20, wn3=2.5e-07, ln3=9.0e-08,
                      mn4=25, wn4=1.0e-06, ln4=1.35e-07, mn5=22, wn5=2.0e-06, ln5=2.25e-07,
                      cap=1.7e-12, res=5100.0),  # gain ~ 1370 V/V, UGBW ~ 49 MHz, PM ~ 70 deg
    'negative_pm': dict(mp1=7, wp1=2.5e-06, lp1=1.8e-07, mn1=1, wn1=1.25e-06, ln1=2.25e-07,
                        mp3=14, wp3=2.5e-07, lp3=1.8e-07, mn3=19, wn3=2.75e-06, ln3=4.5e-08,
                        mn4=3, wn4=2.75e-06, ln4=4.5e-08, mn5=14, wn5=2.5e-07, ln5=9.0e-08,
                        cap=4.9e-12, res=4200.0),  # gain ~ 450 V/V, PM ~ -55 deg (unstable)
}

# control block of the reference netlist: an AC sweep with 1000 points/decade (instead of 10) and
# ngspice's own .meas. "meas ... when" interpolates linearly between the sweep points, so on the dense
# grid it is (almost) exact. cph() is ngspice's continuous (unwrapped) phase, in degrees here.
MEAS_CONTROL = """.control
set units=degrees
ac dec 1000 1 1T
meas ac gain find vm(net6) at=1
meas ac ugbw when vdb(net6)=0 fall=1
let phase = cph(v(net6))
meas ac phase_at_ugbw find phase at=ugbw
.endc
"""


def poles(a0, *pole_freqs):
    # H(f) = A0 / ((1 + j f/p1) (1 + j f/p2) ...)
    h = a0 * np.ones_like(FREQ, dtype=complex)
    for p in pole_freqs:
        h = h / (1 + 1j * FREQ / p)
    return h


def exact_ugbw_and_pm(a0, *pole_freqs):
    # exact unity-gain frequency of the analytic H(f), and PM = 180 - sum of atan(f/p)
    magnitude = lambda f: a0 / np.prod([np.sqrt(1 + (f / p) ** 2) for p in pole_freqs])
    ugbw = 10 ** brentq(lambda log_f: magnitude(10 ** log_f) - 1, 0, 12)
    pm = 180 - sum(np.degrees(np.arctan(ugbw / p)) for p in pole_freqs)
    return ugbw, pm


def write_outputs(folder, name, tran=None, ac=None, dc=None, noise=None):
    # write the 4 CSVs in the layout of the wrdata lines in TwoStage.cir (one header line each)
    defaults = {
        'tran': np.column_stack([np.linspace(0, 30e-6, 601), np.linspace(0, 1.2, 601)]),
        'ac': np.column_stack([FREQ, np.real(poles(500, 3e3)), np.imag(poles(500, 3e3))]),
        'dc': np.array([[0.6, -100e-6]]),
        'noise': np.array([[1e-3, 1e-3]]),
    }
    given = {'tran': tran, 'ac': ac, 'dc': dc, 'noise': noise}
    for analysis, data in defaults.items():
        if given[analysis] is not None:
            data = given[analysis]
        np.savetxt(os.path.join(folder, f'{analysis}_{name}.csv'), data, header='header', comments='')


def make_dut(tmp_path, name):
    dut = dut_testbench.DUT(YAML_PATH)
    dut.output_files_folder = str(tmp_path)
    dut.random_name = name
    dut.circuit_params = MID_DESIGN  # needed for the area estimate
    return dut


# ---------- gain, UGBW, PM on synthetic AC data ----------

def test_single_pole_gain_ugbw_pm():
    dut = dut_testbench.DUT(YAML_PATH)
    a0, fp = 500.0, 3e3
    vout = poles(a0, fp)
    exact_ugbw, exact_pm = exact_ugbw_and_pm(a0, fp)  # UGBW = fp*sqrt(A0^2-1), PM = 180 - atan(UGBW/fp) = 90.1 deg
    # |A(1 Hz)| = A0 / sqrt(1 + (1/fp)^2): equal to A0 within 1e-7
    assert dut.find_dc_gain(vout) == pytest.approx(a0, rel=1e-6)
    # far above the pole |A| falls at exactly -20 dB/dec, a straight line in log-log, so the
    # log-log interpolation is (almost) exact; linear |A| vs log f was 0.5 % off here
    assert dut.find_ugbw(FREQ, vout) == pytest.approx(exact_ugbw, rel=1e-4)
    assert dut.find_phm(FREQ, vout) == pytest.approx(exact_pm, abs=0.01)


def test_two_pole_pm():
    # dominant pole 1 kHz, non-dominant 5 MHz, A0 = 1000: UGBW ~ 0.98 MHz, PM ~ 79 deg
    dut = dut_testbench.DUT(YAML_PATH)
    vout = poles(1000.0, 1e3, 5e6)
    exact_ugbw, exact_pm = exact_ugbw_and_pm(1000.0, 1e3, 5e6)
    assert dut.find_ugbw(FREQ, vout) == pytest.approx(exact_ugbw, rel=1e-3)
    assert dut.find_phm(FREQ, vout) == pytest.approx(exact_pm, abs=0.1)


def test_three_pole_negative_pm_needs_unwrap():
    # three poles: the phase falls below -180 deg before |A| = 1, so PM is negative (unstable).
    # Without np.unwrap, np.angle would jump to +180 deg there and PM would come out above 180 deg.
    dut = dut_testbench.DUT(YAML_PATH)
    vout = poles(1e4, 1e2, 1e5, 2e5)
    exact_ugbw, exact_pm = exact_ugbw_and_pm(1e4, 1e2, 1e5, 2e5)
    assert exact_pm < 0
    assert dut.find_ugbw(FREQ, vout) == pytest.approx(exact_ugbw, rel=1e-2)
    assert dut.find_phm(FREQ, vout) == pytest.approx(exact_pm, abs=1.0)


def test_no_crossing_gives_zero_ugbw_and_pm():
    # DC gain below 1: |vout| never crosses 1 -> a valid simulation that fails the UGBW and PM specs
    dut = dut_testbench.DUT(YAML_PATH)
    assert dut.find_ugbw(FREQ, poles(0.5, 3e3)) == 0.0
    assert dut.find_phm(FREQ, poles(0.5, 3e3)) == 0.0


# ---------- slew rate on synthetic transient data ----------

def trapezoid(time, v_low, v_high, t_rise_start, rise_slope, t_fall_start, fall_slope):
    # ideal output: v_low, then a linear ramp up at rise_slope (V/s), flat at v_high,
    # a linear ramp down at fall_slope, flat at v_low
    up = np.clip(v_low + rise_slope * (time - t_rise_start), v_low, v_high)
    down = np.clip(v_high - fall_slope * (time - t_fall_start), v_low, v_high)
    return np.where(time < t_fall_start, up, down)


def test_slew_rate_ideal_ramp():
    # 0 -> 1.2 V at 4 V/us starting at 0.53 us, back at 2 V/us starting at 5.51 us (off the 50 ns grid).
    # The 10 % and 90 % crossings lie on the straight part of the ramp, where linear interpolation
    # between samples is exact. Only the rising edge counts (as in the TAs' references).
    dut = dut_testbench.DUT(YAML_PATH)
    time = np.arange(0, 30e-6, 50e-9)
    vout = trapezoid(time, 0.0, 1.2, 0.53e-6, 4e6, 5.51e-6, 2e6)
    sr = dut.find_slew_rate(time, vout, threshold_low=0.1, threshold_high=0.9, time_unit='us', vdd=VDD)
    assert sr == pytest.approx(4.0, rel=1e-6)
    # same signal in V/s
    assert dut.find_slew_rate(time, vout, time_unit='s', vdd=VDD) == pytest.approx(4e6, rel=1e-6)


def test_slew_rate_ignores_the_falling_edge():
    # a slow rising edge with a fast falling edge, and the other way round: the result is always the rising edge
    dut = dut_testbench.DUT(YAML_PATH)
    time = np.arange(0, 30e-6, 50e-9)
    assert dut.find_slew_rate(time, trapezoid(time, 0.0, 1.2, 0.53e-6, 2e6, 5.51e-6, 4e6), vdd=VDD) == pytest.approx(2.0, rel=1e-6)
    assert dut.find_slew_rate(time, trapezoid(time, 0.0, 1.2, 0.53e-6, 4e6, 5.51e-6, 1e6), vdd=VDD) == pytest.approx(4.0, rel=1e-6)


def glitchy_edge(time, v_settled, rise_slope, fall_slope, v_glitch):
    # 0 V -> v_settled at rise_slope from 1 us, a short glitch up to v_glitch around 5 us (like the kick through Cc),
    # back to v_settled, then down to 0 V at fall_slope from 6 us. Slow ramps on a 5 ns grid: every 4-sample window
    # around a 10 % / 90 % crossing lies on a straight part, so the crossings are exact.
    up = np.clip(rise_slope * (time - 1e-6), 0.0, v_settled)
    down = np.clip(v_settled - fall_slope * (time - 6e-6), 0.0, v_settled)
    vout = np.where(time < 6e-6, up, down)
    glitch = (time > 4.9e-6) & (time < 5.1e-6)
    vout[glitch] = v_glitch
    return vout


def test_slew_rate_glitch_above_vdd_is_capped():
    # settled at 1.2 V with a glitch to 1.5 V. Uncapped: 90 % = 0 + 0.9 * 1.5 = 1.35 V, never reached by the real
    # edge (only by the glitch). Capped at 0.9 * VDD = 1.08 V. 10 % = 0.15 V. On straight ramps the slew rate is
    # the ramp slope: (1.08 - 0.15) V / ((1.08 - 0.15) V / 2 V/us) = 2 V/us.
    dut = dut_testbench.DUT(YAML_PATH)
    time = np.arange(0, 10e-6, 5e-9)
    vout = glitchy_edge(time, 1.2, 2e6, 1e6, 1.5)
    sr = dut.find_slew_rate(time, vout, vdd=1.2)
    assert dut.slew_rate_levels[0] == pytest.approx(0.15)
    assert dut.slew_rate_levels[1] == pytest.approx(1.08)  # capped (uncapped it would be 1.35 V)
    assert sr == pytest.approx(2.0, rel=1e-6)


def test_slew_rate_kick_below_ground_is_floored():
    # the output kicks down to -0.3 V just before the edge (like the feed-forward through Cc when the input steps
    # up), then rises 0 -> 1.2 V at 2 V/us. Unfloored: 10 % = -0.3 + 0.1 * 1.5 = -0.15 V, crossed when the kick
    # recovers, long before the real edge. Floored at 0.1 * VDD = 0.12 V; 90 % = -0.3 + 0.9 * 1.5 = 1.05 V (below
    # the cap). On the straight ramp: SR = (1.05 - 0.12) V / ((1.05 - 0.12) V / 2 V/us) = 2 V/us.
    dut = dut_testbench.DUT(YAML_PATH)
    time = np.arange(0, 10e-6, 5e-9)
    vout = glitchy_edge(time, 1.2, 2e6, 1e6, 1.2)
    vout[(time > 0.9e-6) & (time < 0.95e-6)] = -0.3
    sr = dut.find_slew_rate(time, vout, vdd=1.2)
    assert dut.slew_rate_levels[0] == pytest.approx(0.12)  # floored (unfloored it would be -0.15 V)
    assert dut.slew_rate_levels[1] == pytest.approx(1.05)
    assert sr == pytest.approx(2.0, rel=1e-6)


def test_slew_rate_flat_output_is_zero():
    # a railed output that never moves has no edge: SR = 0 (valid simulation, failing spec)
    dut = dut_testbench.DUT(YAML_PATH)
    time = np.arange(0, 30e-6, 50e-9)
    assert dut.find_slew_rate(time, np.full_like(time, 3e-3), vdd=VDD) == 0.0


# ---------- failed simulations: measure_metrics returns None instead of crashing ----------

def test_missing_output_files_is_failed(tmp_path):
    # ngspice wrote nothing
    dut = make_dut(tmp_path, 'TwoStage_missing')
    assert dut.measure_metrics() is None


def test_nan_in_output_is_failed(tmp_path):
    ac = np.column_stack([FREQ, np.real(poles(500, 3e3)), np.imag(poles(500, 3e3))])
    ac[10, 1] = np.nan
    write_outputs(str(tmp_path), 'TwoStage_nan', ac=ac)
    assert make_dut(tmp_path, 'TwoStage_nan').measure_metrics() is None


# ---------- real simulation ----------

def ngspice_meas_reference(netlist_path):
    # copy the netlist of the design, swap its control block for MEAS_CONTROL, run ngspice and read the
    # "name = value" lines that meas prints (ngspice's output is captured here, never printed)
    with open(netlist_path) as f:
        text = f.read()
    text = re.sub(r'\.control.*?\.endc\n', MEAS_CONTROL, text, flags=re.S)
    meas_path = netlist_path.replace('.cir', '_meas.cir')
    with open(meas_path, 'w') as f:
        f.write(text)
    result = subprocess.run(['ngspice', '-b', meas_path], capture_output=True, text=True)
    values = dict(re.findall(r'^(\w+)\s*=\s*([-+.\deE]+)', result.stdout, flags=re.M))
    return {'gain': float(values['gain']), 'ugbw': float(values['ugbw']),
            'phm': 180.0 + float(values['phase_at_ugbw'])}


@pytest.mark.parametrize('name', REAL_DESIGNS)
def test_measurements_match_ngspice_meas(tmp_path, name):
    # our gain, UGBW and PM (10 points/decade, log-log interpolation, np.unwrap) against ngspice's own
    # measurement of the same design on a 100x denser sweep (linear interpolation, cph)
    dut =   dut_testbench.DUT(YAML_PATH)
    dut.output_netlists_folder = dut.output_files_folder = dut.logs_folder = str(tmp_path)
    netlist_path = dut.create_new_netlist(REAL_DESIGNS[name], process='TT')
    assert dut.simulate(netlist_path) == 0
    metrics = dut.measure_metrics()
    reference = ngspice_meas_reference(netlist_path)
    if name == 'negative_pm':
        assert reference['phm'] < 0  # the design still is what its name says
    for spec in ['gain', 'ugbw', 'phm']:
        assert metrics[spec] == pytest.approx(reference[spec], rel=0.01), spec


# ---------- the TAs' reference designs (references.csv) ----------

def load_references():
    # {design name: {attribute: value}}, e.g. REFERENCE_DESIGNS['Design 1']['spec_gain']
    table = pd.read_csv(REFERENCES).set_index('Attribute').drop(columns='Unit')
    return {design: table[design].to_dict() for design in table.columns}


REFERENCE_DESIGNS = load_references()


@pytest.mark.parametrize('design', REFERENCE_DESIGNS)
def test_reference_designs(tmp_path, design):
    # all 7 metrics within 1 % of the TAs' values. Two settings matter: 27 degC (the env's pvt_corner; at the netlist
    # default of 25 degC the gain is up to 8 % off) and the testbench's .options trtol=0.1, which makes ngspice take
    # time steps small enough to resolve the fast slew-rate edges
    ref = REFERENCE_DESIGNS[design]
    dut = dut_testbench.DUT(YAML_PATH)
    dut.output_netlists_folder = dut.output_files_folder = dut.logs_folder = str(tmp_path)
    params = {}
    for name in dut.param_names:
        value = ref['param_' + name]
        params[name] = int(value) if name.startswith('m') else value
    assert dut.simulate(dut.create_new_netlist(params, process='TT', temp_pvt=27, vdd=1.2)) == 0
    metrics = dut.measure_metrics()
    assert metrics is not None
    for name in ['area', 'current', 'gain', 'noise', 'phm', 'slewRate', 'ugbw']:
        assert metrics[name] == pytest.approx(ref['spec_' + name], rel=0.01), name

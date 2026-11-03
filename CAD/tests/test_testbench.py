"""Tests for ngspice_interface/dut_testbench.py: the metric calculations.

Run from CAD/ (the course code builds its paths from os.getcwd()).
"""
import os

import numpy as np

from ngspice_interface import DUT

YAML_PATH = os.path.join('ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')

# same frequency grid as the netlist's "ac dec 10 1 1T"
FREQ = np.logspace(0, 12, 121)


def single_pole(a0, fp):
    # H(f) = A0 / (1 + j f/fp); |H| = 1 at f = fp * sqrt(A0^2 - 1) ≈ A0 * fp (gain-bandwidth product)
    return a0 / (1 + 1j * FREQ / fp)


def test_ugbw_single_pole():
    dut = DUT(YAML_PATH)
    a0, fp = 500.0, 3e3
    exact = fp * np.sqrt(a0**2 - 1)
    # far above the pole |A| falls at exactly -20 dB/dec, a straight line in log-log, so the
    # log-log interpolation is (almost) exact; linear |A| vs log f was 0.5 % off here
    assert abs(dut.find_ugbw(FREQ, single_pole(a0, fp)) - exact) / exact < 1e-4


def test_no_crossing_gives_zero_ugbw_and_pm():
    # DC gain below 1: |vout| never crosses 1 -> a valid simulation that fails the UGBW and PM specs
    dut = DUT(YAML_PATH)
    assert dut.find_ugbw(FREQ, single_pole(0.5, 3e3)) == 0.0
    assert dut.find_phm(FREQ, single_pole(0.5, 3e3)) == 0.0


def test_missing_output_files_is_failed(tmp_path):
    # ngspice wrote nothing: measure_metrics reports a failed simulation (None) instead of crashing
    dut = DUT(YAML_PATH)
    dut.output_files_folder = str(tmp_path)
    dut.random_name = 'TwoStage_missing'
    assert dut.measure_metrics() is None


def test_empty_output_files_is_failed(tmp_path):
    dut = DUT(YAML_PATH)
    dut.output_files_folder = str(tmp_path)
    dut.random_name = 'TwoStage_empty'
    for analysis in ['tran', 'ac', 'dc', 'noise']:
        open(os.path.join(str(tmp_path), analysis + '_TwoStage_empty.csv'), 'w').close()
    assert dut.measure_metrics() is None

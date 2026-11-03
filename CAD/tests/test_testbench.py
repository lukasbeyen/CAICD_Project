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
    assert abs(dut.find_ugbw(FREQ, single_pole(a0, fp)) - exact) / exact < 0.01


def test_ugbw_no_crossing():
    # DC gain below 1: |vout| never crosses 1
    dut = DUT(YAML_PATH)
    assert dut.find_ugbw(FREQ, single_pole(0.5, 3e3)) == 0.0

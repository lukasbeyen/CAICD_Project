"""Tests for ngspice_interface/ngspice_wrapper.py: netlist generation and running ngspice.

Run from the repo root (the course code builds its paths from os.getcwd()).
"""
import os

from ngspice_interface import DUT

YAML_PATH = os.path.join('ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')

# A mid-range design on the TwoStage.yaml grid (W, L in m, Cc in F, Rc in ohm)
MID_DESIGN = {}
for dev in ['p1', 'n1', 'p3', 'n3', 'n4', 'n5']:
    MID_DESIGN['m' + dev] = 13
    MID_DESIGN['w' + dev] = 1.5e-06
    MID_DESIGN['l' + dev] = 1.35e-07
MID_DESIGN['cap'] = 5.0e-12
MID_DESIGN['res'] = 5000.0


def make_dut(tmp_path):
    dut = DUT(YAML_PATH)
    # keep test output out of no_backup/
    dut.output_netlists_folder = str(tmp_path)
    dut.logs_folder = str(tmp_path)
    return dut


def test_netlist_has_new_parameters(tmp_path):
    dut = make_dut(tmp_path)
    netlist_path = dut.create_new_netlist(MID_DESIGN, process='TT')
    text = open(netlist_path).read()
    assert '.param wp1=1.5e-06 lp1=1.35e-07 mp1=13' in text
    assert '.param cap=5e-12' in text
    assert '.param res=5000.0' in text
    assert 'p045_TT.sp' in text


def test_simulate_runs_and_writes_log(tmp_path):
    dut = make_dut(tmp_path)
    netlist_path = dut.create_new_netlist(MID_DESIGN, process='TT')
    assert dut.simulate(netlist_path) == 0
    log_path = netlist_path.replace('.cir', '.log')
    assert os.path.isfile(log_path)


def test_simulate_reports_ngspice_error(tmp_path):
    # ngspice exits with code 1 on a missing include file; the original "% 256" check missed this
    dut = make_dut(tmp_path)
    netlist_path = dut.create_new_netlist(MID_DESIGN, process='TT')
    text = open(netlist_path).read().replace('p045_TT.sp', 'p045_missing.sp')
    open(netlist_path, 'w').write(text)
    assert dut.simulate(netlist_path) == 1


def test_simulate_timeout_is_failed(tmp_path):
    # a simulation that runs longer than sim_timeout is killed and reported as failed (info = 1), with timed_out set
    dut = make_dut(tmp_path)
    dut.output_files_folder = str(tmp_path)
    dut.sim_timeout = 0.001  # s: far shorter than any ngspice run
    assert dut.simulate(dut.create_new_netlist(MID_DESIGN, process='TT')) == 1
    assert dut.timed_out
    log = [f for f in os.listdir(str(tmp_path)) if f.endswith('.log')]
    assert 'simulation timeout' in open(os.path.join(str(tmp_path), log[0])).read()
    # the next normal simulation clears the flag
    dut.sim_timeout = 20.0
    assert dut.simulate(dut.create_new_netlist(MID_DESIGN, process='TT')) == 0
    assert not dut.timed_out

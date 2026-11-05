"""Tests for analysis/harness_vs_rl.py with small made-up run folders (no ngspice, no agy)."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis'))
import harness_vs_rl  # noqa: E402


@pytest.fixture
def runs(tmp_path, monkeypatch):
    monkeypatch.setattr(harness_vs_rl, 'RUNS', str(tmp_path))
    os.makedirs(tmp_path / 'h')
    pd.DataFrame({'elapsed_s': [30, 90, 150, 210, 270], 'call': [1, 2, 3, 4, 5],
                  'source': ['simulate'] * 5, 'reason': ['start', 'fails', 'raise Rc', 'worse', 'lower Cc'],
                  'reward': [-1.0, '', 0.55, 0.40, 0.65], 'hard_satisfied': [False, '', True, True, True],
                  'failed': [False, True, False, False, False]}).to_csv(tmp_path / 'h' / 'harness_history.csv', index=False)
    os.makedirs(tmp_path / 'r')
    pd.DataFrame({'sim': [1, 2, 3, 4], 'step': [0, 1, 2, 3],
                  'netlist': [f'TwoStage_{1000 + 60 * i}_abc.cir' for i in range(4)],
                  'reward': ['', -2.0, 0.61, 0.5], 'hard_satisfied': ['', False, True, True]}).to_csv(tmp_path / 'r' / 'designs.csv', index=False)
    return tmp_path


def test_curves_skip_failed_and_reset_rows_and_use_the_right_clock(runs):
    harness = harness_vs_rl.harness_curve('h')
    assert list(harness.sim) == [1, 3, 4, 5]                     # the failed call 2 is left out
    assert harness.minutes.iloc[0] == pytest.approx(0.5)
    rl = harness_vs_rl.rl_curve('r')
    assert list(rl.sim) == [2, 3, 4]                             # the reset design (step 0) has no reward
    assert list(rl.minutes) == [1.0, 2.0, 3.0]                   # from the netlist timestamps, 60 s apart


def test_milestones_give_time_and_simulations_to_each_level(runs):
    harness = harness_vs_rl.harness_curve('h')
    reached = harness_vs_rl.milestones(harness, best_harness=0.65)
    assert reached['first design meeting all specs'] == '2.5 min / 3 sims'
    assert reached['FoM >= 0.6'] == '4.5 min / 5 sims'
    rl = harness_vs_rl.milestones(harness_vs_rl.rl_curve('r'), best_harness=0.65)
    assert rl['FoM >= 0.6'] == '2.0 min / 3 sims' and rl["the harness's best FoM (0.650)"] == 'never'
    assert reached["the harness's best FoM (0.650)"] == '4.5 min / 5 sims'


def test_improvements_are_the_simulations_that_raised_the_best_fom(runs):
    trace = harness_vs_rl.improvements(harness_vs_rl.harness_curve('h'))
    assert list(trace.reason) == ['start', 'raise Rc', 'lower Cc']

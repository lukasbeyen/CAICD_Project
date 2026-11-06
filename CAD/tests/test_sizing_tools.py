"""Tests for sizing_tools.py (milestone 4 backend of the MCP tools): validation, simulate, warmup, train, get_status.

No ngspice: both envs of the experiment get the fake simulator of test_env.py. Run from CAD/.
"""
import math
import os

import numpy as np
import pandas as pd
import pytest
import torch

import circuit_env
from sizing_tools import SizingExperiment
from tests.test_env import FakeEngine

FEASIBLE = {'area': 1e-9, 'current': 1e-4, 'gain': 300.0, 'noise': 0.01, 'phm': 70.0, 'slewRate': 50.0, 'ugbw': 2e8}


class BreakingEngine(FakeEngine):
    """A fake simulator whose measurement raises from the n-th simulation on (an unexpected error, not a failed sim)."""

    def __init__(self, folder, break_at):
        super().__init__(folder)
        self.break_at = break_at

    def measure_metrics(self):
        if len(self.calls) >= self.break_at:
            raise OSError('disk full')
        return super().measure_metrics()


@pytest.fixture
def make_experiment(tmp_path, monkeypatch):
    # the course's plot and solutions helpers write to ./output_figs and ./solutions: not during the tests
    for helper in ['plot_running_maximum', 'plotLearning', 'solutions2pareto', 'save_solutions_csv']:
        monkeypatch.setattr(circuit_env, helper, lambda *args, **kwargs: None)

    def _make(engine=None, seed=0, batch_size=8, **engine_kwargs):
        experiment = SizingExperiment(seed=seed, batch_size=batch_size, replay_size=1000)
        for env, name in [(experiment.env, 'run'), (experiment.evaluation_env, 'run_evaluate')]:
            env.simulation_engine = engine or FakeEngine(str(tmp_path), **engine_kwargs)
            env.run_folder = str(tmp_path / name)
        experiment.history_path = str(tmp_path / 'run' / 'harness_history.csv')
        monkeypatch.setattr(experiment, '_clean', lambda: None)  # clean.sh would empty the real no_backup/
        return experiment
    return _make


def a_design(experiment, action_value=0.3):
    # a valid design: what action_refine makes of one action (all values on the grid)
    return experiment.env.action_refine(np.full(experiment.env.n_actions, action_value))


def history(experiment):
    return pd.read_csv(experiment.history_path)


# ---------- _validate_parameters ----------

def test_valid_design_is_returned_with_canonical_values(make_experiment):
    experiment = make_experiment()
    design = a_design(experiment)
    noisy = {name: (float(value) * (1 + 1e-12) if name.startswith(('w', 'l', 'cap')) else float(value))
             for name, value in design.items()}  # float round-off, and multiplicities as 3.0 (JSON sends floats)
    valid = experiment._validate_parameters(noisy)
    assert valid == design
    assert all(type(valid[name]) is int for name in valid if name.startswith('m'))


def test_the_grid_is_action_refines_grid_and_np_arange(make_experiment):
    # "Use the same np.arange(min, max, step) grids as phase one": every grid value is accepted, and the largest
    # one is what action_refine gives for action +1 (the YAML max itself is excluded)
    experiment = make_experiment()
    top = experiment.env.action_refine(np.ones(experiment.env.n_actions))
    for name, (min_val, max_val, step) in experiment.env.dict_params.items():
        grid = np.arange(min_val, max_val, step)
        assert np.isclose(grid[-1], top[name], rtol=1e-12)
        for value in grid:
            design = dict(top, **{name: float(value)})
            assert np.isclose(experiment._validate_parameters(design)[name], value, rtol=1e-12)


@pytest.mark.parametrize('change', [
    {'wp1': 2.5e-07 + 1.25e-07},  # between two grid points
    {'lp1': 225e-09},             # the YAML max: not on the np.arange grid
    {'mn1': 0},                   # below the min
    {'cap': float('nan')},
    {'res': float('inf')},
    {'mp1': True},                # a bool is not a number here
    {'mp1': '3'},
])
def test_invalid_values_are_rejected_without_simulating(make_experiment, change):
    experiment = make_experiment()
    with pytest.raises(ValueError):
        experiment.simulate(dict(a_design(experiment), **change))
    assert experiment.simulator_calls == 0 and experiment.evaluation_env.simulation_engine.calls == []


def test_missing_or_unknown_parameter_names_are_rejected(make_experiment):
    experiment = make_experiment()
    design = a_design(experiment)
    with pytest.raises(ValueError, match='missing'):
        experiment._validate_parameters({name: value for name, value in design.items() if name != 'res'})
    with pytest.raises(ValueError, match='unknown'):
        experiment._validate_parameters(dict(design, vdd=1.2))


# ---------- simulate ----------

def test_simulate_returns_the_scored_design_and_leaves_the_rl_state_alone(make_experiment):
    experiment = make_experiment()
    experiment.warmup(3)  # an episode in progress, 3 transitions in the buffer
    before = dict(observation=experiment.observation.copy(), replay=experiment.replay.size,
                  episode_steps=experiment.env.episode_steps, env_counter=experiment.env.counter,
                  actor=[p.detach().clone() for p in experiment.agent.actor.parameters()])
    candidate = experiment.simulate(a_design(experiment), reason='test')

    assert np.array_equal(experiment.observation, before['observation'])
    assert experiment.replay.size == before['replay']
    assert experiment.env.episode_steps == before['episode_steps']
    assert experiment.env.counter == before['env_counter']
    assert all(torch.equal(a, b) for a, b in zip(before['actor'], experiment.agent.actor.parameters()))
    assert experiment.evaluation_env.counter == 1
    assert experiment.simulator_calls == 3 + 1 + 1  # 3 steps + 1 reset + this simulation
    # scored with the env's own functions
    env = experiment.evaluation_env
    reward, hard = env.reward_computation(env.normalize_specs(env.simulation_engine.measure_metrics()))
    assert candidate['reward'] == pytest.approx(reward, abs=1e-4) and candidate['hard_constraints_satisfied'] == hard
    assert candidate['source'] == 'simulate' and set(candidate['specs']) == set(env.dict_targets)


def test_a_feasible_design_keeps_its_netlist(make_experiment):
    experiment = make_experiment(metrics=FEASIBLE)
    candidate = experiment.simulate(a_design(experiment))
    assert candidate['hard_constraints_satisfied'] and candidate['reward'] > 0.3
    kept = os.listdir(os.path.join(experiment.env.run_folder, 'feasible_netlists'))
    assert kept == [os.path.basename(experiment.evaluation_env.netlist)]


# ---------- warmup / train ----------

def test_warmup_adds_exactly_n_transitions_and_no_updates(make_experiment):
    experiment = make_experiment()
    status = experiment.warmup(15)
    # episodes of 10 steps: 2 resets (simulations, not transitions) + 15 step simulations
    assert status['steps_completed'] == 15 and status['experiences_added'] == 15
    assert status['simulator_calls_used'] == 17 and status['updates_performed'] == 0
    assert experiment.replay.size == 15 and experiment.updates == 0 and experiment.agent.total_it == 0
    assert experiment.warmup_steps == 15 and status['episode_in_progress']


def test_train_needs_batch_size_experiences_then_one_update_per_transition(make_experiment):
    experiment = make_experiment(batch_size=8)
    with pytest.raises(ValueError, match='warmup'):
        experiment.train(1)
    experiment.warmup(8)
    status = experiment.train(5)
    assert status['updates_performed'] == 5 and experiment.agent.total_it == 5
    assert experiment.training_steps == 5 and experiment.replay.size == 13


@pytest.mark.parametrize('n_steps', [0, 1001, 2.0, True])
def test_step_counts_are_bounded_integers(make_experiment, n_steps):
    experiment = make_experiment()
    with pytest.raises(ValueError):
        experiment.warmup(n_steps)


def test_failed_simulations_are_logged_but_never_in_replay_or_candidates(make_experiment):
    experiment = make_experiment(exit_code=1)  # every ngspice run fails
    status = experiment.warmup(3)
    assert status['steps_completed'] == 3 and status['experiences_added'] == 0 and experiment.replay.size == 0
    assert experiment.candidates == {}
    with pytest.raises(RuntimeError, match='failed'):
        experiment.simulate(a_design(experiment))
    rows = history(experiment)
    assert len(rows) == experiment.simulator_calls == 5  # reset + 3 steps + 1 simulate
    assert rows.failed.all()


def test_an_error_mid_batch_keeps_the_finished_steps(make_experiment, tmp_path):
    experiment = make_experiment(engine=BreakingEngine(str(tmp_path), break_at=6))
    with pytest.raises(RuntimeError, match='4 of 10 steps'):
        experiment.warmup(10)  # simulation 6 = reset + 4 finished steps + the 5th step's simulation
    status = experiment.get_status()
    assert status['warmup_steps'] == 4 and experiment.replay.size == 4


def test_same_seed_gives_the_same_warmup_designs(make_experiment):
    designs = []
    for seed in [5, 5, 6]:
        experiment = make_experiment(seed=seed)
        experiment.warmup(12)
        designs.append(history(experiment).drop(columns=['time', 'elapsed_s', 'netlist']))
        os.remove(experiment.history_path)
    assert designs[0].equals(designs[1]) and not designs[0].equals(designs[2])


# ---------- get_status and the history ----------

def test_get_status_ranks_distinct_designs_and_returns_copies(make_experiment):
    experiment = make_experiment()
    low, high = a_design(experiment, -0.5), a_design(experiment, 0.5)  # the fake gives a higher gain for larger mn1
    experiment.simulate(low)
    experiment.simulate(low)  # a repeat replaces, it doesn't add
    experiment.simulate(high)
    status = experiment.get_status(k=5)
    assert status['candidates_measured'] == 2 and len(status['best_candidates']) == 2
    rewards = [c['reward'] for c in status['best_candidates']]
    assert rewards == sorted(rewards, reverse=True)
    status['best_candidates'][0]['reward'] = 99.0
    assert experiment.get_status(k=1)['best_candidates'][0]['reward'] != 99.0
    for k in [0, 21]:
        with pytest.raises(ValueError):
            experiment.get_status(k)


def test_history_has_one_row_per_simulator_call_with_source_and_reason(make_experiment):
    experiment = make_experiment(batch_size=4)
    experiment.warmup(4, reason='fill the buffer')
    experiment.simulate(a_design(experiment), reason='raise mn1 for gain')
    experiment.train(2, reason='explore near the best design')
    rows = history(experiment)
    assert len(rows) == experiment.simulator_calls
    assert list(rows.call) == list(range(1, experiment.simulator_calls + 1))
    assert list(rows.source) == ['reset'] + ['warmup'] * 4 + ['simulate'] + ['train'] * 2
    assert rows.loc[rows.source == 'simulate', 'reason'].item() == 'raise mn1 for gain'
    assert not math.isnan(rows.elapsed_s.iloc[-1])


def test_tool_results_are_compact_but_the_history_keeps_full_precision(make_experiment):
    # fewer tokens for the LLM: rounded numbers, the units once per status, the top 3 in warmup/train results
    experiment = make_experiment(metrics={'area': 8.634113333333333e-10, 'current': 0.00020590559,
                                          'gain': 663.6944800049262, 'noise': 0.021489595, 'phm': 65.7972831540237,
                                          'slewRate': 55.960804486038334, 'ugbw': 95057613.34824488})
    design = dict(a_design(experiment), wn1=1.4999999999999998e-06)
    result = experiment.simulate(design)
    assert result['parameters']['wn1'] == 1.5e-06 and type(result['parameters']['mn1']) is int
    assert result['specs']['gain'] == 663.7 and result['specs']['ugbw'] == 9.506e7
    assert result['spec_units']['ugbw'] == 'Hz'  # simulate returns spec_units (template)
    assert experiment._validate_parameters(result['parameters']) == experiment._validate_parameters(design)
    status = experiment.get_status(k=1)
    assert 'spec_units' in status and 'spec_units' not in status['best_candidates'][0]
    assert len(experiment.warmup(12)['best_candidates']) == 3
    assert history(experiment).gain.iloc[0] == 663.6944800049262  # the CSV keeps the full value

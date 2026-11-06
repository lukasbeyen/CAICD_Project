"""Tests for hybrid_tools.py (milestone 4, version 2): LLM designs as RL experience, short RL bursts, the design log.

No ngspice: both envs get the fake simulator of test_env.py. Run from CAD/.
"""
import os

import numpy as np
import pandas as pd
import pytest
import torch

import circuit_env
from hybrid_tools import MAX_LOG_CHARS, HybridExperiment
from tests.test_env import FakeEngine


@pytest.fixture
def make_experiment(tmp_path, monkeypatch):
    for helper in ['plot_running_maximum', 'plotLearning', 'solutions2pareto', 'save_solutions_csv']:
        monkeypatch.setattr(circuit_env, helper, lambda *args, **kwargs: None)

    def _make(**engine_kwargs):
        experiment = HybridExperiment(seed=0, log_path=str(tmp_path / 'design_log.md'))
        for env, name in [(experiment.env, 'run'), (experiment.evaluation_env, 'run_evaluate')]:
            env.simulation_engine = FakeEngine(str(tmp_path), **engine_kwargs)
            env.run_folder = str(tmp_path / name)
        experiment.history_path = str(tmp_path / 'run' / 'harness_history.csv')
        monkeypatch.setattr(experiment, '_clean', lambda: None)
        return experiment
    return _make


def a_design(experiment, action_value=0.3):
    return experiment.env.action_refine(np.full(experiment.env.n_actions, action_value))


def history(experiment):
    return pd.read_csv(experiment.history_path)


# ---------- designs <-> actions ----------

def test_every_grid_value_maps_to_an_action_and_back(make_experiment):
    # to_action is the exact inverse of action_refine: the LLM's designs are valid TD3 actions
    experiment = make_experiment()
    names = list(experiment.env.dict_params)
    base = a_design(experiment)
    for name, (min_val, max_val, step) in experiment.env.dict_params.items():
        for value in np.arange(min_val, max_val, step):
            design = experiment._validate_parameters(dict(base, **{name: float(value)}))
            back = experiment.env.action_refine(experiment.to_action(design))
            assert back == design, (name, value)
    assert len(experiment.to_action(base)) == len(names)


# ---------- simulate: full designs, changes, RL experience ----------

def test_simulate_by_changes_relative_to_the_best_or_an_earlier_simulation(make_experiment):
    experiment = make_experiment()
    first = a_design(experiment, -0.5)
    experiment.simulate(parameters=first, reason='start')
    second = experiment.simulate(changes={'cap': 5e-13}, reason='Cc')
    assert second['parameters']['cap'] == 5e-13
    assert {k: v for k, v in second['parameters'].items() if k != 'cap'} == \
        {k: v for k, v in experiment.designs[1]['parameters'].items() if k != 'cap'}
    third = experiment.simulate(changes={'res': 1000.0}, base=1, reason='Rc on sim 1')
    assert third['parameters']['cap'] == pytest.approx(first['cap']) and third['parameters']['res'] == 1000.0


@pytest.mark.parametrize('call', [
    dict(),                                                  # neither parameters nor changes
    dict(parameters={'mp1': 1}, changes={'cap': 5e-13}),     # both
    dict(changes={'vdd': 1.2}),                              # an unknown name
    dict(changes={'cap': 5e-13}, base=99),                   # no such simulation
])
def test_invalid_simulate_calls_are_refused_without_simulating(make_experiment, call):
    experiment = make_experiment()
    experiment.simulate(parameters=a_design(experiment))
    with pytest.raises(ValueError):
        experiment.simulate(**call)
    assert experiment.simulator_calls == 1


def test_the_first_design_must_be_given_in_full(make_experiment):
    experiment = make_experiment()
    with pytest.raises(ValueError, match='in full'):
        experiment.simulate(changes={'cap': 5e-13})


def test_every_simulation_becomes_one_rl_transition(make_experiment):
    experiment = make_experiment()
    designs = [a_design(experiment, a) for a in (-0.4, 0.1, 0.6)]
    for i, design in enumerate(designs, start=1):
        experiment.simulate(parameters=design)
        assert experiment.replay.size == i
        # the stored action gives back exactly this design
        assert experiment.env.action_refine(experiment.replay.action[i - 1]) == experiment._validate_parameters(design)
        stored = experiment.designs[i]
        assert experiment.replay.reward[i - 1, 0] == pytest.approx(stored['reward'])
        assert np.allclose(experiment.replay.next_state[i - 1], experiment.state_of(stored))


def test_a_failed_simulation_adds_no_transition(make_experiment):
    experiment = make_experiment(exit_code=1)
    with pytest.raises(RuntimeError):
        experiment.simulate(parameters=a_design(experiment))
    assert experiment.replay.size == 0 and experiment.designs == {}


# ---------- rl_explore: short bursts around the best design ----------

def test_rl_explore_needs_a_design_and_is_bounded(make_experiment):
    experiment = make_experiment()
    with pytest.raises(ValueError, match='simulate first'):
        experiment.rl_explore(10)
    experiment.simulate(parameters=a_design(experiment))
    for n in [0, 61]:
        with pytest.raises(ValueError):
            experiment.rl_explore(n)


def test_a_burst_is_n_simulations_n_transitions_and_n_updates_without_warm_up(make_experiment):
    # 2 LLM designs in the buffer (far fewer than batch_size 100): TD3 still updates from the first RL step
    experiment = make_experiment()
    experiment.simulate(parameters=a_design(experiment, -0.2))
    experiment.simulate(parameters=a_design(experiment, 0.2))
    report = experiment.rl_explore(25, reason='burst')
    assert report['simulator_calls_used'] == 25 and experiment.simulator_calls == 27
    assert experiment.replay.size == 27 and experiment.updates == 25 and experiment.agent.total_it == 25
    rows = history(experiment)
    assert list(rows.source) == ['simulate'] * 2 + ['rl'] * 25  # no reset and no random warm-up simulations
    assert len(rows) == experiment.simulator_calls
    for key in ['rl_designs_better_than_previous_best', 'warm_started', 'new_best', 'changes_vs_previous_best',
                'best_reward', 'best_specs', 'best_meets_all_specs']:
        assert key in report


def test_episodes_start_at_the_current_best_design(make_experiment):
    experiment = make_experiment()
    experiment.simulate(parameters=a_design(experiment, -0.6))
    experiment.simulate(parameters=a_design(experiment, 0.6))
    best_state = experiment.state_of(experiment._best())
    experiment.rl_explore(1)
    assert np.allclose(experiment.replay.state[2], best_state)  # the first RL transition starts at the best


def test_the_warm_start_pulls_the_actor_to_the_best_design_only_when_it_changed(make_experiment):
    experiment = make_experiment()
    experiment.simulate(parameters=a_design(experiment, -0.3))
    best = experiment._best()
    state = torch.as_tensor(experiment.state_of(best)).reshape(1, -1)
    target = torch.as_tensor(experiment.to_action(best['parameters']))
    with torch.no_grad():
        before = (experiment.agent.actor(state)[0] - target).abs().max().item()
    assert experiment._warm_start(best) is True
    with torch.no_grad():
        after = (experiment.agent.actor(state)[0] - target).abs().max().item()
    assert after < 0.25 * before
    assert experiment._warm_start(best) is False  # same best: no second warm start
    # the target actor is a copy of the warm-started actor
    assert all(torch.equal(a, b) for a, b in zip(experiment.agent.actor.parameters(), experiment.agent.actor_target.parameters()))
    experiment.simulate(changes={'mn1': best['parameters']['mn1'] + 1})
    if experiment._best() is not best:
        assert experiment._warm_start(experiment._best()) is True


# ---------- the design log ----------

def test_log_entries_are_numbered_and_bounded(make_experiment):
    experiment = make_experiment()
    experiment.simulate(parameters=a_design(experiment))
    assert experiment.log_entry('designer', 'first design') == {'entry': 1}
    assert experiment.log_entry('reviewer', 'final') == {'entry': 2}
    text = open(experiment.log_path).read()
    assert text.count('## Session') == 1
    assert '### 1. designer (simulations so far: 1)' in text and '### 2. reviewer' in text
    with pytest.raises(ValueError, match='at most'):
        experiment.log_entry('designer', 'x' * (MAX_LOG_CHARS + 1))
    with pytest.raises(ValueError):
        experiment.log_entry('', 'no agent')

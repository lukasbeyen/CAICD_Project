"""Tests for sizing_tools.py (milestone 4 backend of the MCP tools): validation, simulate, warmup, train, get_status.

No ngspice: both envs of the experiment get the fake simulator of test_env.py. Run from CAD/.
"""
import math

import numpy as np
import pandas as pd
import pytest
import torch

import circuit_env
from sizing_tools import SizingExperiment
from tests.test_env import FakeEngine


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


@pytest.mark.parametrize('change', [
    {'wp1': 2.5e-07 + 1.25e-07},  # between two grid points
    {'mn1': 0},                   # below the min
    {'cap': float('nan')},
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


# ---------- the warm-up around the LLM's design ----------

def test_every_grid_value_maps_to_an_action_and_back(make_experiment):
    # to_action is the exact inverse of action_refine: a design's action is the centre of its action bin
    experiment = make_experiment()
    base = a_design(experiment)
    for name, (min_val, max_val, step) in experiment.env.dict_params.items():
        for value in np.arange(min_val, max_val, step):
            design = experiment._validate_parameters(dict(base, **{name: float(value)}))
            assert experiment.env.action_refine(experiment.to_action(design)) == design, (name, value)


def test_after_a_simulate_the_warmup_explores_around_the_best_design(make_experiment):
    experiment = make_experiment()
    best = experiment.simulate(a_design(experiment, 0.1))['parameters']  # the LLM's design, the only candidate
    designs = [experiment.env.action_refine(experiment._warmup_action()) for _ in range(200)]  # no simulations
    for name, (min_val, max_val, step) in experiment.env.dict_params.items():
        moved = np.array([abs(design[name] - best[name]) / step for design in designs])  # in grid steps
        if name.startswith('l'):  # 4 grid points: the noise sigma 0.1 practically never moves a length
            assert (moved == 0).mean() > 0.97, name
        elif name.startswith('m'):  # 24 grid points: about +-1 step
            assert moved.max() <= 5 and moved.mean() < 1.5, name
    # the centre follows the best measured design (the warm-up is a random local search): without noise, it is the best
    experiment.warmup(20)
    experiment.agent.expl_noise = 0.0
    now_best = max(experiment.candidates.values(), key=lambda candidate: candidate['reward'])['parameters']
    assert experiment.env.action_refine(experiment._warmup_action()) == now_best


def test_the_warmup_is_uniform_until_the_llm_simulates_a_design(make_experiment):
    experiment = make_experiment(seed=3)
    experiment.warmup(30)
    rows = history(experiment).query("source == 'warmup'")
    assert rows['mn1'].max() - rows['mn1'].min() > 10  # spread over the grid: the template's random warm-up


def test_train_first_pulls_the_actor_to_the_best_design(make_experiment):
    experiment = make_experiment(batch_size=8)
    experiment.simulate(a_design(experiment, 0.1))
    experiment.warmup(8)
    best = max(experiment.candidates.values(), key=lambda candidate: candidate['reward'])
    state = torch.as_tensor(experiment.replay.state[:1], dtype=torch.float32)
    target = torch.as_tensor(experiment.to_action(best['parameters']))
    distance = lambda: (experiment.agent.actor(state)[0] - target).abs().max().item()
    with torch.no_grad():
        before = distance()
    experiment._warm_start()
    with torch.no_grad():
        after = distance()
    assert after < 0.25 * before
    assert experiment.warm_started_for == tuple(best['parameters'].values())
    # the target actor is a copy of the warm-started actor
    assert all(torch.equal(a, b) for a, b in zip(experiment.agent.actor.parameters(), experiment.agent.actor_target.parameters()))
    # the same best design: no second clone, so the training's own updates are kept
    weights = [w.detach().clone() for w in experiment.agent.actor.parameters()]
    experiment._warm_start()
    assert all(torch.equal(a, b) for a, b in zip(weights, experiment.agent.actor.parameters()))


def test_without_an_llm_design_train_is_the_templates_plain_td3(make_experiment):
    experiment = make_experiment(batch_size=8)
    experiment.warmup(8)
    experiment.train(2)
    assert experiment.warm_started_for is None


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

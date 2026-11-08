"""Tests for td3_runner.py: the simulation budget, the run folder and reproducibility.

The runner's real main() runs with the fake simulator of test_env.py (no ngspice, a few seconds).
"""
import json
import os
import sys

import pytest

import circuit_env
import td3_runner
from circuit_env import CircuitEnv
from tests.test_env import FakeEngine


def default_args(monkeypatch, **changes):
    # the runner's own argparse defaults (no command-line arguments), with a few values changed for a short run
    monkeypatch.setattr(sys, 'argv', ['td3_runner.py'])
    args = td3_runner.readParser()
    for name, value in changes.items():
        setattr(args, name, value)
    return args


@pytest.fixture
def fake_envs(tmp_path, monkeypatch):
    # the runner builds CircuitEnv(run_id=...): give it an env with the fake simulator and its run folder in tmp_path;
    # the course's plot and solutions helpers write to ./output_figs and ./solutions: not during the tests
    for helper in ['plot_running_maximum', 'plotLearning', 'solutions2pareto', 'save_solutions_csv']:
        monkeypatch.setattr(circuit_env, helper, lambda *args, **kwargs: None)
    envs = []

    def make(run_id):
        env = CircuitEnv(run_id=run_id)
        env.run_folder = str(tmp_path / str(run_id))
        env.simulation_engine = FakeEngine(str(tmp_path))
        env.designs = []  # the sizes of every simulation in order (reset designs included), for the seed test
        evaluate = env.evaluate

        def evaluate_and_record(action):
            evaluate(action)
            env.designs.append(dict(env.param_values))
        env.evaluate = evaluate_and_record
        envs.append(env)
        return env
    monkeypatch.setattr(td3_runner, 'CircuitEnv', make)
    return envs


def test_training_stops_exactly_at_the_simulation_budget(monkeypatch, fake_envs):
    # warm-up: 2 episodes = 20 steps = 22 simulations (every episode starts with a reset simulation).
    # Training: episodes of 11 simulations (23-33, 34-44, 45-55), then a reset (56) and one step (57): the budget
    # stops the run in the middle of that episode. Without --max_sims it would run until --T = 10_000 steps.
    td3_runner.main(default_args(monkeypatch, max_sims=57, w=20, batch_size=16, run_id='budget'))
    env = fake_envs[0]
    assert env.counter == 57  # every simulation is counted, the reset designs included


def test_run_folder_keeps_the_yaml_hyperparameters_and_networks(monkeypatch, fake_envs):
    td3_runner.main(default_args(monkeypatch, max_sims=30, w=10, batch_size=16, run_id='folder'))
    folder = fake_envs[0].run_folder
    assert os.path.isfile(os.path.join(folder, 'TwoStage.yaml'))
    with open(os.path.join(folder, 'hyperparameters.json')) as f:
        assert json.load(f)['max_sims'] == 30
    for part in ['actor', 'actor_optimizer', 'critic', 'critic_optimizer']:  # TD3.save()
        assert os.path.isfile(os.path.join(folder, 'td3_' + part))


def test_same_seed_gives_the_same_run(monkeypatch, fake_envs):
    # same --seed: same random start designs (env.np_random), warm-up actions (action_space), network weights,
    # exploration noise and mini-batches (torch / numpy) -> exactly the same designs. Another seed: other designs.
    for run_id, seed in [('first', 123456), ('second', 123456), ('other', 7)]:
        td3_runner.main(default_args(monkeypatch, max_sims=45, w=20, batch_size=16, run_id=run_id, seed=seed))
    first, second, other = (env.designs for env in fake_envs)
    assert len(first) == 45
    assert first == second
    assert first != other

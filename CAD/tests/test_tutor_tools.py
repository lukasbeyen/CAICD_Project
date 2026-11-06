"""Tests for tutor_tools.py (milestone 4, version 3): the tutor's setup_rl (nominal, search space, warm-up) and run_rl.

No ngspice: both envs get the fake simulator of test_env.py. Run from CAD/.
"""
import numpy as np
import pandas as pd
import pytest

import circuit_env
from tests.test_env import FakeEngine
from tutor_tools import MAX_WARMUP, TutorExperiment


@pytest.fixture
def make_experiment(tmp_path, monkeypatch):
    for helper in ['plot_running_maximum', 'plotLearning', 'solutions2pareto', 'save_solutions_csv']:
        monkeypatch.setattr(circuit_env, helper, lambda *args, **kwargs: None)

    def _make(**engine_kwargs):
        experiment = TutorExperiment(seed=0, log_path=str(tmp_path / 'design_log.md'))
        for env, name in [(experiment.env, 'run'), (experiment.evaluation_env, 'run_evaluate')]:
            env.simulation_engine = FakeEngine(str(tmp_path), **engine_kwargs)
            env.run_folder = str(tmp_path / name)
        experiment.history_path = str(tmp_path / 'run' / 'harness_history.csv')
        monkeypatch.setattr(experiment, '_clean', lambda: None)
        return experiment
    return _make


def plan(experiment, k=2):
    # a nominal in the middle of the grid; 4 free parameters with +-k grid steps; a one-at-a-time warm-up
    nominal = experiment.env.action_refine(np.zeros(experiment.env.n_actions))
    space = {}
    for name in ['mn1', 'mn4', 'cap', 'res']:
        step = experiment.full_grid[name][2]
        space[name] = [nominal[name] - k * step, nominal[name] + k * step]
    warmup = [{'changes': {name: bound}, 'purpose': f'{name} at its bound'} for name, (low, high) in space.items()
              for bound in (low, high)]
    return nominal, space, warmup


def history(experiment):
    return pd.read_csv(experiment.history_path)


# ---------- setup_rl ----------

def test_setup_narrows_only_the_rl_grid(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    result = experiment.setup_rl(nominal, space, warmup)
    assert experiment.evaluation_env.dict_params == experiment.full_grid  # the evaluation env keeps the full grid
    for _ in range(50):  # every RL action gives a design inside the space
        design = experiment.env.action_refine(np.random.uniform(-1, 1, experiment.env.n_actions))
        for name, value in design.items():
            if name in space:
                assert space[name][0] - 1e-18 <= value <= space[name][1] + 1e-18, name
            else:
                assert value == pytest.approx(nominal[name]), name
    for name, (low, high) in space.items():  # the free grid, and the round trip action <-> design inside it
        step = experiment.full_grid[name][2]
        assert result['free'][name][2] == round((high - low) / step) + 1
        for value in np.arange(low, high + step / 2, step):
            design = experiment._validate_parameters(dict(nominal, **{name: float(value)}))
            assert experiment.env.action_refine(experiment.to_action(design)) == design


def test_setup_simulates_the_nominal_and_the_warmup_and_teaches_the_rl(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    result = experiment.setup_rl(nominal, space, warmup, reason='nominal')
    assert experiment.simulator_calls == 1 + len(warmup) and experiment.replay.size == 1 + len(warmup)
    assert len(result['warmup']) == len(warmup)
    for row, item in zip(result['warmup'], warmup):
        assert set(row) == {'changes', 'reward', 'met', 'delta_pct'} and set(row['changes']) == set(item['changes'])
        assert set(row['delta_pct']) == {'gain', 'ugbw', 'phm', 'slewRate', 'current', 'area'}
    rows = history(experiment)
    assert list(rows.reason[1:]) == [item['purpose'] for item in warmup]  # every warm-up design keeps its purpose


@pytest.mark.parametrize('broken', ['nominal outside', 'off grid', 'unknown', 'outside space', 'fixed parameter', 'too many'])
def test_invalid_setups_are_refused_without_simulating(make_experiment, broken):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    step = experiment.full_grid['mn1'][2]
    if broken == 'nominal outside':
        space['mn1'] = [nominal['mn1'] + step, nominal['mn1'] + 3 * step]
    elif broken == 'off grid':
        space['cap'] = [space['cap'][0] + 0.5 * experiment.full_grid['cap'][2], space['cap'][1]]
    elif broken == 'unknown':
        space['vdd'] = [1.0, 1.2]
    elif broken == 'outside space':
        warmup.append({'changes': {'mn1': space['mn1'][1] + step}, 'purpose': 'too far'})
    elif broken == 'fixed parameter':
        warmup.append({'changes': {'wp1': nominal['wp1'] + experiment.full_grid['wp1'][2]}, 'purpose': 'fixed'})
    elif broken == 'too many':
        warmup = warmup * (MAX_WARMUP // len(warmup) + 1)
    with pytest.raises(ValueError):
        experiment.setup_rl(nominal, space, warmup)
    assert experiment.simulator_calls == 0
    assert experiment.env.dict_params == experiment.full_grid  # nothing narrowed


def test_setup_runs_once_and_a_failed_nominal_restores_the_grid(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    experiment.setup_rl(nominal, space, warmup)
    with pytest.raises(ValueError, match='once'):
        experiment.setup_rl(nominal, space, warmup)
    failing = make_experiment(exit_code=1)
    with pytest.raises(RuntimeError):
        failing.setup_rl(*plan(failing))
    assert failing.env.dict_params == failing.full_grid and failing.nominal_call is None


# ---------- run_rl ----------

def test_run_rl_needs_setup_and_is_bounded(make_experiment):
    experiment = make_experiment()
    with pytest.raises(ValueError, match='setup_rl'):
        experiment.run_rl(10)
    experiment.setup_rl(*plan(experiment))
    for n in [0, 201]:
        with pytest.raises(ValueError):
            experiment.run_rl(n)


def test_run_rl_is_n_simulations_inside_the_space(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    experiment.setup_rl(nominal, space, warmup)
    calls = experiment.simulator_calls
    report = experiment.run_rl(70, reason='RL alone')  # 60 + 10 in two bursts
    assert report['simulator_calls_used'] == 70 and experiment.simulator_calls == calls + 70
    rl = history(experiment).query("source == 'rl'")
    assert len(rl) == 70
    for name in nominal:
        if name in space:
            assert rl[name].between(space[name][0] - 1e-18, space[name][1] + 1e-18).all(), name
        else:
            assert np.allclose(rl[name], nominal[name]), name
    curve = report['best_reward_at_25_50_100_pct']
    assert len(curve) == 3 and curve == sorted(curve) and curve[0] >= report['start_reward']
    assert set(report['moved_in_improvements']) <= set(space)  # only free parameters can move
    assert set(report['best_changes_vs_nominal']) <= set(space)
    # the margins of the hard specs at the best: (y - y*)/y* in %, reversed for noise (an upper bound)
    best = experiment._best()
    margins = report['best_margin_pct']
    assert set(margins) == set(experiment.env.hard_constraints)
    assert margins['ugbw'] == round(100 * (best['specs']['ugbw'] / 100e6 - 1), 1)
    assert margins['noise'] == round(100 * (1 - best['specs']['noise'] / 30e-3), 1)
    if report['best_meets_all_specs']:
        assert min(margins.values()) >= 0
    # only free parameters can sit at a range edge, and only at one of their bounds
    for name, side in report['best_at_range_edge'].items():
        assert name in space and best['parameters'][name] == pytest.approx(space[name][0 if side == 'low' else 1])


# ---------- refine: the educated improvement after the RL run ----------

def test_refine_simulates_reasoned_designs_relative_to_the_best(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    experiment.setup_rl(nominal, space, warmup)
    experiment.run_rl(20)
    best = experiment._best()
    step = experiment.full_grid['mn4'][2]
    target = best['parameters']['mn4'] + (step if best['parameters']['mn4'] < space['mn4'][1] else -step)
    size, calls = experiment.replay.size, experiment.simulator_calls
    result = experiment.refine([{'changes': {'mn4': target}, 'purpose': 'balanced current move'}], reason='educated')
    assert experiment.simulator_calls == calls + 1 and experiment.replay.size == size + 1
    assert result['refined'][0]['changes'] == {'mn4': target}
    assert history(experiment).reason.iloc[-1] == 'balanced current move'
    stored = experiment.designs[experiment.simulator_calls]['parameters']
    assert {k: v for k, v in stored.items() if k != 'mn4'} == {k: v for k, v in best['parameters'].items() if k != 'mn4'}


def test_refine_limits_and_invalid_designs(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    with pytest.raises(ValueError, match='setup_rl'):
        experiment.refine([{'changes': {'mn1': nominal['mn1']}, 'purpose': 'x'}])
    experiment.setup_rl(nominal, space, warmup)
    calls = experiment.simulator_calls
    for designs in [[], [{'changes': {'mn1': nominal['mn1']}, 'purpose': 'x'}] * 6,
                    [{'changes': {'wp1': nominal['wp1'] + experiment.full_grid['wp1'][2]}, 'purpose': 'a fixed one'}]]:
        with pytest.raises(ValueError):
            experiment.refine(designs)
    assert experiment.simulator_calls == calls


def test_refine_runs_two_rounds_the_second_from_the_new_best(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    experiment.setup_rl(nominal, space, warmup)
    experiment.run_rl(20)
    with pytest.raises(ValueError):
        experiment.refine([])                                 # a refused call is not a round
    first = experiment.refine([{'changes': {'mn1': space['mn1'][0]}, 'purpose': 'probe'}])
    assert first['rounds_left'] == 1
    best = experiment._best()                                 # the best after round 1
    assert first['best_after']['reward'] == round(best['reward'], 4)
    assert set(first['best_after']['margin_pct']) == set(experiment.env.hard_constraints)
    second = experiment.refine([{'changes': {'cap': space['cap'][1]}, 'purpose': 'combine'}])
    assert second['rounds_left'] == 0
    assert second['best_before']['reward'] == first['best_after']['reward']  # round 2 starts at the new best
    stored = experiment.designs[experiment.simulator_calls]['parameters']
    assert {k: v for k, v in stored.items() if k != 'cap'} == {k: v for k, v in best['parameters'].items() if k != 'cap'}
    calls = experiment.simulator_calls
    with pytest.raises(ValueError, match='at most 2 times'):
        experiment.refine([{'changes': {'mn1': nominal['mn1']}, 'purpose': 'x'}])
    assert experiment.simulator_calls == calls


# ---------- the budget: strictly fewer than 200 simulations ----------

def test_no_sequence_of_calls_goes_over_199_simulations(make_experiment):
    experiment = make_experiment()
    nominal, space, warmup = plan(experiment)
    experiment.setup_rl(nominal, space, warmup)       # 9 simulations
    experiment.run_rl(150)                            # 159
    with pytest.raises(ValueError, match='40 simulations left'):
        experiment.run_rl(41)
    experiment.refine([{'changes': {'mn1': nominal['mn1']}, 'purpose': 'x'}])  # 160
    experiment.run_rl(39)                             # 199
    assert experiment.simulator_calls == 199
    for call in [lambda: experiment.run_rl(1), lambda: experiment.refine([{'changes': {'mn1': nominal['mn1']}, 'purpose': 'x'}])]:
        with pytest.raises(ValueError, match='0 simulations left'):
            call()

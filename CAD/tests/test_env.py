"""Tests for circuit_env.py: action mapping, normalization, reward, failed simulations, logging, episodes.

Most tests replace the simulator by FakeEngine (no ngspice, fast); one test runs the real simulator.
Targets in TwoStage.yaml: gain 200 V/V, noise 0.03 Vrms, phm 60 deg, slewRate 30 V/us, ugbw 1e8 Hz (hard constraints),
area 2e-9 m^2, current 2e-4 A (optimization targets). Normalization: z = (y - y*) / (y + y*).
"""
import math
import os

import gymnasium as gym
import numpy as np
import pandas as pd
import pytest
from gymnasium.utils.env_checker import check_env

import circuit_env
from circuit_env import CircuitEnv

TARGETS = {'area': 2e-9, 'current': 2e-4, 'gain': 200.0, 'noise': 0.03, 'phm': 60.0, 'slewRate': 30.0, 'ugbw': 1e8}
OBS_ORDER = ['area', 'current', 'gain', 'noise', 'phm', 'slewRate', 'ugbw']  # the order of TwoStage.yaml's targets


class FakeEngine:
    """Stands in for the ngspice DUT: writes a dummy netlist, 'simulates' and returns the metrics it is given.
    Without given metrics it derives deterministic ones from the sizing (so different designs give different states)."""

    def __init__(self, folder, metrics=None, exit_code=0, timeout=False):
        self.folder, self.metrics, self.exit_code, self.timeout = folder, metrics, exit_code, timeout
        self.timed_out = False
        self.calls = []

    def create_new_netlist(self, params, process='TT', temp_pvt=None, vdd=None):
        self.calls.append(dict(params=params, process=process, temp_pvt=temp_pvt, vdd=vdd))
        self.params = params
        path = os.path.join(self.folder, f'TwoStage_fake_{len(self.calls)}.cir')
        with open(path, 'w') as f:
            f.write('* fake netlist\n')
        return path

    def simulate(self, netlist_path):
        self.timed_out = self.timeout
        return 1 if self.timeout else self.exit_code

    def measure_metrics(self):
        if self.metrics is not None:
            return dict(self.metrics) if self.metrics != 'broken' else None
        p = self.params
        return {'area': 1e-9 * p['mp1'] / 10, 'current': 1e-4 * p['mn4'] / 10, 'gain': 20.0 * p['mn1'],
                'noise': 1e-3 * p['mp3'], 'phm': 3.0 * p['mn5'], 'slewRate': 1e6 * p['cap'], 'ugbw': 1e4 * p['res'] + 1}


@pytest.fixture
def make_env(tmp_path, monkeypatch):
    # the course's plot and solutions helpers write to ./output_figs and ./solutions: not during the tests
    for helper in ['plot_running_maximum', 'plotLearning', 'solutions2pareto', 'save_solutions_csv']:
        monkeypatch.setattr(circuit_env, helper, lambda *args, **kwargs: None)

    def _make(**engine_kwargs):
        env = CircuitEnv(run_id='test')
        env.run_folder = str(tmp_path / 'run')
        env.simulation_engine = FakeEngine(str(tmp_path), **engine_kwargs)
        return env
    return _make


def designs_csv(env):
    return pd.read_csv(os.path.join(env.run_folder, 'designs.csv'))


# ---------- action mapping ----------

def test_reference_actions_give_the_reference_sizing():
    # the TAs' reference designs: every action_* row must map to exactly the param_* row (all 5 designs, 20 params)
    env = CircuitEnv(run_id='test')
    ref = pd.read_csv('references.csv').set_index('Attribute').drop(columns='Unit')
    for design in ref.columns:
        action = np.array([float(ref.loc['action_' + name, design]) for name in env.param_ranges])
        params = env.action_refine(action)
        for name, value in params.items():
            expected = ref.loc['param_' + name, design]
            if name.startswith('m'):
                assert value == int(expected) and isinstance(value, int), (design, name, value, expected)
            else:  # min + idx * step carries float noise (1.2499999999999999e-06 for 1.25e-06)
                assert value == pytest.approx(float(expected), rel=1e-12), (design, name, value, expected)


def test_action_endpoints():
    # TA mapping: idx = floor((a + 1) / 2 * (n_steps - 1)). a = -1 -> idx 0 -> min.
    # a = +1 -> idx n_steps - 1 -> max - step (e.g. m: 24, L: 180 nm, Cc: 9.9 pF); the YAML max is never reached.
    env = CircuitEnv(run_id='test')
    low = env.action_refine(-np.ones(env.n_actions))
    high = env.action_refine(np.ones(env.n_actions))
    for name, r in env.param_ranges.items():
        assert low[name] == pytest.approx(r['min'])
        assert high[name] == pytest.approx(r['max'] - r['step'])
    assert high['mp1'] == 24 and high['lp1'] == pytest.approx(180e-9) and high['cap'] == pytest.approx(9.9e-12)
    # a = 0: idx = floor(0.5 * (n_steps - 1)); m: floor(11.5) = 11 -> 12, L: floor(1.5) = 1 -> 90 nm
    middle = env.action_refine(np.zeros(env.n_actions))
    assert middle['mp1'] == 12 and middle['lp1'] == pytest.approx(90e-9)


def test_actions_land_on_the_grid_and_m_is_integer():
    env = CircuitEnv(run_id='test')
    rng = np.random.default_rng(0)
    for _ in range(500):
        params = env.action_refine(rng.uniform(-1, 1, env.n_actions))
        for name, r in env.param_ranges.items():
            n = (params[name] - r['min']) / r['step']
            assert abs(n - round(n)) < 1e-6, name
            assert r['min'] - 1e-18 <= params[name] <= r['max'] - r['step'] + 1e-18, name
            if name.startswith('m'):
                assert isinstance(params[name], int)


def test_actions_outside_the_range_are_clipped():
    # exploration noise can push the actor's tanh output past +-1
    env = CircuitEnv(run_id='test')
    assert env.action_refine(3 * np.ones(env.n_actions)) == env.action_refine(np.ones(env.n_actions))
    assert env.action_refine(-3 * np.ones(env.n_actions)) == env.action_refine(-np.ones(env.n_actions))


# ---------- normalization and reward, against hand calculations (docs/fom.md) ----------

def norm_and_reward(env, specs):
    norm = env.normalize_specs(specs)
    reward, hard_satisfied = env.reward_computation(norm)
    return norm, reward, hard_satisfied


def test_all_specs_exactly_met():
    # every metric = its target: z = (y - y) / (y + y) = 0 for all. r_H = 0 (all met), r_T = 0.
    # FoM = 0.3 + r_T = 0.3
    env = CircuitEnv(run_id='test')
    norm, reward, ok = norm_and_reward(env, TARGETS)
    assert all(z == 0.0 for z in norm.values())
    assert ok and reward == pytest.approx(0.3)


def test_gain_at_half_the_spec():
    # gain 100: z = (100 - 200) / (100 + 200) = -1/3 -> r_gain = min(-1/3, 0) = -1/3; others met, r_T = 0.
    # specs not met: FoM = r_H + 0.05 * r_T = -1/3
    env = CircuitEnv(run_id='test')
    norm, reward, ok = norm_and_reward(env, dict(TARGETS, gain=100.0))
    assert norm['gain'] == pytest.approx(-1 / 3)
    assert not ok and reward == pytest.approx(-1 / 3)


def test_noise_at_double_the_spec():
    # noise 60 mVrms (upper bound): z = (0.06 - 0.03) / (0.06 + 0.03) = 1/3 -> r_noise = -max(1/3, 0) = -1/3.
    # FoM = -1/3
    env = CircuitEnv(run_id='test')
    norm, reward, ok = norm_and_reward(env, dict(TARGETS, noise=0.06))
    assert norm['noise'] == pytest.approx(1 / 3)
    assert not ok and reward == pytest.approx(-1 / 3)


def test_specs_met_and_current_at_a_third():
    # all specs met, current = 2e-4 / 3: o = (1/3 - 1) / (1/3 + 1) = -0.5 -> r_current = +0.5; area at target -> 0.
    # all met: FoM = 0.3 + r_T = 0.3 + 0.5 = 0.8
    env = CircuitEnv(run_id='test')
    norm, reward, ok = norm_and_reward(env, dict(TARGETS, current=2e-4 / 3))
    assert norm['current'] == pytest.approx(-0.5)
    assert ok and reward == pytest.approx(0.8)


def test_beating_a_spec_earns_nothing():
    # gain 400 (twice the spec): z = 200 / 600 = +1/3, but r_gain = min(1/3, 0) = 0: FoM stays 0.3
    env = CircuitEnv(run_id='test')
    norm, reward, ok = norm_and_reward(env, dict(TARGETS, gain=400.0))
    assert norm['gain'] == pytest.approx(1 / 3)
    assert ok and reward == pytest.approx(0.3)


def test_negative_pm_and_zero_ugbw_give_minus_one():
    # PM = -55 deg (unstable amp) is clipped to 0 before normalizing: z = (0 - 60) / (0 + 60) = -1 (without the clip:
    # (-55 - 60) / (-55 + 60) = -23, and PM = -100 deg would even give +4). UGBW = 0: z = -1e8 / 1e8 = -1.
    # FoM = r_H = -1 + -1 = -2 (the other specs met, r_T = 0)
    env = CircuitEnv(run_id='test')
    norm, reward, ok = norm_and_reward(env, dict(TARGETS, phm=-55.0, ugbw=0.0))
    assert norm['phm'] == -1.0 and norm['ugbw'] == -1.0
    assert all(-1.0 <= z <= 1.0 for z in norm.values())
    assert not ok and reward == pytest.approx(-2.0)


def test_unclassified_hard_constraint_is_refused(monkeypatch):
    # a hard constraint in TwoStage.yaml that is in neither spec list would be treated inconsistently
    # (reward: as a lower bound, normalize_specs: not clipped), so the env refuses to start
    monkeypatch.setattr(CircuitEnv, 'LOWER_BOUND_SPECS', ['gain', 'phm', 'slewRate'])  # ugbw 'forgotten'
    with pytest.raises(ValueError, match="'ugbw'"):
        CircuitEnv(run_id='test')


def test_reference_designs_normalization_and_reward():
    # the TAs' own normalized values (norm_*) and rewards for their 5 reference designs, from their spec_* values
    env = CircuitEnv(run_id='test')
    ref = pd.read_csv('references.csv').set_index('Attribute').drop(columns='Unit')
    for design in ref.columns:
        specs = {name: float(ref.loc['spec_' + name, design]) for name in env.dict_targets}
        norm, reward, _ = norm_and_reward(env, specs)
        for name in env.dict_targets:
            assert norm[name] == pytest.approx(float(ref.loc['norm_' + name, design]), abs=1e-9), (design, name)
        assert reward == pytest.approx(float(ref.loc['reward', design]), abs=1e-9), design


def test_observation_order_and_dtype(make_env):
    # the observation is the normalized specs as a float32 array, in the order of TwoStage.yaml's targets
    env = make_env(metrics=dict(TARGETS, gain=100.0, current=2e-4 / 3))
    obs = env.reset(seed=0)
    assert obs.dtype == np.float32 and obs.shape == (7,)
    assert obs[OBS_ORDER.index('gain')] == pytest.approx(-1 / 3)
    assert obs[OBS_ORDER.index('current')] == pytest.approx(-0.5)


# ---------- failed simulations ----------

def test_failed_measurement_gives_the_penalty_and_worst_state(make_env):
    # measure_metrics -> None: reward = failed_penalty (-6, below the worst valid FoM of about -5.1),
    # state = worst case: -1 for gain/phm/slewRate/ugbw, +1 for noise/area/current
    env = make_env(metrics='broken')
    obs = env.reset(seed=0)
    worst = {'area': 1.0, 'current': 1.0, 'gain': -1.0, 'noise': 1.0, 'phm': -1.0, 'slewRate': -1.0, 'ugbw': -1.0}
    assert list(obs) == [worst[name] for name in OBS_ORDER]
    obs, reward, done, info = env.step(np.zeros(env.n_actions))
    assert reward == -6.0 and info['failed'] and not info['hard_satisfied']


def test_ngspice_error_is_a_failed_sim(make_env):
    env = make_env(metrics=TARGETS, exit_code=1)
    env.reset(seed=0)
    _, reward, _, info = env.step(np.zeros(env.n_actions))
    assert reward == -6.0 and info['failed'] and not info['timeout']


def test_timeout_is_a_failed_sim_and_logged(make_env):
    env = make_env(metrics=TARGETS, timeout=True)
    env.reset(seed=0)
    _, reward, _, info = env.step(np.zeros(env.n_actions))
    assert reward == -6.0 and info['failed'] and info['timeout']
    rows = designs_csv(env)
    assert rows['timeout'].all() and rows['failed'].all()


@pytest.mark.parametrize('name', ['noise', 'current', 'area'])
def test_impossible_metric_is_a_failed_sim(make_env, name):
    # noise, current (which includes Ibias) and area are > 0 for any real circuit: <= 0 means broken data
    env = make_env(metrics=dict(TARGETS, **{name: 0.0}))
    env.reset(seed=0)
    _, reward, _, info = env.step(np.zeros(env.n_actions))
    assert info['failed'] and reward == -6.0


def test_failed_penalty_is_below_every_valid_reward():
    # worst valid FoM: all 5 specs at z = -1 (r_H = -5) and area, current at o = +1 (r_T = -2): -5 + 0.05 * -2 = -5.1
    env = CircuitEnv(run_id='test')
    worst = env.normalize_specs({'area': 1e3, 'current': 1e3, 'gain': 0.0, 'noise': 1e3, 'phm': -90.0,
                                 'slewRate': 0.0, 'ugbw': 0.0})
    reward, _ = env.reward_computation(worst)
    assert reward == pytest.approx(-5.1, abs=1e-3)
    assert env.failed_penalty < reward


# ---------- simulation counter, logging, episodes ----------

def test_every_simulation_is_counted_and_logged(make_env):
    # reset() simulates a random design too: reset + 3 steps = 4 ngspice runs = 4 rows (step 0 = the reset)
    env = make_env()
    env.reset(seed=0)
    for _ in range(3):
        env.step(np.zeros(env.n_actions))
    assert env.counter == 4
    rows = designs_csv(env)
    assert list(rows['sim']) == [1, 2, 3, 4]
    assert list(rows['step']) == [0, 1, 2, 3]
    assert set(env.param_ranges) <= set(rows.columns)
    assert {'reward', 'failed', 'timeout', 'hard_satisfied', 'norm_gain', 'gain', 'temp'} <= set(rows.columns)
    assert pd.isna(rows['reward'][0]) and rows['reward'][1:].notna().all()  # the reset design gets no reward


def test_simulations_use_the_env_pvt_corner(make_env):
    env = make_env(metrics=TARGETS)
    env.reset(seed=0)
    call = env.simulation_engine.calls[-1]
    assert (call['process'], call['vdd'], call['temp_pvt']) == ('TT', 1.2, 27)


def test_feasible_design_netlist_is_kept(make_env):
    # all specs met -> the netlist is copied to runs/<run_id>/feasible_netlists/ (clean.sh deletes no_backup/)
    env = make_env(metrics=TARGETS)
    env.reset(seed=0)  # reset() doesn't reward or keep designs: only step() does
    _, _, _, info = env.step(np.zeros(env.n_actions))
    assert info['hard_satisfied']
    assert len(os.listdir(os.path.join(env.run_folder, 'feasible_netlists'))) == 1


def test_episode_ends_after_10_steps(make_env):
    env = make_env()
    env.reset(seed=0)
    dones = [env.step(np.zeros(env.n_actions))[2] for _ in range(10)]
    assert dones == [False] * 9 + [True]
    assert len(env.score_history) == 1
    assert env.score_history[0] == pytest.approx(sum(env.reward_history))  # 10 step rewards (reset isn't rewarded)


def test_plots_follow_the_course_steps(tmp_path, monkeypatch):
    # course step() docstring: 6. plot the running maximum when the goal state (all specs met) is reached,
    # 9. every 10 steps plot the learning curve. The course plot functions are replaced by ones that count calls.
    running_max_plots, learning_plots = [], []
    monkeypatch.setattr(circuit_env, 'plot_running_maximum', lambda *args: running_max_plots.append(1))
    monkeypatch.setattr(circuit_env, 'plotLearning', lambda *args: learning_plots.append(1))
    monkeypatch.setattr(circuit_env, 'save_solutions_csv', lambda *args: None)
    env = CircuitEnv(run_id='test')
    env.run_folder = str(tmp_path / 'run')
    env.simulation_engine = FakeEngine(str(tmp_path), metrics=dict(TARGETS, gain=100.0))  # gain fails: not feasible
    env.reset(seed=0)
    for _ in range(10):
        env.step(np.zeros(env.n_actions))
    assert len(running_max_plots) == 0 and len(learning_plots) == 1
    env.simulation_engine.metrics = TARGETS  # all specs met from now on
    for _ in range(3):
        env.step(np.zeros(env.n_actions))
    assert len(running_max_plots) == 3 and len(learning_plots) == 1


def test_reset_with_a_seed_is_reproducible(make_env):
    env = make_env()
    first = env.reset(seed=42)
    params = env.param_values
    assert np.array_equal(env.reset(seed=42), first) and env.param_values == params


# ---------- gymnasium's env checker ----------

class GymnasiumAPI(gym.Wrapper):
    """Test-only adapter: the course's env uses the old API (reset -> obs, step -> 4 values, as td3_runner.py expects);
    gymnasium's checker wants reset -> (obs, info) and step -> (obs, reward, terminated, truncated, info).
    done after 10 steps is a time limit, so it maps to truncated."""

    def reset(self, *, seed=None, options=None):
        return self.env.reset(seed=seed, options=options), {}

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        # info['sim'] is the global simulation counter: it keeps counting across resets on purpose (the 5000-sim
        # budget), so two runs with the same seed differ there. The checker compares info, so leave it out here.
        info = {key: value for key, value in info.items() if key != 'sim'}
        return obs, float(reward), False, done, info


def test_gymnasium_env_checker(make_env):
    check_env(GymnasiumAPI(make_env()), skip_render_check=True)


# ---------- real simulator ----------

def test_real_simulation_reset_and_step(tmp_path, monkeypatch):
    for helper in ['plot_running_maximum', 'plotLearning', 'solutions2pareto', 'save_solutions_csv']:
        monkeypatch.setattr(circuit_env, helper, lambda *args, **kwargs: None)
    env = CircuitEnv(run_id='test')
    env.run_folder = str(tmp_path / 'run')
    engine = env.simulation_engine
    engine.output_netlists_folder = engine.output_files_folder = engine.logs_folder = str(tmp_path)
    obs = env.reset(seed=0)
    obs2, reward, done, info = env.step(np.zeros(env.n_actions))
    for o in (obs, obs2):
        assert o.shape == (7,) and np.all(np.isfinite(o)) and np.all(np.abs(o) <= 1.0)
    assert math.isfinite(reward) and not done
    assert len(designs_csv(env)) == 2 and env.counter == 2

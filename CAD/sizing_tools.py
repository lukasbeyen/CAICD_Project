"""Example of Python tools for one persistent circuit-sizing experiment.

Copy this file and mcp_server.py to your CAD project root.
"""

import csv
import os
import shutil
import time
from copy import deepcopy
from datetime import datetime
from numbers import Real
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
import torch.nn.functional as F

os.environ.setdefault("MPLBACKEND", "Agg")
from circuit_env import CircuitEnv
from td3 import ReplayBuffer, TD3


SPEC_UNITS = {
    "area": "m^2", "current": "A", "gain": "V/V", "noise": "V RMS",
    "phm": "deg", "slewRate": "V/us", "ugbw": "Hz",
}
MAX_STEPS_PER_CALL = 1000
WARM_START_STEPS = 200  # added: Adam steps that pull the actor to the best design before training (no simulations)


def to_builtin(value):
    """Convert NumPy values to JSON-compatible Python values."""
    if isinstance(value, np.ndarray):
        return to_builtin(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(item) for item in value]
    return value


def compact(candidate, units=True):
    """A copy of a candidate with rounded numbers, for the tool results the LLM reads (fewer tokens per result).

    Parameters to 6 significant digits (1.4999999999999998e-06 -> 1.5e-06; the validation accepts them back), specs
    and normalized specs to 4, the reward to 4 decimals. units=False leaves out spec_units (get_status lists them once).
    The full precision stays in the candidate history and in harness_history.csv.
    """
    short = lambda value, digits: value if isinstance(value, int) else float(f"{value:.{digits}g}")
    copy = {key: value for key, value in candidate.items() if units or key != "spec_units"}
    copy["parameters"] = {name: short(value, 6) for name, value in candidate["parameters"].items()}
    copy["specs"] = {name: short(value, 4) for name, value in candidate["specs"].items()}
    copy["normalized_specs"] = {name: short(value, 4) for name, value in candidate["normalized_specs"].items()}
    copy["reward"] = round(candidate["reward"], 4)
    return copy


def check_count(value, name, maximum):
    """Reject booleans, non-integers, and out-of-range requests."""
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{name} must be an integer from 1 to {maximum}.")


class SizingExperiment:
    """One agent, replay buffer, and episode shared by successive tool calls.

    State lives in this object until the Python process exits. Use one experiment
    per process: the existing TD3 code uses NumPy/PyTorch global random generators.
    """

    def __init__(self, seed=123456, batch_size=100, replay_size=100_000):
        check_count(replay_size, "replay_size", 1_000_000)
        check_count(batch_size, "batch_size", replay_size)
        if type(seed) is not int or not 0 <= seed < 2**32:
            raise ValueError("seed must be an integer from 0 to 2**32 - 1.")
        np.random.seed(seed)
        torch.manual_seed(seed)
        self.seed = seed
        self.batch_size = batch_size
        self.run_id = "mcp_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        self.env = CircuitEnv(run_id=self.run_id, success_threshold=0.0)
        # Direct design evaluations must not change the ongoing RL episode.
        self.evaluation_env = CircuitEnv(run_id=self.run_id + "_evaluate",
                                         success_threshold=0.0)
        self.env.action_space.seed(seed)
        Path(self.env.simulation_engine.output_files_folder).mkdir(parents=True, exist_ok=True)
        Path("solutions").mkdir(exist_ok=True)

        args = SimpleNamespace(gamma=0.99, tau=0.005, noise_sigma=0.1,
                               actor_update_interval=2, pi_lr=3e-4, q_lr=3e-4,
                               hidden_size=256, cuda=False)
        self.agent = TD3(self.env.observation_space.shape[0], self.env.action_space, args)
        self.replay = ReplayBuffer(self.env.observation_space.shape[0],
                                   self.env.action_space.shape[0], max_size=replay_size)
        self.observation = None  # None means the next RL step needs a reset.
        self.warmup_steps = 0
        self.training_steps = 0
        self.updates = 0
        self.simulator_calls = 0  # Attempts, including resets and failed calls.
        self.candidates = {}  # Parameter tuple -> latest measured result.
        # added: one row per simulator call (incl. failed ones) with time, source and the agent's reason
        self.start_time = time.time()
        self.history_path = os.path.join(self.env.run_folder, "harness_history.csv")
        self.first_reset = True  # the first episode reset is seeded, like td3_runner seeds env.np_random
        self.calls_at_last_clean = 0
        self.warm_started_for = None  # added: the parameters of the best design the actor was last pulled towards

    def simulate(self, parameters: dict[str, float], reason: str = "") -> dict:
        """Evaluate one complete physical-parameter dictionary on the YAML grid.

        Return parameters, specs, normalized_specs, reward, constraint satisfaction,
        source, and spec_units. Record the candidate, without changing RL state,
        replay, or weights. Validation failures do not invoke the simulator.
        """
        params = self._validate_parameters(parameters)
        # the separate evaluation env: the RL episode, replay buffer and weights stay untouched
        specs = self.evaluation_env.simulate(params)
        self.simulator_calls += 1
        candidate = self._record_and_log(self.evaluation_env, params, specs, "simulate", reason)
        if candidate is None:
            raise RuntimeError("ngspice failed for this design (logged as failed, not recorded): try other values.")
        return compact(candidate)

    def warmup(self, n_steps: int, reason: str = "") -> dict:
        """Append exactly n_steps random transitions, without updating weights.

        Continue the current episode. Return cumulative status plus steps_completed,
        experiences_added, simulator_calls_used, and updates_performed for this call.
        n_steps must be 1..1000. Reset simulations count as calls, not transitions.
        """
        check_count(n_steps, "n_steps", MAX_STEPS_PER_CALL)
        return self._run_steps(n_steps, training=False, reason=reason)

    def train(self, n_steps: int, reason: str = "") -> dict:
        """Collect exactly n_steps policy transitions and perform TD3 updates.

        Require at least batch_size experiences before starting. Reuse the same
        agent, replay, and unfinished episode. One learning update per new
        transition; the agent controls delayed actor updates. Return the same
        status and per-call counts as warmup. n_steps must be 1..1000.
        """
        check_count(n_steps, "n_steps", MAX_STEPS_PER_CALL)
        if self.replay.size < self.batch_size:
            raise ValueError(f"train needs at least batch_size = {self.batch_size} experiences in the replay buffer, "
                             f"it has {self.replay.size}: call warmup first.")
        self._warm_start()  # added: training starts at the LLM's best design, not in the middle of the grid
        return self._run_steps(n_steps, training=True, reason=reason)

    def get_status(self, k: int = 5) -> dict:
        """Return progress and the top k distinct measured designs (k=1..20).

        Rank by reward, highest first; a high reward does not imply feasibility.
        Include reset and standalone evaluations in candidate history. This call
        performs no simulations, sampling, or learning, and returns detached data.
        """
        check_count(k, "k", 20)
        ranked = sorted(self.candidates.values(), key=lambda candidate: candidate["reward"], reverse=True)
        return to_builtin({
            "run_id": self.run_id,
            "simulator_calls": self.simulator_calls,
            "warmup_steps": self.warmup_steps,
            "training_steps": self.training_steps,
            "updates": self.updates,
            "replay_experiences": self.replay.size,
            "ready_to_train": self.replay.size >= self.batch_size,
            "episode_in_progress": self.observation is not None,
            "candidates_measured": len(self.candidates),
            "candidates_meeting_all_specs": sum(c["hard_constraints_satisfied"] for c in self.candidates.values()),
            "spec_units": SPEC_UNITS,  # once here, not in every candidate (fewer tokens)
            # compact copies: the caller can't change the history, and the numbers are rounded for the LLM
            "best_candidates": [compact(candidate, units=False) for candidate in ranked[:k]],
        })

    def _validate_parameters(self, parameters):
        """Require every YAML parameter, finite numbers, and valid grid values.

        Use the same np.arange(min, max, step) grids as phase one. Canonicalize
        floating-point roundoff only; reject off-grid values rather than clipping.
        """
        if not isinstance(parameters, dict):
            raise ValueError("parameters must be a dictionary with the 20 YAML parameter names.")
        names = list(self.env.dict_params)
        missing = [name for name in names if name not in parameters]
        unknown = [name for name in parameters if name not in self.env.dict_params]
        if missing or unknown:
            raise ValueError(f"missing parameters {missing}, unknown parameters {unknown}; expected exactly {names}.")
        valid = {}
        for name, (min_val, max_val, step) in self.env.dict_params.items():
            value = parameters[name]
            if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
                raise ValueError(f"{name} must be a finite number, got {value!r}.")
            # the grid of action_refine = np.arange(min, max, step): n_steps values, the YAML max excluded
            n_steps = round((max_val - min_val) / step)
            position = (value - min_val) / step
            idx = round(position)
            if abs(position - idx) > 1e-6 or not 0 <= idx <= n_steps - 1:
                raise ValueError(f"{name} = {value!r} is not on its grid: allowed are {min_val} + k * {step} for "
                                 f"k = 0 ... {n_steps - 1}, i.e. {min_val} ... {min_val + (n_steps - 1) * step}.")
            # the same number action_refine produces (removes float round-off; 3.0 -> 3 for a multiplicity)
            valid[name] = min_val + idx * step
        return valid

    def _record(self, env, parameters, specs, source):
        """Validate and save one candidate using the environment's scoring methods.

        Return a JSON-compatible candidate. Repeated parameters replace their
        previous measurement; failed or non-finite results must not enter history.
        """
        if specs is None or not all(np.isfinite(float(specs[name])) for name in env.dict_targets):
            raise ValueError("failed or non-finite simulation result: not recorded.")
        # scored with the env's own functions, so exactly the reward the RL agent gets
        normalized = env.normalize_specs(specs)
        reward, hard_satisfied = env.reward_computation(normalized)
        candidate = to_builtin({
            "parameters": dict(parameters),
            "specs": dict(specs),
            "normalized_specs": normalized,
            "reward": reward,
            "hard_constraints_satisfied": bool(hard_satisfied),
            "source": source,
            "spec_units": SPEC_UNITS,
        })
        self.candidates[tuple(parameters[name] for name in env.dict_params)] = candidate  # a repeat replaces
        return candidate

    def _run_steps(self, n_steps, training, reason=""):
        """Run a bounded batch, preserving episode state and reporting partial failures.

        Return get_status() plus per-call counts. Store full replay transitions;
        failed evaluations must not enter replay. Keep already completed work if
        a later step fails, and tell the caller to inspect get_status() before retrying.
        """
        calls_before, updates_before = self.simulator_calls, self.updates
        completed = added = 0
        source = "train" if training else "warmup"
        try:
            for _ in range(n_steps):
                if self.observation is None:  # start a new episode: a random design (one simulation, not a transition)
                    self.observation = self.env.reset(seed=self.seed if self.first_reset else None)
                    self.first_reset = False
                    self.simulator_calls += 1
                    self._record_and_log(self.env, self.env.param_values, self.env.real_specs, "reset", reason)
                if training:
                    action = self.agent.select_action(self.observation)  # actor + exploration noise
                else:
                    action = self._warmup_action()  # random, around the LLM's best design once it simulated one
                next_observation, reward, done, info = self.env.step(action)
                self.simulator_calls += 1
                self._record_and_log(self.env, self.env.param_values, self.env.real_specs, source, reason)
                if self.env.real_specs is not None:  # a failed simulation never enters the replay buffer
                    self.replay.push(self.observation, action, reward, next_observation, done)
                    added += 1
                    if training:  # one TD3 update per new transition (the agent delays its actor updates)
                        self.agent.update_parameters(self.replay.sample(self.batch_size), self.updates)
                        self.updates += 1
                if training:
                    self.training_steps += 1
                else:
                    self.warmup_steps += 1
                completed += 1
                self.observation = None if done else next_observation
                if self.simulator_calls - self.calls_at_last_clean >= 100:  # as td3_runner: keep no_backup/ small
                    self._clean()
        except Exception as error:
            raise RuntimeError(f"{completed} of {n_steps} steps were completed and kept before this error: {error}. "
                               "Inspect get_status() before retrying.") from error
        status = self.get_status(k=3)  # the top 3 (fewer tokens per RL batch); get_status(k) gives more
        status.update({"steps_completed": completed, "experiences_added": added,
                       "simulator_calls_used": self.simulator_calls - calls_before,
                       "updates_performed": self.updates - updates_before})
        return status

    # ---------- added: the warm-up and the training start around the LLM's design ----------

    def _warmup_action(self):
        """A random warm-up action: uniform over the grid, or, once the LLM has simulated a design, around the best
        measured design with TD3's own exploration noise (so the LLM's conclusions steer the RL's first experience)."""
        if not any(candidate["source"] == "simulate" for candidate in self.candidates.values()):
            return self.env.action_space.sample()  # the template's uniform warm-up
        best = max(self.candidates.values(), key=lambda candidate: candidate["reward"])
        noise = self.env.np_random.normal(0, self.agent.expl_noise, self.env.n_actions)
        return np.clip(self.to_action(best["parameters"]) + noise, -1, 1).astype(self.env.action_space.dtype)

    def _warm_start(self):
        """Pull the actor to the best design's action for every state in the buffer (behaviour cloning, no
        simulations), so TD3 starts where its critics learned from the warm-up. Only once the LLM has simulated a
        design (otherwise the template's plain TD3) and only when the best design changed since the last warm start.
        The target actor becomes a copy, so the critics' targets use the same policy."""
        if not any(candidate["source"] == "simulate" for candidate in self.candidates.values()):
            return
        best = max(self.candidates.values(), key=lambda candidate: candidate["reward"])
        key = tuple(best["parameters"].values())
        if key == self.warm_started_for:
            return
        states = torch.as_tensor(self.replay.state[:self.replay.size], dtype=torch.float32)
        target = torch.as_tensor(self.to_action(best["parameters"])).expand(len(states), -1)
        for _ in range(WARM_START_STEPS):
            loss = F.mse_loss(self.agent.actor(states), target)
            self.agent.actor_optimizer.zero_grad()
            loss.backward()
            self.agent.actor_optimizer.step()
        self.agent.actor_target.load_state_dict(self.agent.actor.state_dict())
        self.warm_started_for = key

    def to_action(self, params):
        """The inverse of env.action_refine: grid index k -> the centre of its action bin (k = n-1 needs a = +1)."""
        action = []
        for name, (min_val, max_val, step) in self.env.dict_params.items():
            n_steps = round((max_val - min_val) / step)
            k = round((params[name] - min_val) / step)
            action.append(min((2 * k + 1) / (n_steps - 1) - 1, 1.0))
        return np.array(action, dtype=np.float32)

    # ---------- added: logging every simulator call, keeping feasible netlists, cleaning no_backup/ ----------

    def _record_and_log(self, env, parameters, specs, source, reason):
        """Record a successful design as a candidate; log every call (failed ones too) to harness_history.csv.

        Returns the candidate, or None for a failed or non-finite simulation.
        """
        try:
            candidate = self._record(env, parameters, specs, source)
        except ValueError:
            candidate = None
        if candidate is not None and candidate["hard_constraints_satisfied"]:
            # keep the netlist (no_backup/ is cleaned) for the Solutions folder and the report
            folder = os.path.join(self.env.run_folder, "feasible_netlists")
            os.makedirs(folder, exist_ok=True)
            shutil.copy(env.netlist, folder)
        row = {"time": datetime.now().isoformat(timespec="seconds"),
               "elapsed_s": round(time.time() - self.start_time, 2),
               "call": self.simulator_calls, "source": source, "reason": reason,
               "netlist": os.path.basename(env.netlist)}
        row.update(parameters)
        for name in SPEC_UNITS:
            row[name] = to_builtin(specs[name]) if candidate else ""  # full precision
        row["reward"] = candidate["reward"] if candidate else ""
        row["hard_satisfied"] = candidate["hard_constraints_satisfied"] if candidate else ""
        row["failed"] = candidate is None
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        new_file = not os.path.isfile(self.history_path)
        with open(self.history_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row))
            if new_file:
                writer.writeheader()
            writer.writerow(row)
        return candidate

    def _clean(self):
        os.system("./clean.sh")
        self.calls_at_last_clean = self.simulator_calls

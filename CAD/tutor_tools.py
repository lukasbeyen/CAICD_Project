"""Milestone 4: the LLM as the RL's tutor (TutorExperiment extends the course template's SizingExperiment).

The LLM doesn't design step by step. It prepares the RL's job, the RL optimizes, then the LLM makes an educated
improvement and the session ends:
- setup_rl(nominal, search_space, warmup): a nominal hand design; the RL's search space (the parameters the RL may
  change, each in a small range around the nominal; all others fixed); and a small warm-up set (designs with a
  purpose each, e.g. a one-at-a-time sensitivity study). Every design becomes TD3 experience; the LLM gets back a
  compact sensitivity table;
- run_rl(n_sims): TD3 alone in that space, in short bursts that start at the current best design;
- refine(designs): after the RL run, at most 2 rounds of a few reasoned designs relative to the current best (moves
  the RL can't easily make, e.g. a coupled change that keeps the mirror balance);
- log_entry(agent, text): the shared design log, written by the server (so the agents never write files).
Strictly fewer than 200 simulations in total (MAX_TOTAL_SIMS, enforced). Only the RL env's grid is narrowed; the
TD3 agent and its hyperparameters are the template's (noise 0.1, lr 3e-4/3e-4, batch 100).
"""
import os

import numpy as np
import torch
import torch.nn.functional as F

from sizing_tools import SizingExperiment, check_count, compact

MAX_TOTAL_SIMS = 199    # the whole session: strictly fewer than 200 simulations
MAX_WARMUP = 20         # warm-up designs per setup_rl
MAX_REFINE = 5          # designs per refine
MAX_REFINE_ROUNDS = 2   # refine calls per session: probe at the best, then combine what helped
MAX_BURST = 60          # RL steps per burst; every burst first pulls the actor towards the current best design
WARM_START_STEPS = 200  # Adam steps that pull the actor towards the best design's action (no simulations)
MAX_LOG_CHARS = 1200    # per design-log entry: the log is re-read by the agents, so it must stay short
LOG_PATH = os.path.join("harness", "design_log.md")
SPECS = ("gain", "ugbw", "phm", "slewRate", "current", "area")  # the specs in the sensitivity tables


class TutorExperiment(SizingExperiment):

    def __init__(self, seed=123456, batch_size=100, replay_size=100_000, log_path=LOG_PATH):
        super().__init__(seed, batch_size, replay_size)
        self.log_path = log_path
        self.full_grid = dict(self.env.dict_params)  # the YAML grid; self.env.dict_params becomes the RL's grid
        self.designs = {}                             # simulation number -> the stored candidate (tutor and RL)
        self.nominal_call = None                      # the simulation number of the nominal design (after setup_rl)
        self.refine_rounds = 0                        # refine calls so far
        self.warm_started_for = None                  # the parameters the actor was last pulled towards
        self.log_entries = 0

    # ---------- the tutor's calls ----------

    def setup_rl(self, nominal, search_space, warmup, reason=""):
        """Set up the RL's job: the nominal design, the RL's search space, the warm-up designs (once per session)."""
        if self.nominal_call is not None:
            raise ValueError("setup_rl runs once per session.")
        nominal = self._validate_parameters(nominal)  # on the full grid
        if not isinstance(warmup, list) or len(warmup) > MAX_WARMUP:
            raise ValueError(f"warmup must be a list of at most {MAX_WARMUP} designs.")
        self._budget(1 + len(warmup))
        self.env.dict_params = self._narrow(nominal, search_space)
        try:
            self._check_designs(nominal, warmup)  # everything is checked before anything is simulated
            base = self._simulate_from(None, nominal, reason or "the tutor's nominal design")
        except (ValueError, RuntimeError):  # back to the full grid, so setup_rl can be called again
            self.env.dict_params = self.full_grid
            raise
        self.nominal_call = self.simulator_calls
        short = compact(base, units=False)
        return {
            "nominal": {"reward": short["reward"], "met": base["hard_constraints_satisfied"], "specs": short["specs"]},
            "free": self._free_ranges(search_space),
            "warmup": self._simulate_table(warmup, base),
            "simulator_calls": self.simulator_calls,
        }

    def run_rl(self, n_sims, reason=""):
        """TD3 alone in the tutor's search space: n_sims simulations in bursts that start at the current best design."""
        check_count(n_sims, "n_sims", MAX_TOTAL_SIMS)
        if self.nominal_call is None:
            raise ValueError("call setup_rl first.")
        self._budget(n_sims)
        calls_before, start = self.simulator_calls, self._best()
        try:
            for step in range(n_sims):
                if step % MAX_BURST == 0:
                    self._warm_start(self._best())
                self._rl_step(reason)
        except Exception as error:
            raise RuntimeError(f"{self.simulator_calls - calls_before} of {n_sims} RL steps were completed and kept "
                               f"before this error: {error}. Inspect get_status() before retrying.") from error
        # what happened in this call: the running best, and which parameters the improving designs moved
        new = [self.designs[call] for call in sorted(self.designs) if call > calls_before]
        best_reward, running, moved, improvements = start["reward"], [], {}, 0
        previous_best = start
        for candidate in new:
            if candidate["reward"] > best_reward:
                improvements += 1
                for name, value in candidate["parameters"].items():
                    if value != previous_best["parameters"][name]:
                        moved[name] = moved.get(name, 0) + 1
                best_reward, previous_best = candidate["reward"], candidate
            running.append(best_reward)
        best = self._best()
        nominal = self.designs[self.nominal_call]
        short = compact(best, units=False)
        return {
            "simulator_calls_used": self.simulator_calls - calls_before,
            "simulator_calls": self.simulator_calls,
            "simulations_left": MAX_TOTAL_SIMS - self.simulator_calls,
            "start_reward": round(start["reward"], 4),
            "best_reward_at_25_50_100_pct": [round(running[max(0, round(f * len(running)) - 1)], 4) for f in (0.25, 0.5, 1.0)]
                                            if running else [],
            "improvements": improvements,
            "moved_in_improvements": moved,
            "best_changes_vs_nominal": {name: short["parameters"][name] for name in short["parameters"]
                                        if best["parameters"][name] != nominal["parameters"][name]},
            "best_specs": short["specs"],
            "best_meets_all_specs": short["hard_constraints_satisfied"],
            "best_margin_pct": self._margins(best["specs"]),
            "best_at_range_edge": self._at_edge(best["parameters"]),
        }

    def refine(self, designs, reason=""):
        """After the RL run: <= 5 reasoned designs relative to the current best (they are also RL experience).
        At most 2 rounds: the second one starts from the best after the first."""
        if self.nominal_call is None:
            raise ValueError("call setup_rl first.")
        if self.refine_rounds >= MAX_REFINE_ROUNDS:
            raise ValueError(f"refine runs at most {MAX_REFINE_ROUNDS} times per session.")
        if not isinstance(designs, list) or not 1 <= len(designs) <= MAX_REFINE:
            raise ValueError(f"designs must be a list of 1 to {MAX_REFINE} designs.")
        self._budget(len(designs))
        best = self._best()  # all designs are relative to the best at the start of the call
        self._check_designs(best["parameters"], designs)
        self.refine_rounds += 1  # only a call that passed all checks counts as a round
        best_short = compact(best, units=False)
        table = self._simulate_table(designs, best)
        best_after = self._best()
        return {
            "best_before": {"reward": best_short["reward"], "specs": best_short["specs"]},
            "refined": table,
            "best_after": {"reward": round(best_after["reward"], 4), "margin_pct": self._margins(best_after["specs"])},
            "rounds_left": MAX_REFINE_ROUNDS - self.refine_rounds,
            "simulator_calls": self.simulator_calls,
        }

    def log_entry(self, agent, text):
        """Append one entry to the shared design log (the harness memory); at most MAX_LOG_CHARS characters."""
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError("agent must be the name of the agent writing the entry.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be the entry.")
        if len(text) > MAX_LOG_CHARS:
            raise ValueError(f"the entry has {len(text)} characters, at most {MAX_LOG_CHARS}: shorten it.")
        self.log_entries += 1
        folder = os.path.dirname(self.log_path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(self.log_path, "a") as f:
            if self.log_entries == 1:
                f.write(f"\n## Session {self.run_id}\n")
            f.write(f"\n### {self.log_entries}. {agent.strip()} (simulations so far: {self.simulator_calls})\n"
                    f"{text.strip()}\n")
        return {"entry": self.log_entries}

    # ---------- designs <-> RL states and actions ----------

    def to_action(self, params):
        """The inverse of env.action_refine: grid index k -> the centre of its action bin (k = n-1 needs a = +1)."""
        action = []
        for name, (min_val, max_val, step) in self.env.dict_params.items():
            n_steps = round((max_val - min_val) / step)
            k = round((params[name] - min_val) / step)
            # a fixed parameter (1 grid point in the narrowed space) maps every action to it: use 0
            action.append(0.0 if n_steps == 1 else min((2 * k + 1) / (n_steps - 1) - 1, 1.0))
        return np.array(action, dtype=np.float32)

    def state_of(self, candidate):
        """The RL state of a design: its normalized specs in the env's order (as env.reset/step return them)."""
        return np.array([candidate["normalized_specs"][name] for name in self.env.dict_targets], dtype=np.float32)

    def _best(self):
        return max(self.candidates.values(), key=lambda candidate: candidate["reward"])

    # ---------- simulations: the tutor's designs and the RL's steps ----------

    def _simulate_from(self, base, parameters, reason):
        """One tutor design (the template's simulate); it also becomes a TD3 transition from base's state."""
        super().simulate(parameters, reason)  # validation, the evaluation env, the history; RuntimeError if it failed
        params = self._validate_parameters(parameters)
        candidate = self.candidates[tuple(params[name] for name in self.env.dict_params)]
        state = self.state_of(candidate)
        start = self.state_of(base) if base is not None else state  # the nominal starts from its own state
        self.replay.push(start, self.to_action(params), candidate["reward"], state, False)
        self.designs[self.simulator_calls] = candidate
        return candidate

    def _rl_step(self, reason):
        """One TD3 step (one simulation); every episode starts at the current best design (no reset simulation)."""
        if self.observation is None:
            self.observation = self.state_of(self._best())
            self.env.episode_steps, self.env.episode_score = 0, 0.0
        action = self.agent.select_action(self.observation)  # actor + exploration noise
        next_observation, reward, done, info = self.env.step(action)
        self.simulator_calls += 1
        candidate = self._record_and_log(self.env, self.env.param_values, self.env.real_specs, "rl", reason)
        if candidate is not None:  # a failed simulation never enters the replay buffer
            self.replay.push(self.observation, action, reward, next_observation, done)
            # one TD3 update per new transition; the buffer samples with replacement, so this works from the first
            # RL step with the template's batch size, even with fewer transitions than that
            self.agent.update_parameters(self.replay.sample(self.batch_size), self.updates)
            self.updates += 1
            self.designs[self.simulator_calls] = candidate
        self.training_steps += 1
        self.observation = None if done else next_observation
        if self.simulator_calls - self.calls_at_last_clean >= 100:  # as td3_runner: keep no_backup/ small
            self._clean()

    def _warm_start(self, best):
        """Pull the actor towards the best design's action for the states in the buffer (no simulations).

        Only when the best design changed since the last warm start. Afterwards the target actor is a copy, so the
        critic's targets use the same policy. Returns whether it ran.
        """
        key = tuple(best["parameters"].values())
        if key == self.warm_started_for:
            return False
        device = next(self.agent.actor.parameters()).device
        states = torch.as_tensor(self.replay.state[:self.replay.size], dtype=torch.float32, device=device)
        target = torch.as_tensor(self.to_action(best["parameters"]), device=device).expand(len(states), -1)
        for _ in range(WARM_START_STEPS):
            loss = F.mse_loss(self.agent.actor(states), target)
            self.agent.actor_optimizer.zero_grad()
            loss.backward()
            self.agent.actor_optimizer.step()
        self.agent.actor_target.load_state_dict(self.agent.actor.state_dict())
        self.warm_started_for = key
        return True

    # ---------- helpers ----------

    def _budget(self, n):
        if self.simulator_calls + n > MAX_TOTAL_SIMS:
            raise ValueError(f"over the budget: {MAX_TOTAL_SIMS - self.simulator_calls} simulations left "
                             f"(strictly fewer than 200 in total), {n} asked.")

    def _narrow(self, center, search_space):
        """The RL's grid: a free parameter keeps its YAML grid between [low, high]; every other one is fixed at center."""
        if not isinstance(search_space, dict) or not search_space:
            raise ValueError("search_space must map at least one parameter name to [low, high].")
        unknown = [name for name in search_space if name not in self.full_grid]
        if unknown:
            raise ValueError(f"unknown parameters in search_space: {unknown}.")
        narrowed = {}
        for name, (min_val, max_val, step) in self.full_grid.items():
            if name in search_space:
                low, high = self._range(name, search_space[name], center)
                narrowed[name] = (low, high + step, step)  # the grid excludes the max, so high + step keeps high
            else:
                narrowed[name] = (center[name], center[name] + step, step)  # 1 grid point: fixed
        return narrowed

    def _range(self, name, bounds, center):
        # [low, high] on the YAML grid (checked by the template's validation), with low <= center <= high
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError(f"search_space[{name!r}] must be [low, high].")
        low, high = (self._validate_parameters(dict(center, **{name: value}))[name] for value in bounds)
        if not low <= center[name] <= high or low == high:
            raise ValueError(f"search_space[{name!r}] = [{low}, {high}] must contain {center[name]} and more than one "
                             "grid point.")
        return low, high

    def _check_designs(self, base_params, designs):
        # every design ('changes' relative to base_params) must lie on the RL's grid; nothing is simulated here
        try:
            for item in designs:
                self._validate_parameters(dict(base_params, **item["changes"]))
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError(f"every design needs 'changes' inside the search space: {error}") from error

    def _simulate_table(self, designs, base):
        # simulate each design (it becomes TD3 experience) and return its sensitivity row relative to the base design
        table = []
        for item in designs:
            try:
                candidate = self._simulate_from(base, dict(base["parameters"], **item["changes"]),
                                                str(item.get("purpose", "")))
            except RuntimeError:  # a failed simulation: logged in the history, no transition
                table.append({"changes": item["changes"], "failed": True})
                continue
            short = compact(candidate, units=False)
            table.append({
                "changes": {name: short["parameters"][name] for name in item["changes"]},
                "reward": short["reward"],
                "met": candidate["hard_constraints_satisfied"],
                "delta_pct": {spec: round(100 * (candidate["specs"][spec] - base["specs"][spec]) / base["specs"][spec], 1)
                              for spec in SPECS},
            })
        return table

    def _free_ranges(self, search_space):
        grid = self.env.dict_params
        return {name: [grid[name][0], grid[name][1] - grid[name][2], round((grid[name][1] - grid[name][0]) / grid[name][2])]
                for name in search_space}  # low, high, the number of grid points

    def _margins(self, specs):
        # the margin of each hard spec in % of its target; positive = met, a small one = the binding spec
        margins = {}
        for name in self.env.hard_constraints:
            target = self.env.dict_targets[name]
            sign = -1.0 if name in self.env.UPPER_BOUND_SPECS else 1.0  # noise must stay below its target
            margins[name] = round(100 * sign * (specs[name] - target) / target, 1)
        return margins

    def _at_edge(self, parameters):
        # free parameters at the low or high end of the RL's range: refine can't move them further that way
        edges = {}
        for name, (low, end, step) in self.env.dict_params.items():
            high = end - step
            if high - low < step / 2:
                continue  # a fixed parameter
            if parameters[name] <= low + step / 2:
                edges[name] = "low"
            elif parameters[name] >= high - step / 2:
                edges[name] = "high"
        return edges

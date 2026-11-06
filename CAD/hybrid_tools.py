"""Milestone 4, version 2: the LLM's designs warm-start the RL sizer.

HybridExperiment extends SizingExperiment (sizing_tools.py, unchanged) with three things:
- simulate(parameters | changes, base, reason): a design given in full or as changes to an earlier design; every
  successful simulation also becomes a TD3 transition in the replay buffer (the LLM's designs are RL experience);
- rl_explore(n_steps, reason): one short RL burst around the current best design: the actor is first pulled towards
  the best design (warm start), every episode starts at the best design, TD3 learns from all LLM and RL designs;
- log_entry(agent, text): the shared design log, written by the server (so the orchestrator never writes files).
The TD3 hyperparameters stay the template's (noise 0.1, lr 3e-4/3e-4, batch 100).
"""
import os

import numpy as np
import torch
import torch.nn.functional as F

from sizing_tools import SizingExperiment, check_count, compact

MAX_BURST = 60          # RL steps (= simulations) per rl_explore call: short bursts, the budget is 100-200 in total
WARM_START_STEPS = 200  # Adam steps that pull the actor towards the best design's action (no simulations)
MAX_LOG_CHARS = 1200    # per design-log entry: the log is re-read by the agents, so it must stay short
LOG_PATH = os.path.join("harness", "design_log.md")


class HybridExperiment(SizingExperiment):

    def __init__(self, seed=123456, batch_size=100, replay_size=100_000, log_path=LOG_PATH):
        super().__init__(seed, batch_size, replay_size)
        self.log_path = log_path
        self.designs = {}             # simulation number -> the stored candidate (LLM and RL designs)
        self.warm_started_for = None  # the parameters of the best design the actor was last pulled towards
        self.log_entries = 0

    # ---------- designs <-> RL states and actions ----------

    def to_action(self, params):
        """The inverse of env.action_refine: grid index k -> the centre of its action bin (k = n-1 needs a = +1)."""
        action = []
        for name, (min_val, max_val, step) in self.env.dict_params.items():
            n_steps = round((max_val - min_val) / step)
            k = round((params[name] - min_val) / step)
            action.append(min((2 * k + 1) / (n_steps - 1) - 1, 1.0))
        return np.array(action, dtype=np.float32)

    def state_of(self, candidate):
        """The RL state of a design: its normalized specs in the env's order (as env.reset/step return them)."""
        return np.array([candidate["normalized_specs"][name] for name in self.env.dict_targets], dtype=np.float32)

    def _best(self):
        return max(self.candidates.values(), key=lambda candidate: candidate["reward"])

    def _design(self, base):
        # "best" or the simulation number of an earlier successful design
        if base == "best":
            return self._best()
        if not isinstance(base, int) or base not in self.designs:
            raise ValueError(f"base must be 'best' or the number of a successful simulation, got {base!r}.")
        return self.designs[base]

    # ---------- the tools ----------

    def simulate(self, parameters=None, changes=None, base="best", reason=""):
        """One design, in full (all 20 parameters) or as changes relative to base; it also becomes RL experience."""
        if (parameters is None) == (changes is None):
            raise ValueError("give either parameters (all 20) or changes (relative to base), not both.")
        base_design = self._design(base) if self.candidates else None
        if changes is not None:
            if base_design is None:
                raise ValueError("no design yet: the first design must be given in full (parameters).")
            parameters = dict(base_design["parameters"], **changes)  # unknown names are refused by the validation
        result = super().simulate(parameters, reason)  # validation, the evaluation env, the history, a compact copy
        params = self._validate_parameters(parameters)
        candidate = self.candidates[tuple(params[name] for name in self.env.dict_params)]
        state = self.state_of(candidate)
        # the LLM's step as a TD3 transition: from the base design's state, the action that gives this design
        start = self.state_of(base_design) if base_design is not None else state
        self.replay.push(start, self.to_action(params), candidate["reward"], state, False)
        self.designs[self.simulator_calls] = candidate
        return result

    def rl_explore(self, n_steps, reason=""):
        """One short TD3 burst around the current best design; n_steps = n simulations."""
        check_count(n_steps, "n_steps", MAX_BURST)
        if not self.candidates:
            raise ValueError("rl_explore needs at least one simulated design: simulate first.")
        best_before = self._best()
        warm_started = self._warm_start(best_before)
        calls_before, completed, improved, best_reward = self.simulator_calls, 0, 0, best_before["reward"]
        try:
            for _ in range(n_steps):
                if self.observation is None:  # every episode starts at the current best design (no reset simulation)
                    self.observation = self.state_of(self._best())
                    self.env.episode_steps, self.env.episode_score = 0, 0.0
                action = self.agent.select_action(self.observation)  # actor + exploration noise
                next_observation, reward, done, info = self.env.step(action)
                self.simulator_calls += 1
                candidate = self._record_and_log(self.env, self.env.param_values, self.env.real_specs, "rl", reason)
                if candidate is not None:  # a failed simulation never enters the replay buffer
                    self.replay.push(self.observation, action, reward, next_observation, done)
                    # one TD3 update per new transition; the buffer samples with replacement, so this works from the
                    # first RL step with the template's batch size, even with fewer transitions than that
                    self.agent.update_parameters(self.replay.sample(self.batch_size), self.updates)
                    self.updates += 1
                    self.designs[self.simulator_calls] = candidate
                    if candidate["reward"] > best_reward:
                        improved, best_reward = improved + 1, candidate["reward"]
                self.training_steps += 1
                completed += 1
                self.observation = None if done else next_observation
                if self.simulator_calls - self.calls_at_last_clean >= 100:  # as td3_runner: keep no_backup/ small
                    self._clean()
        except Exception as error:
            raise RuntimeError(f"{completed} of {n_steps} RL steps were completed and kept before this error: {error}. "
                               "Inspect get_status() before retrying.") from error
        best_after = self._best()
        # by parameters, not by object: a repeated design replaces its record with a new object
        new_best = best_after["parameters"] != best_before["parameters"]
        short = compact(best_after, units=False)
        return {
            "simulator_calls_used": self.simulator_calls - calls_before,
            "simulator_calls": self.simulator_calls,
            "rl_designs_better_than_previous_best": improved,
            "warm_started": warm_started,
            "new_best": new_best,
            # what RL changed relative to the previous best: the part the designer has to explain
            "changes_vs_previous_best": {name: short["parameters"][name] for name in short["parameters"]
                                         if best_after["parameters"][name] != best_before["parameters"][name]},
            "best_reward": short["reward"],
            "best_specs": short["specs"],
            "best_meets_all_specs": short["hard_constraints_satisfied"],
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

    # ---------- the warm start ----------

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

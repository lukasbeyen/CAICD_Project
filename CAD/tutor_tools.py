"""Milestone 4, version 3: the LLM as the RL's tutor.

The LLM doesn't design step by step. It prepares the RL's job, the RL optimizes, and in between the LLM makes one
educated improvement:
- setup_rl(nominal, search_space, warmup): a nominal hand design; the RL's search space (the parameters the RL may
  change, each in a small range around the nominal; all others fixed); and a small warm-up set (designs with a
  purpose each, e.g. a one-at-a-time sensitivity study). Every design becomes TD3 experience; the LLM gets back a
  compact sensitivity table;
- run_rl(n_sims): TD3 alone in that space, in short bursts that start at the current best design (hybrid_tools.py);
- refine(designs, search_space): between two RL runs, a few reasoned designs relative to the current best (moves the
  RL can't easily make, e.g. balanced current changes), and optionally a re-centred search space around the best.
Strictly fewer than 200 simulations in total (MAX_TOTAL_SIMS, enforced). Only the RL env's grid is narrowed; the
TD3 agent and its hyperparameters are the template's.
"""
from numbers import Real

from hybrid_tools import MAX_BURST, HybridExperiment
from sizing_tools import check_count, compact
from td3 import ReplayBuffer

MAX_TOTAL_SIMS = 199  # the whole session: strictly fewer than 200 simulations
MAX_WARMUP = 20       # warm-up designs per setup_rl
MAX_REFINE = 5        # designs per refine
SPECS = ("gain", "ugbw", "phm", "slewRate", "current", "area")  # the specs in the sensitivity tables


class TutorExperiment(HybridExperiment):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.full_grid = dict(self.env.dict_params)  # the YAML grid; self.env.dict_params becomes the RL's grid
        self.nominal_call = None                      # the simulation number of the nominal design (after setup_rl)

    # ---------- the tutor's calls ----------

    def setup_rl(self, nominal, search_space, warmup, reason=""):
        """Set up the RL's job: the nominal design, the RL's search space, the warm-up designs (once per session)."""
        if self.nominal_call is not None:
            raise ValueError("setup_rl runs once per session.")
        nominal = self._validate_parameters(nominal)  # on the full grid
        if not isinstance(warmup, list) or len(warmup) > MAX_WARMUP:
            raise ValueError(f"warmup must be a list of at most {MAX_WARMUP} designs.")
        self._budget(1 + len(warmup))
        narrowed = self._narrow(nominal, search_space)
        self._check_designs(nominal, warmup, narrowed)  # everything is checked before anything is simulated
        full_grid, self.env.dict_params = self.env.dict_params, narrowed
        try:
            base = self.simulate(parameters=nominal, reason=reason or "the tutor's nominal design")
        except RuntimeError:  # the nominal failed: back to the full grid, so setup_rl can be called again
            self.env.dict_params = full_grid
            raise
        self.nominal_call = self.simulator_calls
        return {
            "nominal": {"reward": base["reward"], "met": base["hard_constraints_satisfied"], "specs": base["specs"]},
            "free": self._free_ranges(search_space),
            "warmup": self._simulate_table(warmup, self.nominal_call, base["specs"]),
            "simulator_calls": self.simulator_calls,
        }

    def refine(self, designs, search_space=None, reason=""):
        """Between two RL runs: <= 5 reasoned designs relative to the current best, optionally a re-centred space."""
        if self.nominal_call is None:
            raise ValueError("call setup_rl first.")
        if not isinstance(designs, list) or not 1 <= len(designs) <= MAX_REFINE:
            raise ValueError(f"designs must be a list of 1 to {MAX_REFINE} designs.")
        self._budget(len(designs))
        best = self._best()
        base_call = self._call_of(best)  # all designs are relative to the best at the start of the call
        grid = self._narrow(best["parameters"], search_space) if search_space else self.env.dict_params
        self._check_designs(best["parameters"], designs, grid)
        if search_space:  # a new RL grid around the best: re-encode the buffer, and warm-start again at the next burst
            self.env.dict_params = grid
            self._rebuild_buffer()
            self.warm_started_for = None
        best_short = compact(best, units=False)
        return {
            "best_before": {"reward": best_short["reward"], "specs": best_short["specs"]},
            "free": self._free_ranges(search_space) if search_space else None,
            "refined": self._simulate_table(designs, base_call, best["specs"]),
            "replay_experiences": self.replay.size,
            "simulator_calls": self.simulator_calls,
        }

    def run_rl(self, n_sims, reason=""):
        """TD3 alone in the tutor's search space: n_sims simulations in bursts that start at the current best design."""
        check_count(n_sims, "n_sims", MAX_TOTAL_SIMS)
        if self.nominal_call is None:
            raise ValueError("call setup_rl first.")
        self._budget(n_sims)
        calls_before, start = self.simulator_calls, self._best()
        done = 0
        while done < n_sims:
            n_steps = min(MAX_BURST, n_sims - done)
            self.rl_explore(n_steps, reason)
            done += n_steps
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
        }

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
                low, high = self._range(name, search_space[name], center[name])
                narrowed[name] = (low, high + step, step)  # the grid excludes the max, so high + step keeps high
            else:
                narrowed[name] = (center[name], center[name] + step, step)  # 1 grid point: fixed
        return narrowed

    def _check_designs(self, base_params, designs, grid):
        # every design ('changes' relative to base_params) must lie on the given RL grid; nothing is simulated here
        current, self.env.dict_params = self.env.dict_params, grid
        try:
            for item in designs:
                self._validate_parameters(dict(base_params, **item["changes"]))
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError(f"every design needs 'changes' inside the search space: {error}") from error
        finally:
            self.env.dict_params = current

    def _simulate_table(self, designs, base_call, base_specs):
        # simulate each design (it becomes TD3 experience) and return its sensitivity row relative to the base design
        table = []
        for item in designs:
            try:
                result = self.simulate(changes=item["changes"], base=base_call, reason=str(item.get("purpose", "")))
            except RuntimeError:  # a failed simulation: logged in the history, no transition
                table.append({"changes": item["changes"], "failed": True})
                continue
            table.append({
                "changes": {name: result["parameters"][name] for name in item["changes"]},
                "reward": result["reward"],
                "met": result["hard_constraints_satisfied"],
                "delta_pct": {spec: round(100 * (result["specs"][spec] - base_specs[spec]) / base_specs[spec], 1)
                              for spec in SPECS},
            })
        return table

    def _free_ranges(self, search_space):
        grid = self.env.dict_params
        return {name: [grid[name][0], grid[name][1] - grid[name][2], round((grid[name][1] - grid[name][0]) / grid[name][2])]
                for name in search_space}  # low, high, the number of grid points

    def _call_of(self, candidate):
        # the latest simulation number of a stored design
        return max(call for call, design in self.designs.items() if design["parameters"] == candidate["parameters"])

    def _rebuild_buffer(self):
        """After a new RL grid: keep the transitions whose design lies in it, with the action re-encoded for it."""
        old, old_designs = self.replay, self.buffer_designs
        self.replay = ReplayBuffer(old.state.shape[1], old.action.shape[1], max_size=old.max_size)
        self.buffer_designs = []
        for i in range(old.size):
            try:
                params = self._validate_parameters(old_designs[i])  # on the new grid
            except ValueError:
                continue  # outside the new space: no longer reachable, and its old action would mean another design
            self._push(old.state[i], self.to_action(params), old.reward[i, 0], old.next_state[i],
                       bool(1.0 - old.not_done[i, 0]), params)

    def _range(self, name, bounds, center_value):
        # [low, high] on the YAML grid, with low <= center <= high and more than one grid point
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError(f"search_space[{name!r}] must be [low, high].")
        low, high = (self._on_full_grid(name, value) for value in bounds)
        if not low <= center_value <= high or low == high:
            raise ValueError(f"search_space[{name!r}] = [{low}, {high}] must contain {center_value} and more than one "
                             "grid point.")
        return low, high

    def _on_full_grid(self, name, value):
        # the same grid check as _validate_parameters, for one value on the YAML grid
        min_val, max_val, step = self.full_grid[name]
        n_steps = round((max_val - min_val) / step)
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name}: {value!r} is not a number.")
        position = (value - min_val) / step
        idx = round(position)
        if abs(position - idx) > 1e-6 or not 0 <= idx <= n_steps - 1:
            raise ValueError(f"{name} = {value!r} is not on its grid ({min_val} + k * {step}, k = 0 ... {n_steps - 1}).")
        return min_val + idx * step

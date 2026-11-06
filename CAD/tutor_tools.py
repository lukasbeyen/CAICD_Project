"""Milestone 4, version 3: the LLM as the RL's tutor.

The LLM doesn't design step by step. It prepares the RL's job in one call, and the RL then optimizes on its own:
- setup_rl(nominal, search_space, warmup): a nominal hand design; the RL's search space (the parameters the RL may
  change, each in a small range around the nominal; all others fixed); and a small warm-up set (designs with a
  purpose each, e.g. a one-at-a-time sensitivity study). Every design becomes TD3 experience; the LLM gets back a
  compact sensitivity table;
- run_rl(n_sims): TD3 alone in that space, in short bursts that start at the current best design (hybrid_tools.py).
Only the RL env's grid is narrowed; the TD3 agent and its hyperparameters are the template's.
"""
from numbers import Real

from hybrid_tools import MAX_BURST, HybridExperiment
from sizing_tools import check_count, compact

MAX_WARMUP = 20   # warm-up designs per setup_rl
MAX_RL = 200      # simulations per run_rl call (the whole budget is 100-200)
SPECS = ("gain", "ugbw", "phm", "slewRate", "current", "area")  # the specs in the sensitivity table


class TutorExperiment(HybridExperiment):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.full_grid = dict(self.env.dict_params)  # the YAML grid; self.env.dict_params becomes the RL's grid
        self.nominal_call = None                      # the simulation number of the nominal design (after setup_rl)

    # ---------- the tutor's call ----------

    def setup_rl(self, nominal, search_space, warmup, reason=""):
        """Set up the RL's job: the nominal design, the RL's search space, the warm-up designs (once per session)."""
        if self.nominal_call is not None:
            raise ValueError("setup_rl runs once per session.")
        nominal = self._validate_parameters(nominal)  # on the full grid
        if not isinstance(search_space, dict) or not search_space:
            raise ValueError("search_space must map at least one parameter name to [low, high].")
        unknown = [name for name in search_space if name not in self.full_grid]
        if unknown:
            raise ValueError(f"unknown parameters in search_space: {unknown}.")
        if not isinstance(warmup, list) or len(warmup) > MAX_WARMUP:
            raise ValueError(f"warmup must be a list of at most {MAX_WARMUP} designs.")
        # the RL's grid: a free parameter keeps its grid between low and high; every other one is fixed at the nominal
        narrowed = {}
        for name, (min_val, max_val, step) in self.full_grid.items():
            if name in search_space:
                low, high = self._range(name, search_space[name], nominal[name])
                narrowed[name] = (low, high + step, step)  # the grid excludes the max, so high + step keeps high
            else:
                narrowed[name] = (nominal[name], nominal[name] + step, step)  # 1 grid point: fixed
        # check every warm-up design against the RL's grid before anything is simulated
        full_grid, self.env.dict_params = self.env.dict_params, narrowed
        try:
            for item in warmup:
                self._validate_parameters(dict(nominal, **item["changes"]))
        except (ValueError, KeyError, TypeError) as error:
            self.env.dict_params = full_grid
            raise ValueError(f"every warm-up design needs 'changes' inside the search space: {error}") from error
        # the nominal, then the warm-up designs: each one is simulated and becomes a TD3 transition (hybrid_tools)
        try:
            base = self.simulate(parameters=nominal, reason=reason or "the tutor's nominal design")
        except RuntimeError:  # the nominal failed: back to the full grid, so setup_rl can be called again
            self.env.dict_params = full_grid
            raise
        self.nominal_call = self.simulator_calls
        table = []
        for item in warmup:
            try:
                result = self.simulate(changes=item["changes"], base=self.nominal_call,
                                       reason=str(item.get("purpose", "")))
            except RuntimeError:  # a failed simulation: logged in the history, no transition
                table.append({"changes": item["changes"], "failed": True})
                continue
            table.append({
                "changes": {name: result["parameters"][name] for name in item["changes"]},
                "reward": result["reward"],
                "met": result["hard_constraints_satisfied"],
                # the sensitivity: the change of each spec in % of the nominal's value
                "delta_pct": {spec: round(100 * (result["specs"][spec] - base["specs"][spec]) / base["specs"][spec], 1)
                              for spec in SPECS},
            })
        return {
            "nominal": {"reward": base["reward"], "met": base["hard_constraints_satisfied"], "specs": base["specs"]},
            "free": {name: [narrowed[name][0], narrowed[name][1] - narrowed[name][2],
                            round((narrowed[name][1] - narrowed[name][0]) / narrowed[name][2])]
                     for name in search_space},  # low, high, the number of grid points
            "warmup": table,
            "simulator_calls": self.simulator_calls,
        }

    def _range(self, name, bounds, nominal_value):
        # [low, high] on the YAML grid, with low <= nominal <= high and more than one grid point
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError(f"search_space[{name!r}] must be [low, high].")
        low, high = (self._on_full_grid(name, value) for value in bounds)
        if not low <= nominal_value <= high or low == high:
            raise ValueError(f"search_space[{name!r}] = [{low}, {high}] must contain the nominal {nominal_value} and "
                             "more than one grid point.")
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

    # ---------- the RL on its own ----------

    def run_rl(self, n_sims, reason=""):
        """TD3 alone in the tutor's search space: n_sims simulations in bursts that start at the current best design."""
        check_count(n_sims, "n_sims", MAX_RL)
        if self.nominal_call is None:
            raise ValueError("call setup_rl first.")
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

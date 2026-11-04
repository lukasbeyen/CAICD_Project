# Work log — H05D7 CAD project (Brent & Lukas)

Status, questions for the TAs, changes to the course code, how things work, and material for the report and the exam.
(The full step-by-step logs of every commit, `docs/worklog_m1_detailed.md` and `docs/worklog_detailed_2026-11-05.md`,
and the FoM notes `docs/fom.md` are Brent's local notes and not in the repo; the FoM itself is in
`circuit_env.py` `reward_computation`.)

## Status
**Where we are:** milestone 1 on `main` (`f1ee5b1`). Milestone 2 in **PR #6** (`feat/env`, pushed, Lukas reviews, not
merged). Next: milestone 3 (TD3). Deadline: Sun 8 Nov 2026, 23:59.

**Milestone 1 — simulator interface** (PDF §1)
- ✅ 1.0 ngspice wrapper: ngspice from PATH, real exit code, log files, output folder, 20 s timeout
- ✅ 1.1 failure rules: no unity-gain crossing → UGBW = PM = 0 (valid but bad); broken output / error / timeout → failed
- ✅ 1.2 netlist writes its results (`wrdata`), `.options trtol=0.1` for the slew-rate edge
- ✅ 1.3 measurements: gain, UGBW, PM, slew rate (rising edge, VDD-limited levels), noise, current (area: course code)
- ✅ 1.4 unit tests `test_measure.py` + `test_wrapper.py`, incl. the TAs' `references.csv` (all 7 metrics within 1 %)
- ⬜ 1.R report section (material below: "For the report")

**Milestone 2 — circuit environment** (PDF §2) — PR #6
- ✅ 2.1 `action_refine` (the TAs' mapping; reproduces all reference actions → sizes)
- ✅ 2.2 `simulate` (PVT corner, counter, failed sims)
- ✅ 2.3 `normalize_specs` (with clipping), `observation`, `reward_computation` (FoM of `docs/fom.md`)
- ✅ 2.4 `reset`, `step`, logging (`designs.csv`, feasible netlists), throttled plots, `finalize()`
- ✅ 2.5 unit test file `test_env.py` (hand calculations + TA references)
- ⬜ 2.R report section

**Milestone 3 — TD3 agent** (PDF §3)
- ⬜ 3.1 `select_action` (exploration noise) · ⬜ 3.2 `update_parameters` (twin critics, target smoothing, delayed actor, soft updates)
- ⬜ 3.3 tune the 5 required hyperparameters: noise sigma, batch size, warm-up steps, actor lr, critic lr
- ⬜ 3.4 5000-sim run; plots: max FoM vs simulation, current–area Pareto front
- ⬜ 3.5 compare with the TAs' baseline agent within 5k sims · ⬜ 3.R report section
- Runner fixes needed (`td3_runner.py`): stop on `env.counter >= 5000` (simulations, not steps); `env.reset(seed=args.seed)`
  once and `env.action_space.seed(args.seed)` (warm-up uses `action_space.sample()`, not seeded by `np.random.seed`);
  call `env.finalize()` at the end; `agent.update_parameters(memory=batch, ...)` doesn't match the signature
  `update_parameters(self, memory_batch, update)`; the `"???"` defaults of the 5 hyperparameters.

**Milestone 4 — LLM agentic harness** (PDF §4, graded)
- ✅ 4.0 google-genai installed · ⬜ 4.1 Antigravity CLI · ⬜ 4.2 one LLM agent per sub-task (prompt, MCP tools, skills)
- ⬜ 4.3 MCP tools incl. the RL sizer · ⬜ 4.4 context/memory, reasoning per decision · ⬜ 4.5 best solutions, few sims
- ⬜ 4.6 runtime comparison harness vs pure RL · ⬜ 4.R report section

**Submission:** ⬜ report ≤ 10 pages · ⬜ folder `Solutions/` (capital S): Pareto netlists after 5k sims + one CSV ·
⬜ archive `[student number] [last name] G[group number].zip`. **Optional:** PVT over 12 corners; cheap analyses as MCP tools.

---

## Questions for the TAs
**Open**
1. **Action mapping maximum:** `action_refine`'s floor with (n_steps − 1) (the TAs' mapping, copied exactly) means the
   YAML maximum is never reached (L = 225 nm unreachable, 180 nm only at a = +1, W ≤ 2.5 µm, Cc ≤ 9.8 pF). Intended,
   or may we fix it?
2. **Milestone 4:** Antigravity CLI only, or may we also call Gemini through google-genai?
3. **Slew-rate levels:** do you take the 10–90 % swing from the min/max of the whole 30 µs transient? A design whose
   output kicks above VDD when the input falls (Cc feed-forward) then gets a far too low slew rate. We limit the levels
   to 10 %…90 % of VDD, which removes that.
4. **Please confirm** (both already follow from `references.csv`; then the two `TODO(TA)` comments in
   `circuit_env.py` l.65 and l.75 can go): the weight 0.05 on r_T while specs fail, and 27 °C as the simulation temperature.

**Answered by `references.csv`** (5 designs: params, actions, specs, normalized values, reward)
- Temperature: the references match at **27 °C** (at the netlist default 25 °C the gain is up to 8 % off).
- r_T weight while specs fail: **0.05** (our reward on their normalized values = their reward, all 5 designs).
- Slew-rate edge: the **rising edge** (our 10–90 % rising-edge method reproduces all 5 references exactly at 1 ns).
- Time resolution: the references were simulated with **~1 ns**; the original 50 ns testbench read up to 72 % too low.
- Noise band: our noise matches to 0.0 % → the same band (1 Hz–1 THz, the AC sweep).
- Targets: our old YAML was outdated; slew rate **30 V/µs**, UGBW **1e8 Hz** (Lukas updated `TwoStage.yaml`).
- Action mapping: theirs = `floor((a + 1)/2 · (n_steps − 1))` (now ours too).

## Open decisions / to-dos for Brent & Lukas
- **Path with a space** (e.g. OneDrive) silently loses all results: ngspice's `wrdata` cuts the file name at the space.
  Fix idea: relative paths in the netlist (`os.path.relpath`). Not done.
- **`requirements.txt`** (shared): pytest is missing; nvidia/cuda packages pull in CUDA on a fresh install.
- **UGBW when |A| < 1 at DC but peaks above 1:** `find_ugbw` returns 0 (no gain at DC). Fine for now (2 in 200 random designs).
- The observation space stays `Box(-inf, inf)` (course code, Brent's decision); the state is always in [−1, 1] and
  gymnasium's checker only warns.

---

## Changes to the course code
What we changed in files that came with the course (`CAD/` as handed out), and why. "TODO filled" = the assignment.

| file | change | why | where |
|---|---|---|---|
| `ngspice_interface/ngspice_wrapper.py` `simulate()` | ngspice from PATH instead of `/users/micas/.../ngspice` | the path only exists on the student servers | main |
| | `os.system` + `status % 256` → `subprocess.run([...]).returncode` | `os.system` returns exit code × 256, so `% 256` was always 0: ngspice errors were never detected | main (PR #2, #5) |
| | output to `no_backup/logs/<netlist>.log` (`logs_folder`) instead of `/dev/null` | failed sims can be traced; the env points it to `runs/<run_id>/logs` | main |
| | **20 s timeout** (`sim_timeout`), kills ngspice, sets `timed_out`, counts as failed | a few unstable designs make ngspice crawl (68 s default, > 10 min with trtol=0.1) | main (PR #5) |
| `ngspice_wrapper.py` `create_new_netlist()` | `os.makedirs(output_files_folder)` | `wrdata` can't create folders: on a fresh clone every sim failed | main |
| `files/input_netlists/TwoStage.cir` | the 4 `wrdata` lines + the `noise` analysis (TODO filled), column comments | the results must reach Python | main |
| | **`.options trtol=0.1`** (approved by Brent) | the slew-rate edge fell between the 50 ns steps (−72 %); now within 0.6 %, other metrics identical | main (PR #5) |
| `files/yaml_files/TwoStage.yaml` | targets slewRate 15 → **30**, ugbw 1e6 → **1e8** (Lukas) | the TAs' version; reproduces their normalized values | main |
| `ngspice_interface/dut_testbench.py` | TODOs filled: `find_dc_gain`, `find_ugbw` (Lukas's spline), `find_phm`, `find_slew_rate` | the assignment | main |
| | `parse_outputs`/`measure_metrics`: unreadable/short/NaN output → `None` | a broken sim must not crash a 5000-sim run or put NaN in the reward | main (PR #2, #4) |
| | `find_slew_rate(..., vdd=None)`: extra argument; new helper `_rising_crossing_time` | VDD limits on the levels (Cc kick) | main (PR #5) |
| `utils/___init__.py` | renamed `utils/__init__.py` | three underscores: a typo | main |
| `.gitignore` | `no_backup/`, `output_figs/`, `solutions/`, `runs/`, `__pycache__/`, `*.log`, `*.raw`, `*.pyc`; the 8 committed `.pyc` files untracked | they blocked `git pull` | main (PR #4, Lukas) |
| `circuit_env.py` | TODOs filled: `action_refine`, `simulate`, `normalize_specs`, `reset`, `step`, `reward_computation` | the assignment | PR #6 |
| | constructor: + `failed_penalty=-6.0`, `target_weight_when_failing=0.05` (defaults, course call unchanged) | penalty and weight explicit and testable | PR #6 |
| | `evaluate()` extended (reward, logging, feasible copy, plots); new `observation`, `log_design`, `save_feasible_design`, `plot`, `finalize` | every simulation logged, feasible netlists kept before `clean.sh` deletes them, plots every 100 sims | PR #6 |
| | `pvt_corner` passed to every netlist (TT, 1.2 V, 27 °C); `self.counter` = every ngspice run; `run_folder` | the references use 27 °C; the 5000-sim budget counts resets too | PR #6 |
| **not changed** | `td3/agent.py`, `td3/buffer.py`, `td3_runner.py` (milestone 3), `utils/plotting.py`, `utils/saving.py`, `clean.sh`, `area_estimation.py`, spice models, the env's observation/action spaces and its 4-value API | | |

**Added (ours):** `CAD/tests/` (`conftest.py`, `test_wrapper.py`, `test_measure.py`, `test_env.py`), `CAD/references.csv`
(the TAs' file), `CAD/analysis/sr_investigation.py`.

---

## How milestone 1 works (`main`)

### One simulation, step by step
1. `create_new_netlist()` (`ngspice_wrapper.py` l.66) copies `TwoStage.cir` with the 20 sizes and the PVT values under
   a random name `TwoStage_<time>_<letters>`. The `wrdata` file names point to
   `no_backup/output_files/<analysis>_<name>.csv`, so no two simulations share files (no stale results possible).
2. `simulate()` (l.123) runs `ngspice -b` with `subprocess.run(timeout=20 s)`. The output goes to a log file. It returns
   `info = 0` (OK) or 1 (ngspice error or timeout; `timed_out` tells which).
3. ngspice writes 4 CSVs (`TwoStage.cir`):

   | file | analysis | columns |
   |---|---|---|
   | `tran_*.csv` | `tran 50n 30u` + `.options trtol=0.1` | time, v(net6) |
   | `ac_*.csv` | `ac dec 10 1 1T` | f, Re v(net6), Im v(net6) |
   | `noise_*.csv` | `noise v(net6) Vinput dec 10 1 1T` | integrated output noise (Vrms), written twice |
   | `dc_*.csv` | `op` | v(net4), i(vdd) (negative: the supply delivers current) |

   net6 is the output. The input is 1 V differential (`ein1`/`ein2` = ±0.5·aid), so the AC v(net6) *is* the gain A(jf).
4. `measure_metrics()` (`dut_testbench.py` l.12) returns the 7 specs, or `None` = failed.

### The measurements (`dut_testbench.py`)
- **Gain** (l.80): |A| at 1 Hz in V/V (target 200 V/V ≈ 46 dB); 1 Hz is far below the dominant pole.
- **UGBW** (l.88, Lukas's): the frequency where |A| = 1. A cubic spline through log|A| vs log f, then `brentq`.
  - Max error 0.003 % vs a dense ngspice sweep (a straight line between two Bode points: 0.92 %, because it cuts the
    bend near a pole).
  - Needs ≥ 4 points. No crossing → 0.
- **Phase margin** (l.106): PM = 180° + phase of A at the UGBW, read on a log-frequency axis.
  - `np.unwrap` first: `np.angle` jumps from −180° to +180°, and without unwrap an unstable amp (phase −235°) got
    PM = +305° and *passed*.
  - No crossing → 0.
- **Slew rate** (l.124 + helper l.162): the first **rising** edge, 10 %→90 % of the output swing, with levels limited
  to 10 %…90 % of VDD, and linear crossing times. Line by line below.
- **Noise:** `onoise_total` from ngspice. **Current:** −i(vdd). **Area:** the course's estimator.
- **Failed** (`None`): missing/empty/unreadable/too-short file, NaN/inf anywhere. In the env, also an ngspice error or
  timeout (`info = 1`) and noise/current/area ≤ 0.

### The tests (`python -m pytest -q`, from the repo root or `CAD/`; `conftest.py` moves to `CAD/` first)
- **Synthetic data with an exact answer:**
  - 1-, 2- and 3-pole transfer functions: the exact UGBW and PM computed analytically. The 3-pole case has a negative
    PM and fails without `np.unwrap`.
  - No crossing → 0; too few AC points → 0.
- **Slew rate on ideal ramps:**
  - rising edge only, the falling edge ignored;
  - an output starting high / between the levels;
  - an incomplete edge → 0; an undersampled edge reads low, never high;
  - glitch above VDD → capped, kick below 0 V → floored (hand values), the cap follows VDD, inside the rails →
    unchanged;
  - degenerate swing → 0; bad input → 0; no vdd → error.
- **Broken files:** missing, empty, garbled, NaN, too short → `None`.
- **Real designs vs ngspice's own `meas`:** 4 sizings (mid-range, low Cc, high gain, negative PM) on a 100× denser
  sweep; gain, UGBW, PM within 1 %.
- **TA references (`references.csv`, 5 designs, 27 °C):**
  - area/current/gain/noise/PM/UGBW within 1 % (in fact 0.0–0.2 %);
  - slew rate within 1 % on the testbench and on a 1 ns copy.
- **Wrapper:** parameters in the netlist, output folder created, log written, ngspice error detected, timeout → failed.

---

## How milestone 2 works (`circuit_env.py`, PR #6)
- **Action** (`action_refine` l.82): the actor outputs 20 numbers in [−1, 1] (tanh), one per parameter in YAML order,
  and each is a complete, *absolute* design.
  - The action is clipped to [−1, 1] (exploration noise).
  - The TAs' mapping: n_steps = (max − min)/step, `idx = floor((a + 1)/2 · (n_steps − 1))`, `value = min + idx·step`;
    m is an `int`.
  - It reproduces all 100 action → sizing pairs of the references.
  - Chosen for comparability with the reference designs and the TAs' baseline. The price: the YAML maximum is never
    reached (TA question 1).
- **Simulate** (l.103): one ngspice run at `pvt_corner` (TT, 1.2 V, 27 °C); `self.counter += 1` for every run, resets
  included (the 5000-sim budget). `None` = failed.
- **State** (`normalize_specs` l.128, `observation` l.160):
  - `z = (y − y*)/(y + y*)`, always in [−1, 1]. Why normalize: the raw metrics span 15 orders of magnitude (area 1e-9,
    UGBW 1e8), and the network needs one scale; z is the *relative* distance to the spec.
  - Gain/PM/SR/UGBW are clipped to ≥ 0 first: a negative PM would divide by zero at −60° and give a *positive* z below it.
  - State = `[z_gain, z_noise, z_phm, z_slewRate, z_ugbw, o_area, o_current]` (float32).
- **Reward** (`reward_computation` l.318), the FoM of `docs/fom.md`:
  - `r_y = min(z, 0)` (lower-bound specs) or `−max(z, 0)` (noise): only violated specs cost, a beaten spec earns nothing.
  - `r_T = −Σ o_t` (area, current).
  - All met → `0.3 + r_T`; otherwise `r_H + 0.05·r_T`.
- **Failed sim:** reward −6.0 (below the worst valid FoM −5.1, so breaking the simulator is never a way out); state =
  worst case `[−1, +1, −1, −1, −1, +1, +1]` (finite, in range, no valid design produces it).
- **Episode:** `reset()` simulates a random design (seeded `self.np_random`) → s₀; then 10 `step()`s; `done` after 10 is a
  *time limit*, not a goal. The score = sum of the 10 step rewards (the reset design isn't the agent's choice).
- **Logging** (`evaluate` l.168): every simulation is one row in `runs/<run_id>/designs.csv`:
  - bookkeeping: sim, episode, step (0 = reset), netlist, temp;
  - the 20 params, the 7 raw metrics, the 7 `norm_*`;
  - reward, failed, **timeout**, hard_satisfied.

  Feasible designs: the netlist is copied to `runs/<run_id>/feasible_netlists/` and added to the course's solutions CSV.
- **Plots** every 100 simulations and in `finalize()` (+ Pareto plot): one plot takes ~0.25 s, as long as a whole step.
- **Tests (`test_env.py`, 24 functions / 26 cases):**
  - a fake simulator (fast) + one real-ngspice test;
  - TA reference actions → exactly the TA sizes; the TAs' norm_* and reward reproduced;
  - the fom.md hand cases (0.3, −1/3, −1/3, 0.8, a beaten spec 0, negative PM + UGBW 0 → −2);
  - mapping endpoints/grid/clipping;
  - failed sims (broken, error, timeout, impossible metrics) → −6;
  - counter/CSV incl. reset, PVT corner, feasible netlists, 10-step episode, seeded reset;
  - gymnasium's `check_env` via a test-only adapter (old 4-value → new 5-value API).

---

## For the report

### Why most random designs "rail" (systematic offset) and what it means for RL
- The testbench is open-loop (no DC feedback). The output level is set only by the current balance at the output: mp3
  sources, mn5 sinks a mirrored copy of I_bias. Unless (W/L)₆/(W/L)₄ = 2·(W/L)₇/(W/L)₅ (Allen–Holberg), one device
  wins and the output goes to a rail.
- With a gain of 1000, ~1 mV of equivalent input offset already moves the output by 1 V.
- In 40 random designs, 25 had a "gain" below 10 V/V, and none met all specs.
- For RL this means:
  - large flat plateaus (railed designs, z ≈ −1, almost no reward signal);
  - a narrow "balanced" valley where the gain jumps by orders of magnitude;
  - odd but valid numbers on the plateau (negative PM) that the reward must guard against (the clip);
  - and enough warm-up exploration is needed to find balanced designs at all.

### Slew-rate measurement (milestone 1)
**Figure:** `docs/report/figures/sr_methods.png` (reference Design 1: ground truth, 50 ns samples, linear vs spline,
the adaptive trtol points, the 10/90 % levels). The table as CSV: `docs/report/sr_methods_Design_1.csv`. Reproduce with
`cd CAD && python analysis/sr_investigation.py`.

**Method comparison, Design 1** (ground truth: fixed max step 0.1 ns; ngspice = median of 10 runs; +min = extra minutes
per 5000 sims vs the 50 ns grid):

| method | SR rise | SR fall | err rise | err fall | ngspice | +min/5000 |
|---|---|---|---|---|---|---|
| ground truth, tmax 0.1 ns | 72.69 | 20.37 | 0 | 0 | 39.3 s | +3291 |
| a. 50 ns grid (original), linear | 20.36 | 12.17 | −72.0 % | −40.2 % | 0.166 s | 0 |
| b. 50 ns grid, spline crossings | 21.99 | 13.67 | −69.8 % | −32.9 % | 0.168 s | +0.2 |
| c. fixed tmax 5 ns | 63.90 | 20.23 | −12.1 % | −0.7 % | 0.868 s | +60 |
| c. fixed tmax 1 ns | 72.44 | 20.37 | −0.34 % | −0.02 % | 4.02 s | +324 |
| d1. `trtol=1` | 70.48 | 19.93 | −3.0 % | −2.2 % | 0.165 s | −0.1 |
| d1. `trtol=0.5` | 71.17 | 20.30 | −2.1 % | −0.3 % | 0.216 s | +4.1 |
| d1. `trtol=0.2` | 72.22 | 20.28 | −0.65 % | −0.42 % | 0.216 s | +4.1 |
| **d1. `trtol=0.1` (adopted)** | **72.54** | **20.36** | **−0.20 %** | **−0.07 %** | **0.215 s** | **+4.0** |
| d1. `reltol=1e-4` | 70.87 | 20.21 | −2.5 % | −0.8 % | 0.215 s | +4.1 |
| d1. `trtol=1 reltol=1e-4` | 72.55 | 20.36 | −0.18 % | −0.07 % | 0.266 s | +8.3 |
| d2. forced breakpoints every 1 ns at the input edges | 70.49 | 20.35 | −3.0 % | −0.08 % | 1.32 s | +97 |
| d3. two-pass, 1 ns points at the located edges | 70.50 | 20.35 | −3.0 % | −0.08 % | 0.733 s | +48 |
| d4. breakpoints 1 ns + `method=gear` | 72.49 | 20.37 | −0.27 % | −0.01 % | 1.32 s | +97 |
| e. trtol=1 + spline | 71.79 | 20.24 | −1.2 % | −0.6 % | 0.165 s | −0.1 |
| e. tmax 5 ns + spline | 69.36 | 20.34 | −4.6 % | −0.17 % | 0.867 s | +59 |
| e. trtol=0.1 + `tran 50n 5.5u` (rise only) | 72.54 | – | −0.20 % | – | 0.065 s | −8.5 |

Confirmation: other references within −0.57 % (rise) / −0.45 % (fall); 40 random designs worst −0.6 %; the TA
references within 1 %.

**Why the alternatives don't work:**
- **Spline on the coarse grid:** a 13 ns edge has at most one 50 ns sample. A cubic spline through 6 samples can't
  invent the missing shape: it swings 311 mV beyond the samples and still reads −70 %.
- **Forced breakpoints** (a dummy PWL source with a corner every 1–2 ns where the input switches): the edge waveform is
  then correct, but in the *other* periods the trapezoidal integrator rings at the coarse 50 ns steps (max 1.214 V
  instead of 1.163 V). The min/max-based levels shift, and the result stays −3 % whatever the spacing.
- **Two-pass:** ngspice can't restart a transient at t > 0 from a saved state, so pass 2 is a full simulation again
  (3× the cost), with the same level problem.
- **Not possible in ngspice:** a time-dependent max step within one `tran` (one global TMAX); `.options interp` only
  resamples the output.
- **`method=gear`** (an alternative, not adopted): it damps the trapezoidal ringing and makes the breakpoint run exact,
  but trtol=0.1 removes the ringing too and is 6× cheaper.
- **Why trtol works:** ngspice chooses each step from an estimate of the local truncation error; `trtol` (default 7) is
  how much that estimate is assumed to overestimate. A smaller value is stricter: small steps only where the waveform
  bends (1109 points instead of 686; fixed 1 ns: 30 041). It only acts on the transient: the other metrics are
  identical (200 designs).

**Why the 10 % floor and 90 % cap (the Cc feed-forward kick):**
- Cc connects the first-stage output to the opamp output, so a fast input step couples straight through Cc to the
  output before the second stage reacts. This is the path that also creates the right-half-plane zero gm/Cc.
- When the input steps up, the output first dips below 0 V (−79 mV in a random design); when it steps down, it jumps
  up (to 1.47 V, above VDD).
- With 10/90 % of min…max, the dip lowers v_10 (the edge seems to start on its slow foot) and the jump raises v_90 (in
  the worst case only the jump crosses v_90: an 8 V/µs edge read 0.25 V/µs).
- Limiting the levels to 10 %…90 % of VDD keeps them on the real edge, and changes nothing for outputs inside the rails.

**Robustness (200 random designs, 20 s timeout):**

| | default (trtol 7) | trtol=0.1 |
|---|---|---|
| failed sims | 2 (timeouts) | 1 (timeout) |
| ngspice errors / "timestep too small" | 0 / 0 | 0 / 0 |
| median per sim | 0.165 s | 0.215 s |
| gain/UGBW/PM/noise/current/area | – | identical (198 designs) |

The timeouts are unstable designs (e.g. Rc = 0, output chattering above VDD for the whole transient). Their runtime is
chaotic (68 s default, > 10 min with trtol=0.1), hence the timeout.

### Line by line: `find_slew_rate` (`dut_testbench.py` l.124–171)
```python
def find_slew_rate(self, time, signal, threshold_low=0.1, threshold_high=0.9, time_unit='us', vdd=None):
```
The course's signature plus `vdd`. `time` in s, `signal` = v(net6) in V; the thresholds are the 10 %/90 % fractions.
```python
    if vdd is None:
        raise ValueError(...)
```
The only exception: a programming error (the caller forgot VDD), never a bad design. Never guess a supply voltage.
```python
    time = np.asarray(time, dtype=float);  signal = np.asarray(signal, dtype=float)
    self.slew_rate_levels = None
    if time.size < 4 or time.shape != signal.shape:
        return 0.0
```
Accept lists or arrays; clear the levels of a previous call. Too few samples or arrays of different length → 0.0 (a
failing spec, never a crash in a 5000-sim run).
```python
    v_low, v_high = np.min(signal), np.max(signal)
    v_10 = max(v_low + threshold_low * (v_high - v_low), threshold_low * vdd)
    v_90 = min(v_low + threshold_high * (v_high - v_low), threshold_high * vdd)
    self.slew_rate_levels = (v_10, v_90)
```
10/90 % of the output swing, but not below 10 % / above 90 % of VDD (the Cc kicks). The levels are kept for the tests.
```python
    if v_90 <= v_10:
        return 0.0
```
No room between the levels: a flat output, or a swing entirely above 90 % / below 10 % of VDD → nothing to measure.
```python
    t_10 = self._rising_crossing_time(time, signal, v_10)
    t_90 = None if t_10 is None else self._rising_crossing_time(time, signal, v_90, after=t_10)
    if t_90 is None:
        return 0.0
```
t_10 = the first rise through v_10; t_90 = the first rise through v_90 *after* t_10 (an output that starts between the
levels would otherwise give a 90 % crossing without a complete edge). No complete edge → 0.0: a valid sim with a
failing spec.
```python
    to_time_unit = {'s': 1.0, 'us': 1e-6}[time_unit]
    return (v_90 - v_10) / (t_90 - t_10) * to_time_unit
```
The slope between the levels actually used, V/s → V/µs (the unit of the 30 V/µs spec).
```python
def _rising_crossing_time(self, time, signal, level, after=-np.inf):
    for i in range(len(signal) - 1):
        if time[i + 1] > after and signal[i] < level <= signal[i + 1]:
            return np.interp(level, [signal[i], signal[i + 1]], [time[i], time[i + 1]])
    return None
```
The first interval (ending after `after`) where the signal goes from below `level` to at/above it. `np.interp` puts the
crossing on the straight line between the two samples, as ngspice's `meas ... when` does. None if it never rises
through the level.

### Which sizes the action mapping can reach (milestone 2)
| parameter | YAML grid | reachable for −1 ≤ a < 1 | only at a = +1 | never |
|---|---|---|---|---|
| m (all 6) | 1 … 25 | 1 … 23 | 24 | 25 |
| W (all 6) | 0.25 … 3 µm | 0.25 … 2.5 µm | 2.75 µm | 3 µm |
| L (all 6) | 45 … 225 nm | **45, 90, 135 nm** | 180 nm | **225 nm** |
| Cc | 0.1 … 10 pF | 0.1 … 9.8 pF | 9.9 pF | 10 pF |
| Rc | 0 … 9.9 kΩ | 0 … 9.7 kΩ | 9.8 kΩ | 9.9 kΩ |

a = +1 isn't rare in training: the actor's tanh saturates and the exploration noise is clipped to ±1.

**Why the missing long-L designs matter for gain:**
- The intrinsic gain is g_m·r_o, with r_o = 1/(λ·I_D) and λ ∝ 1/L, so r_o ∝ L.
- The opamp's DC gain A ≈ g_m1(r_o2 ‖ r_o4) · g_m6(r_o6 ‖ r_o7) is a product of two stages, so it scales roughly with L²
  when all lengths grow; DIBL at 45 nm makes the short devices worse still.
- With L ≤ 135 nm (180 nm only at a = +1), the high-gain corner is out of reach. The 200 V/V gain then has to come from
  g_m (W/L, m, current), which costs current and area, the two targets we optimize.
- Fair for the comparison with the TAs (same mapping), but our best designs are best *within* this restricted grid.

---

## Exam questions to prepare
- Why is `status % 256` wrong? (`os.system` returns the wait status: exit code in the high byte.)
- Why `np.unwrap` for PM? What would an unstable amp get without it?
- Why only the rising edge, and why 10–90 % instead of 0–100 %?
- Why can't a spline fix the undersampled edge, and why does `trtol` fix it?
- Why does an undersampled edge always read too *low*?
- Why the 10 %/90 % VDD limits (the Cc feed-forward kick, the RHP zero)?
- Why does a cubic spline beat log-log interpolation for the UGBW near a pole?
- Why is i(vdd) negative? Why 27 °C?
- Why does an open-loop testbench rail, and what does that do to the reward landscape?
- Why normalize the specs, and why is z bounded to [−1, 1]? Why clip PM at 0?
- Why does a beaten spec earn nothing? Why must the failed penalty be below −5.1?
- Why is the action absolute and in [−1, 1]? What does the TAs' mapping do at a = +1?
- What is in one transition (s, a, r, s', done)? Why is the reset design counted but not in the score?
- `done` after 10 steps is a time limit, not a terminal state. With absolute actions the task is close to a contextual
  bandit: s' depends only on a. So what do γ and (1 − d) in the TD3 target `r + γ(1 − d)·min Q'(s', π'(s'))` mean here?

---

## History (short)
| date | what | where |
|---|---|---|
| 3 Nov | wrapper fixes, first tests; checklist checked against the PDF | local |
| 3 Nov | `dut_testbench.py` UGBW fix at Lukas's request | PR #1 → main |
| 3 Nov | Lukas's own measurement implementation; PM/parse/wrapper bugs fixed, tests | PR #2 → main |
| 4 Nov | TA `references.csv` (Brent); reference tests; conftest (tests run from the root); broken-data checks restored after `2ceb44d`; `.pyc` untracked | PR #4 → main (PR #3 closed as superseded) |
| 4 Nov | Lukas: YAML targets SR 30 / UGBW 1e8 (`2ceb44d`), `.pyc` in `.gitignore` (`d1de3fd`) | main |
| 5 Nov | slew rate: rising edge, VDD-limited levels, `trtol=0.1`, 20 s timeout, investigation script | PR #5 → main `f1ee5b1` |
| 5 Nov | milestone 2: circuit environment + `test_env.py` | **PR #6 (open, Lukas reviews)** |

Remote branches kept (never deleted): `brent` (old, superseded), `fix/dut-testbench`, `fix/slew-rate-phm`,
`fix/measurements-sync`, `fix/m1-final`, `feat/sr-improvements` (all merged or superseded), `feat/env` (PR #6).

---

## Log
New entries go below (Goal / What changed / How it works / Decisions / Verification / For Brent to check).

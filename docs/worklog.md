# Work log — H05D7 CAD project (Brent & Lukas)

Status, questions for the TAs, changes to the course code, how things work, and material for the report and the exam.
(The full step-by-step logs of every commit, `docs/worklog_m1_detailed.md` and `docs/worklog_detailed_2026-11-05.md`,
and the FoM notes `docs/fom.md` are Brent's local notes and not in the repo; the FoM itself is in
`circuit_env.py` `reward_computation`.)

## Status
**Where we are:** milestone 1 on `main` (`efe150e` = state of PR #5). Milestone 2 on branch `feat/env` only (merged as
PR #6 and reverted again via PR #7 at Brent's request). Next: milestone 3 (TD3). Deadline: Sun 8 Nov 2026, 23:59.

**Milestone 1 — simulator interface** (PDF §1)
- ✅ 1.0 ngspice wrapper: ngspice from PATH, real exit code, log files, output folder, 20 s timeout
- ✅ 1.1 failure rules: no unity-gain crossing → UGBW = PM = 0 (valid but bad); broken output / error / timeout → failed
- ✅ 1.2 netlist writes its results (`wrdata`), `.options trtol=0.1` for the slew-rate edge
- ✅ 1.3 measurements: gain, UGBW, PM, slew rate (rising edge, VDD-limited levels), noise, current (area: course code)
- ✅ 1.4 unit tests `test_measure.py` + `test_wrapper.py`, incl. the TAs' `references.csv` (all 7 metrics within 1 %)
- ⬜ 1.R report section (material below: "For the report")

**Milestone 2 — circuit environment** (PDF §2) — on `feat/env` (not on main)
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
3. **Please confirm** the weight 0.05 on r_T while specs fail. It already follows from `references.csv`; once
   confirmed, the `TODO(TA)` comment in `circuit_env.py` l.65 can go.

**Answered by the TAs**
- **Temperature 27 °C:** the TAs said that some specs (e.g. gain and GBW) only pass at 27 °C, so it's normal that the
  references only match there. (The `TODO TA` comment in `circuit_env.py` l.75 is replaced by this note.)
- **Slew rate:** in their references the TAs took the **average slew rate over the edges**. Limiting the 10–90 %
  levels to a percentage of VDD (our 10 %…90 % of VDD limits) **is allowed**.
  - Our check on the 5 references: their value is the average over the **rising** edges.
  - The three rising edges in 30 µs are identical to within 0.3 %, so our first rising edge gives the same number
    (all within 1 %).
  - Averaging rising and falling edges together would *not* match (Design 1: 46 V/µs instead of their 72 V/µs, because
    its falling edge is only 20 V/µs).
  - So no code change is needed.

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
This section covers what we changed in the files that came with the course, and why. Filling in the TODOs is the
assignment itself. Everything else below is a fix or an addition we needed along the way.

**The simulator wrapper (`ngspice_wrapper.py`)**
- **Finding ngspice.** The course code called ngspice from a fixed path that only exists on the university servers. We
  call it from the PATH instead.
- **Detecting errors.** The course code ran ngspice with `os.system` and checked the result with `status % 256`. That
  check was always 0, because `os.system` returns the exit code multiplied by 256. So an ngspice error was never
  noticed. We now use `subprocess.run`, which gives the real exit code.
- **Log files.** ngspice's output went to `/dev/null`. It now goes to a log file per simulation, so we can see why a
  simulation failed. During a training run these logs go to the run folder.
- **Timeout.** A few unstable designs make ngspice run for minutes instead of 0.2 s. After 20 s ngspice is now stopped
  and the simulation counts as failed.
- **Output folder.** ngspice's `wrdata` can't create a missing folder, so on a fresh clone every simulation failed. The
  wrapper now creates the folder first.

**The testbench netlist (`TwoStage.cir`)**
- **Writing the results.** We filled in the TODO: four `wrdata` lines write the transient, AC, DC and noise results to
  CSV files that Python reads.
- **Step control.** We added `.options trtol=0.1`, which makes ngspice take small time steps on the fast output edges.
  With the original 50 ns steps the slew rate read up to 72 % too low; now it's within 0.6 %. The other metrics don't
  change at all.

**The specifications (`TwoStage.yaml`)**
- Lukas updated two targets to the TAs' version: slew rate 15 → 30 V/µs and UGBW 1 MHz → 100 MHz. With these, we
  reproduce the TAs' normalized values exactly.

**The measurements (`dut_testbench.py`)**
- **The four TODO functions:** gain, unity-gain frequency (Lukas's spline version), phase margin and slew rate.
- **Broken data.** A missing, empty, unreadable, too short or NaN result now marks the simulation as failed, instead of
  crashing a 5000-simulation run or putting NaN into the reward.
- **Slew rate.** `find_slew_rate` gets one extra argument, the supply voltage, plus a small helper function. It keeps
  the measurement levels between 10 % and 90 % of VDD. The TAs confirmed that this is allowed.

**Small fixes**
- `utils/___init__.py` had three underscores (a typo) and is now `utils/__init__.py`.
- Lukas extended `.gitignore` with the output folders and Python cache files, and the cache files that were committed
  by accident are removed (they blocked `git pull`).

**The environment (`circuit_env.py`), only on `feat/env`**
- We filled in the six TODO methods: action → sizing, simulate, normalize, reset, step and reward.
- The constructor gets two extra settings with default values, so the course's call still works: the penalty for a
  failed simulation (−6) and the weight of the area/current term while specs fail (0.05).
- `evaluate()` now also computes the reward, logs every simulation and keeps the netlists of designs that meet all
  specs. We added a few helper methods for this, and `finalize()` for the end of a run.
- Every simulation is run at the env's PVT corner (TT, 1.2 V, 27 °C), and `self.counter` counts every simulation,
  towards the 5000 budget.

**Deliberately unchanged**
- the TD3 files (`td3/agent.py`, `td3/buffer.py`, `td3_runner.py`, for milestone 3);
- the plotting and saving utilities, `clean.sh`, the area estimator and the spice models;
- the env's observation and action spaces and its 4-value `step()` API.

**Added by us:**
- the tests in `CAD/tests/`;
- the TAs' `CAD/references.csv`;
- the slew-rate investigation script `CAD/analysis/sr_investigation.py`.

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

## What we did for milestone 2, in plain words (branch `feat/env`)
Milestone 2 asks for the "environment": the piece between the TD3 agent and the simulator. The agent says "try this
design", and the environment turns that into transistor sizes, simulates it, and answers with a score (the reward)
and a description of how the design did (the state). The course gave the file `circuit_env.py` with empty methods. We
filled them in one at a time, with one commit per step, and then wrote a test file.

**Step 1: from the agent's numbers to transistor sizes** (`action_refine`, commits `0d64d5a`, then `67b60db`)
- The agent outputs 20 numbers between −1 and +1, one per design parameter (6 multipliers, 6 widths, 6 lengths, Cc, Rc).
- Each number has to become a value on the parameter's grid in `TwoStage.yaml`, e.g. Cc from 0.1 to 10 pF in steps of
  0.1 pF.
- First we wrote a straightforward linear mapping (−1 → minimum, +1 → maximum, rounded to the nearest grid point).
- Then we compared it with the TAs' `references.csv`, which lists for 5 designs both the agent's numbers and the
  resulting sizes. Our mapping reproduced none of the 100 pairs. We worked out the TAs' formula, which rounds down and
  stops one grid step short of the maximum, and switched to it. Now all 100 pairs match exactly.
- We chose the TAs' version so that our results compare fairly with their reference designs and their baseline agent.
- The side effect: the largest value in the YAML can never be chosen (e.g. L = 225 nm). That is an open TA question.

**Step 2: simulating one design** (`simulate`, commit `c1e7479`)
- The sizes are written into a fresh copy of the netlist and ngspice is run once.
- The environment always simulates at the same conditions: typical process, 1.2 V supply and 27 °C. We first checked
  that the temperature setting really reaches ngspice. The TAs confirmed 27 °C.
- A counter goes up for every simulation, because the assignment's budget is 5000 *simulations*.
- If anything goes wrong (an ngspice error, the 20 s timeout, broken output, or impossible values such as zero current),
  the simulation is marked as failed instead of crashing the run.

**Step 3: turning the measurements into a state and a reward** (`normalize_specs`, `reward_computation`, commit
`8846d63`)
- The 7 measured values (gain, noise, phase margin, slew rate, UGBW, area, current) differ hugely in size: area is
  around 1e-9 m², UGBW around 1e8 Hz. A neural network can't handle that well.
- So each value is replaced by its relative distance to the target, (value − target)/(value + target). That is always
  between −1 and +1, and 0 means "exactly on target". These 7 numbers are the state the agent sees.
- Specs that must be *at least* something (gain, PM, slew rate, UGBW) are first clipped at 0. A negative phase margin
  would otherwise break the formula.
- The reward is the course's figure of merit:
  - **While specs fail:** only the failing specs cost points (beating a spec earns nothing), plus a small push (×0.05)
    towards less area and current.
  - **Once all specs pass:** a bonus of 0.3, plus the full area/current term.
- **A failed simulation** gets −6, worse than any real design can score. That way the agent never learns that breaking
  the simulator is a way out.

**Step 4: episodes, logging and plots** (`reset`, `step`, commit `85587d5`, then `084907d`)
- **An episode:** `reset()` simulates one random design as a starting point, then the agent gets 10 tries (`step()`).
- **The log:** every simulation, the random reset designs included, is written as one row in
  `runs/<run_id>/designs.csv`. The row holds all 20 sizes, all 7 measurements, the normalized values, the reward, and
  whether the simulation failed or timed out.
- **Designs that meet all specs:** their netlist is copied to the run folder, because `clean.sh` regularly wipes the
  scratch folder and the final submission needs these netlists.
- **The course's plots:** they were redrawn after every step. One plot takes as long as a whole simulation, so we now
  redraw them every 100 simulations and once at the end (`finalize()`, which also draws the Pareto plot).
- **The timeout:** after the slew-rate work added the 20 s timeout, the log got its own "timeout" column, and the two
  old slew-rate columns (rising/falling edge) were dropped.

**Step 5: the test file** (`tests/test_env.py`, commit `9ca85e0`)
26 tests that check the environment against numbers we know independently:
- The TAs' reference actions give exactly the TAs' sizes, and their measurements give exactly their normalized values
  and reward.
- Hand-calculated examples from the FoM definition, e.g. a gain of 100 instead of 200 gives a reward of exactly −1/3.
- Failed simulations always get −6 and the worst-case state, whatever the cause.
- The bookkeeping: the counter, the CSV rows, the 10-step episode, the kept netlists and reproducible random starts.
- gymnasium's own environment checker passes.
- Most tests use a fake simulator and run in about 1.5 s. One test runs the real ngspice.

**What happened with the PR**
- Milestone 2 went to Lukas for review as PR #6.
- Brent merged it and then reverted it again (PR #7), so `main` doesn't have milestone 2 yet.
- It's complete on `feat/env`, and all 81 tests pass there.

**What we deliberately did not change**
- The observation space stays as the course defined it.
- `step()` keeps the course's 4-value return, because `td3_runner.py` and the TAs' baseline expect that.

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
| 5 Nov | milestone 2: circuit environment + `test_env.py` | PR #6, merged and reverted again (PR #7); lives on `feat/env` |

Remote branches kept (never deleted): `brent` (old, superseded), `fix/dut-testbench`, `fix/slew-rate-phm`,
`fix/measurements-sync`, `fix/m1-final`, `feat/sr-improvements` (all merged or superseded), `feat/env` (PR #6).

---

## Log
New entries go below (Goal / What changed / How it works / Decisions / Verification / For Brent to check).

### 2026-11-05 — PR #6 merge reverted on main (PR #7 merged)
- Brent merged PR #6 himself (merge commit `2b0e278`) and then asked to revert it, so that milestone 2 is no longer on main.
- Branch `revert/pr-6`: `git revert -m 1 2b0e278` → `83382ed`. **PR #7 merged** (Brent's explicit request) →
  **main = `efe150e`**, identical to `f1ee5b1` (PR #5): `circuit_env.py` is the course version again; `test_env.py`,
  `docs/worklog.md` and the report figure are not in the repo. pytest on main: 55 passed.
- Both the revert and the pull of main deleted `docs/worklog.md` and `docs/report/` from disk (PR #6 had tracked them).
  Restored from `cc96732` as local, git-ignored files.
- Milestone 2 stays on `feat/env` (`cc96732`, pushed). **To bring it back later: revert the revert**
  (`git revert efe150e` / `83382ed`). A plain merge of `feat/env` won't re-apply its commits, because git considers
  them already merged.

### 2026-11-04 — TA answers (temperature, slew rate); work log rewritten in plain text
- **Goal:** record two TA answers and make the course-code changes and milestone 2 readable without the code.
- **TA answers:**
  - 27 °C is normal: some specs (gain, GBW) only pass at 27 °C.
  - Slew rate: the TAs averaged it over the edges, and limiting the 10–90 % levels to a percentage of VDD is allowed.
- **Check (scratch script, not committed):** the 5 references simulated with the testbench. Per design, the three rising
  edges are identical within 0.3 %, and their average = our first rising edge = the TA value within 1 %. Averaging
  rising and falling edges together doesn't match (Design 1: 46.4 V/µs vs TA 72.1 V/µs). So the TAs' "all edges" means
  all rising edges, and no code change is needed.
- **What changed:** TA questions 3 (slew-rate levels) and the 27 °C half of question 4 moved to "Answered by the TAs".
  "Changes to the course code" is now plain text instead of a table. There is a new section, "What we did for
  milestone 2, in plain words". `docs/worklog.md` only; no code changed.
- **Also:** the `TODO TA: 25 or 27 degC?` comment in `circuit_env.py` l.75 is replaced by a note that the TAs confirmed
  27 °C (Brent's OK; comment only, no behaviour change). pytest: 81 passed. Committed on `feat/env`, not pushed.


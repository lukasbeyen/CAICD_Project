# Work log — H05D7 CAD project (Brent & Lukas)

Status, questions for the TAs, changes to the course code, how things work, and material for the report and the exam.
(The full step-by-step logs of every commit, `docs/worklog_m1_detailed.md` and `docs/worklog_detailed_2026-11-05.md`,
and the FoM notes `docs/fom.md` are Brent's local notes and not in the repo; the FoM itself is in
`circuit_env.py` `reward_computation`.)

## Status
**Where we are:** milestones 1 and 2 on `main` (PR #8). Milestone 3 on branch `feat/td3` (not pushed): agent,
runner fixes and tests done, tuning in progress (stage B running). Deadline: Sun 8 Nov 2026, 23:59.

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
- ✅ 2.3 `normalize_specs` (with clipping), `reward_computation` (FoM of `docs/fom.md`)
- ✅ 2.4 `reset`, `step`, logging (`designs.csv`, feasible netlists), plots as in the course docstring, `finalize()`
- ✅ 2.6 rebuilt on Lukas's simpler structure (numbered course steps), his bugs fixed — branch `feat/td3`
- ✅ 2.5 unit test file `test_env.py` (hand calculations + TA references)
- ⬜ 2.R report section

**Milestone 3 — TD3 agent** (PDF §3) — guide with explanations, open decisions and step plan: `docs/milestone3_guide.md`
- ✅ 3.1 `select_action` (exploration noise) · ✅ 3.2 `update_parameters` (twin critics, target smoothing, delayed actor,
  soft updates) + `tests/test_agent.py` — branch `feat/td3`
- ✅ 3.3 runner fixes (stop at 5000 sims, seeding, `finalize()`, yaml/hyperparameter copy, start values) + `tests/test_runner.py`
- ✅ 3.4 5000-sim run with the start values (`runs/start_values_s123456`); plots: max FoM vs simulation, current–area Pareto front
- 🔄 3.5 tune the 5 required hyperparameters (noise sigma, batch size, warm-up steps, actor lr, critic lr):
  ✅ stage A (one at a time, 9 runs) · 🔄 stage B (3 seeds, 4 settings) · ⬜ Brent picks the final values
- ⬜ 3.6 final run + plots + `Solutions/` · ⬜ compare with the TAs' baseline agent within 5k sims · ⬜ 3.R report section
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
1. **Simulation budget:** is 5k simulations a hard cap per run, or only the point where results are compared (PDF:
   "compare … within 5k simulations", "Pareto solutions (after 5k simulations)")? Our runner stops at 5000
   (`--max_sims`); Lukas's and the SAC runner go to ~11 000.
2. **Solutions folder:** the Pareto front of one run (we use our best seed, `B_pilr_w_s123456`), or of all our runs
   together?
3. **Baseline comparison:** is one SAC run enough, or do you expect several seeds (we compare TD3 over 3 seeds)?
4. **Negative phase margin** (low impact): a PM ≤ 0 gives z = −1 in our normalization (2 in 150 random designs). The
   references all have PM > 0 (44–103°), so they can't tell. Do you do the same?
5. **Please confirm** the weight 0.05 on r_T while specs fail (low impact: it already follows from `references.csv`;
   once confirmed, the `TODO(TA)` comment in `circuit_env.py` can go).

**Answered by the milestone 4 template / slides (lab sessions 3–4)**
- **Action mapping maximum** (was question 1): `sizing_tools.py` says "use the same `np.arange(min, max, step)` grids as
  phase one". The grid leaves out the YAML max on purpose, so `floor((a+1)/2·(n_steps−1))` is their convention.
- **Milestone 4 tool** (was question 2): Antigravity CLI with MCP tools and skills (slides 3–16); the slides allow
  "more/better tools" than the 4 examples.

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
- The constructor keeps the course's signature. Two settings are plain attributes in `__init__`: the penalty for a
  failed simulation (−6) and the weight of the area/current term while specs fail (0.05).
- `evaluate()` is the course's 3 lines. `step()` computes the reward (−6 for a failed sim), keeps the netlists of
  designs that meet all specs and logs the design (`log_design()`). `reset()` only logs its random design, without a
  reward. `finalize()` draws the Pareto plot at the end of a run.
- `reset()` and `step()` follow the course docstrings step by step (numbered comments, Lukas's style), including the
  plots: the max-FoM plot on every step that meets all specs, the learning curve every 10 steps.
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
- **The course's plots:** first we redrew them every 100 simulations (one plot costs as much as a simulation). In the
  rebuild on Lukas's structure (below) we went back to exactly what the course docstring says, for simplicity.
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
- **Action** (`action_refine` l.84): the actor outputs 20 numbers in [−1, 1] (tanh), one per parameter in YAML order,
  and each is a complete, *absolute* design.
  - The action is clipped to [−1, 1] (exploration noise).
  - The TAs' mapping: n_steps = (max − min)/step, `idx = floor((a + 1)/2 · (n_steps − 1))`, `value = min + idx·step`;
    m stays an `int` (the YAML m values are ints).
  - It reproduces all 100 action → sizing pairs of the references.
  - Chosen for comparability with the reference designs and the TAs' baseline. The price: the YAML maximum is never
    reached (TA question 1).
- **Simulate** (l.100): one ngspice run at `pvt_corner` (TT, 1.2 V, 27 °C); `self.counter += 1` for every run, resets
  included (the 5000-sim budget). `None` = failed.
- **State** (`normalize_specs` l.125):
  - `z = (y − y*)/(y + y*)`, always in [−1, 1]. Why normalize: the raw metrics span 15 orders of magnitude (area 1e-9,
    UGBW 1e8), and the network needs one scale; z is the *relative* distance to the spec.
  - Gain/PM/SR/UGBW are clipped to ≥ 0 first: a negative PM would divide by zero at −60° and give a *positive* z below it.
  - State = the 7 normalized values in the YAML `targets` order:
    `[o_area, o_current, z_gain, z_noise, z_phm, z_slewRate, z_ugbw]` (float32).
- **Reward** (`reward_computation` l.307), the FoM of `docs/fom.md`:
  - `r_y = min(z, 0)` (lower-bound specs) or `−max(z, 0)` (noise): only violated specs cost, a beaten spec earns nothing.
  - `r_T = −Σ o_t` (area, current).
  - All met → `0.3 + r_T`; otherwise `r_H + 0.05·r_T`.
- **Failed sim:** reward −6.0 (below the worst valid FoM −5.1, so breaking the simulator is never a way out); state =
  worst case `[+1, +1, −1, +1, −1, −1, −1]` (area, current, gain, noise, PM, SR, UGBW; finite, in range, no valid
  design produces it).
- **Episode:** `reset()` simulates a random design (seeded `self.np_random`) → s₀; then 10 `step()`s; `done` after 10 is a
  *time limit*, not a goal. The reset design is simulated (counted) and logged, but **not rewarded** (template
  behaviour, Brent's choice). The score = sum of the 10 step rewards.
- **Logging** (`log_design` l.166, called from `reset` and `step`): every simulation is one row in `runs/<run_id>/designs.csv`:
  - bookkeeping: sim, episode, step (0 = reset), netlist, temp;
  - the 20 params, the 7 raw metrics, the 7 `norm_*`;
  - reward, failed, **timeout**, hard_satisfied.

  Feasible designs: the netlist is copied to `runs/<run_id>/feasible_netlists/` and added to the course's solutions CSV.
- **Plots** as in the course `step` docstring: the max-FoM plot on every step that meets all specs (step 6), the
  learning curve every 10 steps (step 9); `finalize()` draws the Pareto plot. One plot takes ~0.25 s, about as long as
  a simulation (~2 min per run for the learning curve, more once the agent finds feasible designs often).
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

### 2026-11-04 — 3.0: milestone 3 guide (no code)
- **Goal:** Brent can follow milestone 3 closely: what is asked, what TD3 does in circuit terms, what we must write,
  what's wrong in the course runner, the hyperparameters, and the step plan.
- **What changed:** new `docs/milestone3_guide.md` (local, not committed).
- **Content:**
  - the PDF requirements;
  - the RL ↔ circuit table;
  - the three TD3 tricks with the equations (paper §4.2, §5.2, §5.3);
  - the given Actor/Critic/buffer;
  - runner problems R1–R9: `"???"` defaults; the `memory=` keyword → `TypeError`; misleading but harmless batch
    names; stop on 10 000 steps instead of 5000 sims; seeding that misses the env and action space; no `finalize()`;
    no yaml/hyperparameter copy;
  - the start values and tuning plan;
  - the tests;
  - exam questions.
- **Measured:** one TD3 update on this VM costs 3.7 ms (batch 64) / 7.0 ms (batch 256), against ~0.2 s per sim, so
  a 5000-sim run is ~21–25 min. The VM has 2 cores → at most 2 runs in parallel.
- **For Brent (decisions D1–D4 in the guide §6):**
  - D1: stop on `env.counter >= 5000`;
  - D2: keep the course's `done` at the 10-step time limit;
  - D3: branch `feat/td3` from `feat/env`;
  - D4: minimal runner fixes R1–R7.

### 2026-11-04 — 3.0–3.2: branch `feat/td3`, `select_action`, `update_parameters`, `test_agent.py`
- **Brent's decisions on the guide §6:**
  - D1: stop at 5000 sims, marked clearly in the code so it can be reverted;
  - D2: keep the course's `done` at the 10-step time limit;
  - D3: branch `feat/td3` from `feat/env`;
  - D4: minimal runner fixes. The `memory=` keyword (R2) Brent fixed himself; the misleading batch names (R3) stay as
    they are.
- **What changed:**
  - branch `feat/td3` from `feat/env` (`73ac392`, local);
  - `00a4ac3`: Brent's runner fix, `update_parameters(memory_batch=batch, ...)`;
  - `td3/agent.py`: `select_action` (l.87–118), `update_parameters` (l.120–194);
  - new `tests/test_agent.py` (11 tests).
- **How `select_action` works (l.107–118):** state → float tensor of shape (1, 7) → the actor's μ(s) under
  `no_grad` → plus Gaussian noise N(0, (max_action·σ)²) per dimension → clipped to [−1, 1].
- **How `update_parameters` works (l.156–194), TD3 paper Algorithm 1:**
  1. `total_it += 1`;
  2. unpack (s, a, s', r, not_done) in the buffer's order;
  3. under `no_grad`: target smoothing, ã = clip(π'(s') + clip(N(0, 0.2), ±0.5), ±1) (§5.3);
  4. y = r + γ·not_done·min(Q₁', Q₂') (§4.2);
  5. critic loss = MSE(Q₁, y) + MSE(Q₂, y);
  6. one Adam step on the critics;
  7. every 2nd update (§5.2): actor loss −mean Q₁(s, π(s)), an Adam step on the actor, then the soft update
     θ' ← τθ + (1−τ)θ' for both critics and the actor.
- **Decisions:**
  - Written exactly as in the docstrings and the paper, with no extras: no loss logging (can be added for tuning if
    needed) and `update` stays unused (the docstring says so).
  - The actor's backward also fills the critic's `.grad`; that's harmless, because the next update starts with
    `critic_optimizer.zero_grad()`. Same as the authors' reference code.
- **Verification:** `test_agent.py`, 11 tests:
  - the action's shape, bounds, σ = 0 → μ(s), numpy/tensor input, noise spread = σ;
  - the critic changes every update, the actor and the targets every 2nd;
  - no gradients reach the targets; the soft update is exactly τ;
  - y uses min(Q₁', Q₂'); y = r at the end of an episode; the smoothing noise is clipped;
  - a toy bandit is learned (the critic loss −90 %, the actor within 0.1 of the best action).

  **Mutation check:** 8 typical mistakes (max instead of min, `not_done` ignored, no delay, τ swapped, unclipped
  smoothing noise, the actor minimising Q, an unclipped action, no `no_grad`): each makes ≥ 1 test fail.
  Full pytest: 92 passed.
- **For Brent:** I explain both functions line by line in the chat (stop after 3.2). Next: 3.3, the runner fixes.

### 2026-11-04 — 2.x: `circuit_env.py` more readable (no behaviour change)
- **Goal:** Brent asked to make the implemented env functions simpler and more readable without breaking correctness.
- **What changed (`circuit_env.py`, branch `feat/td3`):**
  - `__init__` l.38–39: a new list `self.lower_bound_specs`, the hard constraints that must *reach* their target
    (gain, phm, slewRate, ugbw). It's derived from the YAML's `hard_constraints` minus `UPPER_BOUND_SPECS`, so the
    YAML stays the source of truth.
  - `normalize_specs`: the failed case (`spec_dict is None`) is handled first, in one line, before the loop. The
    loop now only normalizes; `goal` is renamed `target`.
  - `reward_computation`: the variable `reward` was first used as r_H and then overwritten with the FoM. Now there
    are separate `r_hard` (r_H) and `r_targets` (r_T), as in `docs/fom.md`, and `hard_satisfied` is computed in one
    line; the unused `hard_satisfied = False` start value is gone.
- **Deliberately not changed:**
  - `action_refine` (the TAs' mapping, already 10 lines);
  - `simulate`, `evaluate`, `log_design`, `reset`, `step` (already one line per action);
  - the course docstrings, signatures and API.
- **Verification:**
  - old vs new version on 20 000 random measurement sets (0.001×–1000× the target, negative values, failed sims):
    the normalized values and the rewards are identical, in value and in type;
  - one detail found this way: `r_hard >= 0` gives a numpy bool, so `bool(...)` keeps a plain True/False as before;
  - pytest: 92 passed.

### 2026-11-04 — Lukas's `circuit_env.py` on main (`814f00c`) compared with ours
- **What Lukas did:** pushed `814f00c` directly to main, with his own `circuit_env.py` (on top of the course version;
  independent of ours) and `tests/test_reference_rewards.py` (the reward on the TAs' norm_* = their reward). Local
  main is fast-forwarded to it (without switching branches).
- **Checked by running his file from a scratch copy:**
  - `action_refine`:
    - `action_space.contains()` rejects every float64 action, i.e. every action from TD3's `select_action` →
      `ValueError`;
    - his linear mapping reproduces 5/100 TA action → sizing pairs (ours 100/100).
  - `simulate` passes `random_name` instead of the netlist path to `engine.simulate` → **every simulation fails**.
  - `normalize_specs`:
    - `observation_space.contains()` rejects float64 metrics → `ValueError` even on valid metrics;
    - `None` (a failed sim) → `AttributeError`;
    - no clip, so PM = −100° gives z = +4 and the unstable amp **counts as meeting all specs** (reward 0.3,
      hard_satisfied True).
  - `reset()` crashes (because of the two points above).
  - `reward_computation`, all specs met: 0.3 − 0.05·Σo instead of 0.3 + r_T (fom.md; hand case 4: 0.325 instead of
    0.8). Both are equal while specs fail, which is why the TA references can't tell them apart.
  - `step` passes a file path where the course plot functions expect `run_id` → `FileNotFoundError` at the first
    feasible design; it also plots on every feasible step.
  - Missing: the simulation counter, failed-sim penalty, designs.csv, feasible netlists, solutions CSV / Pareto.
- **Good in his version:** numbered comments that follow the course docstring step by step; short; explicit
  LOWER/UPPER spec lists; the seeded reset as ours; a simple, useful reference test (it passes against our env too).
- **Recommendation:** keep our implementation, take over his test file and the numbered-step comment style in
  `reset`/`step`. To agree with Lukas: main now has his env while ours is on `feat/env`/`feat/td3` → a conflict in
  `circuit_env.py` when merging.

### 2026-11-04 — 2.6: `circuit_env.py` rebuilt on Lukas's simpler structure, his bugs fixed
- **Goal:** Brent: Lukas's version is simpler. Take it over and fix its issues (see the comparison entry above).
  Understandability and simplicity first, as long as it works.
- **What changed (branch `feat/td3`):**
  - `1983994`: Lukas's `tests/test_reference_rewards.py`, copied unchanged from main.
  - `circuit_env.py`: Lukas's structure, with the course docstrings and numbered `# 1.`…`# 10.` comments in `reset`,
    `step` and `reward_computation`.
- **Fixed relative to Lukas's version:**
  - `simulate`: the netlist path instead of `random_name`, `self.counter += 1`, failed → `None`, the ≤ 0 check;
  - no `contains()` checks (they reject float64 actions/metrics) and no `raise`s inside a run;
  - `normalize_specs`: `None` → the worst-case state, and the clip at 0 for gain/PM/SR/UGBW;
  - `reward_computation`: 0.3 + r_T when all specs pass (fom.md), and one loop instead of the duplicated one;
  - plot calls with `run_id`;
  - the TAs' mapping (100/100 references) instead of the linear one (5/100);
  - added back: `designs.csv` logging, feasible netlists, the solutions CSV, the −6 penalty, `finalize()`
    (Pareto).
- **Simpler than our previous version:**
  - the course constructor signature again (penalty and 0.05 are plain attributes);
  - explicit `LOWER_BOUND_SPECS`/`UPPER_BOUND_SPECS` lists;
  - no `observation()`, `plot()`, `plot_every`, `save_feasible_design()` or float-noise rounding;
  - plots exactly as the course docstring says (Brent's choice).
- **Behaviour changes (deliberate):**
  - the state order is now the YAML `targets` order (area, current, gain, noise, phm, slewRate, ugbw), as in Lukas's
    `list(cur_norm_specs.values())`;
  - the plots follow the docstring: the max-FoM plot on every feasible step, the learning curve every 10 steps.
- **One deviation from the docstring order:** step 7 (the counters) comes first in `step`, so `designs.csv` logs the
  design as step 1…10 (the logging happens inside `evaluate`).
- **Verification:**
  - old vs new on 20 000 random spec sets: `normalize_specs` and `reward_computation` identical (values and types);
  - `action_refine` on 10 000 actions: the same grid point, at most 1.7e-16 relative difference (float noise), same
    types;
  - a real ngspice smoke run of 3 episodes: 33 rows, sim 1…33, counter 33, 10 steps per episode, the learning curve
    written;
  - pytest: 94 passed (+ `test_plots_follow_the_course_steps`, + Lukas's test).
- **For Brent / Lukas:** main still has Lukas's original version (and the revert of PR #6). Merging needs the
  "revert the revert" route, to agree with Lukas.

### 2026-11-04 — 2.7: refuse a hard constraint that is in neither spec list
- **Goal:** put back the useful one of Lukas's `raise ValueError` checks (Brent asked why they were removed).
  - His checks (a) and (c) ("spec missing from norm_specs") were redundant: `norm_specs[spec]` already raises a
    `KeyError` naming the spec.
  - Check (b) ("neither a lower nor an upper bound") was a real guard. Without it, a new hard constraint in the YAML
    would count as a lower bound in `reward_computation`, but wouldn't be clipped in `normalize_specs`: an
    inconsistency without any error.
- **What changed:**
  - `circuit_env.py` `__init__` l.40–44: every YAML hard constraint must be in `LOWER_BOUND_SPECS` or
    `UPPER_BOUND_SPECS`, else `ValueError` at construction. It's a configuration check, so it fails at once, never
    in the middle of a run.
  - New `test_unclassified_hard_constraint_is_refused`.
- **Correction to the comparison above:** "raises end a long run" holds for the `contains()` data checks, not for
  these configuration checks (they fail on the first simulation).
- **Verification:** pytest 95 passed.

### 2026-11-05 — 2.8: `evaluate` and `step` back to the template; reset designs not rewarded
- **Goal (Brent):**
  1. `evaluate`/`step` as in the course template; the reset design no longer gets a reward, and that's OK;
  2. reason about the clip of negative PM;
  3. is `self.last_netlist_path` needed?
  4. recheck the 11 000-sims reasoning;
  5. where the mapping formula comes from.
- **What changed (`circuit_env.py`, branch `feat/td3`):**
  - `evaluate` is the course's 3 lines again.
  - `step` follows the docstring steps 1–10 in order:
    - 2: the reward, or the −6 penalty for a failed sim;
    - 4: `reward_history` + score;
    - 5: creates the output folders;
    - 6: the plot + keeps the netlist + the solutions CSV;
    - 7: the counters, then `log_design`.
  - `reset` calls `log_design()` without a reward (reward/hard_satisfied empty in `designs.csv`).
  - `log_design(reward=None, hard_satisfied=None)` works out `failed` itself.
  - The attributes `self.reward`, `self.hard_satisfied`, `self.failed` are gone.
  - Tests: the failed/feasible tests now use `step` (reset isn't rewarded), the score test uses all of
    `reward_history`, and the logging test checks the empty reward of the reset row.
- **Consequences:**
  - `reward_history` (and so the course's max-FoM plot) now has one point per *step*, not per simulation: about 9 %
    fewer points than simulations. For the report's "max FoM vs simulation", use `designs.csv` (`sim` column).
  - A random reset design that happens to meet all specs isn't kept. That's rare: 0 of 150 random designs (and 0
    of 40 earlier) met all specs.
- **2. The PM clip:** 150 random designs:
  - PM < 0 in only 2 (both ≈ −45°, gain ≈ 9 V/V, i.e. not near a good design);
  - PM = 0 (no unity-gain crossing) in 64, which are z = −1 anyway.

  Unclipped, those two would get z ≈ −6 … −8, and PM < −60° would even give z > +1 ("met"). Verdict: the clip is
  fine for training. It keeps the state and the reward bounded (r_H ≥ −5, the −6 penalty stays the worst value);
  the lost information (−5° vs −47°) concerns rare designs whose gain term already dominates. Added as TA question 4.
- **3. `self.last_netlist_path`:** needed as an attribute. `step()` copies that file when the design meets all specs,
  and `log_design()` writes its name, both after `simulate()` returned. Alternatives: rebuild the path from
  `engine.random_name` (duplicates the wrapper's naming rule), or return it from `simulate` (changes the course's
  return value). Not changed.
- **4. The 11 000 sims:** still correct. `reset()` still *simulates* its random design; only its reward is dropped.
  The budget counts ngspice runs, so 10 steps cost 11 sims; T = 10 000 → 1000 episodes → 11 000 sims. Without a
  counter the runner can only approximate it: T = 4540 → 4994 sims, T = 4550 → 5005 (over). `self.counter` is the
  course's own attribute (it's in the template `__init__`, never incremented); we increment it in `simulate`.
  Real smoke run: 3 episodes = 30 steps = 33 simulations, counter 33, 30 rewarded rows.
- **5. The mapping formula:** reverse-engineered from `references.csv`. It's not in any TA code: `baseline_runner.py` is
  still an empty stub, and the course docstring gives no formula. Candidates:

  | candidate | matches |
  |---|---|
  | `floor((a+1)/2·(n_steps−1))` (ours) | 100/100 |
  | `floor((a+1)/2·n_steps)` | 39 |
  | `round((a+1)/2·(n_steps−1))` | 39 |
  | `floor(… (n_steps+1))`, capped | 12 |
  | linear + nearest grid point | 0 |

  Likely origin: a grid from `np.arange(min, max, step)` (which leaves out max) indexed with
  `floor((a+1)/2·(len−1))`. The references never hit ±1, so the end behaviour is extrapolated. That's TA question 1.
- **Verification:** pytest 95 passed; the 3-episode real ngspice smoke run above.

### 2026-11-05 — 2.9: `circuit_env.py` = Lukas's latest version (`3c7904b`) + only the necessary fixes
- **Goal (Brent):** option A for reset (the template: a random design is simulated but not rewarded; we count and log
  it). Use Lukas's file as the template and add only what's necessary from our design; leave the rest (our comments
  and extras) out.
- **Lukas's `3c7904b` (pushed to main)** fixed:
  - the float64 actions (`np.clip` instead of `action_space.contains`);
  - the netlist path in `simulate`;
  - 0.3 + r_T when all specs pass.

  He also changed the normalization to `(v − g)/(|v| + |g|)`: identical to our clip (any v ≤ 0 gives exactly −1).
- **What changed (branch `feat/td3`):** `circuit_env.py` is his file (323 lines) + 48 lines. Each change fixes a crash
  or meets a project requirement:
  1. `action_refine` l.78: the TAs' mapping instead of his linear one (5/100 → 100/100 reference pairs;
     comparability with the baseline).
  2. `simulate` l.96: `self.netlist` kept (needed for the feasible copy and the log); `self.counter += 1` (the
     5000-sim budget).
  3. `normalize_specs` l.116:
     - `None` → the worst-case state instead of `raise` (a failed sim mustn't end a 5000-sim run);
     - his `observation_space.contains` check removed: it rejects every float64 measurement, so `reset()` crashed;
     - his comment on `abs()` corrected.
  4. `log_design` l.154 + `finalize` l.181 added (`designs.csv` per CLAUDE.md, Pareto plot).
  5. `reset` l.190: `self.episode += 1`, `log_design()` without a reward.
  6. `step` l.228:
     - failed sim → −6 penalty;
     - the plot folder `output_figs/<run_id>` and `run_id` passed to the course plot functions (his file paths
       crashed);
     - feasible netlist copy + `save_solutions_csv`;
     - `log_design`.
  7. `UPPER_BOUND_SPECS`/`LOWER_BOUND_SPECS` moved from `reward_computation` to the class (normalize_specs needs
     LOWER too).
  8. `__init__`: `failed_penalty`, `episode`, `run_folder`, the ngspice logs to `runs/<run_id>/logs`.
- **Left out on purpose (ours, not necessary):**
  - the ≤ 0 noise/current/area check (never triggered in 350 random designs; its test removed);
  - the hard-constraint check in `__init__` (his `raise` inside `reward_computation` does the same);
  - `info` back to his `{'hard_satisfied'}`;
  - our comments and docstring edits.

  Kept as he wrote them: his `print("Simulation failed")`, the duplicated target loop, the `TODO:` docstrings.
- **Tests:**
  - FakeEngine uses the wrapper's argument name `parameters` (he calls `create_new_netlist(parameters=...)`);
  - the failed-sim tests check `env.real_specs is None` / `timed_out` / `designs.csv` instead of `info`;
  - the hard-constraint test calls `reward_computation`;
  - `test_impossible_metric_is_a_failed_sim` removed.
- **Verification:**
  - vs the previous commit: `normalize_specs` and `reward_computation` the same on 20 000 random spec sets (max
    difference 8.9e-16), `action_refine` identical on 5000 actions;
  - a real ngspice run: 3 episodes → 33 rows, counter 33, 30 rewarded rows;
  - pytest: 92 passed.
- **Merge:** this file is now Lukas's latest plus fixes, so the conflict with main is small. Route: a branch from main →
  `git revert efe150e` (brings milestone 2 back) → merge `feat/td3` → resolve `circuit_env.py` to this version. A
  plain merge would silently drop `docs/report/` (dry run).

### 2026-11-05 — milestone 2 pushed to `feat/env` (milestone 3 stays local)
- **Goal (Brent):** push the env work, but none of the milestone 3 implementation.
- **What changed:**
  - In a temporary git worktree (so this working tree wasn't touched), the 6 milestone 2 commits of `feat/td3` were
    cherry-picked onto `feat/env` (`73ac392`): `ddd1b67`, `1983994`, `f8b0399`, `ed201de`, `0027a7b`, `d340c83` →
    `517f2e8` … `c36701a`.
  - The only conflict was in `docs/worklog.md`, resolved to each commit's own version.
  - Pushed: `origin/feat/env` `cc96732..c36701a`. No force, no push to main, no PR.
- **Not pushed:**
  - `00a4ac3` (the runner's `memory_batch` fix) and `357c400` (`select_action`, `update_parameters`,
    `test_agent.py`);
  - Brent's uncommitted comments in `td3/agent.py`.

  The pushed work log does describe the milestone 3 work (Brent: push it as is).
- **Verification:** on the pushed state, `circuit_env.py`, `test_env.py`, `test_reference_rewards.py` and the work log are
  identical to `feat/td3`; `agent.py`/`td3_runner.py` are the course versions. pytest there: 81 passed (= 92 minus
  the 11 agent tests).
- **Branches now:**
  - `feat/env` = milestone 2 (pushed);
  - `feat/td3` = milestone 2 + milestone 3 (local, its M2 commits have other hashes than on `feat/env`).

  Later, rebase `feat/td3` onto `feat/env` (both mine, `feat/td3` unpushed) so that it only adds the M3 commits.

### 2026-11-05 — PR #8: milestone 2 back on main (waiting for Brent's merge)
- **Goal (Brent):** milestone 2 on main.
- **What changed:** branch `merge/m2-env` from main (`3c7904b`), built in a temporary worktree:
  1. `a659fe0` reverts `83382ed` (the revert of the PR #6 merge; `efe150e` is PR #7's merge commit). The only
     conflict was `circuit_env.py` (Lukas's edits after the revert), resolved to its PR #6 state (`cc96732`).
  2. `91c9380` merges `feat/env` (no conflicts).

  The result is identical to `feat/env` (`c36701a`): no milestone 3 code, `docs/report/` back. pytest: 81 passed.
  Pushed, **PR #8** opened.
- **Not done:** `gh pr merge 8` was blocked by the permission system ("Merge Without Review"), as for PR #3/#6. No
  workaround via a direct push. Brent merges PR #8 himself.

### 2026-11-05 — 3.3: `feat/td3` rebased onto main; runner fixes + `tests/test_runner.py`
- **Rebase (Brent: continue milestone 3):**
  - PR #8 is merged (main `696ff53` = milestone 2).
  - `feat/td3` rebuilt on main with only its 2 milestone 3 commits: `00a4ac3` → `73c23c5`, `357c400` → `f6b2773`.
    The work-log conflict was resolved to main's version, which already contained that entry.
  - Files identical to before; Brent's uncommitted agent.py comments + the work log stashed and restored.
  - Backup: local branch `backup/feat-td3-before-rebase`.
- **What changed in `td3_runner.py`** (every change marked `# CHANGED`, so it can be reverted):
  - R1: defaults for the 5 hyperparameters: σ 0.1, batch 128, w 500, actor lr 3e-4, critic lr 1e-3 (the guide's start
    values; tuning in 3.5).
  - R4 (D1): new `--max_sims 5000`. The warm-up and the training loops (outer and inner) stop at
    `env.counter >= max_sims`, so a run ends at exactly 5000 simulations, possibly mid-episode. `--T` stays: whichever
    comes first. Course behaviour back: `--max_sims 1000000`.
  - R5: `env.np_random = np.random.default_rng(seed)` (random start designs) and `env.action_space.seed(seed)`
    (random warm-up actions). `np.random.seed` doesn't reach either. No extra simulation (unlike
    `env.reset(seed=)`).
  - R6/R7: `runs/<run_id>/` gets `TwoStage.yaml`, `hyperparameters.json`, and at the end the networks
    (`agent.save` → `td3_actor`, …); `env.finalize()` draws the Pareto plot.
  - A progress line every 100 steps (steps, simulations, best reward) and a final summary line.
  - R2 was Brent's own fix; R3 (the misleading batch names) left as it is (Brent).
- **`tests/test_runner.py` (4 tests, the real `main()` with the fake simulator):**
  - the defaults are numbers;
  - the stop at exactly 57 simulations in the middle of an episode;
  - the run folder content;
  - the same seed → identical designs, another seed → different ones.

  **Mutation check:** removing the mid-episode stop, the training-loop budget, either seeding line or the checkpoint
  each makes ≥ 1 test fail.
- **A real smoke run** (`--max_sims 220 --w 100`, 36 s):
  - 220 rows, 0 failed, 0 timeouts, 0 feasible;
  - mean step reward −3.06 in the warm-up vs −2.18 in training; best −0.241;
  - ~0.16 s per simulation → a 5000-simulation run ≈ 15 min.
- **pytest:** 96 passed.
- **Next:** 3.4, one full 5000-simulation run with the start values; then look at the plots together.

### 2026-11-05 — 3.4: first full run with the start values (`runs/start_values_s123456`)
- **Settings:** the runner defaults: σ 0.1, batch 128, w 500, actor lr 3e-4, critic lr 1e-3, γ 0.99, τ 0.005, seed
  123456. 5000 simulations (4545 steps), 17 min.
- **Results** (`designs.csv`):
  - failed: 11 sims, all timeouts;
  - **42 feasible designs**, the first at sim 663 (~110 sims after the warm-up ended at sim 550);
  - **best FoM 0.615** at sim 1677: area 0.88e-9 m² (target 2e-9), current 232 µA (target 200 µA), gain 1086 V/V,
    PM 64.7°, SR 62 V/µs, UGBW 109 MHz, noise 22 mV;
  - Pareto front: 6 designs, 470–880 µm² and 230–950 µA.

  | sims | mean step reward | feasible |
  |---|---|---|
  | 1–550 (warm-up) | −2.85 | 0 |
  | 551–1500 | −0.83 | 6 |
  | 1501–2500 | −0.77 | 24 |
  | 2501–3500 | −1.14 | 1 |
  | 3501–5000 | −1.70 | 11 |
- **Interpretation:**
  - TD3 learns quickly at first: −2.85 → −0.8, and the episode score goes from −30 to about −3.
  - **After ~2500 sims the performance gets worse again** and noisier (episode scores −10 … −30); no better design
    after sim 1677.
  - **Not the cause:** saturated actions (the share of parameters at the grid ends stays at the warm-up level,
    13–19 % / 5–9 %).
  - **Late phase:** gain is violated in 90 % of the steps, SR in 68 %, UGBW in 61 %, PM in 41 %.
  - Hypotheses for 3.5 (not verified): the critic lr 1e-3 is too high, so Q drifts late (overestimation / forgetting);
    the constant σ 0.1 prevents refining; the 10-step time-limit `done`.
- **Note on the course plot:** `max_reward.png` is drawn over `reward_history` (only step rewards), so its x-axis
  labelled "# Simulation" is really the step index (0…4545). For the report, draw over the `sim` column of
  `designs.csv`.
- **For Brent:** look at `output_figs/start_values_s123456/` together; then tuning (3.5).


### 2026-11-05 10:45 — 3.5: tuning stage A (one hyperparameter at a time)
**Goal:** see which of the 5 required hyperparameters matter, before spending simulations on repeated runs.

**What changed:**
- New `CAD/analysis/tuning_summary.py`: one table row per run folder (hyperparameters + best FoM, when it was found,
  first feasible design, number of feasible designs, Pareto-front size, mean reward of the last 1500 sims, failures).
- New `CAD/analysis/fom_evolution.py`: how the FoM evolves during the runs, one plot column per hyperparameter
  (base run + the runs that change only that one). Top row: best FoM so far vs simulation; bottom row: mean reward of
  the last 500 sims. Plot: `CAD/output_figs/fom_evolution_A.png`.
- Runs `CAD/runs/A_*` (+ `output_figs/A_*`, `solutions/A_*.csv`). No code of the env/agent/runner changed.

**How it works:**
- 9 runs of 5000 simulations, seed 123456, each changes **one** hyperparameter from the start values
  (σ 0.1, batch 128, w 500, actor lr 3e-4, critic lr 1e-3).
- Two runs at a time, each in its own git worktree (scratchpad `lane_a`, `lane_b`, at `6d416fe`): `clean.sh` empties
  `no_backup/` every 100 steps, which would delete the files of a run sharing the folder. `OMP_NUM_THREADS=1` so the
  two runs don't fight over the 2 cores. ~15 min per run.
- `A_base_1thread` (start values, 1 thread) gives exactly the numbers of `start_values_s123456` → the runs are
  reproducible and the thread setting doesn't change anything.

**Results:**

| run | changed | best FoM | @sim | first feasible | n feasible | Pareto | mean last 1500 |
|---|---|---|---|---|---|---|---|
| A_pilr_1e-4 | actor lr 1e-4 | **0.696** | 2821 | 709 | 184 | 12 | −0.53 |
| A_w_250 | w 250 | 0.683 | 1114 | 792 | 1179 | 10 | −0.15 |
| A_w_1000 | w 1000 | 0.682 | 2852 | 1072 | 1170 | 13 | **+0.02** |
| A_qlr_3e-4 | critic lr 3e-4 | 0.659 | 2484 | 2292 | 19 | 4 | −0.51 |
| A_base_1thread | — | 0.615 | 1677 | 663 | 42 | 6 | −1.70 |
| A_noise_0.2 | σ 0.2 | 0.603 | 4591 | 663 | 102 | 6 | −0.55 |
| A_noise_0.05 | σ 0.05 | 0.579 | 4282 | 2367 | 12 | 2 | −1.25 |
| A_batch_64 | batch 64 | 0.511 | 2929 | 1161 | 236 | 4 | −1.09 |
| A_batch_256 | batch 256 | 0.474 | 1399 | 1399 | 16 | 3 | −1.14 |

FoM evolution (best so far at 1000/2000/3000/5000 sims; mean reward of the last 500 sims at 3000 → 5000):

| run | best @1000 → 2000 → 3000 → 5000 | mean @3000 → 5000 |
|---|---|---|
| start values | 0.27 → 0.62 → 0.62 → 0.62 | −0.77 → −1.86 |
| σ 0.05 | −0.19 → −0.07 → 0.49 → 0.58 | −1.33 → −1.17 |
| σ 0.2 | 0.36 → 0.60 → 0.60 → 0.60 | −0.50 → −0.62 |
| batch 64 | −0.19 → 0.48 → 0.51 → 0.51 | −0.14 → −0.86 |
| batch 256 | −0.19 → 0.47 → 0.47 → 0.47 | −0.94 → −1.77 |
| w 250 | 0.57 → 0.68 → 0.68 → 0.68 | 0.03 → −0.18 |
| w 1000 | −0.15 → 0.59 → 0.68 → 0.68 | 0.00 → −0.05 |
| actor lr 1e-4 | 0.29 → 0.63 → 0.70 → 0.70 | −0.44 → −0.30 |
| critic lr 3e-4 | −0.18 → −0.01 → 0.66 → 0.66 | −0.71 → −0.52 |

**Interpretation:**
- The best FoM saturates early: every run has its best design by ~sim 3000, most by sim 2000.
- With the start values the agent **degrades** in the second half (mean −0.4 at sim 2500 → −1.86 at 5000). Most
  changes keep it stable: actor lr 1e-4, critic lr 3e-4, w 250/1000, σ 0.2. A slower actor (TD3 paper §5: the actor
  should change slowly relative to the critic) fits that picture.
- The warm-up mostly **shifts the curve in time**: the mean reward rises right after the random warm-up ends
  (w steps = w·1.1 sims). w 250 finds good designs earliest; w 1000 ends with the best mean (more varied data in the
  buffer before learning starts).
- σ 0.05 (too little exploration) and critic lr 3e-4 find their first feasible design late (~sim 2300).
- Batch 64 and 256 are both worse than 128 on best FoM.
- **Caveat:** one seed per setting. Changing any hyperparameter changes the whole random trajectory, so w 250 and
  w 1000 both beating 500 may be partly luck. That is why stage B repeats the best settings with 3 seeds.

**Decisions:**
- Stage B: the start values, actor lr 1e-4, w 1000, and the combination actor lr 1e-4 + w 1000; seeds 123456, 1, 2
  (seed 123456 of the first three is from stage A). 9 new runs, ~75 min. w 1000 rather than w 250: better and still
  rising late mean; w 250 is kept as the alternative if w 1000 doesn't hold up.

**Verification:** `tuning_summary.py` reproduces the hand-computed numbers of 3.4 on `start_values_s123456`;
`A_base_1thread` equals that run exactly. Plot checked visually.

**For Brent to check:** `CAD/output_figs/fom_evolution_A.png`. Which criterion matters most for the final choice:
best FoM, number of feasible designs, or a stable mean at the end?
- **Brent's answer (criterion):** the best FoM is the main goal. Stage B is ranked on the **mean of the best FoM over
  the 3 seeds** (one run's best is a maximum, so a single lucky seed can't decide), with the spread over the seeds and
  the simulation at which the best was reached as tie-breakers. This matches the PDF's comparison with the baseline
  (max FoM within 5k sims).
- **Added stage B2 (Brent's question: combine the best value of every hyperparameter):** stage B only had one
  combination (actor lr 1e-4 + w 1000). The best stage-A value per hyperparameter, by best FoM: σ 0.1 and batch 128
  (the start values were already best), w 250 (0.683, vs 0.682 for w 1000), actor lr 1e-4 (0.696), critic lr 3e-4
  (0.659). Runs `B_allbest_s{123456,1,2}` with `--w 250 --pi_lr 1e-4 --q_lr 3e-4`, queued after stage B (~35 min more).
  Caveat: hyperparameters interact (e.g. a slower critic and a slower actor together may learn too slowly in 5000
  sims), so the combination of one-at-a-time winners isn't guaranteed to be the best; the seeds will show it.

### 2026-11-05 12:30 — 3.5: tuning stage B + B2 (3 seeds per setting)
**Goal:** check the stage-A winners over several seeds and pick the final hyperparameters on the **mean best FoM**.

**What changed:** runs `CAD/runs/B_*` (+ `output_figs/B_*`, `solutions/B_*.csv`), same worktree method as stage A.
No code changed.

**Results** (σ 0.1 and batch 128 in every setting; seeds 123456, 1, 2):

| setting | best FoM per seed (123456 / 1 / 2) | mean | std | worst | mean sim of best | mean n feasible | mean late reward |
|---|---|---|---|---|---|---|---|
| start values (w 500, actor 3e-4, critic 1e-3) | 0.615 / 0.617 / 0.684 | 0.639 | 0.039 | 0.615 | 2100 | 375 | −0.99 |
| actor lr 1e-4 | 0.696 / 0.622 / 0.668 | 0.662 | 0.037 | 0.622 | 2323 | 393 | −0.58 |
| w 1000 | 0.682 / 0.684 / 0.638 | 0.668 | 0.026 | 0.638 | 2291 | 459 | −0.38 |
| **actor lr 1e-4 + w 1000** | 0.702 / 0.660 / 0.662 | **0.675** | **0.024** | **0.660** | 4097 | 494 | **−0.22** |
| all-best (w 250, actor 1e-4, critic 3e-4) | 0.632 / 0.628 / 0.695 | 0.652 | 0.038 | 0.628 | 2596 | 956 | −0.50 |

**Interpretation:**
- Both single changes beat the start values on the mean best FoM (+0.02 / +0.03) and their combination is best
  (+0.036), with the smallest spread and the best worst case. It also degrades least at the end (late reward −0.22).
- The "best value of every hyperparameter" combination is **worse** than actor lr 1e-4 + w 1000 (0.652): the
  hyperparameters interact. Most likely the slower critic (3e-4) together with the slower actor learns too little in
  5000 sims, and w 250 gives a less varied buffer. One-at-a-time winners don't simply add up.
- The differences are small compared with the seed spread: with 3 seeds the standard error of a mean is ≈ 0.02, so
  only the ~0.04 gap to the start values is a clear trend; 0.675 vs 0.668 is not.
- Cost of the winner: it finds its best design late (mean sim 4097, one seed at 4615), so it uses almost the whole
  5000-sim budget. w 1000 alone finds its best at ~2300.

**Recommendation (for Brent to decide):** actor lr 1e-4 + w 1000, the rest at the start values
(σ 0.1, batch 128, critic lr 1e-3). Alternative if an earlier best matters: w 1000 alone.

**For Brent to check:** choose the final values; then 3.6 (final run, plots, `Solutions/`).

### 2026-11-05 — 3.6 prep: TAs' SAC baseline + milestone 4 template placed for the student server
**Goal:** Brent got the lab session 3–4 files; put everything where it belongs so the `CAD/` folder can be copied to
the student server as is.

**What changed (branch `feat/td3`):**
- Moved: `sac_runner.cpython-39-x86_64-linux-gnu.so` → `CAD/`, `sac_baseline.cpython-39-x86_64-linux-gnu.so` →
  `CAD/td3/` (slide 2); `mcp_server.py`, `sizing_tools.py` → `CAD/` (milestone 4 template, imports `circuit_env`/`td3`);
  `session3-4.pptx` → `docs/course/` (private). The `.so` files and the template are **not committed** (binaries /
  course material; to agree with Lukas).
- `CAD/baseline_runner.py`: `import sac_runner as sr; sr.main()` (slide 2).
- `CAD/td3/__init__.py`: `from .sac_baseline import SAC` (slide 2), inside `try/except ImportError` → `SAC = None`.
  The `.so` files only load on **x86-64 Linux with Python 3.9**; on our ARM VM (Python 3.14) an unguarded import
  would break `import td3` and every test.

**How it works:**
- SAC = Soft Actor-Critic, the TAs' reference agent, compiled with Nuitka (no source). Its runner uses our
  `CircuitEnv` (same FoM, logging) and has the same options as `td3_runner.py` plus `--alpha_lr`,
  `--init_temperature`, `--target_update_interval`.
- Milestone 4: `mcp_server.py` (complete) exposes 4 tools to an LLM coding agent over MCP: `simulate`, `warmup`,
  `train`, `get_status`. `sizing_tools.py` (`SizingExperiment`, 7 TODOs) is ours to fill in with the milestone 2–3 code.
- **Brent:** the template's hyperparameters (σ 0.1, actor lr 3e-4, critic lr 3e-4, batch 100) **stay as given**;
  only `td3_runner.py`'s are ours to choose.
- Its `_validate_parameters` docstring says the grids are `np.arange(min, max, step)` "as phase one" → confirms our
  answer to TA question 1 (the max is excluded, hence `n_steps − 1` in the mapping).

**Verification:**
- Our code has no Python ≥ 3.10 features (`ast.parse(..., feature_version=(3, 9))` + union-annotation check), so it
  should run under the server's Python 3.9.
- Fresh copy of `CAD/` without `runs/ no_backup/ output_figs/ solutions/` (1.9 MB): 96 tests pass, a real 40-sim
  `td3_runner.py` run works, all output folders are created automatically.
- On the VM: `import td3` works (`SAC = None`); `python baseline_runner.py` fails with "No module named sac_runner"
  (expected: wrong platform).

**For Brent:** copy with
`rsync -av --exclude runs/ --exclude no_backup/ --exclude output_figs/ --exclude solutions/ --exclude __pycache__/ CAD/ <user>@<server>:<dir>/CAD/`,
then on the server `cd CAD && python baseline_runner.py` (needs Python 3.9 + the course packages + ngspice there).
Unknown until it runs: the SAC runner's defaults, and whether it stops at 5000 sims (our `--max_sims` is in
`td3_runner.py`, not in the env).

### 2026-11-05 14:00 — 3.5: Lukas's milestone 3 (`07d2e87` on main) compared; his hyperparameters on our code, 4 seeds
**Goal:** Brent: compare Lukas's TD3 with ours, and run his hyperparameters with our implementation on 4 seeds.

**Lukas's commit** (`07d2e87` "agent implementation v1", pushed directly to `main`): fills in `select_action` and
`update_parameters` in `td3/agent.py`; `td3_runner.py`: defaults σ 0.1, batch 64, w 200, actor lr 1e-3, critic lr
1e-3 (as strings, argparse converts them) and the `memory_batch=` fix.

**Agent comparison:**
- His agent passes all 11 tests of our `tests/test_agent.py` (run in a worktree at `07d2e87`).
- Same seed + same batches: identical actions and **bit-identical weights after 200 updates** (max difference 0.0).
  Algorithmically the two are the same.
- His `select_action` step 1 is simpler: one line `torch.as_tensor(state, dtype=torch.float32, device=device)
  .reshape(1, -1)` (handles numpy, lists and tensors) vs our 3 lines. His structure follows the docstring 1:1 (steps 3
  and 4 as two `no_grad` blocks). Our comments explain the why (paper sections) and we have the tests.
- Suggestion (not done; Brent's uncommitted comments are in `agent.py`): take his one-line step 1.

**Runner comparison:** his is the course runner with the values filled in. Missing vs ours: the 5000-sim stop (his runs
`--T 10000` steps = 11000 sims), seeding of `env.np_random` / `env.action_space` (so not reproducible), the run folder
(YAML, `hyperparameters.json`, networks) and `env.finalize()`.

**Runs:** our code (`feat/td3` `8000072`, same agent/runner/env as the tuning), his hyperparameters, seeds 123456, 1,
2, 3, 5000 sims each (`CAD/runs/L_lukas_s*`). The VM had restarted (13:17) and `/tmp` was wiped: worktrees recreated.

| seed | best FoM | @sim | first feasible | n feasible | mean late reward |
|---|---|---|---|---|---|
| 123456 | 0.669 | 4865 | 811 | 2194 | +0.11 |
| 1 | 0.606 | 4964 | 302 | 789 | −0.59 |
| 2 | 0.687 | 4950 | 356 | 1799 | −0.17 |
| 3 | 0.665 | 1220 | 579 | 374 | −0.24 |

| setting | seeds | mean best | std | worst | best | mean n feasible |
|---|---|---|---|---|---|---|
| start values | 3 | 0.639 | 0.039 | 0.615 | 0.684 | 375 |
| **ours: actor lr 1e-4 + w 1000** | 3 | **0.675** | **0.024** | **0.660** | **0.702** | 494 |
| Lukas's values | 4 | 0.657 | 0.035 | 0.606 | 0.687 | **1289** |

Same seeds side by side (best FoM, ours / Lukas): 123456: 0.702 / 0.669, 1: 0.660 / 0.606, 2: 0.662 / 0.687.

**Interpretation:**
- On the best FoM within 5000 sims ours is ahead (+0.018 on the mean, wins on 2 of 3 shared seeds, better worst
  case), but the gap is within the seed spread (standard error ≈ 0.015–0.02): a trend, not a proof.
- His values are better at finding *many* feasible designs early (first at sim 300–800, ~1300 per run vs ~500): useful
  for the Pareto front. Fast actor (1e-3) + short warm-up (200) = learns quickly, then exploits.
- 3 of his 4 runs found their best in the last 150 sims (still improving at the budget). That fits Lukas's 0.711 on one
  seed being found **after sim 5000** (his runner goes to 11000 sims) or a lucky seed; none of our 4 runs reaches 0.711
  within 5000 sims.

**For Brent / Lukas:** ask Lukas at which simulation his 0.711 was found (`designs.csv`, `sim ≤ 5000`). Choose the final
values: best mean FoM → ours; many feasible designs / Pareto → his.

### 2026-11-05 — 3.6 prep: the SAC baseline's hyperparameters, read from the compiled runner
**Goal:** know the TAs' baseline settings before comparing with it (the `.so` can't run on our ARM VM).

**How:** `sac_runner.cpython-39-x86_64-linux-gnu.so` is compiled with Nuitka, which stores the module's constants as
typed values: `l` + a 7-bit varint for an int, `f` + an 8-byte little-endian double for a float, `u` + text for a
string. Each `add_argument` default sits right before its help text. Decoded with a short Python script (no
execution of the binary), cross-checked with the help texts (e.g. `l c0 c4 07` = 123456 = "default: 123456").

| argument | default | note |
|---|---|---|
| `--seed` | 123456 | |
| `--batch_size` | 100 | |
| `--w` (warm-up steps) | 100 | |
| `--pi_lr` | 3e-4 | policy (actor) |
| `--q_lr` | 3e-4 | critics |
| `--alpha_lr` | 3e-4 | SAC only: entropy temperature |
| `--init_temperature` | 0.1 | SAC only: initial α |
| `--target_update_interval` | 1 | SAC only |
| `--gamma` / `--tau` | 0.99 / 0.005 | same as ours |
| `--hidden_size` | 256 | same network width as our TD3 |
| `--T` | 10 000 steps | ≈ 11 000 sims, no simulation stop |
| `--replay_size` | 1 000 000 | |
| `--noise_sigma` | 0.1 | "unused placeholder to keep parity with TD3 args" (SAC explores through its stochastic policy) |
| `--actor_update_interval` | 1 | "kept for interface compatibility (unused)" |

**Runner structure** (from the names it uses): the same as the course `td3_runner.py`: `readParser`, `warmup_exploration`,
`train`, `train_policy` (`update_parameters(memory=..., update=...)`), `main`; `./clean.sh` every 100 steps; seeds only
`np.random` and `torch` (no `env.np_random` / `action_space.seed`, so not exactly reproducible); no `counter` /
budget stop. It takes the usual command-line options (`sr.main()` parses `sys.argv`).

**Consequence for the comparison (3.6):** the baseline runs ~11 000 sims by default → compare on its **first 5000
simulations** (`designs.csv`, `sim ≤ 5000`; same env, so same logging and FoM), and run it on several seeds
(`python baseline_runner.py --seed 1 --run_id sac_s1`, …) because one seed is one sample.

### 2026-11-05 14:47 — 3.5: stage C, our TD3 with the SAC baseline's hyperparameters (+2 variations)
**Goal:** Brent: on the student server the SAC baseline currently does better than our TD3. Run our TD3 with SAC's
hyperparameters and try to beat its FoM.

**Runs** (`CAD/runs/C_*`, our code `8000072`, 5000 sims, seeds 123456, 1, 2):
- `C_sac_*`: SAC's values exactly: σ 0.1, batch 100, w 100, actor lr 3e-4, critic lr 3e-4.
- `C_sac_pilr_*`: the same with actor lr 1e-4 (slower actor = our clearest tuning effect).
- `C_sac_qlr_*`: the same with critic lr 1e-3 (our start value).
- TD3's delayed actor update stays at 2 (part of TD3; SAC's `--actor_update_interval 1` is "unused").

**For Brent:** the SAC FoM to beat must be its best over **sim ≤ 5000** of its `designs.csv` (its runner goes to ~11 000 sims).
- **Restart (14:58):** Brent gave the VM 3 cores / 5.4 GB (was 2 / 3.4 GB); the first attempt (2 lanes in `/tmp`) was
  stopped by the VM shutdown. Restarted with 3 lanes as git worktrees in `~/td3_lanes/lane_{a,b,c}` (at `c171eeb`, same
  agent/runner/env code), outside `/tmp` so a restart doesn't wipe them. Log: `~/td3_lanes/tune_stage_c.log`.
- **Result (aborted at 15:45 on Brent's call, 5 of 9 runs finished; the 4 unfinished ones are not kept):**

  | setting (batch 100, w 100, σ 0.1) | seed 123456 | seed 1 | seed 2 (aborted, best so far) |
  |---|---|---|---|
  | SAC's values (actor 3e-4, critic 3e-4) | 0.300 | 0.368 | (0.311 @ sim 3677) |
  | + actor lr 1e-4 | 0.366 | (0.075 @ sim 4613) | (0.661 @ sim 3872) |
  | + critic lr 1e-3 | 0.584 | 0.335 | — |

  Our TD3 with SAC's hyperparameters is far worse than with our tuned values (0.675 mean): 0.30–0.37. Likely the
  short warm-up (100 steps ≈ 110 sims): TD3's critic starts from very few, one-sided samples, and TD3 has only the small
  fixed exploration noise, while SAC keeps exploring through its entropy term. So SAC's lead is not explained by its
  hyperparameters. **Decision (Brent):** stop stage C; our previous tuned values stay the candidate. The comparison with
  SAC waits for its best FoM over `sim ≤ 5000`.

### 2026-11-05 — 3.6: final hyperparameters, final results, comparison with the SAC baseline
**Goal:** Brent chose the final values (actor lr 1e-4 + w 1000) and the 3 existing runs with them as the final result.

**What changed (branch `feat/td3`):**
- `CAD/td3_runner.py` (`60bc219`): defaults `--w 1000`, `--pi_lr 1e-4` (σ 0.1, batch 128, critic lr 1e-3 unchanged).
  `python td3_runner.py` without options now has exactly the settings of `B_pilr_w_s123456` (checked against its
  `hyperparameters.json`: only `run_id` differs). The budget comment now says what the PDF says (comparison and
  Solutions at 5k sims, no hard cap stated).
- New `CAD/analysis/final_results.py`: the two required plots + the `Solutions/` folder.
  - `CAD/output_figs/final_max_fom.png`: maximum FoM against the **simulation** number, the 3 seeds (the course's
    `max_reward.png` has the step index on its x-axis).
  - `CAD/output_figs/final_pareto.png`: current–area Pareto front of `B_pilr_w_s123456`: all 891 designs that met all
    specs, the 9 Pareto designs, the best-FoM design.
  - `Solutions/` (repo root, next to `CAD/`): the 9 Pareto netlists (from `runs/<run>/feasible_netlists`) +
    `Solutions.csv` (sim, netlist, 20 parameters, 7 specs, reward). Not in `CAD/`: on macOS (case-insensitive)
    `Solutions/` and the course's `CAD/solutions/` would be one folder. **Not committed yet** (new top-level folder in
    the shared repo: Brent/Lukas decide).
- Pareto rule: no other feasible design with both smaller-or-equal area and current (one strictly smaller);
  duplicate (area, current) points counted once.

**Final results** (TD3: σ 0.1, batch 128, w 1000, actor lr 1e-4, critic lr 1e-3, 5000 sims):

| | seed 123456 | seed 1 | seed 2 | mean ± std |
|---|---|---|---|---|
| best FoM | 0.702 (sim 3724) | 0.660 (sim 3952) | 0.662 (sim 4615) | 0.675 ± 0.024 |
| designs that met all specs | 891 | 403 | 187 | |

Pareto front of seed 123456 (area µm² / current µA / FoM): 616/286/0.652, **657/246/0.702** (best FoM), 708/236/0.695,
810/234/0.645, 865/234/0.618, 866/231/0.623, 923/229/0.601, 925/225/0.609, 1182/207/0.539. All meet every hard spec.

**SAC baseline** (Brent, student server, 1 seed): best FoM **0.662**. Ours: mean 0.675, best 0.702, both other seeds at
0.660–0.662. So our tuned TD3 is at least as good as SAC within 5k sims, and better on the default seed and on the
mean, but one SAC seed is one sample.

**For Brent:** for the report, run SAC on 2 more seeds (`python baseline_runner.py --seed 1 --run_id sac_s1`, `--seed
2`) and take the best `reward` with `sim ≤ 5000` from each `designs.csv`; with the CSVs I can draw SAC's curve in
`final_max_fom.png`. Decide whether `Solutions/` gets committed.

### 2026-11-05 — 4.1 + 4.2: milestone 4 branch; `sizing_tools.py` filled in (+ `tests/test_sizing_tools.py`)
**Goal:** the backend of the MCP tools (plan: `~/.claude/plans/streamed-sauteeing-moonbeam.md`). Brent's decisions:
agents by role (analyst → designer → RL operator → reviewer), and an optional `reason` on the tools for traceability.

**What changed (branch `feat/m4-harness`, from `feat/td3`):**
- `a4076e3`: `CAD/sizing_tools.py` + `CAD/mcp_server.py` committed **unchanged** (course template), so the diffs show
  only our work. The template hyperparameters stay (σ 0.1, lr 3e-4 / 3e-4, batch 100).
- `CAD/sizing_tools.py`, the 7 TODOs:
  - `_validate_parameters`: exactly the 20 YAML names, finite reals (no bool/str), on the `np.arange(min, max, step)`
    grid (= `action_refine`'s grid, the YAML max excluded) within 1e-6 of a grid index; returns `min + idx·step`,
    exactly the number `action_refine` makes (3.0 → 3 for a multiplicity; JSON sends floats). Off-grid → a
    `ValueError` with the allowed range; nothing is simulated.
  - `_record`: scores with the env's own `normalize_specs` + `reward_computation` (so the same reward the agent gets);
    a failed / non-finite result is refused; stored in `self.candidates` by parameter tuple (a repeat replaces).
  - `simulate`: validate → the **separate `evaluation_env`** → record. The RL episode, buffer and weights stay untouched.
  - `_run_steps`: the episode loop across calls: reset when no episode is running (the first reset seeded), action =
    `action_space.sample()` (warmup) or `agent.select_action` (train), `env.step`, a failed sim is not pushed to the
    buffer, one `update_parameters` per new transition in training. `./clean.sh` every 100 calls (as `td3_runner`).
    An unexpected error mid-batch keeps the finished steps and says how many.
  - `warmup` / `train`: 1…1000 steps; `train` refuses before `batch_size` experiences ("call warmup first").
  - `get_status`: counters, the targets, the top-k distinct designs by reward (copies).
- Added: `reason` arguments; `_record_and_log` writes **every** simulator call (reset/warmup/train/simulate, failed
  ones too) to `runs/<run_id>/harness_history.csv` (time, elapsed s, call number, source, reason, netlist, 20
  params, 7 specs, reward, hard_satisfied, failed) and keeps the netlists of designs that meet all specs in
  `runs/<run_id>/feasible_netlists/`.
- `CAD/tests/test_sizing_tools.py`: 23 tests (fake simulator): grid = `np.arange` = `action_refine`, round-off and
  `3.0 → 3`, 7 kinds of invalid values rejected without simulating, missing/unknown names, simulate leaves the RL
  state alone and scores like the env, feasible netlist kept, warmup = n transitions + 0 updates, train needs
  `batch_size` then 1 update per transition, bounded step counts, failed sims logged but not in buffer/candidates,
  mid-batch error keeps the finished steps, same seed = same designs, ranking + copies + bounds of `get_status`,
  one history row per call with source and reason.

**Verification:**
- Mutation check: 5 deliberate bugs (failed sim into the buffer, simulate in the RL env, no update in train, the
  grid max allowed, a wrong step count) are each caught by the tests.
- Real ngspice: TA reference design 1 via `simulate`: all 7 specs within 0.6 % of `references.csv`, reward −0.2533
  (TA −0.2528). `warmup(20)` → 20 transitions, 22 sims, 0 updates; `train(10)` → 10 transitions, 11 sims, 10
  updates; `harness_history.csv` rows = `simulator_calls` (133).
- Our code still parses as Python 3.9.

**For Brent:** the line-by-line explanation follows in the chat. Next: 4.3, the `reason` argument in `mcp_server.py`
plus an MCP client test over stdio.

### 2026-11-05 — 4.3: `mcp_server.py`: the `reason` argument; stdio test
**What changed:**
- `CAD/mcp_server.py`: `simulate`, `warmup` and `train` take an optional `reason: str = ""` and pass it to the
  backend, which stores it with every design in `harness_history.csv`. The docstrings (what the LLM reads) say what
  to put there ("hypothesis -> expected effect on the specs"). Nothing else changed: same tool names, the lock, the
  stdout redirect.
- New `CAD/tests/test_mcp_server.py`: starts the real `mcp_server.py` as a subprocess with the `mcp` package's stdio
  client, the way agy does: the 4 tools are listed, `reason` is in the schemas and optional, `get_status` of a fresh
  experiment answers (0 calls), and an incomplete design comes back as a readable tool error, not a server crash.
- Note: `mcp` 2.3 uses snake_case fields (`input_schema`, `is_error`).

**Verification:** all tests pass (120).

### 2026-11-05 — 4.4: the harness files (agents, skills, rules, MCP config, memory)
**Goal:** everything Antigravity CLI needs to run the harness, in `CAD/` so it travels with the folder. Formats from the
agy docs (antigravity.google/docs: subagents, skills, rules, mcp).

**What changed:**
- `CAD/AGENTS.md` (6 KB; agy loads it in every session from the start folder):
  - the goal;
  - the circuit map (20 parameters → devices and roles);
  - the allowed grid values;
  - the spec table (hard vs optimise, how each is measured);
  - the FoM in words;
  - the 4 tools with their cost;
  - the agents with the MCP tools each gets;
  - the **workflow**: analyst → designer rounds (≤ 10 sims) → decision after each round (designer again /
    `rl-operator` when stuck: no improvement in 2 rounds or still infeasible after 30 sims / `reviewer` when converged
    or at ~300 sims);
  - context management: subagents get only the relevant log entries + the 3 best designs, and return ≤ 300 words;
  - rules: a `reason` on every call, numbers only from tools, one change per simulation, on-grid values.
- `CAD/.agents/agents/`: `circuit-analyst`, `designer`, `rl-operator`, `reviewer`; the body is each agent's prompt
  (input, procedure, output format). Frontmatter `tools: [view_file]` only: the docs warn that an unknown tool name
  can hang a subagent. The MCP tools per agent are granted by the orchestrator (AGENTS.md table) and named in each
  prompt; whether agy can also enforce this per agent is checked in 4.5.
- `CAD/.agents/skills/`:
  - `two-stage-opamp-design`: the first-order equations: currents from the mirror ratios, gm, A0 = A1·A2,
    GBW = gm1/(2πCc), p2 = gm6/(2πCL), the zero and Rc (LHP zero, Rc ≈ (1 + CL/Cc)/gm6), PM ↔ p2 ≥ 2.2·GBW,
    SR = I_tail/Cc on the rising edge, noise, balance;
  - the knob table (spec → change → side effects) and the area formula from `area_estimation.py` (1 pF ≈ 333 µm²,
    1 kΩ ≈ 71 µm², the pair and the mirror count twice);
  - the "calibrate early" warning.
  - `rl-sizer`: what TD3 is and costs (≈ 1.1 sims per step; milestone 3: first feasible after ~700–2000 sims), when it
    is worth it, a batch procedure with stop criteria.
  - `design-log`: the memory format (entry: goal, reasoning, actions, result, conclusion) and the rules (append only,
    numbers from tools).
- `CAD/.agents/mcp_config.json`: server `cad` = the venv Python + `mcp_server.py`; VM paths; ngspice on `PATH`;
  timeout 1800 s.
- `CAD/harness/`: `design_log.md` (empty memory), `session_prompt.md` (the task for a full run), `README.md` (how to
  run, interactive and headless with `--output-format stream-json`), `sessions/` (transcripts).
- `CAD/tests/test_harness_files.py` (5 tests):
  - frontmatter of every agent/skill (name = file/folder name, description, body);
  - `AGENTS.md` ≤ 24 000 bytes and names every agent, skill and tool;
  - the MCP config points at `mcp_server.py`.

**Decisions:**
- No designs or results from milestone 3 in the prompts (a fair harness-vs-RL comparison). Only process knowledge:
  the check of the formulas on the TD3 Pareto designs showed that the textbook mirror currents are ~2× too low and the
  slew-rate estimate 2–3× too high in this 45 nm process; the skill says so ("calibrate early") without giving values.
- The orchestrator (agy's main agent) writes the log, so the subagents need only `view_file`.

**For Brent:** check the equations and the knob table in `two-stage-opamp-design` (your analog expertise; it's what
the examiners will ask about). Next, 4.5: install agy on the VM and do the first contact (see `harness/README.md`).

### 2026-11-05 — 4.6 (prepared): `analysis/harness_vs_rl.py`, the runtime comparison for the report
**Goal:** PDF "Finalize and Report": runtime vs. max FoM, harness vs. pure RL, plus explainability examples.

**What changed:**
- New `CAD/analysis/harness_vs_rl.py --harness <runs> --rl <runs>`:
  - harness: `harness_history.csv`, where `elapsed_s` counts from the MCP server start, so it includes the LLM's
    thinking time;
  - TD3: `designs.csv`, with the time from the netlist names (`TwoStage_<unix time>_…`, 1 s resolution: no rerun
    needed);
  - outputs: `output_figs/harness_vs_rl.png` (max FoM against runtime); a table of runtime and simulations to the
    first design meeting all specs and to FoM 0.5, 0.6 and the harness's best (exact value, rounded label); the
    trace of the simulations that raised the harness's best FoM, with their `reason`.
- New `CAD/tests/test_harness_vs_rl.py` (3 tests, made-up runs): failed and reset rows are skipped, the clocks, the
  milestones, the improvement trace.
- Integration check: a 3-simulation session through the backend (TA references 1–3) + `B_pilr_w_s123456` → the
  table and the trace come out right. A bug found and fixed: a rounded best-FoM level (−0.253 > −0.2533) was "never
  reached". The check's run folders were removed again.
- Fairness of the timing: the tuning runs ran two at a time on 2 cores. `T_final_timing_s123456` reruns the final
  configuration alone (same seed, in `~/td3_lanes/lane_a` so its `clean.sh` can't touch a harness session in `CAD/`)
  for a clean TD3 runtime.

**Verification:** all tests pass (128).

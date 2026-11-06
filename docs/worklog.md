# Work log — H05D7 CAD project (Brent & Lukas)

Status, questions for the TAs, changes to the course code, how things work, and material for the report and the exam.
(The full step-by-step logs of every commit, `docs/worklog_m1_detailed.md` and `docs/worklog_detailed_2026-11-05.md`,
and the FoM notes `docs/fom.md` are Brent's local notes and not in the repo; the FoM itself is in
`circuit_env.py` `reward_computation`.)

## Status
**Where we are (Thu 5 Nov, evening):** all 4 milestones implemented and tested (129 tests pass); the report is next.
- Milestones 1 and 2 on `main` (PR #8).
- Milestone 3 on `feat/td3` (not pushed).
- Milestone 4 on `feat/m4-harness` (from `feat/td3`). Both merged with `main` (Lukas's M3) on 6 Nov and pushed as
  **`einstein_LLM`**. **Current branch: `feat/m4-template`** (harness v4: only the course template's tools + the warm-up around the LLM's design inside our TODO; the v4.1 warm start reverted; from `feat/m4-tutor` = v3.2; not pushed; 133 tests pass).
- Report material per section: `docs/report/report_material.md` (figures in `docs/report/figures/`).
- Deadline: Sun 8 Nov 2026, 23:59.

**Milestone 1: simulator interface** (PDF §1), on `main`
- ✅ 1.0 ngspice wrapper: ngspice from PATH, real exit code, log files, output folder, 20 s timeout
- ✅ 1.1 failure rules: no unity-gain crossing → UGBW = PM = 0 (valid but bad); broken output / error / timeout → failed
- ✅ 1.2 netlist writes its results (`wrdata`), `.options trtol=0.1` for the slew-rate edge
- ✅ 1.3 measurements: gain, UGBW, PM, slew rate (rising edge, VDD-limited levels), noise, current (area: course code)
- ✅ 1.4 unit tests `test_measure.py` (50) + `test_wrapper.py` (5), incl. the TAs' `references.csv` (all 7 within 1 %)
- ⬜ 1.R report section (material: `docs/report/report_material.md` §1)

**Milestone 2: circuit environment** (PDF §2), on `main`
- ✅ 2.1 `action_refine` (the TAs' mapping; all 100 reference action → size pairs)
- ✅ 2.2 `simulate` (PVT corner, counter, failed sims) · ✅ 2.3 `normalize_specs`, `reward_computation` (the course FoM)
- ✅ 2.4 `reset`, `step`, logging (`designs.csv`, feasible netlists), plots as in the course docstring, `finalize()`
- ✅ 2.5 `test_env.py` (25) + Lukas's `test_reference_rewards.py` · ✅ 2.6–2.9 rebuilt on Lukas's structure
- ⬜ 2.R report section (material §2)

**Milestone 3: TD3 agent** (PDF §3), on `feat/td3`
- ✅ 3.1 `select_action` · ✅ 3.2 `update_parameters` + `test_agent.py` (11)
- ✅ 3.3 runner fixes (5000-sim stop, seeding, run folder, `finalize()`) + `test_runner.py` (4)
- ✅ 3.4 first full run (start values)
- ✅ 3.5 tuning: stages A (9 runs), B + B2 (3 seeds), C (SAC's values); Lukas's values on 4 seeds
- ✅ final values (Brent): σ 0.1, batch 128, w 1000, actor lr 1e-4, critic lr 1e-3, given as options; since the merge of
  6 Nov the runner defaults are Lukas's (batch 64, w 200, actor lr 3e-4, critic lr 1e-3)
- ✅ 3.6 final results: 3 seeds (0.675 ± 0.024, best 0.702), `final_max_fom.png`, `final_pareto.png`, `Solutions/`
  (9 Pareto netlists + CSV, **not committed yet**); SAC baseline (Brent, student server, 1 seed): 0.662
- ⬜ 3.R report section (material §3) · ⬜ optional: SAC on 2 more seeds

**Milestone 4: LLM agentic harness** (PDF §4), on `feat/m4-harness`
- ✅ 4.1 template committed as given · ✅ 4.2 `sizing_tools.py` (7 TODOs, history CSV) + `test_sizing_tools.py` (23)
- ✅ 4.3 `mcp_server.py`: `reason` argument + `test_mcp_server.py` (stdio)
- ✅ 4.4 harness files: `AGENTS.md`, 4 subagents, 3 skills, MCP config, design log, session prompt + `test_harness_files.py`
- ✅ 4.5 agy on the VM (DNS allowlist, login, permissions: see the log entry)
- ✅ 4.6 one complete session (Gemini 3.8 Flash): 16 simulations, FoM 0.684; `harness_vs_rl.py` + `harness_vs_rl.png`
- ⬜ 4.R report section (material §4) · ⬜ optional: a 2nd session (another model) / a session that uses RL
- ⬜ optional (PDF appendix): cheap DC operating-point tool; PVT robustness

**Submission:**
- ⬜ report ≤ 10 pages
- ⬜ `Solutions/` (decide: commit it; make its netlists portable, see the open decisions)
- ⬜ archive `[student number] [last name] G[group number].zip` with the report, the project directory and `Solutions/`
- ⬜ PRs `feat/td3` and `feat/m4-harness` → `main` (conflicts with Lukas's `07d2e87` in `agent.py`/`td3_runner.py`)

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
- **`Solutions/` netlists are not portable:** their `wrdata` lines contain the absolute path of the machine that
  simulated them (for our Pareto netlists a `/tmp/…/lane_a/…` scratch folder, which no longer exists). The circuit is
  correct; only the output paths would fail elsewhere. Fix idea: `final_results.py` rewrites `…/CAD/no_backup/` to the
  relative `no_backup/` when copying. Not done (a change to a deliverable: Brent decides). Then commit `Solutions/`?
- **Harness prompt tweaks after the session** (proposed, not done, so the report describes the harness as it ran):
  a "no shell commands" rule; a lower budget (~40 simulations, 3 designer rounds); `k = 3` in the designer prompt;
  `model: flash` for the designer and the RL operator.
- **Merging to `main`:** `feat/td3` and `feat/m4-harness` are unpushed; Lukas's `07d2e87` on `main` filled in the same
  TODOs (`agent.py`: algorithmically identical; keep his one-line `select_action` step 1 + our comments;
  `td3_runner.py`: keep our fixes).
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

### 2026-11-05 17:15 — 3.6: TD3 timing rerun (`T_final_timing_s123456`): invalid timing, a reproducibility lesson
**Goal:** a clean (solo) TD3 runtime for the harness comparison: the tuning runs ran two at a time.

**What happened:**
- Same code, same settings, seed 123456, in `~/td3_lanes/lane_a`.
- Identical to `B_pilr_w_s123456` up to sim 625. At sim 626 this run hit the 20 s simulation timeout and the tuning
  run didn't. Cause (Brent): the laptop was closed, the VM paused, the clock jumped.
- From that one difference (−6 instead of −3.92) the trajectory diverges; this run's best is 0.683 (vs 0.702).
- It took 20.8 min, but that includes the pause and an `agy` session sharing the CPU, so **the timing is invalid**. The
  TD3 runtimes in the report are the tuning runs' (`B_pilr_w_*`, ~17 min, two runs in parallel on 2 cores: somewhat
  pessimistic).

**Lessons:**
- A seeded run is exactly reproducible only while the same simulations hit the wall-clock timeout. The seeding itself
  is proven by `test_runner.py` (fake simulator).
- Don't close the laptop during runs.

The run is kept in `CAD/runs/T_final_timing_s123456`.

### 2026-11-05 17:00–17:50 — 4.5: Antigravity CLI (`agy` 1.5.1) on the VM: what was needed
**Goal:** run the harness in agy on Brent's VM (agy has a `linux_arm64` build; the SAC server isn't needed for it).

**Problems and fixes:**
- **Model unreachable (`dial tcp 0.0.0.0:443`):** the VM has a DNS allowlist (dnsmasq, `/etc/dnsmasq.d/allowlist.conf`,
  `address=/#/0.0.0.0`), which only listed `antigravity.google`.
  - agy needs `daily-cloudcode-pa.googleapis.com` (the model), `aicode.googleapis.com`, `www.googleapis.com` and
    `play.googleapis.com`.
  - Brent added `server=/googleapis.com/192.168.64.1` and restarted dnsmasq (it only reads its config at start).
  - Why it worked at first: the catch-all only blocks IPv4 (A) answers. IPv6 answers passed, and the VM had IPv6 via
    the Mac's network until the laptop slept.
- **`/mcp` empty:**
  - after the network problems the stored login was rejected (`401 UNAUTHENTICATED`), and agy only loads MCP servers
    once logged in → fixed with `/logout` and signing in again;
  - `agy mcp list` saying "No MCP servers configured" is normal: it only lists `agy mcp add` registrations. Our
    workspace file `CAD/.agents/mcp_config.json` is picked up when agy starts in `CAD/`; agy cached the 4 tools
    including `reason` in `~/.gemini/antigravity-cli/mcp/cad/`.
- **Permission prompts:** `CallMcpTool`, `RunCommand`, `EditFile`.
  - The session stopped once because a permission request waited too long.
  - Recommended: "always allow" (project scope) for the `cad` tools and for editing the design log; shell commands
    stay on "ask".
  - The two shell commands it asked for were harmless `ls` calls on its own config.
  - Not: `--dangerously-skip-permissions` or `command(*)`.
- **Quota:** each subagent is its own model conversation, and tool results fill the context, so a session costs a lot
  of tokens (Gemini and Claude/GPT have separate weekly limits, `/usage`). No automatic model fallback was found;
  switching with `/model` mid-session is fine, because the memory is the design log.

### 2026-11-05 17:28–17:56 — 4.6: the harness session (Gemini 3.8 Flash): 16 simulations, FoM 0.684
**Goal:** one complete session: analyst → designer rounds → (RL if stuck) → reviewer.

**What happened** (`CAD/harness/design_log.md`, entries 1–7):
- **The analyst** (0 sims): PM is the bottleneck with CL = 10 pF → an LHP zero via Rc; a hand design (Cc 1 pF, the
  mirror balance S_p3/S_p1 = 2·S5/S4, L = 90 nm).
- **Designer round 1** (10 sims):
  - UGBW 40.6 MHz → Cc 0.3 pF, Rc 9.8 kΩ, a balanced current increase → all specs met at sim 10, FoM 0.565;
  - it calibrated itself on the way: "gm scales with current, not W (moderate inversion)", "L = 45 nm kills gain
    (DIBL)", "breaking the balance crushed gain to 39 V/V".
- **The orchestrator:** "not stuck, RL is not needed" → round 2 for current.
- **The interruption:** round 2 waited for a permission and was cancelled, and the login expired. After re-login the
  session continued from the design log; a new MCP server meant a new experiment, so the best design was passed in
  again (and re-simulated).
- **Designer round 2** (6 sims): mn3 3 → 4 scales both currents by 0.75 → 211.5 µA, **FoM 0.684** (PM 60.6°,
  UGBW 100.7 MHz).
- **The reviewer:** margins (UGBW +0.7 %, PM +1.05 %: risks), 2 Pareto-optimal designs, the 3 key decisions, 16 sims,
  0 RL.

**Analysis:**
- `analysis/harness_vs_rl.py` now joins the server runs of one session (the next run's clock and call numbers
  continue after the previous run's last simulation, so the pause is excluded), plus a test.
- Two panels: against runtime, and against the number of simulations (log).
- Fixed colours per run, never cycled (the harness and one TD3 seed had shared the blue).

| reached | LLM harness | TD3 s123456 | TD3 s1 | TD3 s2 |
|---|---|---|---|---|
| first design meeting all specs | 10.5 min / 10 sims | 5.5 min / 1072 | 5.3 min / 1225 | 8.5 min / 1956 |
| FoM ≥ 0.684 | 13.4 min / 12 sims | 13.3 min / 3724 | never | never |

The harness is ~300× more simulation-efficient and comparable in wall-clock time (its runtime is LLM reasoning; the
first simulation comes after 6.3 min of analysis).

**Frozen copy:** `CAD/harness/sessions/2026-11-05_gemini-3.8-flash/` (both history parts, the 6 feasible netlists,
`final_design.cir`, a README), because `runs/` is git-ignored.

### 2026-11-05 18:15 — tidy-up: report material, work log
- New `docs/report/report_material.md`: per PDF section (M1–M4, "What to report"), with ready-to-use facts, tables,
  numbers, the explainability examples and the honest caveats, plus a page budget.
- Figures copied to `docs/report/figures/`: `final_max_fom.png`, `final_pareto.png`, `fom_evolution_A.png`,
  `harness_vs_rl.png` (plus the existing `sr_methods.png`).
- The Status at the top rewritten to the current state; new open decisions: the non-portable `wrdata` paths in the
  `Solutions/` netlists, the proposed harness prompt tweaks (not done, so the report describes the harness as it
  ran), the merge to `main`.
- Note: `docs/worklog_detailed_2026-11-05.md` is an older private snapshot (milestones 1–2); this work log is complete.

### 2026-11-06 11:20 — 4.7: test run: Claude Code plays the harness (no agy tokens); token measurement
**Goal:** Brent: run the whole harness workflow without agy and report the token usage.

**How:** Claude Code played the orchestrator and the 4 subagents as written in `AGENTS.md` and `.agents/agents/`.
It called the real backend through a persistent driver (scratchpad) that behaves like the MCP server and logs the
bytes of every tool request and result. Seed 123456. **Not an independent replicate** (the operator had seen the agy
log). Record: `CAD/harness/sessions/2026-11-06_claude-code-test/` (README with the compact log, the history, the sizes).

**Result:**
- **10 `simulate` calls** (+1 off-grid request rejected by the validation) → FoM **0.660** (215 µA, 864 µm², PM 65.9°,
  UGBW 101.8 MHz). All specs were met at sim 4 (FoM 0.638).
- vs agy: a slightly lower FoM (0.684) but 10 instead of 16 sims and a PM margin of 5.9° instead of 0.6°.
- Model insights in the log:
  - UGBW ∝ I_tail;
  - Cc mainly sets PM;
  - Rc and gm6 set UGBW through the LHP zero;
  - **the dominant area item is Rc (9.8 kΩ ≈ 700 µm²), not Cc**, which corrects the agy reviewer.
- **The RL path, first test inside the harness, a labelled demonstration:** warmup 200 + train 2 × 150 = 550 sims, 0
  designs meeting all specs (best −0.187). This confirms "RL not needed" and the stage-C finding (TD3 with the
  template's short-warm-up settings is weak).

**Tokens** (an agy estimate: the measured tool traffic plus a turn model where every turn rereads its agent's context;
agy's own system prompt and tool schemas are not included):
- ≈ 248k input + 13k output tokens;
- the orchestrator ≈ 115k input: many turns rereading its growing context;
- `AGENTS.md` reread in ~30 turns ≈ 47k;
- tool results 50 kB (`get_status(20)` 20 kB, `warmup`/`train` 5.5 kB, `simulate` ~0.95 kB).

Claude Code's own usage can't be read from inside the session, and isn't comparable: every call rereads this very long
conversation.

### 2026-11-06 — 4.8: token savings (Brent's choice: leaner tool results, leaner log entries, circuit details into the skill)
**Not done, on purpose (Brent):** relaxing the one-change rule; a batch/sweep tool (explainability first).

**What changed:**
- `CAD/sizing_tools.py`:
  - a new `compact(candidate, units)` makes the copy the LLM reads: parameters to 6 significant digits
    (`1.4999999999999998e-06` → `1.5e-06`; the validation accepts them back), specs and normalized specs to 4, the
    reward to 4 decimals;
  - `simulate` returns the compact copy (with `spec_units`, as the template asks);
  - `get_status` lists `spec_units` once instead of in every candidate, and drops the static targets/constraint lists
    (they are in `AGENTS.md`);
  - `warmup`/`train` include the top 3 instead of 5;
  - the history CSV and the candidate store keep full precision.
- `AGENTS.md`: the device table and the allowed values moved to the skill `two-stage-opamp-design` (which the analyst
  and the designer load); a 4-line circuit summary stays. Subagent summaries ≤ 150 words (was 300); designs as changes
  relative to the previous best, all 20 values only for a new best.
- The agents' output sections: ≤ 150 words (reviewer ≤ 200 + its tables); the designer refers to simulation numbers
  instead of listing every simulation (the history has every reason); the RL operator gives the top 3.
- `design-log` skill: entries ≤ 150 words, no separate "Goal", changes + simulation numbers instead of repeating
  reasons.
- **A factual correction:** the designer prompt and the skill called Cc "the largest single area item". By the
  area formula, Rc is (9.8 kΩ ≈ 700 µm² vs 0.3 pF ≈ 100 µm²); this misled the agy reviewer. Fixed; this is arithmetic
  from the area formula, not a session result, so the prompts stay free of results.
- Tests: `test_sizing_tools.py` +1 (compact results, full-precision history), `test_mcp_server.py` adapted; all 130
  pass.

**Effect** (measured on the test run's tool traffic + the same turn model):
- tool results 50.3 kB → 31.3 kB (−38 %);
- the whole session ≈ 254k → 220k input tokens (−13 %) and 13k → 10k output tokens (−21 %).

The fixed context per designer turn still dominates (`AGENTS.md` + `designer.md` + the skill ≈ 13 kB), and so does
the orchestrator's number of turns (≈ 100k of the 220k). Next lever, within Brent's constraints: the orchestrator
writes its routing decision in the same log entry as the subagent's summary (about half its turns). Not done.

**Note for the report:** the agy session of 5 Nov ran with the previous version (300-word summaries, Cc called the
largest area item).


### 2026-11-06 — merge of `main` (Lukas's milestone 3, `07d2e87` + `ae39174`); pushed as `einstein_LLM`
**Goal:** Brent: start from Lukas's version on `main` and add only our necessary changes.

**What Lukas pushed (`ae39174` "milestone 3 k version"):**
- `td3_runner.py`: actor lr 3e-4, critic lr 1e-3 (batch 64, w 200 unchanged); a hard-coded `env.counter < 5000` in
  the outer training loop; the correct variable names in `train_policy`;
- `circuit_env.py`: `self.episode += 1` removed from `reset()`;
- new `analysis/best_design.py`.

**How it was merged (Brent's decisions):**
1. Brent's uncommitted comments in `agent.py` stashed (`stash@{0}`, not needed).
2. On `feat/td3`: `git merge origin/main` (`20e2b4b`):
   - `agent.py` = Lukas's (algorithmically identical to ours; our 11 agent tests pass on it);
   - `circuit_env.py` = Lukas's, the episode counter stays removed (Brent);
   - `td3_runner.py` = **Lukas's file and his defaults**, plus our additions:
     - `--max_sims` (default 5000), checked in all 4 loops, so exactly 5000 (his check gave 5005 and didn't cover
       the warm-up);
     - seeding of `env.np_random` and `env.action_space` (same seed = same run);
     - the run folder with the YAML and `hyperparameters.json`;
     - `env.finalize()` and saving the networks;
     - the progress lines;
   - his `train_policy` names kept.
3. `feat/td3` merged into `feat/m4-harness` (`afae1ae`, no conflicts): **130 tests pass**.

**Found and fixed on the way:** our runner's progress lines used `float('nan')` inside a single-quoted f-string, which
is a SyntaxError before Python 3.12 (the student server has 3.9; the earlier `ast` check doesn't catch it). Now
`best = max(..., default=float("nan"))` first; a scan of `CAD/` finds no other such f-string.

**Consequences:**
- `python td3_runner.py` without options now uses Lukas's defaults. Our final runs `B_pilr_w_*` need
  `--batch_size 128 --w 1000 --pi_lr 1e-4` (report material updated).
- The episode column of `designs.csv` is now 0 in every row (nothing reads it).

**Pushed:** branch `einstein_LLM` = `feat/m4-harness` (milestones 3 + 4 on top of `main`).

### 2026-11-06 12:20 — 4.H1: harness v2, the backend: `hybrid_tools.py` (LLM designs warm-start the RL)
**Goal:** Brent: redo the harness for minimal tokens, with the LLM's simulations combined with short RL bursts.
Plan: `~/.claude/plans/streamed-sauteeing-moonbeam.md`. Branch `feat/m4-hybrid` from `einstein_LLM`.

**Brent's choices:**
- warm-start + local RL;
- 3 agents + a thin orchestrator;
- a new file (`sizing_tools.py`/`mcp_server.py` untouched);
- the total budget is 100–200 simulations, so ~30-simulation RL bursts alternating with a few LLM simulations.

**What changed:** new `CAD/hybrid_tools.py`, `HybridExperiment(SizingExperiment)`.
- **`to_action(params)`:** the exact inverse of `action_refine` (grid index k ↦ a = min((2k+1)/(n−1) − 1, 1); all 432
  grid points checked). `state_of(candidate)` = its normalized specs in the env order.
- **`simulate(parameters | changes, base, reason)`:**
  - a full design, or only the changes relative to the best or to an earlier simulation (fewer output tokens);
  - every successful simulation is **pushed as a TD3 transition** (s = the base design's state, a = `to_action`,
    r = its FoM, s′ = its state);
  - failed simulations are not pushed.
- **`rl_explore(n ≤ 60, reason)`, one burst:**
  - the **actor is warm-started** (200 Adam steps on MSE(actor(s), a_best), then actor → target actor) whenever the
    best design changed;
  - every **episode starts at the current best design** (no reset simulation);
  - n steps = n simulations, each with one TD3 update;
  - there's **no random warm-up**: `ReplayBuffer.sample` draws with replacement, so the template's batch size of 100
    works from the first step;
  - the template hyperparameters are unchanged;
  - it reports what RL changed relative to the previous best (~550 bytes).
- **`log_entry(agent, text)`:** the server appends a numbered entry (≤ 1200 characters) to `harness/design_log.md`,
  so the orchestrator never writes files.
- New `CAD/tests/test_hybrid_tools.py` (14 tests): the inverse on all grids, simulate by changes / base / invalid
  calls / first design in full, one transition per simulation (its action maps back, reward, next state), failed →
  none, burst bounds, a burst = n sims/transitions/updates with < batch_size transitions and no reset, episodes start
  at the best, the warm start (the actor moves to a_best, only once per best, target copied), the log.

**Verification:**
- Mutation check: 4 deliberate bugs (no push, a wrong inverse, a wrong episode start, no target copy) are each caught.
- Real ngspice: TA reference 1 matches (reward −0.2533 vs TA −0.2528); a change works; **a 20-simulation burst from
  that design found 3 improvements, the best +0.309** (from −0.253). The smoke run's folders were removed.
- All 144 tests pass.

### 2026-11-06 12:30 — 4.H2: harness v2, the MCP server `hybrid_mcp_server.py`
**What changed:**
- New `CAD/hybrid_mcp_server.py`: the structure of the template server (one `HybridExperiment` per process, the lock,
  the stdout redirect, `ToolError`), with 4 tools:
  - `simulate(parameters | changes, base, reason)`;
  - `rl_explore(n_steps, reason)`;
  - `get_status(k = 3)`;
  - `log_entry(agent, text)`.
- **Short tool descriptions:** the model gets them on every turn. Together 1.5 kB (`simulate` 723 B, `rl_explore`
  383 B, `log_entry` 256 B, `get_status` 182 B).
- Type hints with `Optional`/`Union` (no `X | None`, which breaks on Python 3.9).
- New `CAD/tests/test_hybrid_mcp_server.py` (over stdio):
  - the 4 tools are listed;
  - the descriptions and schemas are < 3000 B (a token-budget check);
  - `get_status` answers;
  - `rl_explore` before any design gives a readable error.
- `mcp_server.py` (the template) is unchanged.

### 2026-11-06 12:45 — 4.H3: harness v2, the harness files from scratch (lean)
**What changed:**
- **Removed:** the v1 `AGENTS.md`, the 4 v1 agents, the 3 v1 skills. The v1 design log moved to
  `harness/sessions/2026-11-05_gemini-3.8-flash/design_log.md` (next to that session's history).
- **New `CAD/AGENTS.md` (2.3 kB, v1 6.3 kB):**
  - the goal with the **budget of 100–200 simulations**;
  - the spec table, the FoM in 3 lines, the 4 tools;
  - **the fixed pipeline:** designer A+B (≤ 10 sims) → cycles of [`rl-explorer`, one burst of ~30 sims → designer
    phase C, explain RL's change + 2–4 sims] until ~150 sims or 2 cycles without improvement → `reviewer`;
  - the orchestrator passes only the phase, the count and the previous return;
  - the rules: a reason on every call, one change per simulation, numbers from tools, one `log_entry` per step,
    returns ≤ 80 words.
- **New agents** (`.agents/agents/`):
  - `designer` (1.3 kB): A+B analysis/hand design/refinement; C: explain RL's `changes_vs_previous_best` in circuit
    terms, then 2–4 reasoned changes;
  - `rl-explorer` (0.75 kB): one burst, its size as a judgment (30; 20 after a burst without improvement; fewer near
    the budget);
  - `reviewer` (0.8 kB): margins, Pareto, the 3 key decisions (LLM or RL), the cost.
- **New skills:**
  - `opamp-design` (3.2 kB): v1's circuit map, allowed values, equations and knobs, trimmed; incl. the area
    correction (Rc dominates);
  - `hybrid-rl` (1.5 kB): how the tool learns from every design, starts at the best, explores σ 0.1 ≈ ±5 % of each
    range (W and L rarely move), the cost, the report, the burst sizing.
- `.agents/mcp_config.json` → `hybrid_mcp_server.py`; `harness/session_prompt.md` (3 lines); `harness/README.md`; a
  fresh `harness/design_log.md`.
- `tests/test_harness_files.py` rewritten (5 tests):
  - **size budgets** (`AGENTS.md` ≤ 3.5 kB, agents ≤ 2 kB, skills ≤ 4.5 kB);
  - frontmatter; the agents name only real MCP tools;
  - `AGENTS.md` names every agent/skill/tool;
  - the config.

**Fixed context:** 9.9 kB in total (v1 ≈ 22 kB). All tests pass.

### 2026-11-06 12:50 — 4.H4: harness v2 test run (Claude Code plays the agents) + an RL diagnostic
**Record:** `CAD/harness/sessions/2026-11-06_claude-code-hybrid/` (README with the full table, the design log
written via `log_entry`, the history, the sizes).

**Result:**
- 97 simulations: 7 by the designer, 90 in 4 RL bursts. All specs met at **sim 2**. Final **FoM 0.677** (sim 56:
  215 µA, 831 µm², PM 60.3°, UGBW 104.3 MHz).
- The final design came entirely from the designer's 7 simulations. **The RL bursts found 0 improvements** (5 RL
  designs met all specs, best 0.607).
- **Tokens:** ≈ 126k input + 8.5k output, vs ≈ 244k for v1 (**−48 %**), despite 53 turns. The orchestrator ≈ 28k (v1
  ≈ 100k), thanks to the small `AGENTS.md`, the 1.5 kB tool descriptions (v1 2.5 kB) and the log via the tool.

**Diagnostic** (the same seeded buffer, one 30-step burst, 2 seeds, only the exploration noise varied; not part of
the harness): σ 0.1 / 0.05 / 0.02 → improvements 0 / 0 / 0. RL designs meeting all specs: 3 % / 10–20 % / 20 %.
Median RL reward −1.1 / −0.7 / −0.3.

**Three causes:**
1. The template noise moves all 20 parameters at once (~5 % of each range), which breaks the mirror balance.
2. The actor drifts from the warm-started design with every TD3 update of a still-untrained critic (even at σ 0.02).
3. The converged best design sits on the PM boundary (+0.3°).

**For Brent to decide** (none done):
- stop the cycles after the first burst without improvement (fewer tokens and simulations);
- the bursts earlier, before the designer converges, where RL has room;
- a smaller exploration noise for the bursts only (our tool's parameter; σ 0.02 made 7× more RL designs feasible, but
  not better);
- no actor updates during the first bursts, to avoid the drift (deviates from TD3's delayed updates);
- or keep it, and report honestly that around a converged, constraint-bound design the RL adds nothing.

### 2026-11-06 12:50 — 4.T0: harness v3 (the LLM as the RL's tutor): feasibility check
**Goal:** Brent: v2 still uses too many tokens. The LLM shouldn't design everything itself (the RL's rival) but tutor
the RL: give it a very good environment and warm-up. Plan: `~/.claude/plans/streamed-sauteeing-moonbeam.md` (v3).
Branch `feat/m4-tutor` from `feat/m4-hybrid`. Brent's choices:
- the tutor sets the search space and the warm-up;
- one plan call;
- 2 agents (tutor + reviewer) + a thin orchestrator.

**Change:** `hybrid_tools.to_action` gives action 0 for a fixed parameter (1 grid point), which used to be a division
by zero.

**T0, Python only, no LLM:**
- the nominal = v2's sim-3 design (FoM 0.622);
- the RL grid narrowed: 6 free parameters with ~11 grid points (mn1, mp3, mn4, mn5 ±5 fingers; Cc 0.1–0.9 pF;
  Rc 8.8–9.8 kΩ), 14 fixed (all W and L, mp1, mn3);
- 15 warm-up designs (±1 step of each free parameter + 3 coupled moves);
- then 120 RL simulations (2 × 60), 2 seeds.

| | v2 (full space) | T0 seed 1 | T0 seed 2 |
|---|---|---|---|
| RL designs better than the warm-up best | 0 | 7 | 8 |
| RL designs meeting all specs | 3 % | 48 % | 72 % |
| median RL reward | −1.1 | +0.01 | +0.52 |
| best FoM (nominal 0.622 → warm-up 0.644 →) | – | 0.658 | 0.664 |

All RL designs stayed inside the space.

**Conclusion:** in a tutor-narrowed space the RL works as a local optimizer. Still below the LLM-only best (0.677 /
0.684) after 136 simulations, partly from the weaker nominal. Continue with T1–T4.

**A design rule for the tutor (into the skill):** with σ 0.1 the chance that a free parameter moves ≥ 1 grid step per
step depends on its number of grid points in the range: 5 points ≈ 1 % (practically frozen), 11 points ≈ 32 %,
21 points ≈ 62 %. The tutor controls the exploration through the number of grid points, not the physical width.

### 2026-11-06 13:00 — 4.T1: harness v3, the backend `tutor_tools.py`
**What changed:** new `CAD/tutor_tools.py`, `TutorExperiment(HybridExperiment)`.
- **`setup_rl(nominal, search_space, warmup, reason)`**, once per session:
  1. validates the nominal on the full grid;
  2. **narrows only the RL env's grid**: a free parameter keeps its grid between [low, high] (both on the YAML grid,
     low ≤ nominal ≤ high, ≥ 2 points); every other parameter is fixed at the nominal (1 grid point);
     `action_refine` is unchanged and maps [−1, 1] onto the small ranges;
  3. checks every warm-up design (`changes` relative to the nominal) against that grid **before** simulating
     (outside the space, or changing a fixed parameter → refused, the grid restored);
  4. simulates the nominal and the warm-up designs through `HybridExperiment.simulate`, so each becomes a TD3
     transition and its `purpose` is stored as the reason;
  5. returns the compact sensitivity table: per design the changes, reward, met, the Δ % of gain/UGBW/PM/SR/
     current/area; plus the free ranges with their number of grid points.
  
  A failed nominal restores the full grid.
- **`run_rl(n ≤ 200)`:** TD3 alone, in `rl_explore` bursts of ≤ 60 (the warm start on the current best, episodes from
  there). It reports the start reward, the running best at 25/50/100 %, the number of improvements, which parameters
  the improving designs moved, and the best design as changes relative to the nominal.
- New `CAD/tests/test_tutor_tools.py` (11 tests):
  - only the RL grid narrows; every RL action stays inside the space; the round trip in the narrowed grid;
  - nominal + warm-up simulated and pushed, the table fields, the purposes stored;
  - 6 invalid setups refused without simulating (nominal outside, off-grid bound, unknown name, warm-up outside,
    warm-up on a fixed parameter, too many);
  - once per session; a failed nominal restores the grid;
  - `run_rl` needs setup and is bounded; 70 = 60 + 10 simulations, all inside the space, the report consistent.

**Verification:**
- Mutation check: 3 deliberate bugs (fixed parameters not fixed, the grid not restored, only one burst) are each
  caught.
- Real ngspice: the T0 plan with 8 warm-up designs → a 1.6 kB table; `run_rl(30)` → a 420 B report, 1 improvement
  (Rc 9.8 → 9.7 kΩ). All 156 tests pass.

### 2026-11-06 13:05 — 4.T2: harness v3, the MCP server `tutor_mcp_server.py`
- New `CAD/tutor_mcp_server.py`: the template server's structure, with 4 tools: `setup_rl(nominal, search_space,
  warmup, reason)` (a warm-up item = a small pydantic model `WarmupDesign(changes, purpose)`), `run_rl(n_sims,
  reason)`, `get_status(k = 3)`, `log_entry(agent, text)`.
- There's no `simulate`: the tutor doesn't design step by step.
- The descriptions and schemas are 1.7 kB together (`setup_rl` 968 B).
- New `CAD/tests/test_tutor_mcp_server.py` (stdio):
  - the 4 tools; < 2500 B;
  - `get_status` answers;
  - `run_rl` before setup → a readable error;
  - an incomplete nominal → a readable error.

### 2026-11-06 13:10 — 4.T3: harness v3, the harness files from scratch
**What changed:**
- **Removed:** the v2 `AGENTS.md`, `designer`/`rl-explorer`/`reviewer`, the `hybrid-rl` skill. Kept the
  `opamp-design` skill. The v2 server files stay as the record of v2.
- **`CAD/AGENTS.md` (1.5 kB):**
  - the goal: the LLM sets up the RL's job, TD3 optimizes; within 100–200 simulations;
  - the specs; the FoM; the 4 tools;
  - **the pipeline: the main agent calls `tutor`, then `reviewer`, nothing else**;
  - the rules: a purpose per warm-up design, numbers from tools, one `log_entry` + ≤ 80 words per agent.
- **`.agents/agents/tutor.md` (1.1 kB):** a nominal from the equations, a search space (~11 grid points per free
  parameter, the rest fixed, and why), 10–20 warm-up designs with purposes, `setup_rl` once, read the table,
  `run_rl` with the rest (100–150), one log entry.
- **`.agents/agents/reviewer.md` (0.8 kB):** `get_status(5)` + the tutor's entry; the final design vs the nominal,
  the margins, why the RL's changes work (from the tutor's sensitivities), Pareto, the cost.
- **New skill `rl-tutoring` (1.7 kB):** what the RL does with the space and the warm-up; **the grid-point rule**
  (5 points ≈ 1 % chance of a move per step, 11 ≈ 30 %, 21 ≈ 60 %); what to free (mn4, mn5, mp3, mn1, Cc, Rc) and
  what to fix (all L, mn3, usually the W's), and why; a good warm-up; the budget split.
- `.agents/mcp_config.json` → `tutor_mcp_server.py`; `harness/session_prompt.md` (2 lines), `harness/README.md`, a
  fresh `harness/design_log.md`.
- `tests/test_harness_files.py` for v3: the 2 agents, the 2 skills, the 4 tools, the size budgets (`AGENTS.md`
  ≤ 2 kB, agents ≤ 1.5 kB, skills ≤ 3.5 kB), the config.

**Fixed context:** 8.3 kB (v2 9.9 kB, v1 ≈ 22 kB). All 157 tests pass.

### 2026-11-06 13:20 — 4.T4: harness v3 test run (Claude Code plays tutor + reviewer); tokens
**Record:** `CAD/harness/sessions/2026-11-06_claude-code-tutor/` (README with all the tables, the design log, the
history, the sizes).

**The session: 5 tool calls, 146 simulations.**
- **The tutor started from the failing first hand design** (UGBW 67 MHz, FoM −0.17).
- **Space:** 6 free parameters (mn4, mn5, mp3, mn1, Cc, Rc, 9–11 grid points each), 14 fixed.
- **Warm-up:** 15 designs. The table shows mn4 as the lever (+1 finger: UGBW +24 %) and that Cc moves PM; the
  balanced coupled moves meet all specs (0.606).
- **`run_rl(130)`: 0.606 → 0.650** (6 improvements), all by the RL.
- **Final:** FoM 0.649, 223 µA, 850 µm², PM +9 %, UGBW +5.4 %. 88 of 118 distinct designs met all specs.

**Tokens** (the same turn model):
- **≈ 30k input + 2.5k output, 13 turns**: −88 % vs v1 (≈ 244k), −76 % vs v2 (≈ 126k);
- tutor 18k, reviewer 8k, orchestrator 3.4k.

**Trade-off:** fewer tokens, the RL really optimizes and finds many feasible designs (a rich Pareto set). But the
best FoM (0.650, 146 sims) is a little below the LLM-only results (0.677 in 7 sims, 0.684 in 16 sims), and it needs
more simulations.

### 2026-11-06 13:25 — 4.T5: report material for v3
`docs/report/report_material.md` §4, new subsection "Version 3: the LLM as the RL's tutor": why, what changed (the
grid-point rule), the test run, a comparison table of v1/v2/v3 (tokens, simulations, best FoM, who found it), and the
honest reading. Test table: 157 tests.

### 2026-11-06 13:45 — 4.T6: harness v3.1: two RL runs with an educated LLM improvement in between, < 200 sims
**Goal:** Brent: the tutor calls `run_rl` twice, with an educated LLM improvement in between; strictly fewer than 200
simulations in total.

**What changed:**
- `CAD/tutor_tools.py`:
  - **`MAX_TOTAL_SIMS = 199`, enforced:** `setup_rl`, `refine` and `run_rl` refuse a call that would go over it, and
    give the remaining count; `run_rl` reports `simulations_left`;
  - **new `refine(designs, search_space = None, reason)`**: 1–5 reasoned designs relative to the best at the start of
    the call, each with a purpose, simulated and pushed as TD3 experience. With a `search_space`:
    - the RL grid is re-narrowed around the current best (one helper `_narrow` for setup and refine);
    - the **replay buffer is rebuilt**: the transitions whose design lies in the new space are kept, with their
      action re-encoded for the new grid; outside designs are dropped;
    - the next burst warm-starts again;
  - factored helpers: `_check_designs` (everything checked before simulating), `_simulate_table`, `_free_ranges`,
    `_call_of`.
- `CAD/hybrid_tools.py`: every push goes through `_push(…, params)`, which also stores the design in
  `buffer_designs` (aligned with the buffer), so the actions can be re-encoded.
- `CAD/tutor_mcp_server.py`: a 5th tool `refine`; the descriptions are 2.6 kB in total.
- `AGENTS.md`: < 200 simulations (enforced); the 5 tools. `tutor.md`: setup → `run_rl` (~80) → `refine` (2–5
  designs, maybe a new space) → `run_rl` (`simulations_left`) → log (1.49 kB, within its 1.5 kB budget).
  `rl-tutoring`: what to do in `refine` (balanced coupled moves, when to re-centre/fix/widen) and the budget split.
- Tests:
  - `test_tutor_tools.py` +4:
    - `refine` relative to the best (1 simulation + 1 transition, the other parameters unchanged, the purpose
      stored);
    - the limits (needs setup, 1–5 designs, a fixed parameter refused) without simulating;
    - a new space: the grid re-centred and fixed parameters, every buffer action maps back to its design in the new
      grid, outside designs dropped, the warm start forced, the next run moves only the new free parameters;
    - **the budget**: 9 + 150 → a 41-simulation `run_rl` refused ("40 simulations left") → refine + 39 = 199 → any
      further call refused ("0 left").
  - `test_tutor_mcp_server.py`: 5 tools, < 3000 B.
  - All 161 pass.

**Verification:** the mutation check (no buffer rebuild, no budget in `run_rl`, no forced warm start): each is caught.

### 2026-11-06 14:05 — 4.T7: harness v3.1 test run (Claude Code as tutor + reviewer)
**Record:** `CAD/harness/sessions/2026-11-06_claude-code-tutor2/`. The `setup_rl` is byte for byte the v3 run's.

**Result:**
- **199 simulations** (the budget, enforced), 7 tool calls.
- `setup_rl` → 0.606; `run_rl(80)` → 0.646.
- **`refine` → 0.686**: Cc 0.3 pF + an I2 cut (mn5 10, mp3 12). The cut alone fails UGBW and Cc's UGBW gain makes it
  pass: a coupled move the RL hadn't found. The space was re-centred (mp3/mn4 at their range edges); 87 transitions
  were kept.
- `run_rl(98)` → no improvement (the design sits on the PM 60.04° and UGBW 101.3 MHz limits).
- Final: 213 µA, 822 µm²; 124 of 177 designs met all specs.

**Tokens:** ≈ 46k input + 2.9k output, 15 turns (v3 ≈ 30k; v2 ≈ 126k; v1 ≈ 244k).

**Comparison:** v3.1 gives the **best FoM of all versions** (0.686 vs v1's 0.684, v2's 0.677, v3's 0.650) at ~1/5 of
v1's tokens. The deciding step was the LLM's educated improvement between the RL runs. The RL's own share: 0.606 →
0.646 in run 1, nothing in run 2 (the design was constraint-bound).

### 2026-11-06 14:20 — 4.T8: harness v3.2 (final): one RL run, then refine, then the end
**Goal:** Brent: the second RL run didn't help, so remove it; after `refine` the session ends (fewer tokens and
simulations).

**What changed:**
- `tutor.md`: the steps are now:
  1. the circuit in 2–3 sentences + the nominal;
  2. the space;
  3. the warm-up;
  4. `setup_rl`;
  5. **the tutor's judgment** on the RL size (typically 60–100) → one `run_rl`;
  6. `refine` (2–5 designs) → stop;
  7. the log.
  
  Steps 1 and 5 also cover two phrases of the PDF: "explain its functionality" and "run the RL-based sizer … based
  on its own judgment".
- `AGENTS.md`, `rl-tutoring`: one RL run, then `refine`; the budget ≈ 80–120 (hard cap 199 unchanged). The sentence
  that named a concrete successful move from a test session was removed from the skill again (no results in the
  prompts).
- **Removed, because only the second RL run needed it:** `refine`'s optional re-centred `search_space`,
  `_rebuild_buffer`, `buffer_designs` and `_push` in `hybrid_tools.py`, the re-centring test. `refine` is now
  `refine(designs, reason)`.
- The tool descriptions are 2.4 kB.

**Result** (derived: v3.1's run has exactly this session as its first 101 simulations, deterministic): **FoM 0.686 in
101 simulations, ≈ 39k input tokens, 14 turns** (v3.1: 199 sims, ≈ 46k). All 160 tests pass.

### 2026-11-06 14:00 — 4.T9: the first real agy session of harness v3.2 (Claude Sonnet 4.6): no design met all specs
**Record:** `CAD/harness/sessions/2026-11-06_agy-claude-sonnet/` (README, the stream, both subagent transcripts, the
design log, the history). Failed attempts in `failed_attempts/`:
- interrupted;
- **the Gemini quota is exhausted** (resets in ~144 h, after the deadline);
- `--effort` isn't supported for `claude-sonnet-4-6`.

**Result:**
- 101 simulations, 249 s, but **no design met all specs**: best −0.68 (UGBW 38 MHz, PM 35°).
- The tutor anchored on the netlist's placeholder `.param` values: W fixed at 0.5 µm, Cc 2 pF against its own GBW
  estimate, Rc 1.5 kΩ.
- **It fenced the RL in:** Cc 1–3 pF, Rc 0.5–2 kΩ, which excludes the region where all specs are met (Cc 0.3–0.5 pF,
  Rc ≈ 9–10 kΩ).
- The RL and `refine` improved inside the fence (−0.89 → −0.77 → −0.68).
- The reviewer wrongly called the UGBW target "fundamentally unreachable".
- Start from scratch: checked, no earlier results were read.

**Tokens (agy's counts):**
- input 58.8k + cached 207.5k + output 13.2k (orchestrator 14.5k/41.1k/1.8k, tutor 29.7k/126.9k/9.9k, reviewer
  14.7k/39.6k/1.5k);
- the ≈ 39k estimate missed agy's own system prompt and tool definitions (≈ 10k per call).

**Lesson:** in v3 everything depends on the tutor's setup. A bad nominal and a fenced search space can't be repaired
by the RL. My own test runs were optimistic, because Claude Code played the tutor knowing the earlier sessions.

### 2026-11-06 14:25 — 4.T10: the prompt fixes after the first agy session + a disciplined test run
**Fixes** (`c60508e`, `372f6bb`; circuit knowledge, no results):
- `opamp-design`: "the netlist's `.param` values are placeholders; choose every value, the widths included";
- `tutor.md`: "check the nominal with your own equations; if a hard spec misses by > 2×, fix it" before `setup_rl`;
- `rl-tutoring`: "the space must contain what the equations demand: Cc ≤ gm1/(2π·100 MHz) (usually < 1 pF), Rc around
  (1 + CL/Cc)/gm6 (several kΩ)";
- `reviewer.md`: "if no design meets all specs: could the space have excluded the solution?".

**A process slip:** `c60508e` was committed while `test_harness_files` failed (`tutor.md` 1 byte over its budget); it
was fixed in `372f6bb`. Commits now happen only if pytest is green (checked in the commit command).

**Test run** (`CAD/harness/sessions/2026-11-06_claude-code-fresh/`; Claude Code played the agents following only the
prompt files, every value derived from the skill's equations; a disciplined replay, not an independent agent):
- the nominal from the equations misses only UGBW (87.8 MHz);
- the warm-up: mn4 +1 → all specs met (0.656);
- RL (80) → **0.669**;
- refine (5): no gain. The current cuts fail, because the sensitivities measured at the nominal (mn5 −1: −2.8 % UGBW)
  had shifted at the RL's best (−8.6 %);
- **101 simulations, FoM 0.669**, 21 of 92 designs met all specs.

**Lesson:** with the fixes, the tutor's equations alone (no knowledge of earlier results) lead to a nominal that
almost meets the specs. The RL does the last step. `refine` helps only if its move is still valid at the new design.

### 2026-11-06 — 4.v3.2: refine guided by the spec margins (no extra simulations)
**Goal:** Brent: make `refine` perform better without costing many runtime tokens; no simulation needed.

**What changed** (branch `feat/m4-tutor`, commit `c1cbc9f`):
- `CAD/tutor_tools.py`: `run_rl` returns two new fields, computed from numbers it already has:
  `best_margin_pct` (`_margins`) and `best_at_range_edge` (`_at_edge`). Lines: 116:            "best_margin_pct": self._margins(best["specs"]), 117:            "best_at_range_edge": self._at_edge(best["parameters"]), 177:    def _margins(self, specs): 186:    def _at_edge(self, parameters): 
- `CAD/tutor_mcp_server.py`: the `run_rl` description mentions the margins.
- `CAD/.agents/agents/tutor.md` step 6: "read `best_margin_pct` first: never spend a spec with < 3 % margin"
  (1485 B, budget 1500).
- `CAD/.agents/skills/rl-tutoring/SKILL.md` "After the RL run": the binding-spec rule; sensitivities measured at the
  nominal don't hold at the best, so mix single steps with coupled ones; the range edges.
- `tests/test_tutor_tools.py`: asserts for both fields.

**How it works:** a constrained optimiser (the RL) stops where a hard spec *just* passes: the optimum of
"minimise area + current subject to specs" lies on a constraint boundary. That spec is binding. Any refine move that
costs it fails the spec and drops the reward far below the best's. So the tutor must see which spec is binding.
Margin = (y − y*)/y* · 100 % (reversed for noise, an upper bound). A refine move must then either buy headroom on
the binding spec with another spec's margin (e.g. PM margin → Cc ↓ → GBW ≈ gm1/(2πCc) ↑) or leave it untouched.
`best_at_range_edge` lists the free parameters at the edge of the RL's range. `refine` is checked against that
grid, so a move past the edge would be refused, and a refused call costs a retry turn (tokens).

**Decisions:**
- First idea: a local sensitivity table (a linear fit on the RL's designs near the best). I tested it offline on the
  fresh run's history. It predicted −2 % UGBW for mp3 +1 / mn5 −1; the measurement was −8.6 % (the two interact
  through the mirror balance). It would not have helped, so it was not built.
- Diagnosis: the fresh run's best had a UGBW margin of only +0.3 % (100.3 MHz). All 3 current cuts failed UGBW;
  the 2 designs that didn't cut current stayed just below the best. The margins make that visible for ≈ 30 tokens.
- The prompt rule is general constrained-optimisation knowledge, not a session result.

**Verification:** 160 tests pass. Not simulated (Brent: not needed).

**For Brent to check:** the effect shows only in the next real agy session.

### 2026-11-06 — 4.v3.2: refine in two rounds (probe, then combine)
**Goal:** Brent: improve the tutor slightly, e.g. give it another simulation round of its own. The 1500 B limit on
`tutor.md` may be relaxed, but without a big step up in tokens. Brent tests it himself in agy.

**What changed** (branch `feat/m4-tutor`, commit `2dfd720`):
- `CAD/tutor_tools.py`: `MAX_REFINE_ROUNDS = 2` and the counter `self.refine_rounds`. A third call is refused;
  a refused call doesn't count as a round. `refine` also returns `best_after` (reward + `margin_pct` of the best
  after the round) and `rounds_left`. Lines: 23 33 66 67 74 77 81 82 
- `CAD/.agents/agents/tutor.md` step 6: round 1 = probe, 3–5 single steps at the best; round 2 = combine the
  helpful steps or buy headroom on the binding spec (1692 B).
- `tests/test_harness_files.py`: the agent-file budget goes from 1500 to 1800 B.
- `AGENTS.md`, the `rl-tutoring` skill (the budget is now ≈ 85–130 sims), the `refine` description in
  `tutor_mcp_server.py`.
- `tests/test_tutor_tools.py`: `test_refine_runs_two_rounds_the_second_from_the_new_best`.

**How it works:** the warm-up measures the sensitivities around the nominal. After the RL run the operating point
has moved (other currents, another mirror balance), so those numbers no longer hold (the fresh run: mn5 −1 gave
−2.8 % UGBW at the nominal and −8.6 % at the best). Round 1 measures them again where it matters: one-at-a-time
steps at the best, i.e. a finite-difference sensitivity measurement. Round 2 combines the steps that helped. A
round-1 step that is itself a better design becomes the new best, and round 2 starts from there. This is the same
idea as the warm-up, a one-at-a-time sensitivity table, applied at the optimum instead of at the nominal.

**Decisions:**
- Capped at 2 rounds in the code, so the tokens stay bounded: each extra tool call is one more model turn that
  rereads the tutor's context. Estimate: +1 turn and ≈ +3–5 simulations per session (≈ 7 → 8 tutor turns).
- `tutor.md` +200 B (≈ +50 tokens per tutor turn).
- No second RL run (Brent removed it earlier); the extra round is the LLM's own.

**Verification:** 161 tests pass. Not simulated; Brent tests it in agy.

**For Brent to check:** in the agy session, does round 1 contain single steps, and does round 2 build on its table?

### 2026-11-06 — 4.v3.2: one file for the final harness (v2 code removed)
**Goal:** Brent: as little extra code as possible for the oral exam, without losing any functionality of the final
harness. Brent chose to drop v2 (it stays on branch `feat/m4-hybrid` and in its session record).

**What changed** (branch `feat/m4-tutor`, commit `7dc544d`):
- `CAD/tutor_tools.py`: `TutorExperiment` now extends the course template's `SizingExperiment` directly
  (323 lines). Map: 24:MAX_TOTAL_SIMS, 25:MAX_WARMUP, 26:MAX_REFINE, 27:MAX_REFINE_ROUNDS, 28:MAX_BURST, 29:WARM_START_STEPS, 30:MAX_LOG_CHARS, 31:LOG_PATH, 32:SPECS, 35:TutorExperiment, 37:__init__, 49:setup_rl, 73:run_rl, 120:refine, 144:log_entry, 165:to_action, 175:state_of, 179:_best, 184:_simulate_from, 195:_rl_step, 216:_warm_start, 239:_budget, 244:_narrow, 260:_range, 270:_check_designs, 278:_simulate_table, 298:_free_ranges, 303:_margins, 312:_at_edge.
- Moved over from `hybrid_tools.py`, unchanged: `to_action`, `state_of`, `_best`, `_warm_start`, `log_entry`;
  `rl_explore`'s per-step body is now `_rl_step`.
- Removed (v2 only):
  - the `simulate(parameters | changes, base="best" | n)` override and `_design` → `_simulate_from(base, parameters,
    reason)`, where base is the design itself;
  - `_call_of`, no longer needed;
  - `rl_explore`'s 15-line report, which `run_rl` discarded;
  - `_on_full_grid` → the template's `_validate_parameters`. At `setup_rl` time the grid is still the full one, so it
    is the same check.
- `setup_rl`: the narrowed grid is set first; `_check_designs` + the nominal run inside one `try` that restores the
  full grid on an error. So `_check_designs` no longer swaps grids itself.
- Deleted: `hybrid_tools.py`, `hybrid_mcp_server.py`, `tests/test_hybrid_tools.py`, `tests/test_hybrid_mcp_server.py`.
- `tests/test_tutor_tools.py` (19 tests): the v2 tests that cover behaviour v3.2 still uses, ported to the
  `setup_rl`/`run_rl` API:
  - the action ↔ design inverse on the full grid;
  - every design is one transition (action, reward, next state);
  - a failed sim adds no transition;
  - one RL step = 1 sim, 1 transition, 1 update; the episode starts at the best;
  - the warm start only when the best changed;
  - the log.
- `CAD/harness/README.md` (the chain, `refine`); `docs/report/report_material.md` (v2's code location, the tests
  table).

**How it works:** the stack for the exam is now 2 files on top of the template: `tutor_mcp_server.py` (the 5 MCP
tools) → `tutor_tools.py` → `sizing_tools.py` (the course's TODOs, filled in).

**Decisions:**
- `sizing_tools.py` and `mcp_server.py` not touched (the course template).
- `run_rl`'s bursts are now `step % MAX_BURST == 0 → _warm_start`: the same moments as before (steps 0, 60, 120).
- One detail: the warm-up's `delta_pct` is now computed from the nominal's full-precision specs. Before, it used the
  4-digit rounded copy; `refine` already used full precision. The rows can differ at most in the 0.1 % digit.

**Verification:**
- 150 tests pass (161 − 15 v2 tests + 4 new; the other ported checks were added to existing tests).
- No `.py` file references `hybrid` anymore.
- Real-ngspice smoke test, 9 sims (`setup_rl` with the fresh run's nominal + 2 warm-up, `run_rl(5)`, `refine(1)`):
  - nominal −0.0447 and mn4 +1 → 0.6562, the same as in the fresh run;
  - history sources simulate×3, rl×5, simulate; buffer = 9 = successful sims;
  - margins reported. The run folder was deleted afterwards.
- M4 code beyond the template: 565 → 408 lines.

**For Brent to check:** nothing pushed.

### 2026-11-06 — 4.v4: only the course's tools; the warm-up explores around the LLM's design
**Goal:** Brent: no server or tools of our own. Use the received `mcp_server.py` and `sizing_tools.py` the
template way, with the LLM's conclusions feeding the warm-up. He chose option B (the warm-up around the best design)
and one test run before his own agy session.

**What changed** (branch `feat/m4-template` from `feat/m4-tutor`, commit `3d85360`; test run in a second commit):
- `CAD/sizing_tools.py`: `_warmup_action` and `to_action` (lines 247 276 285 ). In `_run_steps`, the warm-up branch calls
  `self._warmup_action()` instead of `self.env.action_space.sample()`.
- `CAD/mcp_server.py`: unchanged. `.agents/mcp_config.json` now starts it.
- Deleted: `tutor_tools.py`, `tutor_mcp_server.py`, their tests, `harness/design_log.md` (no `log_entry` any
  more).
- Prompts rewritten for the 4 template tools: `AGENTS.md`, `tutor.md`, `reviewer.md`, the `rl-tutoring` skill.
  `opamp-design` is unchanged.
- `tests/test_sizing_tools.py` (+3): the inverse `to_action`; the warm-up around the best design (the L's
  practically fixed, the multiplicities ±1 step, the centre follows the best); the uniform warm-up before any
  `simulate`.
- `tests/test_harness_files.py`: the 4 template tools; the config starts `mcp_server.py`.

**How it works:**
- TD3's action is a whole design. `to_action` gives the centre of each parameter's action bin (the inverse of
  `action_refine`'s `floor((a+1)/2·(n−1))`).
- The warm-up action = that centre for the best measured design + N(0, σ) with σ = `agent.expl_noise` = 0.1, the
  template's own TD3 exploration noise, clipped to [−1, 1]. The noise is drawn from `env.np_random`, so a seed
  reproduces it.
- σ 0.1 against the bin widths 2/(n−1):
  - multiplicities (n = 24, bin 0.087): ≈ ±1 step;
  - widths (n = 11, bin 0.2): a step in 32 % of the draws;
  - L (n = 4, bin 0.67): practically never (0.09 %);
  - Cc, Rc (n = 99): ≈ ±5 steps.
- So the warm-up is a random local search around the LLM's design, and its 100 transitions teach TD3's critics
  that region.
- The template's 10-step episodes still reset to a uniformly random design (one simulation each). A reset moves the
  centre only if it is better.
- Only when a design has source `simulate` (the LLM gave one); otherwise the template's uniform warm-up.

**Decisions:**
- σ = the TD3 exploration noise, so no new hyperparameter. The template hyperparameters stay as given.
- A moving centre (the best of all measured designs, not only the LLM's): it can then climb.
- The < 200 budget is a prompt rule only; no tool of our own enforces it.

**Verification:**
- 133 tests pass.
- Test run (Claude Code following only the prompt files; `harness/sessions/2026-11-06_claude-code-template/`):
  - nominal −0.559 → 2 fixes → 0.606 (3 sims);
  - `warmup(100)` → 0.646;
  - `train(60)` → no gain;
  - refining: 0.662, then **0.678**;
  - **189 sims, 4.1 min, ≈ 165k input tokens** (turn model; v3.2 ≈ 39k).

**For Brent to check / open questions:**
- v4 costs ≈ 4× v3.2's tokens: each refining design is a `simulate` turn, and the results are full candidates.
  Fewer refining designs (e.g. 1 round of 3) would cut ≈ 60k.
- Is the template way worth that cost? v3.2 stays on `feat/m4-tutor` if you want to compare.

### 2026-11-06 — 4.v4.1: `train` starts at the LLM's design (actor warm start inside our `train` TODO)
**Goal:** Brent asked why `train` gave nothing while the warm-up did, since the warm-up should prepare the training.
Diagnosis (v4 history): training's designs were a median 134 grid steps from the best. The untrained actor
outputs ≈ 0 = the middle of every range (mn4 12, mp3 12, Cc 5 pF, Rc 4.6 kΩ), where the critics have no data. Brent
chose option B.

**What changed** (branch `feat/m4-template`, commit `5c8824f`; A/B run `505cac6`):
- `CAD/sizing_tools.py` (lines 30 151 289 ): `WARM_START_STEPS = 200`, `self.warm_started_for`, `_warm_start()`. It is
  called in `train` after the batch-size check, before `_run_steps`.
- `tests/test_sizing_tools.py` (+2): the clone shrinks the actor's distance to the best action > 4×; the target
  actor is a copy; no second clone for the same best; without an LLM design, no warm start.
- `rl-tutoring` skill: the `train` paragraph.
- Where "our TODO" is: the course file had `raise NotImplementedError("TODO: ...")` in `simulate`, `warmup`,
  `train`, `get_status`, `_validate_parameters`, `_record` and `_run_steps`. The warm-up change is one line in our
  `_run_steps` (the warm-up action) plus `_warmup_action` / `to_action`. The warm start is one line in our `train`
  plus `_warm_start`. All of it sits under the header "added: the warm-up and the training start around the LLM's
  design".

**How it works:**
- The actor is a network: state (normalized specs) → action (a whole design).
- Behaviour cloning:
  - for all states in the replay buffer, MSE(actor(s), to_action(best)), 200 Adam steps with the actor's own
    optimizer (lr 3e-4), no simulations;
  - then actor_target = actor, so TD3's target policy (TD3 paper: target networks) is consistent.
- After the clone the actor answers "≈ the best design" for any state. A template reset (a random design, 1
  simulation per 10 steps) only changes the state, and the next design is again near the best.
- The critics are untouched.

**Decisions:**
- The same rule as the warm-up: only once the LLM has simulated a design; otherwise plain TD3.
- Only when the best changed, so a second `train` call doesn't undo the learning.
- 200 steps as in v3.2 (tested there).

**Verification:**
- 135 tests pass.
- **A/B run** (the same seed and calls as v4, the first 113 simulations identical):

  | | start of training | end of training | feasible | best |
  |---|---|---|---|---|
  | v4 | 145 grid steps from the best | 110 | 0 | −1.51 |
  | v4.1 | 16 grid steps | 96 | 2 | 0.594 |

  The final FoM is the same 0.678 (189 sims; refining replayed from the same state).

**For Brent to check / open questions:**
- The warm start fixes the start, but TD3 drifts away within 60 steps. Its critics have had only 60 updates and
  their slope is unreliable, and 30 delayed actor updates follow it. The random resets show the actor unseen states.
- Within this budget, `train` still doesn't improve the FoM.
- Options:
  - keep it (it doesn't hurt, gives more feasible designs, and it's honest material for the report);
  - re-clone at every `train` call and train in short pieces (e.g. 3 × 20), which keeps pulling it back;
  - drop `train` and spend the 66 simulations on the warm-up.

### 2026-11-06 — 4.v4.1 experiment: `train(200)` instead of 60
**Goal:** Brent: see how much longer training improves.

**What:** the same seed and first 4 calls as the v4 run (113 identical simulations, best 0.6462), then
`train(200)` with the warm start. 333 simulations, deliberately over the harness budget. Record:
`CAD/harness/sessions/2026-11-06_experiment-train200/` (commit `6bdc0dd`). No code change.

**Result:**
- No improvement: the best stays 0.6462, no training design beats it, and 4 of 200 meet all specs.
- A U-shape in the median distance from the best:
  - 19 grid steps (steps 1–25);
  - up to 120 (steps 76–100);
  - back to 34 (steps 176–200).
- The median reward goes −0.8 → −3.5 → −0.9.

**Interpretation (for the exam):**
- The warm-started actor starts right.
- In the first ~100 steps the immature critics' slope pulls it away.
- After that the critics have learned enough to bring it back.
- So TD3 learns, but 200 steps only bring it back near its start. To beat a local search around a good design it
  needs many more steps, as in milestone 3 (thousands of simulations).

**For Brent:** within the < 200 budget, `train` can't pay off. Options: keep it as an honest demonstration; or drop
it and give its simulations to the warm-up.

### 2026-11-06 — 4.v4.1 experiment: `train(2000)`
**Goal:** Brent: see how TD3 reacts with 2000 training steps.

**What:** the same seed and first 4 calls as v4 (113 identical simulations, best 0.6462), then 2 × `train(1000)`
(the template's maximum per call). No re-clone in part 2, because the best didn't change. 2313 simulations. Record:
`CAD/harness/sessions/2026-11-06_experiment-train2000/` (commit `7d8451e`). No code change.

**Result:**
- The U-shape of the first 200 steps.
- Then TD3 settles ≈ 21–30 grid steps from the LLM's region and improves steadily:
  - the median reward per 100 steps −2.1 → −0.3;
  - the feasible designs per 100 steps 2 → 20.
- It first beats the warm-up's 0.646 at training step 1515.
- Best **0.699** at simulation 1780: 192 µA, 902 µm², UGBW +0.1 %.
- 172 designs meet all specs; 5 simulations failed.

**Interpretation (for the exam / report):**
- The RL is not useless; it is slow. With the LLM's design as warm-up centre and warm start, TD3 needs ≈ 1500
  training steps to beat a 100-sample local search around a good design, and then finds the best FoM of all
  harness versions.
- Within the harness's < 200 budget it can't get there.
- One seed only.

### 2026-11-06 — 4.v4: the actor warm start removed again
**Goal:** Brent: take the warm start out of `train` (and the second warm-up, if it never helped).

**What changed** (branch `feat/m4-template`, commit `4e56f63` = `git revert 5c8824f`, no history rewrite):
- `sizing_tools.py`, `tests/test_sizing_tools.py` and the `rl-tutoring` skill are back to v4. The code and prompts
  are byte-identical to `3d85360`, the tested v4.
- `train` is again the template's plain TD3 (our TODO implementation without the clone).
- The **second warm-up** was only part of a proposed "lean" flow and was never tested or put into a prompt, so
  there was nothing to remove. The prompts keep one `warmup(100)`, still drawn around the LLM's best design (it
  gave +0.04 in the v4 run).

**Decisions:** the experiments that used the warm start (the v4.1 A/B, `train(200)`, `train(2000)`) stay recorded
in `harness/sessions/` as experiments; their READMEs say they used the warm start.

**Verification:** 133 tests pass; `git diff 3d85360 HEAD` on the code and the prompts is empty.

**For Brent:** the harness is v4 as tested: FoM 0.678, 189 sims, ≈ 165k tokens (turn model).

### 2026-11-06 — 4.v4: the real agy session (Brent, Claude Sonnet 4.6)
**Record:** `CAD/harness/sessions/2026-11-06_agy-claude-sonnet-v4/` (README + history committed in `1933d51`). The
3 agy transcripts are copied there but **not committed**: the permission check blocked committing files from
`~/.gemini`; Brent decides.

**Checks:**
- Start from scratch: passed (the skills, the netlist, agy's own MCP tool-definition files).
- 191 simulations (< 200), 0 failed, 5.8 min. Pipeline main → tutor → reviewer.

**Result: FoM 0.490.**

| phase | simulations | best |
|---|---|---|
| hand phase | 10 | −0.218, never all specs |
| `warmup(100)` | 110 | 0.337 (7 feasible, all ≈ 450 µA) |
| `train(60)` | 66 | nothing |
| refining | 5 | 0.490 (Cc and Rc for area) |

The final design: current 452 µA, area 538 µm², PM +2.5 %.

**Tokens (agy):** 32 model calls; 85.2k input + 628.7k cached + 17.0k output (tutor: 24 calls, 572.6k cached).
v3.2's agy session: 58.8k + 207.5k + 13.2k.

**Why low:**
- The tutor never budgeted the current. mn3 = 1 finger makes the mirror ratios large, so the hand designs drew
  305–629 µA.
- The warm-up searched around a ≈ 450 µA design, and the refining only reduced the area.
- Rules broken: 10 hand sims instead of ≤ 6; a failing design handed over; the returns misreport the hand count;
  the reviewer says "RHP zero".

**For Brent:** possible prompt fixes (circuit knowledge only):
- budget the current in the nominal: 30 µA + I_tail + I2 ≈ the 200 µA target;
- refining spends its moves on the larger FoM term (z_current vs z_area);
- the reviewer reports the counters from `get_status`.

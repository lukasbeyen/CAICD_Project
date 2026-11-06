# Report material: H05D7 CAD project (TD3 sizing of a two-stage opamp + LLM harness)

Source material for the 10-page report, ordered as the PDF's "What to report" per milestone. Every number below comes
from a run, a test or a log in the repo (file names given), so it can be checked and quoted. Figures:
`docs/report/figures/`.

**Suggested page budget (10 pages):** introduction 0.5 · M1 1.5 · M2 1.5 · M3 3 · M4 3 · conclusion 0.5.

---

## 1. Simulator interface (PDF §1)
*Report: the circuit topology, how each spec is measured, proof of correctness through the unit test.*

### Topology
Two-stage Miller opamp (`ngspice_interface/files/input_netlists/TwoStage.cir`, 45 nm PTM models, TT, 27 °C).
S = m·W/L.

| parameters | device(s) | role |
|---|---|---|
| `mp1 wp1 lp1` | mp1 + mp2 (PMOS) | current-mirror load of the input pair (mp1 diode-connected) |
| `mn1 wn1 ln1` | mn1 + mn2 (NMOS) | input differential pair |
| `mn3 wn3 ln3` | mn3 (NMOS, diode) | bias reference, carries Ibias = 30 µA |
| `mn4 wn4 ln4` | mn4 (NMOS) | tail current source, I_tail ≈ 30 µA · S4/S3 |
| `mp3 wp3 lp3` | mp3 (PMOS) | second stage, common source |
| `mn5 wn5 ln5` | mn5 (NMOS) | second-stage current sink, I2 ≈ 30 µA · S5/S3 |
| `cap`, `res` | Cc, Rc | Miller compensation with a nulling resistor |

Fixed: CL = 10 pF, VDD = 1.2 V, VCM = 0.6 V, 1 V differential AC input (so v(net6) *is* the gain A(jf)).

### How each spec is measured (`dut_testbench.py`; the netlist writes 4 CSVs with `wrdata`)
| spec | analysis | measurement |
|---|---|---|
| gain | `ac dec 10 1 1T` | \|A\| at 1 Hz (far below the dominant pole), V/V |
| UGBW | AC | frequency where \|A\| = 1: cubic spline through log\|A\| vs log f, root with `brentq` (0.003 % from a dense sweep; a straight line between Bode points: 0.92 %) |
| phase margin | AC | 180° + phase at the UGBW, after `np.unwrap` (without it an unstable amp with −235° read +305° and *passed*) |
| slew rate | `tran 50n 30u` + `.options trtol=0.1` | first **rising** edge, 10 % → 90 % of the swing, levels limited to 10–90 % of VDD (allowed by the TAs); `trtol=0.1` makes ngspice step finely on the edges: within 0.6 % of a 0.1 ns reference instead of up to 72 % too low |
| noise | `noise v(net6) Vinput dec 10 1 1T` | integrated output noise 1 Hz–1 THz (`onoise_total`), V rms |
| current | `op` | −i(vdd): total supply current incl. the 30 µA bias |
| area | — | the course's estimator (`area_estimation.py`) |

**Robustness** (changes to the course wrapper, `ngspice_wrapper.py`):
- ngspice from the PATH; the real exit code via `subprocess.run` (the course's `os.system` check was always 0);
- a log file per simulation;
- a 20 s timeout;
- the output folder created.

A broken, empty, NaN or too-short result marks the simulation as **failed** instead of crashing a run.

### Proof of correctness: `tests/test_measure.py` (50 tests) + `tests/test_wrapper.py` (5)
- **Synthetic transfer functions with an analytic answer:** 1-, 2-, 3-pole systems with exact UGBW and PM. The 3-pole
  case has a negative PM and fails without `np.unwrap`. No crossing → 0.
- **Slew rate on ideal ramps:** rising edge only, outputs starting high or between the levels, incomplete edges,
  glitches above VDD / below 0 V (capped/floored).
- **Broken files → failed.**
- **Real designs vs ngspice's own `meas`:** 4 sizings on a 100× denser sweep, gain/UGBW/PM within 1 %.
- **The TAs' 5 reference designs** (`references.csv`): all 7 metrics within 1 % (area, current, gain, noise, PM, UGBW
  0.0–0.2 %).

Figure: `figures/sr_methods.png` (slew-rate methods vs the 0.1 ns reference).

---

## 2. Circuit environment (PDF §2)
*Report: action refinement, spec normalization, step and reset, proof of correctness through the unit test.*

### Action → sizes (`action_refine`)
- The actor outputs 20 numbers in [−1, 1], one *absolute* design. They are clipped to [−1, 1] (exploration noise).
- Per parameter: n = round((max − min)/step), `idx = floor((a + 1)/2 · (n − 1))`, value = min + idx·step.
- This is **the TAs' mapping**, reverse-engineered from `references.csv`: it reproduces all 100 action → size pairs
  (a linear rounding mapping reproduced none). It matches the `np.arange(min, max, step)` grid of the milestone 4
  template: the YAML maximum itself is never chosen.

### Normalization (`normalize_specs`)
- z = (y − y*) / (|y| + |y*|) per spec, always in [−1, 1]; 0 = exactly on target.
- Why: the raw specs span ~17 orders of magnitude (area 1e-9 m², UGBW 1e8 Hz); the networks need one scale.
- The |·| in the denominator: a value ≤ 0 (e.g. a negative phase margin) gives exactly −1 instead of a wrong sign.
- The state = the 7 z values (YAML order: area, current, gain, noise, PM, SR, UGBW), float32.

### Reward (`reward_computation`, the course FoM)
- **Hard specs** (gain, UGBW, PM, SR ≥ target; noise ≤ target): only violations count,
  r_H = Σ min(z, 0) (−max(z, 0) for noise).
- **Targets** (area, current): r_T = −(z_area + z_current).
- **All hard specs met:** reward = 0.3 + r_T. **Otherwise:** reward = r_H + 0.05·r_T (the 0.05 follows from the TAs'
  reference rewards).
- **Failed simulation:** −6 (below the worst valid reward ≈ −5.1, so breaking the simulator is never a way out), and
  the state is the worst case [+1, +1, −1, +1, −1, −1, −1].

### reset and step
- **reset:** simulates one random design (seeded `np_random`) as s₀. It is counted and logged but not rewarded (the
  template).
- **step:** refine → simulate → normalize → reward; the netlist of a design meeting all specs is kept (for
  `Solutions/`); every simulation is a row in `runs/<run>/designs.csv`; the course's plots; `done` after 10 steps (a
  time limit, not a goal).
- `self.counter` counts every simulation (resets included) for the 5000-simulation comparison.

### Proof of correctness: `tests/test_env.py` (25) + `tests/test_reference_rewards.py` (1, Lukas)
- The TAs' reference actions → exactly the TAs' sizes; their measurements → exactly their normalized specs and reward.
- Hand-calculated FoM cases, e.g. gain 100 instead of 200 → reward exactly −1/3; all met at target → 0.3.
- Mapping endpoints, grid and clipping; failed simulations (error, timeout, broken output) → −6 + the worst-case state.
- Bookkeeping: counter and CSV rows incl. resets, PVT corner, kept netlists, 10-step episodes, seeded resets.
- gymnasium's `check_env`.
- A fake simulator (fast) + one real-ngspice test.

---

## 3. RL agent: TD3 (PDF §3)
*Report: the TD3 implementation, the episodic loop of the runner, the reasons for the hyperparameter values; the plots;
the comparison with the baseline within 5k simulations.*

### TD3 (`td3/agent.py`; Fujimoto et al. 2018, Algorithm 1)
- **`select_action`:** a = clip(π(s) + ε, −1, 1), ε ~ N(0, σ), with σ = `noise_sigma`; no gradients while acting.
- **`update_parameters`,** per mini-batch (s, a, s′, r, not_done) from the replay buffer:
  1. **Target policy smoothing** (§5.3): a′ = clip(π′(s′) + clip(N(0, 0.2), −0.5, 0.5), −1, 1).
  2. **Clipped double Q-learning** (§4.2): y = r + γ · not_done · min(Q1′, Q2′)(s′, a′), under `no_grad`.
  3. **Both critics** regress onto y (MSE); one Adam step.
  4. **Delayed policy update** (§5.2), every 2nd update: actor loss −Q1(s, π(s)), then soft target updates
     θ′ ← τθ + (1 − τ)θ′ with τ = 0.005.
- **Proof** (`tests/test_agent.py`, 11 tests):
  - the bounds and the spread of the noise;
  - which networks change at which update;
  - no gradients reach the targets;
  - the soft update by τ;
  - y uses the smaller critic; y = r at the end of an episode;
  - the smoothing noise is clipped;
  - the agent learns a toy bandit.
- **Lukas's independent implementation** (`07d2e87`) gives bit-identical weights after 200 updates with the same seed.

### The episodic loop (`td3_runner.py`)
- **Warm-up:** `w` steps with random actions (`action_space.sample()`), stored in the replay buffer.
- **Training:**
  - every episode starts with `env.reset()` (a random design), then 10 steps;
  - each step: `select_action` → `env.step` → push (s, a, r, s′, done) → one `update_parameters` on a batch;
  - `clean.sh` empties the scratch folder every 100 steps.
- **Our changes to the course runner:**
  - **stop at 5000 simulations** (`--max_sims`; the course's 10 000 steps would be ~11 000 simulations, because every
    episode adds a reset);
  - seeding of the env's random start designs and of the warm-up actions (the course seeded only numpy/torch);
  - a run folder with the YAML, `hyperparameters.json` and the networks;
  - `env.finalize()` (the Pareto plot).
  - Tested in `tests/test_runner.py` (4): the stop is exact, the run folder, same seed → same run.

### Hyperparameter tuning: why these values (all runs 5000 simulations; `CAD/runs/`, analysis scripts in `CAD/analysis/`)
Selection criterion: the **mean best FoM over seeds**. One run's best is a maximum, so a single lucky seed can't decide.

**Stage A**: one hyperparameter at a time from the start values (σ 0.1, batch 128, w 500, actor lr 3e-4, critic lr
1e-3), seed 123456. Figure `figures/fom_evolution_A.png`.

| changed | best FoM | mean reward, last 1500 sims |
|---|---|---|
| none (start values) | 0.615 | −1.70 |
| actor lr 1e-4 | **0.696** | −0.53 |
| w 250 / w 1000 | 0.683 / 0.682 | −0.15 / **+0.02** |
| critic lr 3e-4 | 0.659 | −0.51 |
| σ 0.2 / σ 0.05 | 0.603 / 0.579 | −0.55 / −1.25 |
| batch 64 / 256 | 0.511 / 0.474 | −1.09 / −1.14 |

With the start values the agent degrades in the second half. A slower actor and a longer warm-up keep it stable.

**Stages B, C**: the best settings repeated with 3 seeds (123456, 1, 2):

| setting (σ 0.1, batch 128 unless stated) | best FoM per seed | mean ± std |
|---|---|---|
| start values | 0.615 / 0.617 / 0.684 | 0.639 ± 0.039 |
| actor lr 1e-4 | 0.696 / 0.622 / 0.668 | 0.662 ± 0.037 |
| w 1000 | 0.682 / 0.684 / 0.638 | 0.668 ± 0.026 |
| **actor lr 1e-4 + w 1000 (final)** | 0.702 / 0.660 / 0.662 | **0.675 ± 0.024** |
| w 250 + actor lr 1e-4 + critic lr 3e-4 ("best of each") | 0.632 / 0.628 / 0.695 | 0.652 ± 0.038 |
| Lukas's values (batch 64, w 200, actor/critic lr 1e-3), 4 seeds | 0.669 / 0.606 / 0.687 / 0.665 | 0.657 ± 0.035 |
| SAC baseline's values (batch 100, w 100, lr 3e-4/3e-4), 2 seeds | 0.300 / 0.368 | 0.334 |

**Final values:** σ 0.1, batch 128, **w 1000**, **actor lr 1e-4**, critic lr 1e-3 (γ 0.99, τ 0.005, delay 2).
These were given on the command line (`python td3_runner.py --batch_size 128 --w 1000 --pi_lr 1e-4 --seed <s>`);
the runner's own defaults are Lukas's (σ 0.1, batch 64, w 200, actor lr 3e-4, critic lr 1e-3). Reasons:
- the highest mean best FoM, the smallest spread and the best worst seed;
- the least degradation late in the run;
- a slower actor relative to the critic fits TD3's own argument for delayed policy updates;
- a longer warm-up gives the critics more varied data before learning starts.

**Lessons for the report:**
- One-at-a-time winners don't add up: the "best of each" combination was worse, because the hyperparameters interact.
- The baseline's settings make TD3 *much* worse (short warm-up, and only a small fixed exploration noise, where SAC
  explores through its entropy term).
- The differences between settings (~0.02–0.04) are close to the seed spread (~0.03): with 3 seeds the standard error
  is ≈ 0.02.

### The two required plots (final setting)
- **`figures/final_max_fom.png`:** maximum FoM against the simulation number, the 3 seeds. The course's
  `max_reward.png` has the *step* index on its x-axis, so this one is drawn from `designs.csv`.
- **`figures/final_pareto.png`:** the current–area Pareto front of seed 123456: 891 designs met all specs, 9 are
  Pareto-optimal.

| area (µm²) | current (µA) | FoM |
|---|---|---|
| 616 | 286 | 0.652 |
| **657** | **246** | **0.702** (best) |
| 708 | 236 | 0.695 |
| 810 | 234 | 0.645 |
| 865 | 234 | 0.618 |
| 866 | 231 | 0.623 |
| 923 | 229 | 0.601 |
| 925 | 225 | 0.609 |
| 1182 | 207 | 0.539 |

`Solutions/` (repo root): these 9 netlists + `Solutions.csv` (parameters, specs, reward).

### Comparison with the baseline (SAC, the TAs' compiled agent), within 5000 simulations
| | best FoM |
|---|---|
| TD3, tuned, 3 seeds | 0.702 / 0.660 / 0.662, mean **0.675 ± 0.024** |
| SAC baseline, 1 seed (student server) | 0.662 |

Our tuned TD3 is at least as good as the baseline, and better on the mean and on the default seed. Caveat: only one
SAC seed.

The SAC runner's defaults (read from the compiled module) are batch 100, warm-up 100, lr 3e-4, `init_temperature` 0.1,
and 10 000 steps (≈ 11 000 sims). The comparison uses its first 5000.

**Reproducibility note:** a seeded run is exactly reproducible as long as the same simulations hit the 20 s
wall-clock timeout. A rerun of the final setting diverged at simulation 626, because that simulation timed out
there: the laptop slept and paused the VM.

---

## 4. LLM-based agentic harness (PDF §4)
*Report: the task breakdown and the agents (prompts, context, memory), the MCP tools, the skills, context/memory
management, examples of explainability, the best solutions with reasoning, few simulations; runtime vs pure RL.*

### Architecture
- **Antigravity CLI** (`agy` 1.5.1), started in `CAD/`, runs the harness. It loads `CAD/AGENTS.md` (always-on
  context), the subagents `CAD/.agents/agents/*.md`, the skills `CAD/.agents/skills/*/SKILL.md`, and the MCP server
  `cad` (`CAD/.agents/mcp_config.json`).
- **MCP server** `mcp_server.py` (course template) → backend `sizing_tools.py` (`SizingExperiment`: one env, one
  TD3 agent, one replay buffer kept across tool calls).

| tool | what it does | cost |
|---|---|---|
| `simulate(parameters, reason)` | one complete design (20 physical values, validated on the grid) in a separate evaluation env: never touches the RL state | 1 simulation |
| `warmup(n, reason)` | n random RL transitions, no learning | ≈ 1.1 sims/step |
| `train(n, reason)` | n TD3 transitions + one update each (template hyperparameters, unchanged) | ≈ 1.1 sims/step |
| `get_status(k)` | counters + the k best distinct designs | free |

- **Our addition:** the optional `reason` argument. Every simulation is stored with its reason, source and timestamp
  in `runs/<run>/harness_history.csv`. This is the server-side decision trace, and the data for the runtime comparison.

### The task breakdown: agents by role (the main agent orchestrates)
| agent | sub-task | MCP tools | output |
|---|---|---|---|
| orchestrator (main) | routes the work, passes context, keeps the memory | all, delegates | design-log entries |
| `circuit-analyst` | device roles, critical specs, a hand-calculated first design | none | analysis + 20 values |
| `designer` | hypothesis → one change → simulate → compare (≤ 10 sims per round) | `simulate`, `get_status` | round summary |
| `rl-operator` | decides *whether* RL is worth it; runs warmup/train in batches | `warmup`, `train`, `get_status` | top RL designs + what distinguishes them |
| `reviewer` | margins, Pareto trade-off, decision trace, cost | `get_status` | final summary |

**Routing rule** (`AGENTS.md`): after every designer round, the orchestrator writes a decision:
- another round if it improved;
- the RL operator if stuck (no improvement in 2 rounds, or not feasible after 30 sims);
- the reviewer once converged (or at ~300 sims).

**Skills:**
- `two-stage-opamp-design`: first-order equations (A0, GBW = gm1/2πCc, p2 = gm6/2πCL, the LHP zero via Rc,
  SR = I_tail/Cc), a knob table (spec → change → side effects), the area formula, and the instruction to calibrate the
  textbook estimates against the first simulations;
- `rl-sizer`: when RL is worth its simulations, a batch procedure with stop criteria;
- `design-log`: the memory format.

**Context and memory:**
- `harness/design_log.md` is the shared, append-only memory. The orchestrator writes one entry per step (goal,
  reasoning, actions, result, conclusion).
- Subagents get only the relevant entries and the 3 best designs, and return ≤ 300 words.
- **This survived an `agy` restart mid-session:** the new session continued from the log (entries 4–5).

**No milestone 3 results are in the prompts** (a fair comparison with RL): only circuit and process knowledge.

### The session (2026-11-05, Gemini 3.8 Flash; `CAD/harness/design_log.md`, `CAD/harness/sessions/2026-11-05_gemini-3.8-flash/`)
| entry | agent | what happened | sims |
|---|---|---|---|
| 1 | analyst | CL = 10 pF makes PM the bottleneck → Rc for an LHP zero; Cc 1 pF; I_tail ≈ 60 µA, I2 ≈ 90 µA; mirror balance S_p3/S_p1 = 2·S5/S4; L = 90 nm | 0 |
| 3 | designer, round 1 | baseline: UGBW only 40.6 MHz → Cc ↓, Rc ↑ to 9.8 k, balanced current increase → **all specs met at sim 10** (FoM 0.565) | 10 |
| 4 | orchestrator | "not stuck, RL is not needed" → round 2 for current | 10 |
| 5 | designer, round 2 | mn3 3 → 4 scales both currents by 0.75 with the balance intact → **211.5 µA, FoM 0.684** | 16 |
| 7 | reviewer | margins, Pareto front, 3 key decisions, risks | 16 |

**Explainability examples** (quote from the design log / the `reason` column):
- **Calibration against the textbook:** "Widening W1 gave negligible gm increase as devices operate in weak/moderate
  inversion; gm primarily scales with tail current." "L = 45 nm degraded DC gain to 110 V/V … due to DIBL; L = 90 nm is
  required."
- **A hypothesis before every simulation,** e.g. "UGBW 40.6 MHz < 100 MHz: reduce Cc 1.0p → 0.5p to scale GBW; expect
  UGBW ~75–80 MHz", with the result compared against it.
- **A failure explained and fixed:** "Breaking mirror balance (S_p3/S_p1 ≠ 2·S5/S4) crushed DC gain to 39 V/V" →
  "scale current in balanced ratio (2·S5/S4 = S_p3/S_p1 = 3.0)" → all specs met.
- **The reviewer's 3 key decisions:** (1) Cc 0.3 pF + Rc 9.8 kΩ, the LHP zero rescues PM; (2) the systematic mirror
  balance, from non-compliant to compliant; (3) mn3 3 → 4, −21 % current with the balance kept.
- **Risks named by the reviewer:** UGBW margin +0.7 %, PM margin +1.05 %, and Rc is already at the grid maximum, so an
  SS-corner or Monte Carlo check is recommended.

**The best solution** (`final_design.cir`, FoM **0.684**, 16 simulations):

| gain | UGBW | PM | SR | noise | current | area |
|---|---|---|---|---|---|---|
| 637 V/V | 100.7 MHz | 60.6° | 58.7 V/µs | 21.0 mV | 211.5 µA | 833 µm² |

Parameters: mp1 4 × 1.0 µm/90 nm · mn1 10 × 1.5 µm/90 nm · mp3 8 × 1.5 µm/90 nm · mn3 4 × 1.0 µm/90 nm ·
mn4 10 × 1.0 µm/90 nm · mn5 15 × 1.0 µm/90 nm · Cc 0.3 pF · Rc 9.8 kΩ.

Pareto alternative: mn3 3, mn4 8, mn5 12 → 830.5 µm², 222.6 µA, PM 61.1°, UGBW 107.8 MHz, FoM 0.660 (more margin).

### Runtime: harness vs pure RL (`figures/harness_vs_rl.png`, `analysis/harness_vs_rl.py`)
| reached | LLM harness | TD3 seed 123456 | TD3 seed 1 | TD3 seed 2 |
|---|---|---|---|---|
| first design meeting all specs | 10.5 min / 10 sims | 5.5 min / 1072 sims | 5.3 min / 1225 sims | 8.5 min / 1956 sims |
| FoM ≥ 0.6 | 13.4 min / 12 sims | 7.7 min / 1867 sims | 10.7 min / 3285 sims | 16.6 min / 4580 sims |
| FoM ≥ 0.684 (the harness's best) | 13.4 min / 12 sims | 13.3 min / 3724 sims | never (5000 sims) | never (5000 sims) |

**Reading:**
- **In simulations** the harness is two to three orders of magnitude more efficient: 12 vs 3724 to FoM 0.684.
- **In wall-clock time** it is comparable with the best TD3 seed and faster than the other two. Its runtime is almost
  entirely LLM reasoning: the first simulation only comes after 6.3 min of analysis; 16 simulations are ~5 s of
  ngspice. TD3's runtime is almost entirely simulation (5000 × ~0.2 s).
- So the harness wins where simulations are expensive (e.g. PVT corners, larger circuits). TD3 still found the higher
  maximum on one seed (0.702), with the whole 5000-simulation budget.

**Fairness notes:**
- the harness clock includes the LLM time and the re-read after the `agy` restart; the pause itself is excluded;
- the TD3 runs ran two at a time on a 2-core VM, so their times are somewhat pessimistic;
- one harness session, with one model.

### Limitations / honest notes
- One session with one model (Gemini 3.8 Flash); a second session or model would show the spread.
- The RL operator was never needed in this session. That's a reasoned decision (entry 4), but the RL-as-a-tool path is
  only shown by the tests, not by a session.
- The final design's UGBW and PM margins are < 1.1 %, at the TT corner only.
- The subagents' MCP tool limits are set in their prompts and the orchestrator's routing, not in an `agy`
  configuration. Whether `agy` can enforce them per agent was not tested.

### Version 2: a token-lean harness where the LLM's designs warm-start the RL (branch `feat/m4-hybrid`)
**Why:** v1 cost ≈ 244k input tokens per session (turn model). The orchestrator alone took ≈ 100k, because it wrote
every log entry itself. And the LLM and the RL never met.

**What changed:**
- **The backend** (`hybrid_tools.py`, `HybridExperiment` on top of the unchanged `SizingExperiment`):
  - **every LLM simulation becomes a TD3 transition**, via the exact inverse of `action_refine`;
  - the LLM can give a design **as changes** to an earlier one;
  - `rl_explore(n)` runs **short TD3 bursts** (~30 simulations): the actor is warm-started on the current best design
    (supervised, 0 simulations), every episode starts at the best design, one TD3 update per step, no random warm-up
    (the buffer samples with replacement, so batch 100 works from the start);
  - `log_entry` lets the agents write the log through the server.
- **The harness:**
  - 3 agents (designer, rl-explorer, reviewer) + a thin orchestrator;
  - a fixed alternating pipeline (designer → [RL burst → designer explains RL's change + 2–4 sims] × n → reviewer)
    within **100–200 simulations**;
  - `AGENTS.md` 2.3 kB (v1 6.3 kB); tool descriptions 1.5 kB (v1 2.5 kB); agent returns ≤ 80 words.

**Test run** (Claude Code playing the agents; `CAD/harness/sessions/2026-11-06_claude-code-hybrid/`):
- **Tokens:** ≈ 126k input (−48 % vs v1).
- **Results:** all specs met at **sim 2**, final **FoM 0.677** after 97 simulations (7 by the designer, 90 RL).
- **The RL bursts found no improvement.** A diagnostic shows why:
  - the template's exploration noise (σ 0.1 on all 20 parameters at once) breaks the mirror balance (3 % of RL designs
    feasible; 20 % at σ 0.02);
  - the actor drifts from the warm-started design while the critic is still untrained;
  - the converged design sits on the PM boundary (+0.3°).
- **Honest reading for the report:** the token saving works. The LLM did the design. The RL, as a local explorer
  around a converged, constraint-bound design, adds nothing with the course's TD3 settings. It found feasible
  alternatives, but no better ones.

### Version 3: the LLM as the RL's tutor (branch `feat/m4-tutor`)
**Why:** v2 still cost ≈ 126k tokens, and its RL found nothing, because the template noise moves all 20 parameters
across their full ranges. New role: **the LLM is the RL's tutor, not its rival.** It uses its circuit knowledge to
set up the RL's job, and the RL optimizes.

**What changed** (`tutor_tools.py`, `TutorExperiment` on top of `HybridExperiment`): one tool call,
`setup_rl(nominal, search_space, warmup)`.
- **The nominal:** a hand design from the equations.
- **The search space:** only the parameters that matter are free, each with ~11 grid points around the nominal; the
  rest are fixed. Only the RL env's grid is narrowed, so the template noise σ 0.1 becomes local. The design rule: the
  chance that a free parameter moves ≥ 1 grid step per RL step is ≈ 1 % with 5 grid points, ≈ 30 % with 11, ≈ 60 %
  with 21.
- **The warm-up:** 10–20 designs with a purpose each (a one-at-a-time sensitivity study + balanced coupled moves). All
  of them become TD3 experience, and the tutor gets a sensitivity table back.
- **Then `run_rl(n)`:** TD3 alone in that space, in bursts starting at the current best design.
- **The harness:** 2 agents (tutor, reviewer) + a 2-step orchestrator; `AGENTS.md` 1.5 kB; 4 tools (1.7 kB).

**Test run** (Claude Code playing the agents; `CAD/harness/sessions/2026-11-06_claude-code-tutor/`):
- **5 tool calls, 13 model turns, ≈ 30k input tokens** (v1 ≈ 244k, v2 ≈ 126k).
- **From a failing nominal** (FoM −0.17), the tutor's balanced warm-up designs meet all specs (0.606).
- **The RL improves alone** to **0.650** in 130 simulations, and 88 of 118 distinct designs meet all specs.

| | tokens (input) | simulations | best FoM | found by |
|---|---|---|---|---|
| v1 (LLM designs) | ≈ 244k | 16 | 0.684 | the LLM |
| v2 (LLM + RL bursts) | ≈ 126k | 97 | 0.677 | the LLM |
| v3 (LLM tutors the RL) | ≈ 30k | 146 | 0.650 | the RL |
| v3.1 (+ `refine` between two RL runs) | ≈ 46k | 199 | 0.686 | the LLM's refine, after the RL |
| **v3.2, final (one RL run, then `refine`, end)** | **≈ 39k** | **101** | **0.686** | **the LLM's refine, after the RL** |

**Reading:**
- v3 is 8× cheaper in tokens, and the RL really optimizes in a space the LLM made well-conditioned, which gives many
  feasible designs. It costs more simulations and ends slightly below the LLM-only best.

**Version 3.1** (the same branch): the tutor calls `run_rl` twice, with **one educated improvement** in between:
- `refine`: 1–5 reasoned designs relative to the best, and optionally a re-centred search space (the replay buffer
  keeps the designs inside it, with re-encoded actions);
- a **hard budget of 199 simulations** in the code.

Test run (`CAD/harness/sessions/2026-11-06_claude-code-tutor2/`), with the same setup as v3:
- `setup_rl` → 0.606;
- RL run 1 (80 sims) → 0.646;
- **`refine` → 0.686**: Cc 0.3 pF together with an I2 cut, a coupled move. The cut alone fails UGBW; Cc's UGBW gain
  makes it pass. The RL hadn't found it;
- RL run 2 (98 sims) → no further gain, because the design sits on the PM and UGBW limits;
- **199 simulations, 7 tool calls, ≈ 46k input tokens**;
- **the best FoM of all versions**, at about a fifth of v1's tokens.

**Version 3.2, the final harness:** RL run 2 of v3.1 found nothing, so it was dropped. The session is now setup →
one RL run (the tutor judges its size, 60–100) → `refine` → end. The same 0.686 in **101 simulations, ≈ 39k
tokens** (derived from v3.1's first 101 simulations, which are exactly this session). `refine`'s optional re-centred
space was removed with the second run.

**The first real agy session of v3.2** (Claude Sonnet 4.6, `CAD/harness/sessions/2026-11-06_agy-claude-sonnet/`):
- 101 simulations and 249 s, but **no design met all specs** (best −0.68: UGBW 38 MHz, PM 35°).
- **Why:** the tutor anchored on the netlist's placeholder `.param` values (W fixed at 0.5 µm, Cc 2 pF against its own
  GBW estimate, Rc 1.5 kΩ) and **fenced the RL in** (Cc 1–3 pF, Rc 0.5–2 kΩ). The region that meets the specs was
  unreachable, and the reviewer didn't question it. In v3, the tutor's setup is a single point of failure, and the
  trace shows exactly where it went wrong: a good explainability example.
- **Tokens** (agy's counts): 58.8k input + 207.5k cached input + 13.2k output. Most of it is agy's own system prompt
  and tool definitions, which are reread on every call.

**Prompt fixes** (circuit knowledge only):
- the netlist values are placeholders;
- check the nominal with your own equations before `setup_rl`;
- the space must contain what the equations demand (sub-pF Cc, Rc of several kΩ);
- the reviewer questions the space if nothing meets the specs.

A disciplined test run afterwards (Claude Code following only the prompt files, values derived from the equations;
`CAD/harness/sessions/2026-11-06_claude-code-fresh/`):
- the nominal misses only UGBW (87.8 MHz);
- the warm-up meets all specs (0.656);
- RL (80) → **0.669**;
- refine: no gain, because its moves were derived from the nominal's sensitivities, which had shifted;
- 101 simulations.
- A second real agy session with the fixed prompts is still to be run.

**The division of labour that works:**
- the LLM sets up the space and the warm-up and makes the circuit-level coupled move;
- the RL does the local search and supplies many feasible alternatives (124 of 177 designs met all specs).

---

## Tests overall
`cd CAD && python -m pytest -q`: **160 passed** (branch `feat/m4-tutor`):

| file | tests |
|---|---|
| `test_measure.py` | 50 |
| `test_env.py` | 25 |
| `test_sizing_tools.py` | 24 |
| `test_agent.py` | 11 |
| `test_wrapper.py` | 5 |
| `test_harness_files.py` | 5 |
| `test_runner.py` | 4 |
| `test_harness_vs_rl.py` | 4 |
| `test_reference_rewards.py` | 1 |
| `test_mcp_server.py` | 1 |
| `test_hybrid_tools.py` | 14 |
| `test_hybrid_mcp_server.py` | 1 |
| `test_tutor_tools.py` | 14 |
| `test_tutor_mcp_server.py` | 1 |

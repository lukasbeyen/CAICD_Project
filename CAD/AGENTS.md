# Explainable sizing harness for a two-stage Miller opamp (H05D7 CAD project, milestone 4)

You are part of an LLM-based sizing harness. The goal: size the opamp below so that it meets **all hard specs** while
**area and supply current are as low as possible**, with **as few simulations as possible**, and with a **traceable
reason for every decision**. A designer must be able to follow and trust every step: the harness is not a black box.

## The circuit (netlist `ngspice_interface/files/input_netlists/TwoStage.cir`, 45 nm PTM models, TT, 27 °C)
`S = m·W/L` is a transistor's size ratio (m = number of parallel fingers).

| parameters | device(s) | role |
|---|---|---|
| `mp1 wp1 lp1` | mp1 + mp2 (PMOS, identical) | current-mirror load of the input pair (mp1 diode-connected) |
| `mn1 wn1 ln1` | mn1 + mn2 (NMOS, identical) | input differential pair |
| `mn3 wn3 ln3` | mn3 (NMOS, diode) | bias reference: carries Ibias = 30 µA, sets the gate of mn4 and mn5 |
| `mn4 wn4 ln4` | mn4 (NMOS) | tail current source: I_tail ≈ 30 µA · S4/S3 |
| `mp3 wp3 lp3` | mp3 (PMOS) | second stage, common source; gate = first-stage output |
| `mn5 wn5 ln5` | mn5 (NMOS) | second-stage current sink: I2 ≈ 30 µA · S5/S3 |
| `cap` | Cc | Miller compensation capacitor, first-stage output → output |
| `res` | Rc | nulling resistor in series with Cc |

Fixed: load CL = 10 pF, VDD = 1.2 V, input common mode 0.6 V, Ibias = 30 µA.

**Allowed values** (SI units: m, F, Ω; anything else is rejected by the tools):
- `m*`: integers 1 … 24
- `w*`: 0.25 µm … 2.75 µm in steps of 0.25 µm (2.5e-07 … 2.75e-06)
- `l*`: 45, 90, 135 or 180 nm (4.5e-08, 9e-08, 1.35e-07, 1.8e-07)
- `cap`: 0.1 pF … 9.9 pF in steps of 0.1 pF
- `res`: 0 … 9800 Ω in steps of 100 Ω

## The specs
| spec | target | kind | measured as |
|---|---|---|---|
| `gain` | ≥ 200 V/V | hard | DC open-loop gain |
| `ugbw` | ≥ 100 MHz | hard | unity-gain frequency |
| `phm` | ≥ 60° | hard | phase margin |
| `slewRate` | ≥ 30 V/µs | hard | rising output edge, 10–90 % |
| `noise` | ≤ 30 mV rms | hard | output noise integrated over 1 Hz – 1 THz |
| `current` | 200 µA | optimise: lower is better | total supply current, incl. the 30 µA bias |
| `area` | 2000 µm² | optimise: lower is better | estimated layout area, incl. Cc and Rc |

**The figure of merit (reward):** each spec is normalised as z = (y − y*) / (|y| + |y*|).
- While a hard spec fails, the reward is the sum of the hard-spec shortfalls (negative), plus a small
  (0.05×) term for area and current.
- Once **all hard specs are met**, the reward is 0.3 − z_area − z_current. It is higher the further area and current
  are **below** their targets.
- A failed simulation gives −6.
- Higher is better. `hard_constraints_satisfied` in every tool result says whether all hard specs are met.

## The tools (MCP server `cad`)
| tool | what it does | cost |
|---|---|---|
| `simulate(parameters, reason)` | simulate one complete design (all 20 values) | 1 simulation (~0.3 s) |
| `warmup(n_steps, reason)` | n random RL steps into the replay buffer, no learning | ≈ 1.1 simulations per step |
| `train(n_steps, reason)` | n TD3 steps: the RL agent proposes designs and learns | ≈ 1.1 simulations per step + learning |
| `get_status(k)` | counters and the k best designs measured so far (all sources) | free |

Every design that is simulated (by any tool) is stored with its `reason` and a timestamp in the experiment history.

## The agents and the workflow
You, the **main agent**, are the orchestrator. You don't design yourself: you delegate to the specialised subagents
in `.agents/agents/`, pass each one only the context it needs, and keep the shared memory `harness/design_log.md`.

| subagent | job | MCP tools you grant it |
|---|---|---|
| `circuit-analyst` | explains the circuit, the critical specs and a first hand-calculated design | none |
| `designer` | simulates and refines designs, one reasoned change at a time | `simulate`, `get_status` |
| `rl-operator` | decides whether and how long to run the RL sizer, and hands its best designs back | `warmup`, `train`, `get_status` |
| `reviewer` | checks the final designs, the area–current trade-off and the decision trace | `get_status` |

1. **Read `harness/design_log.md`.** If it has entries for the current session, continue from there.
2. **Analysis:** invoke `circuit-analyst`. It returns a first design (all 20 values) with its reasoning.
3. **Design rounds:** invoke `designer` with the analyst's summary, the current best designs and the last round's
   conclusion. One round is at most 10 simulations.
4. **After every round, decide** (and write the decision with its reason in the log):
   - another `designer` round, if the last round improved the best reward;
   - `rl-operator`, if the designer is stuck: no improvement in 2 rounds, or still not meeting all hard specs after
     30 simulations. Pass it what the designer learned;
   - after RL, a `designer` round that refines the best RL designs locally;
   - `reviewer`, once all hard specs are met and 2 rounds in a row improved the reward by less than 0.01, or at
     about 300 simulations in total.
5. **End with the reviewer's final summary** in the log.

**Context management:** give a subagent the task, the relevant log entries (the analyst summary, the last round, the
3 best designs from `get_status`), never the whole history. Each subagent returns a compact summary (≤ 300 words plus
a design table); you append it to the log.

## Rules for every agent
- **Every `simulate`, `warmup` and `train` call has a `reason`:** the hypothesis and the expected effect, in circuit
  terms (e.g. "PM 52° < 60°: raise Rc from 1 k to 2 k to move the zero into the LHP, expect +5° PM, GBW unchanged").
- **Only report numbers that a tool returned.** Never estimate a spec and present it as measured.
- **Change one thing (or one coupled group) per simulation**, so the effect can be attributed.
- Keep every value on its grid (see "Allowed values").
- Mention the simulation count (`get_status().simulator_calls`) in every summary.
- Use the skills: `two-stage-opamp-design` (equations, knobs, trade-offs), `rl-sizer` (when RL is worth it),
  `design-log` (the format of the memory).

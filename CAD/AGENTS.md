# Opamp sizing harness (LLM + RL)

Goal: size the two-stage Miller opamp so that all hard specs are met and area and supply current are as low as
possible, within **100–200 simulations in total**, with a reason for every decision.

| spec | target | kind |
|---|---|---|
| gain | ≥ 200 V/V | hard |
| ugbw | ≥ 100 MHz | hard |
| phm | ≥ 60° | hard |
| slewRate | ≥ 30 V/µs (rising edge) | hard |
| noise | ≤ 30 mV rms | hard |
| current | 200 µA, lower is better | target |
| area | 2000 µm², lower is better | target |

**FoM** (the reward, higher is better), with z = (y − y*)/(|y| + |y*|):
- while a hard spec fails, the sum of the hard-spec shortfalls (+ 0.05 × the target terms);
- once all hard specs are met, 0.3 − z_area − z_current;
- a failed simulation: −6.

The circuit, its 20 parameters and their allowed values: skill `opamp-design`. How the RL tool works: skill
`hybrid-rl`.

## Tools (MCP server `cad`)
- `simulate(parameters | changes, base, reason)`: 1 simulation. Give only the changed values relative to `base`
  ("best" or a simulation number). Every design also becomes RL experience.
- `rl_explore(n_steps, reason)`: n simulations of TD3 around the current best design.
- `get_status(k)`: the k best designs; no simulation.
- `log_entry(agent, text)`: your step in the design log (≤ 1200 characters).

## Pipeline (the main agent runs it; it delegates and does not design itself)
1. `designer`, phase A+B: analysis, a hand design, refinement (≤ 10 simulations).
2. Repeat the cycle: `rl-explorer` (one burst, ~30 simulations) → `designer` phase C (explain RL's change, 2–4
   simulations). Stop when about 150 simulations are used, or after 2 cycles without a better design.
3. `reviewer`: the final check and summary.

Pass each agent only its phase, the simulation count and the previous agent's return. The memory is
`harness/design_log.md`; agents read it only when they need it.

## Rules (all agents)
- Every `simulate` and `rl_explore` call has a `reason`: hypothesis → expected effect.
- The designer changes one thing (or one coupled group) per simulation.
- Report only numbers that the tools returned.
- Log your step with one `log_entry` (reasoning, actions with simulation numbers, result, next), and return ≤ 80
  words.

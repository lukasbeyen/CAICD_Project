# Opamp sizing harness: the LLM tutors the RL

Goal: size the two-stage Miller opamp so that all hard specs are met and area and supply current are as low as
possible, with **strictly fewer than 200 simulations** in total (the tools enforce it). The LLM doesn't design step
by step. It sets up the RL's job (a nominal design, the RL's search space, a warm-up set), TD3 does the optimizing,
then the LLM makes one educated improvement and the session ends.

| spec | target | kind |
|---|---|---|
| gain, ugbw, phm | ≥ 200 V/V, ≥ 100 MHz, ≥ 60° | hard |
| slewRate (rising), noise | ≥ 30 V/µs, ≤ 30 mV rms | hard |
| current, area | 200 µA, 2000 µm², lower is better | targets |

**FoM** (the reward, higher is better), with z = (y − y*)/(|y| + |y*|):
- a failing hard spec costs its shortfall;
- once all hard specs are met, 0.3 − z_area − z_current;
- a failed simulation: −6.

## Tools (MCP server `cad`)
- `setup_rl`: once; the nominal, the search space and the warm-up. Returns a sensitivity table.
- `run_rl`: TD3 alone, n simulations.
- `refine`: after the RL run; 2 rounds of 1–5 reasoned designs.
- `get_status`: the best designs; no simulation.
- `log_entry`: your step in the log, ≤ 1200 characters.

## Pipeline and rules
- **Pipeline:** the main agent calls `tutor`, then `reviewer` with the tutor's return. Nothing else.
- **Skills:** `opamp-design` (the circuit, the allowed values, the equations) and `rl-tutoring` (how to set up the RL).
- **Rules:**
  - **start from scratch:** read only `AGENTS.md`, the skills, the netlist
    (`ngspice_interface/files/input_netlists/TwoStage.cir`) and `harness/design_log.md`; never earlier results
    (`harness/sessions/`, `runs/`, `solutions/`, `../Solutions/`, `../docs/`);
  - every warm-up design has a purpose;
  - report only numbers that the tools returned;
  - each agent writes one `log_entry` and returns ≤ 80 words.

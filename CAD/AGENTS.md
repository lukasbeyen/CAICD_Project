# Opamp sizing harness: the LLM tutors the RL

Goal: size the two-stage Miller opamp so that all hard specs are met and area and supply current are as low as
possible, with **strictly fewer than 200 simulations** in total (count them with `simulator_calls`;
nothing else stops you). The LLM gives the RL a good start: a hand design from the equations, around which the
RL's warm-up explores. Then TD3 trains, and the LLM refines the best design.

| spec | target | kind |
|---|---|---|
| gain, ugbw, phm | ≥ 200 V/V, ≥ 100 MHz, ≥ 60° | hard |
| slewRate (rising), noise | ≥ 30 V/µs, ≤ 30 mV rms | hard |
| current, area | 200 µA, 2000 µm², lower is better | targets |

**FoM** (the reward, higher is better), with z = (y − y*)/(|y| + |y*|):
- a failing hard spec costs its shortfall;
- once all hard specs are met, 0.3 − z_area − z_current;
- a failed simulation: −6.

## Tools (MCP server `cad`, the course's `mcp_server.py`)
- `simulate`: one design (all 20 values), 1 simulation; the best design so far is where `warmup` explores.
- `warmup`: n random RL transitions **around the best design so far**, without learning.
- `train`: TD3 learns, n transitions; needs ≥ 100 transitions first (`warmup(100)`).
- `get_status`: the k best designs and the counters; no simulation.

Every 10 RL steps an episode reset costs one extra simulation. Each call takes a one-sentence `reason`.

## Pipeline and rules
- **Pipeline:** the main agent calls `tutor`, then `reviewer` with the tutor's return. Nothing else.
- **Skills:** `opamp-design` (the circuit, the equations) and `rl-tutoring` (how the RL tools work).
- **Rules:**
  - **start from scratch:** read only `AGENTS.md`, the skills and the netlist
    (`ngspice_interface/files/input_netlists/TwoStage.cir`); never earlier results (`harness/sessions/`, `runs/`,
    `solutions/`, `../Solutions/`, `../docs/`);
  - report only numbers that the tools returned;
  - each agent returns ≤ 80 words (the reviewer ≤ 150).

# Sizing a two-stage Miller opamp with TD3 and an LLM agentic harness

H05D7 Computer-Aided IC Design, CAD project 2026 — Brent and Lukas.

This folder is the complete, runnable project: the course's `CAD/` folder with all TODOs filled in, the unit tests,
the LLM harness, and the results of our final runs. The netlists of the Pareto solutions are in `../Solutions/`, next to
this folder.

## Where each milestone is

| milestone | code | tests (`tests/`) |
|---|---|---|
| 1. Simulator interface | `ngspice_interface/files/input_netlists/TwoStage.cir` (the testbench writes its results with `wrdata`), `ngspice_interface/ngspice_wrapper.py`, `ngspice_interface/dut_testbench.py` (gain, UGBW, phase margin, slew rate, noise, current; area: `area_estimation.py`) | `test_measure.py`, `test_wrapper.py` |
| 2. Circuit environment | `circuit_env.py` (action refinement, spec normalization, reward, `reset`, `step`) | `test_env.py`, `test_reference_rewards.py` |
| 3. TD3 agent | `td3/agent.py` (`select_action`, `update_parameters`), `td3_runner.py` (episodic loop, hyperparameters) | `test_agent.py`, `test_runner.py` |
| 4. LLM harness | `sizing_tools.py` (the template's tools), `mcp_server.py`, `AGENTS.md`, `.agents/agents/` (`tutor`, `reviewer`), `.agents/skills/` (`opamp-design`, `rl-tutoring`), `session_prompt.md` | `test_sizing_tools.py`, `test_mcp_server.py`, `test_harness_files.py` |

The circuit definition (parameters, grid, targets, hard constraints, weights) is
`ngspice_interface/files/yaml_files/TwoStage.yaml`; the TAs' reference designs are `references.csv`.

## Setup
- Linux, `ngspice` in the PATH (tested with ngspice 45.2), Python ≥ 3.10.
- The TAs' SAC baseline (`sac_runner…so`, `td3/sac_baseline…so`) only loads on x86-64 Linux with Python 3.9. Everything
  else works without it (`td3` then sets `SAC = None`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Run everything from this folder:** the course code builds its paths from the current directory.

## Unit tests
```bash
python -m pytest -q          # 75 tests, about 15 s; a few of them run ngspice
```

## TD3 (milestone 3)
```bash
python td3_runner.py --seed 123456              # one run: 5000 simulations, about 15 min on one CPU core
python td3_runner.py --help                     # the hyperparameters (noise sigma, batch size, warm-up, learning rates)
```
- The run stops after `--max_sims` simulations (default 5000, the budget for comparing with the baseline). Every
  simulation counts, including the random design of each episode's reset.
- Output:
  - `runs/<run_id>/`: the YAML and the hyperparameters of the run, the trained networks, the netlists of every design
    that met all hard specs, and the ngspice logs;
  - `solutions/<run_id>.csv`: every design that met all hard specs;
  - `output_figs/<run_id>/`: the maximum reward, the average score per episode and the current-area Pareto front.
- `clean.sh` empties `no_backup/` (the working netlists and ngspice output) every 100 steps.

The baseline: `python baseline_runner.py` (Python 3.9, x86-64).

## LLM harness (milestone 4)
The harness runs in Antigravity CLI (`agy`). The main agent calls the **tutor** and then the **reviewer**.

1. **The tutor runs RL → LLM → RL:**
   - TD3 from scratch: `warmup(100)` + `train(800)`;
   - then at most 5 `simulate` refinements, each reasoned with the design equations;
   - then a second `warmup(200)` + `train(800)` around the best design;
   - finally it decides whether at most 3 more refinements can still help.
2. **The reviewer** explains the final design, its margins, the Pareto designs and the cost per phase.

A session uses about 2100 simulations and 26–28 model calls, and takes about 13 minutes.

**Once:**
1. Install agy with `curl -fsSL https://antigravity.google/cli/install.sh | bash`, then log in.
2. agy reads the MCP server from `.agents/mcp_config.json` when it is started in this folder. The paths in that file
   are those of our machine. Set them for yours, all absolute:
   - `command`: the venv's python (the one with `mcp` installed);
   - `args`: the path to `mcp_server.py`;
   - `cwd`: this folder;
   - `PATH`: keep `/usr/local/bin:/usr/bin:/bin` and add the folder of `ngspice` if it is elsewhere.

   The seed: add `"--seed", "N"` after `mcp_server.py` (default 123456). The seed belongs to the MCP server, not to
   `td3_runner.py`.

**A session:**
```bash
agy --new-project --model claude-sonnet-4-6 \
  --settings '{"permissions":{"allow":["mcp(cad/simulate)","mcp(cad/warmup)","mcp(cad/train)","mcp(cad/get_status)"]}}'
```
- Type `/mcp` first. `cad` must list 4 tools: `simulate`, `warmup`, `train` and `get_status`.
- If it lists none, check the paths in `.agents/mcp_config.json`. Without the tools the agents cannot simulate, but
  they still spend tokens.
- Then paste the contents of `session_prompt.md`.
- agy may ask to approve reading the skill files: that is expected. The harness itself never edits files.

Output: `runs/mcp_<time>/harness_history.csv` has one row per simulation. Each row holds the tool that caused it, the
agent's reason, the 20 sizes, the specs and the reward. The netlists of the designs that met all specs are in
`runs/mcp_<time>/feasible_netlists/`. The reviewer's summary is agy's final answer.

## Results (`results/`)
The numbers and the comparisons are in the report; this folder holds the raw data behind them.
- `results/harness/*.csv`: the `harness_history.csv` of each harness session in the report. The `reason` column is
  the decision trace: why the agent chose each design it simulated, and why it called each warm-up or training.
  - `agy_rl_llm_rl_seed{123456,3}.csv`: the final harness in agy (the setup above);
  - `rl_llm_rl_seed{3,4,5}.csv` and `llm_first_big_rl_seed{3,4,5}.csv`: the earlier evaluations of the two flows.
- `results/td3/`: the final TD3 runs *(to be added)*.

## Solutions
`../Solutions/` holds the netlists of the Pareto designs of the final TD3 run after 5000 simulations,
plus `Solutions.csv` with their parameters, specs and FoM.

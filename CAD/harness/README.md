# Running the sizing harness (version 4: the course's tools, the LLM tutors the RL) with Antigravity CLI (`agy`)

The harness uses only the course's milestone 4 template: `mcp_server.py` and its 4 tools, implemented in
`sizing_tools.py`. The LLM gives the RL a good start:
- **tutor:**
  - designs a nominal from the equations and checks it with `simulate`;
  - runs `warmup(100)`: since a design has been simulated, the random warm-up designs are drawn around the best
    design so far (TD3's noise σ 0.1), not over the whole grid;
  - runs `train`;
  - refines the best design with a few `simulate` calls.
- **reviewer:** explains the final design, its margins and the cost.

The harness consists of:
- `AGENTS.md`;
- `.agents/agents/`: `tutor`, `reviewer`;
- `.agents/skills/`: `opamp-design`, `rl-tutoring`;
- `.agents/mcp_config.json` → `mcp_server.py` → `sizing_tools.py` (`SizingExperiment`).

## Once
1. Install with `curl -fsSL https://antigravity.google/cli/install.sh | bash`, then `agy --version`.
2. The paths in `.agents/mcp_config.json` are for Brent's VM; adapt `command`, `args` and `cwd` elsewhere.
3. In `agy`: "always allow" (project scope) for the `cad` tools.

## A session
```bash
cd CAD
agy --new-project       # paste harness/session_prompt.md
```
It leaves behind `runs/mcp_<time>/harness_history.csv` (one row per simulation: source `simulate` / `reset` /
`warmup` / `train`, the agent's reason) and `runs/mcp_<time>/feasible_netlists/`.

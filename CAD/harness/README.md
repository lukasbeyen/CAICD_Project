# Running the sizing harness (RL → LLM → RL, the course's tools) with Antigravity CLI (`agy`)

The harness uses only the course's milestone 4 template: `mcp_server.py` and its 4 tools, implemented in
`sizing_tools.py`. The main agent calls the tutor, then the reviewer:
- **tutor:**
  - RL first: `warmup(100)` (uniform, nothing simulated yet) and `train(800)`, TD3 from scratch;
  - refines the best design with ≤ 5 iterative `simulate` calls, reasoned with the equations;
  - RL again: `warmup(200)`, now drawn around the best design (TD3's noise σ 0.1), and `train(800)`, which first
    pulls the actor to the best design (the warm start);
  - decides whether ≤ 3 last `simulate` refinements can still help.
- **reviewer:** explains the final design, its margins, the Pareto designs and the cost per phase.

The harness consists of:
- `AGENTS.md`;
- `.agents/agents/`: `tutor`, `reviewer`;
- `.agents/skills/`: `opamp-design`, `rl-tutoring`;
- `.agents/mcp_config.json` → `mcp_server.py` → `sizing_tools.py` (`SizingExperiment`).

## Once
1. Install with `curl -fsSL https://antigravity.google/cli/install.sh | bash`, then `agy --version`.
2. The paths in `.agents/mcp_config.json` are for Brent's VM; adapt `command`, `args`, `cwd` and `PATH`
   elsewhere. `"--seed", "N"` after `mcp_server.py` in `args` picks the seed (default 123456). One `train(800)`
   must finish within `timeoutSeconds` (600; raise it on a slow machine).
3. In `agy`: "always allow" (project scope) for the `cad` tools.

## A session
```bash
cd CAD
agy --new-project --model claude-sonnet-4-6 \
  --settings '{"permissions":{"allow":["mcp(cad/simulate)","mcp(cad/warmup)","mcp(cad/train)","mcp(cad/get_status)"]}}'
# then paste harness/session_prompt.md
```
It leaves behind `runs/mcp_<time>/harness_history.csv` (one row per simulation: source `simulate` / `reset` /
`warmup` / `train`, the agent's reason) and `runs/mcp_<time>/feasible_netlists/`.

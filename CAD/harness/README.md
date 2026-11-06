# Running the sizing harness (version 2: LLM + RL) with Antigravity CLI (`agy`)

The harness consists of:
- `AGENTS.md`: the always-loaded context and the pipeline;
- `.agents/agents/`: `designer`, `rl-explorer`, `reviewer`;
- `.agents/skills/`: `opamp-design`, `hybrid-rl`;
- `.agents/mcp_config.json`: the MCP server `cad` = `hybrid_mcp_server.py` over `hybrid_tools.py`, which builds on
  `sizing_tools.py`;
- `harness/design_log.md`: the memory, written by the agents through `log_entry`.

The designer's designs become TD3 experience. Short RL bursts (`rl_explore`, ~30 simulations) search around the
current best design, and the designer explains and builds on what they find. The total budget is 100–200 simulations.

## Once
1. Install with `curl -fsSL https://antigravity.google/cli/install.sh | bash`, then `agy --version`.
2. The paths in `.agents/mcp_config.json` are for Brent's VM; adapt `command`, `args` and `cwd` on another machine.
3. In `agy`: allow the `cad` tools with "always allow" (project scope), so a session doesn't stop on a permission
   question.

## A session
```bash
cd CAD
agy                     # interactive: paste harness/session_prompt.md
agy -p "$(cat harness/session_prompt.md)" --output-format stream-json > harness/sessions/session_$(date +%Y%m%d_%H%M).jsonl
```

## What a session leaves behind
- `harness/design_log.md`: the reasoning per step.
- `runs/mcp_<time>/harness_history.csv`: every simulation (source `simulate` or `rl`, reason, specs, reward).
- `runs/mcp_<time>/feasible_netlists/`: the designs that met all specs.

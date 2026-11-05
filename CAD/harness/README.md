# Running the sizing harness with Antigravity CLI (`agy`)

The harness = `AGENTS.md` (always-loaded context and workflow), `.agents/agents/` (the 4 subagents),
`.agents/skills/` (3 skills), `.agents/mcp_config.json` (the `cad` MCP server = `mcp_server.py` + `sizing_tools.py`),
and `harness/design_log.md` (the shared memory).

## Once
1. Install: `curl -fsSL https://antigravity.google/cli/install.sh | bash` (Linux arm64/amd64, macOS), then open a
   new terminal; `agy --version`.
2. The paths in `.agents/mcp_config.json` are for Brent's VM. On another machine, change `command` (a Python with the
   course packages + `mcp`), `args` (the absolute path of `mcp_server.py`) and `cwd` (this `CAD/` folder). ngspice
   must be on the `PATH` given there.

## A session (interactive)
```bash
cd CAD
agy                      # first time: sign in with the Google AI Plus account
```
Inside `agy`:
- `/mcp`: `cad` is connected with 4 tools (`simulate`, `warmup`, `train`, `get_status`);
- `/skills`: `two-stage-opamp-design`, `rl-sizer`, `design-log`;
- `/model`: choose the model (write it in the session header of the design log);
- first test: *"Use the CAD tools to show the current experiment status."*;
- full run: paste the text of `harness/session_prompt.md`. Allow the `cad` tools when asked.

## A session (headless, for the traces in the report)
```bash
cd CAD
agy -p "$(cat harness/session_prompt.md)" --output-format stream-json > harness/sessions/session_$(date +%Y%m%d_%H%M).jsonl
```
In headless mode, tools that need approval are refused without asking. Allow the `cad` tools first (permission rule
`mcp(cad/*)`), or use the interactive mode.

## What a session leaves behind
- `harness/design_log.md`: the reasoning per step (the memory).
- `runs/mcp_<timestamp>/harness_history.csv`: every simulation with its time, source, reason, specs and reward.
- `runs/mcp_<timestamp>/feasible_netlists/`: the netlists of designs that met all specs.
- `harness/sessions/*.jsonl` (headless): the full transcript with every tool call.

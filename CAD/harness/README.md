# Running the sizing harness (version 3: the LLM tutors the RL) with Antigravity CLI (`agy`)

The LLM doesn't design step by step: the **tutor** sets up the RL's job in one call, and TD3 optimizes alone.
- `setup_rl`: a nominal hand design, the RL's search space (the free parameters with ~11 grid points each, the rest
  fixed) and a warm-up set with a purpose per design. Every design becomes TD3 experience, and a sensitivity table
  comes back.
- `run_rl`: TD3 in that space, in bursts that start at the current best design. It reports the best design's spec
  margins.
- `refine`: at most 2 rounds of reasoned designs relative to the best: probe single steps, then combine them.
- The **reviewer** then explains what the RL changed and checks the margins.

The harness consists of:
- `AGENTS.md`;
- `.agents/agents/`: `tutor`, `reviewer`;
- `.agents/skills/`: `opamp-design`, `rl-tutoring`;
- `.agents/mcp_config.json` → `tutor_mcp_server.py` over `tutor_tools.py` (`TutorExperiment`) → `sizing_tools.py` (the course template);
- `harness/design_log.md`: the memory, written through `log_entry`.

## Once
1. Install with `curl -fsSL https://antigravity.google/cli/install.sh | bash`, then `agy --version`.
2. The paths in `.agents/mcp_config.json` are for Brent's VM; adapt `command`, `args` and `cwd` elsewhere.
3. In `agy`: "always allow" (project scope) for the `cad` tools.

## A session
```bash
cd CAD
agy                     # paste harness/session_prompt.md
agy -p "$(cat harness/session_prompt.md)" --output-format stream-json > harness/sessions/session_$(date +%Y%m%d_%H%M).jsonl
```
It leaves behind: `harness/design_log.md`, `runs/mcp_<time>/harness_history.csv` (sources `simulate` = the tutor's
designs, `rl`), and `runs/mcp_<time>/feasible_netlists/`.

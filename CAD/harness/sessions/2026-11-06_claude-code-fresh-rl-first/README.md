# A fresh Claude Code session (Sonnet), RL-first flow (2026-11-06 17:47; started by Brent; 1985 simulations)

A new Claude Code chat with no history, locked down to resemble agy:
- `--tools "Read,Glob,Grep"`: no Bash, Write, Edit, web or subagents;
- `--strict-mcp-config` with only the course's `mcp_server.py`;
- reading `harness/sessions/`, `runs/` and `docs/` denied;
- `--model sonnet`.

`CLAUDE.md` and the auto-memory were still loaded (rules and two notes, no results). The flow was given in the
prompt, overriding the < 200 budget:
1. `warmup(100)` + `train(800)`;
2. ≤ 5 `simulate` refinements;
3. `warmup(100)` + `train(800)`;
4. a stop rule (a hard spec < 3 % margin → stop), else ≤ 3 more;
5. the reviewer summary.

**Checks:**
- **What it read:** `AGENTS.md`, `tutor.md`, `reviewer.md`, the two skills (one Glob of `.agents/skills/`). Not even
  the netlist.
- **It followed the flow:** 17 tool calls (6 reads, 4 RL calls, 2 × `get_status`, 5 × `simulate`).
- **The stop rule fired:** PM +2.8 %.

| phase | sims | best | running best | feasible |
|---|---|---|---|---|
| RL 1: `warmup(100)` uniform + `train(800)` | 990 | −0.025 | −0.025 | 6 |
| LLM 1: 5 × `simulate` (Cc 4.4 → 2.3 pF, balanced current cuts of mn4 + mn5 + mp3, mn1 ↑) | 5 | **0.333** | 0.333 | 5 |
| RL 2: `warmup(100)` around 0.333 | 100 | 0.597 | 0.597 | 50 |
| RL 2: `train(800)` | 800 | **0.601** | 0.601 | 394 |

- **Final: FoM 0.601**: 369 µA, 503 µm², UGBW 121 MHz, PM 61.7° (+2.8 %).
- 1985 sims, 1 failed, 455 feasible.
- Wall time 10.7 min (the API time, i.e. the LLM, 1.8 min).
- RL 1 is identical to `../2026-11-06_experiment-rl-llm-x2/` (the same seed and calls, verified), so the two runs
  differ only from the LLM step on.

**Tokens and cost (Claude Code's `/cost`):**
- 16 requests: 1.6k input + 501.1k cache read + 39.0k cache write + 8.3k output (Sonnet);
- a tiny Haiku call;
- $0.29 at API prices.

**Comparison with Claude Code in the long chat (`../2026-11-06_experiment-rl-llm-x2/`):**

| | the first LLM step | the next warm-up | train(800) | final |
|---|---|---|---|---|
| that run | 0.193 | 0.674 | 0.676 | 0.676 |
| this run | 0.333 | 0.597 | 0.601 | 0.601 |

A better first LLM step ended lower. That run handed over a design with large margins (UGBW +57 %, PM +38 %); this
one handed over a design whose UGBW was binding (+2.9 %), which left the local search less room to climb. One run
each, so this could be chance.

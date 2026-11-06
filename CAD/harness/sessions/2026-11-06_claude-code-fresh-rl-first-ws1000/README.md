# A fresh Claude Code session (Sonnet), RL-first flow with the warm start and `train(1000)` (2026-11-06 18:18; started by Brent; 2424 simulations)

The same locked-down launch as `../2026-11-06_claude-code-fresh-rl-first/`:
- `--tools "Read,Glob,Grep"`, only `cad` via `--strict-mcp-config`, sessions/runs/docs denied, `--model sonnet`;
- the same prompt with `train(1000)` in both RL phases.

The code has the actor warm start (`09ac3b5`); it only acts in phase 2's `train`.

**Checks:**
- It read only `AGENTS.md`, the agent prompts and the skills.
- 16 tool calls (6 reads, 4 RL, 2 × `get_status`, 4 × `simulate`).
- The stop rule fired: UGBW +2.2 %, PM +1.9 %.
- The first 990 simulations are identical to the earlier sessions (the same seed).

| phase | sims | best | running best | feasible | ends at |
|---|---|---|---|---|---|
| RL 1: `warmup(100)` + `train(1000)` | 1210 | 0.005 | 0.005 | 12 | 4.0 min |
| LLM: 4 × `simulate` (Cc ↓ for SR and area, balanced I2 cut mn5 + mp3) | 4 | **0.200** | 0.200 | 4 | 4.5 min |
| RL 2: `warmup(100)` around it | 111 | **0.634** | 0.634 | 38 | 5.1 min |
| RL 2: `train(1000)` with the warm start | 1099 | 0.625 | 0.634 | 378 | 9.5 min |

**Final: FoM 0.634** (from the warm-up):
- 271 µA, 693 µm²;
- UGBW 102.2 MHz (+2.2 %), PM 61.2° (+1.9 %).

2424 simulations, 1 failed, 432 feasible.

**Tokens (`/cost`):** 13 requests; Sonnet 1.5k input + 375.9k cache read + 28.3k cache write + 6.1k output; $0.22 at
API prices. Wall time 10.6 min, of which 1.4 min LLM (API).

**Reading:**
- RL 1's extra 200 steps lifted its best from −0.025 to 0.005 (12 instead of 6 feasible designs).
- The LLM step again turned it into a feasible design (0.200).
- The warm-up around that design again did the big climb (+0.43).
- Phase 2's training, despite the warm start, found nothing better than 0.634. The warm-up's best sat on two
  binding specs (UGBW +2.2 %, PM +1.9 %), so there was little room left to improve.
- Compare the controlled replay (`../2026-11-06_experiment-warmstart-replay/`): there the warm start gave +0.051 in
  phase 2. Not an A/B with this run (its phase 1 and LLM step differ).

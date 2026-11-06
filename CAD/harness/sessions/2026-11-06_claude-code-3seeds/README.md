# Three seeds in parallel: fresh Claude Code sessions (Sonnet), the RL-first flow, the warm start (2026-11-06 18:40; started by Brent)

**Setup:**
- One locked-down `claude --model sonnet --tools "Read,Glob,Grep" --strict-mcp-config` session per seed (123456,
  1, 2).
- Each in its own copy of `CAD/` (`~/harness_lanes/s<seed>/`): not in the repo, so no `CLAUDE.md` and no
  auto-memory, and no `harness/sessions/` or `runs/` to read. The copies also keep the parallel runs from deleting
  each other's files via `clean.sh`.
- The code has the actor warm start (`09ac3b5`).
- The flow (in the prompt):
  1. `warmup(100)` + `train(500)`;
  2. ≤ 5 `simulate`;
  3. `warmup(100)` + `train(800)`;
  4. the stop rule (a hard spec < 3 % margin → stop), else ≤ 3 `simulate`;
  5. the reviewer summary.

**Checks:**
- All three read only `AGENTS.md`, the agent prompts and the skills.
- Seed 1: one warm-up simulation failed, so the buffer held 99 < 100 transitions and `train` refused. The agent
  added `warmup(1)`, a sensible recovery.
- Seed 2: **inverted the stop rule.** It stopped "because every hard spec has more than 3 % margin" (UGBW +59 %,
  PM +21 %) instead of doing ≤ 3 more refinements.
- Claude Code moves MCP calls longer than 120 s to the background; the server's lock kept the order correct.

| seed | RL 1 | LLM 1 | warm-up 2 | train 2 (warm start) | LLM 2 | **final** | design | sims / feasible | time |
|---|---|---|---|---|---|---|---|---|---|
| 123456 | −0.168 | 0.064 | 0.626 | **0.636** | 0.629 (3 sims) | **0.636** | 324 µA, 545 µm² | 1657 / 460 | 9.8 min |
| 1 | −0.028 | 0.082 | **0.421** | 0.371 | stop (UGBW +0.4 %) | **0.421** | 235 µA, 1329 µm² | 1656 / 76 | 9.2 min |
| 2 | 0.151 | 0.248 | 0.322 | **0.410** | none (rule inverted) | **0.410** | 306 µA, 1031 µm² | 1655 / 41 | 8.4 min |

**Final FoM: mean 0.489, standard deviation 0.127.** All three runs had 2 failed simulations.

**Tokens** (from the transcripts):

| seed | requests | input | cache read | cache write | output |
|---|---|---|---|---|---|
| 123456 | 18 | 38 | 400k | 31k | 7.2k |
| 1 | 15 | 30 | 297k | 34k | 6.7k |
| 2 | 14 | 28 | 275k | 25k | 5.0k |

**Reading:**
- The seed matters a lot, as for TD3 in milestone 3 (0.702 / 0.660 / 0.662).
- Where it is lost:
  - RL 1 with 500 steps hands the LLM a poor design (−0.17 to 0.15);
  - the LLM's 5 refinements only reach 0.06–0.25;
  - the warm-up's climb depends on where it starts (+0.56, +0.34, +0.07).
- The warm start's effect on train 2: +0.01, none, and +0.09.

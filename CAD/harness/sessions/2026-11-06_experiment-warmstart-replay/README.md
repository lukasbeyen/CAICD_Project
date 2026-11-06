# Controlled replay: the warm start's effect on the second RL phase (2026-11-06 18:10; 1985 simulations)

The exact MCP calls of the fresh Claude Code session `../2026-11-06_claude-code-fresh-rl-first/` (taken from its
transcript): `warmup(100)`, `train(800)`, its 5 `simulate` designs, `warmup(100)`, `train(800)`. The same seed
(123456). The only difference is the code: `train` first pulls the actor to the best design (commit `09ac3b5`).
That happens only in phase 2, because phase 1 has no LLM design yet. **The first 1106 simulations are identical**
(verified), so only phase 2's `train(800)` differs.

| phase 2 `train(800)` | best before | best in train | gain | train designs better than before | first at train step | feasible |
|---|---|---|---|---|---|---|
| no warm start (the session) | 0.597 | 0.601 | +0.004 | 1 | 617 | 394 |
| **warm start (replay)** | 0.597 | **0.648** | **+0.051** | **8** | **7** | 336 |

**Final:** 0.6475, 343 µA, 483 µm², UGBW 101 MHz (+1 %), PM 61.8°.

**Reading:**
- With the warm start, TD3's training starts at the best design. It improves within 7 steps and finds 8 better
  designs.
- Without it, the actor starts where phase 1 left it. It needs 617 steps for one small improvement.
- The warm start costs 0 simulations and 0 tokens.
- One seed: a controlled A/B, not a statistic.

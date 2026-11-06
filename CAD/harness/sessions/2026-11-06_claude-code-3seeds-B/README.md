# Three seeds in parallel, round 3 ("B"): the adaptive LLM goal, the Cc rule in the skill, `warmup(200)`, a polish `warmup(50)` (2026-11-06 19:19–19:40; started by Brent)

The same setup as rounds 1 and 2: fresh locked-down Claude Code (Sonnet) sessions, one copy of `CAD/` per seed, the
warm start in the code. The `rl-tutoring` skill has the Cc sentence (`a2a41c6`). The flow (in the prompt):
1. `warmup(100)` + `train(800)`;
2. ≤ 5 iterative `simulate`, with an adaptive goal: margin ≥ 10 % if the best is weak or near a limit, else FoM;
3. `warmup(200)` + `train(800)`;
4. a polish `warmup(50)`;
5. the stop rule, else ≤ 3 `simulate`;
6. the reviewer summary.

**Checks:**
- All three read only the allowed files. Seeds 123456 and 2 did not read `AGENTS.md` explicitly (Claude Code seems
  to load it as a project file).
- Seed 1 recovered from a 99-transition buffer with `warmup(5)`.
- Seed 1 stopped correctly (PM +2.4 %); seeds 123456 and 2 did their 3 final refinements.

| seed | RL 1 | LLM 1 (Cc) | warm-up 2 | train 2 | polish | LLM 2 | **final** | design |
|---|---|---|---|---|---|---|---|---|
| 123456 | −0.025 | 0.085 (3.7 → 3.5 pF) | 0.564 | 0.586 | **0.633** | **0.664** | **0.664** | 291 µA, 583 µm², Cc 0.8 pF |
| 1 | −0.031 | 0.035 (6.3 → 5.0 pF) | 0.446 | **0.452** | 0.437 | none (stop) | **0.452** | 267 µA, 1087 µm², Cc 1.5 pF |
| 2 | 0.599 | 0.563 (0.4–0.6 pF) | **0.675** | 0.627 | 0.629 | **0.694** | **0.694** | 235 µA, 714 µm², Cc 0.4 pF |

Each phase cell is the best design of that phase alone.

| round | final FoM (s123456 / s1 / s2) | mean ± sd |
|---|---|---|
| 1 | 0.636 / 0.421 / 0.410 | 0.489 ± 0.127 |
| 2 | 0.671 / 0.337 / 0.610 | 0.539 ± 0.178 |
| **3 (B)** | 0.664 / 0.452 / 0.694 | **0.603 ± 0.132** |

≈ 2155 sims each (1–3 failed), 9.4–9.6 min (seed 2: 16.4 min; it started earlier and shared the CPU).

**Tokens:**

| seed | requests | cache read | cache write | output |
|---|---|---|---|---|
| 123456 | 20 | 483k | 33k | 10.2k |
| 1 | 16 | 376k | 31k | 10.3k |
| 2 | 19 | 466k | 34k | 11.0k |

**Reading:**
- The polish warm-up helped seed 123456 (+0.05).
- The final LLM step found the final design in 2 of 3 runs (+0.03, +0.02). In earlier rounds it never gained.
- The bigger second warm-up gave seed 2 +0.11.
- Seed 1 improved (0.337 → 0.452), but its first LLM step still only moved Cc 6.3 → 5.0 pF: the 10 % margin goal
  overrode the new Cc rule.

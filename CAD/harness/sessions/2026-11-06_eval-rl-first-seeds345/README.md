# Evaluation: the RL-first flow (B, general wording) on unseen seeds 3, 4, 5 (2026-11-06 19:49; started by Brent)

The frozen harness: the code at `908d8a6` (the warm start; the skills with general knowledge only). Seeds 3, 4, 5
were never used to tune the flow. One fresh locked-down Claude Code (Sonnet) session per seed, each in its own copy
`~/harness_lanes/s<seed>/`. The prompt (general wording):
1. `warmup(100)` + `train(800)`;
2. `get_status(10)`, ≤ 5 iterative `simulate`, each `reason` estimating the effect on the margins and both FoM terms;
   the margin is weighed against the FoM by the agent itself;
3. `warmup(200)` + `train(800)`;
4. a polish `warmup(50)`;
5. a judgement stop, else ≤ 3 refinements;
6. the reviewer summary.

**Checks:**
- All three read only the allowed files.
- All three stopped by their own judgement (PM or UGBW limiting, with reasons).
- Seed 4 recovered from a 99-transition buffer with `warmup(5)`.

| seed | RL 1 | LLM step (sims; Cc) | warm-up 2 | train 2 (warm start) | polish | **final** | design |
|---|---|---|---|---|---|---|---|
| 3 | 0.015 | **0.691** (2; 0.6 pF) | 0.697 | **0.702** | 0.634 | **0.702** | 230 µA, 716 µm², Cc 0.5 pF |
| 4 | 0.433 | 0.593 (4; 1.0 pF) | 0.603 | **0.616** | 0.558 | **0.616** | 256 µA, 780 µm², Cc 0.8 pF |
| 5 | 0.325 | **0.652** (5; 2.6 → 0.6 pF) | 0.644 | **0.698** | 0.662 | **0.698** | 221 µA, 762 µm², Cc 0.5 pF |

Each phase cell is the best of that phase alone.

- **Final FoM: mean 0.672, standard deviation 0.049** (min 0.616, max 0.702).
- ≈ 2150 sims each (1–3 failed), 9.0–10.2 min in parallel. The best was found at sims 1687–1868.

**Tokens:**

| seed | requests | cache read | cache write | output |
|---|---|---|---|---|
| 3 | 13 | 269k | 32k | 6.2k |
| 4 | 17 | 414k | 36k | 8.1k |
| 5 | 17 | 421k | 37k | 9.3k |

**Reading:**
- **The LLM step made the large moves itself.** Following the general skill sentence ("large moves must come from
  you, derived from the equations"), it brought Cc into the sub-pF range: seed 3 in 2 simulations (0.015 → 0.691);
  seed 5 iteratively, 2.6 → 0.6 pF (0.325 → 0.652).
- **Train 2 with the warm start improved in all three** (+0.005, +0.013, +0.054) and produced every final design.
- The polish warm-up never produced the final design here.
- Compared with the development rounds on seeds 123456 / 1 / 2 (0.489 → 0.539 → 0.603, sd 0.13–0.18): a higher
  mean and a much smaller spread.

# Experiment: `train(2000)` with the warm start (2026-11-06 15:55; not a harness session, 2313 simulations)

The same seed and first 4 tool calls as `../2026-11-06_claude-code-template/`: the first 113 simulations are
identical (best 0.6462 from the warm-up). Then 2 × `train(1000)`; the template allows at most 1000 steps per call.
The best design didn't change in part 1, so part 2 didn't warm-start the actor again: pure TD3 after the single
initial clone.

| training steps | median distance from the warm-up's best (grid steps) | median reward | best in the block | feasible | training's running best |
|---|---|---|---|---|---|
| 1–100 | 88 | −2.06 | 0.594 | 2 | 0.594 |
| 101–200 | 48 | −1.07 | 0.359 | 2 | 0.594 |
| 201–300 | 26 | −0.88 | 0.582 | 3 | 0.594 |
| 401–500 | 24 | −0.91 | −0.022 | 0 | 0.594 |
| 701–800 | 28 | −0.87 | 0.613 | 3 | 0.613 |
| 1001–1100 | 24 | −0.57 | 0.618 | 9 | 0.618 |
| 1101–1200 | 21 | −0.46 | 0.635 | 10 | 0.635 |
| 1401–1500 | 24 | −0.33 | 0.600 | 15 | 0.635 |
| **1501–1600** | 24 | **−0.28** | **0.699** | **20** | **0.699** |
| 1801–1900 | 26 | −0.29 | 0.610 | 17 | 0.699 |
| 1901–2000 | 30 | −0.52 | 0.596 | 11 | 0.699 |

**Best: FoM 0.6987** (simulation 1780, training step ≈ 1580):
- current 192 µA (below the 200 µA target), area 902 µm²;
- UGBW 100.1 MHz (+0.1 %), PM 64.7°.

That's above all harness versions (≤ 0.686). 172 designs meet all specs; 5 simulations failed.

**Reading:**
- After the U-shape of the first 200 steps (see `../2026-11-06_experiment-train200/`), TD3 settles around the
  LLM's region (≈ 21–30 grid steps from the warm-up's best).
- It then improves steadily: the median reward −2.1 → −0.3, and the feasible designs per 100 steps 2 → 20.
- It first beats the warm-up's 0.646 at training step 1515.
- So the RL is not useless. It needs ≈ 1500 training steps here, far beyond the harness's < 200 budget.
- One seed: a single run, not a statistic.

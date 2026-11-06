# Experiment: `train(200)` with the warm start (2026-11-06 15:52; not a harness session, 333 simulations)

The same seed and first 4 tool calls as `../2026-11-06_claude-code-template/`: the first 113 simulations are
identical (best 0.6462 from the warm-up). Then `train(200)` with the actor warm start (v4.1) instead of 60 steps.
This exceeds the harness budget (< 200) on purpose. The question: does TD3 improve with more steps?

| training steps | median distance from the best (grid steps) | median reward | best | feasible |
|---|---|---|---|---|
| 1–25 | 19 | −0.81 | 0.594 | 2 |
| 26–50 | 72 | −1.81 | −0.846 | 0 |
| 51–75 | 103 | −2.33 | −1.278 | 0 |
| 76–100 | 120 | −3.48 | −1.653 | 0 |
| 101–125 | 105 | −3.30 | −0.904 | 0 |
| 126–150 | 63 | −1.15 | −0.256 | 0 |
| 151–175 | 44 | −0.70 | 0.359 | 2 |
| 176–200 | 34 | −0.88 | −0.025 | 0 |

**No improvement:** the best stays 0.6462 (the warm-up's). No training design beats it; 4 of 200 meet all specs.

**Reading: a U-shape.**
- The warm-started actor starts at the design.
- In the first ~100 steps it is pulled away (to ~120 grid steps), because the critics' slope is still unreliable.
- From ~step 100 the critics have learned enough that the actor comes back: 34 grid steps, the median reward
  −3.5 → −0.9.
- So TD3 is learning, but after 200 steps it has only got back near where it started. It would need many more
  steps to beat a local search around a good design. That's consistent with milestone 3, where TD3 needed
  thousands of simulations.

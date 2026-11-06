# A/B test of harness v4.1: `train` with the actor warm start (2026-11-06 15:33)

The same seed and the same tool calls as `../2026-11-06_claude-code-template/` (v4). Only the code differs: `train`
first pulls the actor to the best design (behaviour cloning, no simulations).
- The first 113 simulations (3 × `simulate` + `warmup(100)`) are identical to v4, except for the netlist file names
  (timestamps).
- Then `train(60)`.
- The best design after training is the same as in v4, so the tutor's refining starts from the same state; v4's 10
  refining calls were replayed.

| `train(60)` | median distance from the best (first 10 steps) | last 10 steps | median reward | feasible | best |
|---|---|---|---|---|---|
| v4, no warm start | 145 grid steps | 110 | −2.67 | 0 / 60 | −1.508 |
| **v4.1, warm start** | **16** | **96** | −1.68 | **2 / 60** | 0.594 |

**Final: FoM 0.678, 189 simulations** (the same as v4; 24 instead of 22 designs meet all specs).

**Reading:**
- The warm start puts the training where it should start, at the LLM's design (16 instead of 145 grid steps).
- Within 60 steps TD3 drifts away again. Its critics have had only 60 updates, so their slope is still unreliable,
  and 30 delayed actor updates following it pull the actor out of the good region. The random reset every 10 steps
  also shows the actor states it never saw.
- Net result: training finds 2 feasible designs instead of 0, but nothing better than the warm-up's 0.646.

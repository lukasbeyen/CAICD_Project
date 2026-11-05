---
name: rl-sizer
description: When and how to use the TD3 reinforcement-learning sizer (the CAD warmup and train tools) - what it costs in simulations, what it is good at, and a batch procedure with stop criteria.
---
# Using the RL sizer (TD3) as a tool

## What it is
- **TD3** (twin-delayed DDPG, Fujimoto et al. 2018): an actor network proposes all 20 sizes at once; two critic
  networks learn the expected reward from the stored experience.
- **Episodes:** each one starts from a **random** design (a reset, one extra simulation) and takes 10 steps. The RL
  sizer therefore does *not* start from the designer's best design: it explores the whole design space.
- **Fixed settings** (given by the course, not ours to change): exploration noise 0.1, actor and critic learning
  rate 3e-4, batch size 100.

## What it costs
- `warmup(n)`: n random designs, ≈ 1.1·n simulations (the resets), no learning.
- `train(n)`: n designs proposed by the actor, ≈ 1.1·n simulations, plus one network update per step.
- Reference from milestone 3 (our TD3 runner, other settings): the first design meeting all specs came after
  ~700–2000 simulations, the best after ~2000–4500. RL is **expensive in simulations**. It is worth it only when it
  is likely to find something the designer cannot.

## When it is worth it
- **Yes:** the designer is stuck in an infeasible region (two specs fight and every local change trades one for the
  other); or the designer has no good starting point; or you want to see whether a very different region of the
  design space (other currents, Cc, lengths) does better.
- **No:** the designer is still improving; one spec misses by a few percent (a local change will fix it); or the
  remaining simulation budget is small.

## Procedure
1. `warmup` in batches of ≤ 200 steps until the buffer is well above the batch size (100). More random data gives
   the critics a better first picture: in milestone 3 a long warm-up (~1000 steps) worked best, but that costs
   ~1100 simulations, so weigh it against the budget.
2. `train` in batches of 100–200 steps; after each batch call `get_status` and note the best reward.
3. Stop after 2 batches without a new best design, or at the budget.
4. Hand the top designs back to the designer **with what distinguishes them**: they are starting points for local
   refinement, which the designer does far more efficiently than RL.

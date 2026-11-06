---
name: hybrid-rl
description: How the rl_explore tool works - TD3 seeded with the designer's designs, short bursts around the best design - and how to size a burst and read its report.
---
# The RL tool (`rl_explore`)
- **It learns from every design.** Each `simulate` call also stores a TD3 transition (state = the normalized specs
  of the base design, action = the new design, reward = its FoM). There's no random warm-up: TD3 learns from the
  designer's designs right away.
- **It starts at the best design.** Before a burst the actor is pulled towards the current best design (no
  simulations), and every 10-step episode starts there. TD3 proposes the actor's output + noise σ 0.1 in action
  space. That's about ±5 % of each range: ±1 finger, ±0.5 pF Cc, ±0.5 kΩ Rc; less than a grid step for W and L, so
  those rarely move.
- **It learns while it searches:** one TD3 update per simulation, from all designs. A burst is a learned local
  search around the best design, and the designer's next changes become experience for the next burst.
- **Cost:** n steps = n simulations, ~0.3 s each, no LLM tokens per step. The settings (batch 100, learning rates
  3e-4) are the course's, fixed.
- **The report:**
  - `changes_vs_previous_best`: what the RL changed in its best design;
  - `rl_designs_better_than_previous_best`: how often it improved;
  - `new_best`, `best_reward`, `best_specs`.
- **Sizing a burst:** ~30 steps; 20 if the last burst found nothing; fewer near the end of the budget.

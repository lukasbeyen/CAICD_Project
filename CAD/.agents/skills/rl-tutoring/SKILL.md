---
name: rl-tutoring
description: How the course's RL tools work (simulate, warmup around the best design, train, episode resets), how far TD3's noise moves each parameter, how to split the budget and how to refine after the RL.
---
# Tutoring the RL
- **The RL:** TD3 (an actor and twin critics). Its action is a whole design (each parameter's grid mapped to
  [−1, 1]); its state is the normalized specs of the last design. It learns from its replay buffer.
- **`simulate`** doesn't enter the buffer, but it decides where the warm-up explores. `warmup` draws its random
  actions around **the best design measured so far** (by reward), with TD3's exploration noise σ 0.1. When a warm-up
  design is better, the centre moves there: a random local search around your design.
- **How far σ 0.1 moves a parameter**, per draw:
  - multiplicities (24 values): about ±1 finger, sometimes 2;
  - widths (11 values): one step in ≈ 30 % of the draws;
  - lengths (4 values): practically never;
  - Cc, Rc (99 values each): about ±0.5 pF and ±500 Ω.

  All parameters move at once, so every draw shifts the mirror balance a little. **Hand over a balanced design that
  passes all hard specs.** Margin gives the local search room to trade it for current or area, but it isn't free:
  weigh it against the FoM yourself, rather than maximizing either one alone.
- **Large changes must come from you.** The noise moves each parameter only a few grid steps per draw (above), so
  the RL can't make a large move, e.g. Cc to a very different value, by itself. Derive the values the specs actually
  need from the equations in `opamp-design`, rather than nudging the RL's design, and re-tune what depends on them.
- **Episodes** last 10 steps. Every reset is a uniformly random design: one simulation, usually far worse; it moves
  the centre only if it's better.
- **`train(n)`:** TD3 learns from every transition (one update per step). It needs ≥ 100 transitions (batch 100), so
  `warmup(100)` first. Before its first step, the actor is pulled to the best design (no simulation), so TD3 starts
  at your design and searches locally, where its critics learned from the warm-up. A reset costs one random
  simulation, but the next design is again near the best.
- **Budget** (strictly < 200, by rule): the nominal + fixes ≤ 6, `warmup(100)` ≈ 110, `train` 40–60 (+ resets),
  refining ≤ 10: ≈ 180–190 in total.
- **Refining after the RL** (`get_status(5)`, then `simulate` with all 20 values):
  - the margin of each hard spec = (y − y*)/y* (reversed for noise). The RL stops where a spec just passes; a spec
    with < 3 % margin is binding, and a current or area cut that costs it fails. First buy it headroom with another
    spec's margin (e.g. PM → Cc ↓ for UGBW), or step only on parameters that don't move it;
  - the sensitivities from your nominal don't hold at the best: probe single steps first, then combine;
  - a coupled move that keeps the mirror balance (mn4, mn5 and mp3 together), which random noise rarely finds;
  - a step that spends a spec's margin (e.g. PM headroom on area via Cc).

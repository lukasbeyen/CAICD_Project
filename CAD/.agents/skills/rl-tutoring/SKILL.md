---
name: rl-tutoring
description: How to set up the TD3 sizer's job - the search space (which parameters to free, how many grid points), the warm-up set - and how the RL uses them.
---
# Tutoring the RL
- **What the RL does:**
  - TD3 learns from every design in its replay buffer: the nominal, the warm-up, its own.
  - Each burst starts at the current best design, and the actor is first pulled towards it.
  - It proposes the actor's output + noise σ 0.1 in the action space [−1, 1] of each free parameter's range. Fixed
    parameters never move.
- **The search space sets the exploration.** With σ 0.1, the chance that a free parameter moves at least one grid
  step per RL step depends on its number of grid points:
  - 5 points ≈ 1 % (practically frozen);
  - 11 points ≈ 30 %;
  - 21 points ≈ 60 %, with larger jumps.
  
  So give the parameters to optimize about 11 points (e.g. multiplicities ±5 fingers, Cc ±0.5 pF, Rc ±500 Ω) and
  fix the rest.
- **The space must contain what the equations demand**, or the RL can never reach it: Cc small enough for
  GBW ≥ 100 MHz (Cc ≤ gm1/(2π·100 MHz), usually below 1 pF) and Rc around (1 + CL/Cc)/gm6 (several kΩ).
- **What to free:** the levers of the specs and targets: the tail and second-stage currents (mn4, mn5), mp3 (balance,
  gm6), the input pair (mn1), Cc, Rc.
- **What to fix:** all L (in 45 nm a different L breaks the mirror balance), the bias diode mn3 (the mirror ratios
  already set the currents), usually the widths.
- **A good warm-up** teaches the critic the local landscape:
  - ±1 grid step of every free parameter, one at a time;
  - 2–3 coupled moves, e.g. both mirror currents up/down with the balance S_p3/S_p1 = 2·S5/S4 kept.
  
  Every design is real data for the RL, and the table shows you the sensitivities.
- **After the RL run** (`refine`), use its report:
  - `best_margin_pct`: the RL stops where a spec just passes. A spec with < 3 % margin is binding: a current or area
    cut that costs it fails. First buy it headroom with another spec's margin (e.g. PM → Cc ↓ for UGBW), or step
    only on parameters that don't move it;
  - the warm-up's sensitivities hold at the nominal, not at the best: mix single steps with coupled ones;
  - `best_at_range_edge`: `refine` can't go further that way;
  - a coupled move that keeps the mirror balance (mn4, mn5 and mp3 together), which the RL's noise rarely finds.
- **Budget** (strictly < 200, enforced): nominal + warm-up ≈ 10–20, `run_rl` 60–100, `refine` 2–5: ≈ 80–120 in
  total.

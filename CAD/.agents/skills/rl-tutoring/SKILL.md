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
- **What to free:** the levers of the specs and targets: the tail and second-stage currents (mn4, mn5), mp3 (balance,
  gm6), the input pair (mn1), Cc, Rc.
- **What to fix:** all L (in 45 nm a different L breaks the mirror balance), the bias diode mn3 (the mirror ratios
  already set the currents), usually the widths.
- **A good warm-up** teaches the critic the local landscape:
  - ±1 grid step of every free parameter, one at a time;
  - 2–3 coupled moves, e.g. both mirror currents up/down with the balance S_p3/S_p1 = 2·S5/S4 kept.
  
  Every design is real data for the RL, and the table shows you the sensitivities.
- **Between the two RL runs** (`refine`), use the first run's report:
  - **reasoned designs:** a coupled move keeps the mirror balance (mn4, mn5 and mp3 together), which the RL's
    one-parameter-at-a-time noise rarely finds; or a step against the binding spec's margin;
  - **a new space**, only if needed: re-centre a parameter whose best value sits at the edge of its range; fix a
    parameter that never moved in the improvements; give a promising one more grid points. The buffer keeps the
    designs inside the new space.
- **Budget** (strictly < 200, enforced): nominal + warm-up ≈ 10–20, `run_rl` ≈ 80, `refine` 2–5, `run_rl` with
  the rest.

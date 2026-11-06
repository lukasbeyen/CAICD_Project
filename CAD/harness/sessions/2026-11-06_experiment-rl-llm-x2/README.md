# Experiment: RL first, then a little LLM refining, twice (2026-11-06 17:26; 1990 simulations)

Brent's idea: ≈ 1000 RL simulations, then a bit of LLM reasoning, twice. The course's 4 tools only: harness v4
(the warm-up around the best design, plain TD3 `train`, no actor warm start), seed 123456. Claude Code did the LLM
steps by the tutor's refining rules (not a blind agent). With the course tools, a `simulate` design reaches the RL
only through `warmup`, so each RL phase starts with a short warm-up.

| phase | calls | sims | best in phase | running best | feasible | time |
|---|---|---|---|---|---|---|
| RL 1 | `warmup(100)` (uniform: no LLM design yet) + `train(800)` | 990 | −0.025 (SR 29.8 V/µs, 589 µA) | −0.025 | 6 | 2.8 min |
| LLM 1 | 5 × `simulate`: Cc 4.4 → 2.5–3.5 pF + balanced cuts of I_tail and I2 | 5 | **0.193** | 0.193 | 5 | 1.0 min* |
| RL 2 | `warmup(100)` around the LLM's design + `train(800)` | 990 | **0.676** | 0.676 | 435 | 3.8 min |
| LLM 2 | 5 × `simulate`: gm1 ↑ for UGBW headroom, current cuts | 5 | 0.657 | 0.676 | 1 | 0.6 min* |

\* the LLM times are Claude Code's reasoning.

**Final: FoM 0.6756** (RL 2's `train`):
- gain 324, UGBW 102 MHz (+2 %), PM 63.5°, SR 64 V/µs, noise 7.3 mV;
- current 273 µA, area 615 µm².

1990 simulations, 1 failed, 447 feasible, 8.2 min.

**Reading:**
- **RL 1**, TD3 from scratch: 990 simulations, only 6 feasible designs; the best is a near-miss at 589 µA.
- **LLM 1**, 5 reasoned designs (I_tail/Cc for SR, balanced current cuts, Cc for area): −0.025 → 0.193, the first
  feasible design with a positive FoM.
- **RL 2's warm-up** around that design: 0.193 → 0.674 within 74 draws (at 4.2 min). The moving centre climbs, and
  TD3's buffer fills with a good region.
- **RL 2's `train`**: the median reward per 200 steps −0.03 → 0.32, and 387 of 800 designs feasible (vs 6 in
  phase 1). Best 0.676 (+0.002).
- **LLM 2**: no gain. UGBW is binding (+2 %), and every current cut fails it.
- Compared with:
  - milestone 3's TD3 alone: 0.684 after 3724 sims / 13.3 min on its best seed, never on the other two;
  - this run: 0.674 after 1069 sims / 4.2 min.

# Three seeds in parallel, round 2: RL 1 800 steps, an iterative LLM step with the 10 % margin rule, an unambiguous stop rule (2026-11-06 19:00; started by Brent)

The same setup as `../2026-11-06_claude-code-3seeds/`: fresh locked-down Claude Code (Sonnet) sessions, one copy of
`CAD/` per seed, the warm start in the code. The prompt changes:
- RL 1 = `warmup(100)` + `train(800)` (was 500);
- the LLM step: up to 5 iterative `simulate`, aiming for all hard specs with ≥ 10 % margin and the current near
  200 µA. It must not simulate a design that pushes a spec below 10 %, because the warm-up explores around the
  highest-reward design;
- a fallback if the buffer holds < 100 transitions;
- an unambiguous stop rule.

**Checks:**
- All three read only the allowed files.
- The stop rule was applied correctly in all three (PM +0.5 %, PM +0.6 %, UGBW +1.1 %).
- Seed 1 again recovered from a 99-transition buffer with `warmup(1)`.

| seed | RL 1 | LLM step (hand-over) | warm-up 2 | train 2 (warm start) | **final** | design | Cc: RL 1 → LLM → final |
|---|---|---|---|---|---|---|---|
| 123456 | −0.025 | 0.086 (472 µA, ≥ 13 % margins) | 0.601 | **0.671** | **0.671** | 288 µA, 580 µm² | 4.4 → 3.2 → 0.7 pF |
| 1 | 0.003 | 0.056 (311 µA, ≥ 13 %) | 0.281 | **0.337** | **0.337** | 257 µA, 1443 µm² | 5.6 → 4.2–4.9 → 2.6 pF |
| 2 | **0.599** | 0.570 (269 µA, ≥ 9 %; below RL 1's best) | 0.576 | **0.610** | **0.610** | 310 µA, 621 µm² | 0.5 → 0.5–0.6 → 0.6 pF |

**Final FoM: mean 0.539, standard deviation 0.178.** Round 1 was 0.489 ± 0.127. ≈ 1985 sims each (2–6 failed),
9.7–11.0 min in parallel.

**Tokens:**

| seed | requests | cache read | cache write | output |
|---|---|---|---|---|
| 123456 | 17 | 389k | 31k | 8.2k |
| 1 | 15 | 322k | 31k | 11.3k |
| 2 | 14 | 289k | 28k | 7.4k |

**Reading:**
- Train 2 with the warm start helped in all three runs (+0.07, +0.06, +0.03).
- RL 1 with 800 steps: seed 2's TD3 alone found 0.599 at Cc 0.5 pF.
- The margin rule made the LLM step cautious: +0.11, +0.05, and −0.03 (the hand-over was below RL 1's best, so the
  warm-up centred on the RL design).
- **What separates the seeds is Cc**, which dominates the area. Seed 1 never left the multi-pF region: the LLM's
  safe small steps (5.6 → 4.2–4.9 pF), the RL to 2.6 pF.
- The equations demand Cc ≤ gm1/(2π·100 MHz), usually below 1 pF. A bold LLM move into that region (Cc ≈ 0.5–1 pF,
  with Rc and the currents re-tuned) is what was missing.

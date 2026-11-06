# Evaluation: LLM first, then one big RL, on unseen seeds 3, 4, 5 (2026-11-06 20:01; started by Brent)

The same frozen harness and the same locked-down fresh Claude Code (Sonnet) sessions as
`../2026-11-06_eval-rl-first-seeds345/`, in the same copies, as new sessions. The prompt:
`../../prompts/llm_first_big_rl_evaluated.txt` (byte for byte from the transcripts, identical in all three):
1. a nominal from the equations, ≤ 6 `simulate`;
2. `warmup(200)` + 2 × `train(1000)`;
3. a polish `warmup(50)`;
4. a judgement stop, else ≤ 3 refinements;
5. the reviewer.

**Checks:**
- All three read only the allowed files (+ the netlist, allowed here). Seed 4 also ran one `Glob` for a
  non-existent pattern, apparently to wait.
- Seed 4 used **7** hand simulations (the limit was 6).
- All three stopped by judgement (UGBW or PM limiting).

| seed | nominal | hand best (sims) | warm-up | train 1 (warm start) | train 2 | polish | **final** | design |
|---|---|---|---|---|---|---|---|---|
| 3 | −0.492 | 0.597 (4) | 0.535 | **0.651** | 0.655 | 0.634 | **0.655** | 207 µA, 914 µm² |
| 4 | −0.913 | −0.008 (7, still failing) | 0.618 | **0.671** | 0.657 | 0.621 | **0.671** | 226 µA, 793 µm² |
| 5 | −0.211 | 0.596 (4) | 0.632 | 0.657 | **0.677** | 0.513 | **0.677** | 225 µA, 786 µm² |

**Final FoM: mean 0.668, standard deviation 0.011.** ≈ 2480 sims each (1–2 failed), 10–12 min in parallel.

**Tokens:**

| seed | requests | cache read | cache write | output |
|---|---|---|---|---|
| 3 | 14 | 443k | 46k | 22.3k |
| 4 | 19 | 505k | 37k | 13.4k |
| 5 | 14 | 328k | 32k | 9.7k |

**The best FoM so far at equal simulation counts** (mean over seeds 3/4/5):

| after | LLM first, big RL | RL → LLM → RL |
|---|---|---|
| 200 sims | **0.612** | −0.451 |
| 500 sims | **0.624** | 0.030 |
| 1000 sims | 0.652 | 0.645 |
| 1500 sims | 0.666 | 0.658 |
| 2150 sims | 0.668 | 0.672 |

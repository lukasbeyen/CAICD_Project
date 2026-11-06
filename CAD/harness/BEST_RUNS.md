# Best harness runs (blind sessions only)

Only fresh agents without memory: new agy or Claude Code sessions that saw only `AGENTS.md`, the agent prompts and
the skills. No runs played by Claude Code in the development chat.
- **Seeds 3, 4, 5:** never used to tune the flows. The code was frozen at `908d8a6` (the course's 4 tools,
  general-only skills).
- **Claude Code runs:** locked down (`--tools "Read,Glob,Grep"`, only the `cad` server), one copy of `CAD/` per seed,
  3 runs in parallel on 3 cores. The times include that sharing.
- **Tokens:** model calls · new input (input + cache write) · cached input · output.

| structure | agent | seed | FoM | tokens | sims | time | details |
|---|---|---|---|---|---|---|---|
| **RL → LLM → RL** | agy, Sonnet 4.6 | 3 | **0.705**¹ | 15 · 50k · 294k · 7k | 2094 | 9.9 min | prompt `prompts/rl_first_final_agy.txt`, no subagents |
| RL → LLM → RL | Claude Code, Sonnet | 3 | 0.702 | 13 · 32k · 269k · 6k | 2147 | 9.0 min | prompt `prompts/rl_first_evaluated.txt` |
| RL → LLM → RL | Claude Code, Sonnet | 4 | 0.616 | 17 · 36k · 414k · 8k | 2155 | 10.2 min | 〃 |
| RL → LLM → RL | Claude Code, Sonnet | 5 | 0.698 | 17 · 37k · 421k · 9k | 2150 | 9.3 min | 〃 (mean of 3–5: **0.672 ± 0.049**) |
| LLM → big RL | Claude Code, Sonnet | 3 | 0.655 | 14 · 46k · 443k · 22k | 2479 | 12.2 min | prompt `prompts/llm_first_big_rl_evaluated.txt` |
| LLM → big RL | Claude Code, Sonnet | 4 | 0.671 | 19 · 37k · 505k · 13k | 2481 | 11.1 min | 〃 |
| LLM → big RL | Claude Code, Sonnet | 5 | 0.677 | 14 · 32k · 328k · 10k | 2479 | 10.1 min | 〃 (mean of 3–5: **0.668 ± 0.011**) |
| LLM only (v1) | agy, Gemini 3.8 Flash | 123456 | 0.684 | 95 · 806k · 1.39M · 117k | 16 | 15.7 min | branch `einstein_LLM`: analyst / designer / reviewer subagents; the RL tools were available but not used |

¹ agy's quota ran out after the second warm-up (its own best then: 0.699). The missing second `train(800)` was
replayed deterministically from agy's exact tool calls; the first 1214 simulations are identical (difference 0.0).
agy's final stop decision was not replayed.

**The structures:**
- **RL → LLM → RL:**
  1. `warmup(100)` + `train(800)`: TD3 from scratch;
  2. ≤ 5 iterative LLM `simulate`, each reasoned on the margins and the FoM terms;
  3. `warmup(200)` around the best + `train(800)`, starting from the best design (warm start);
  4. a judgement stop, or ≤ 3 refinements;
  5. the reviewer.

  The Claude Code runs also had a polish `warmup(50)` before step 4; it never produced the final design.
- **LLM → big RL:**
  1. ≤ 6 LLM `simulate` (a nominal from the equations);
  2. `warmup(200)` + 2 × `train(1000)` (warm start);
  3. a polish `warmup(50)`;
  4. a judgement stop;
  5. the reviewer.

Records: `sessions/2026-11-06_agy-rl-first-seed3/`, `sessions/2026-11-06_eval-rl-first-seeds345/`,
`sessions/2026-11-06_eval-llm-first-big-rl-seeds345/`, `sessions/2026-11-05_gemini-3.8-flash/`.

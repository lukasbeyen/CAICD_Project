# The final RL → LLM → RL flow in agy, seed 3 (2026-11-06 20:24; started by Brent; stopped by the quota)

`agy --new-project --model claude-sonnet-4-6` in the seed-3 lane (`~/harness_lanes/s3/CAD`; its `mcp_config.json`
starts the lane's `mcp_server.py --seed 3`). The prompt: `../../prompts/rl_first_final_agy.txt`, the final report
prompt plus "no subagents". The code is the frozen harness (`908d8a6`: the warm start, general-only skills).

**It stopped after the second warm-up:** agy's quota ran out. Brent's "continue" at 20:30 got no answer. The
second `train(800)`, the stop decision and the reviewer summary were not run.

**Checks:**
- It read `AGENTS.md`, `tutor.md`, `reviewer.md`, the two skills, the netlist (not in the prompt's list, harmless),
  agy's own MCP tool-definition files, and one of its own step-output files (a large `get_status` result that agy
  stored in a file).
- No earlier results.
- **RL 1 is identical to the Claude Code run of seed 3** (`../2026-11-06_eval-rl-first-seeds345/`): the first 990
  simulations, value for value. So the LLM step and the warm-up compare cleanly between the two agents.

| | RL 1 | LLM step (sims; Cc) | warm-up 2 (200) | train 2 | best |
|---|---|---|---|---|---|
| **agy, Sonnet 4.6** | 0.015 | **0.699** (4; 0.6 pF) | 0.682 | not run (quota) | **0.699** |
| Claude Code, Sonnet (latest) | 0.015 | 0.691 (2; 0.6 pF) | 0.697 | 0.702 | **0.702** |

**agy's best design:** 0.6986 (its 2nd LLM refinement, simulation 992). 224 µA, 751 µm², UGBW 103 MHz, PM 60.2°,
Cc 0.6 pF.

**The LLM step's 4 designs:**
1. Rc 7.6 → 8.2 kΩ for PM: worse;
2. Rc 6.8 kΩ: **0.699**, PM fixed;
3. a current cut mn4 + mn5: fails;
4. an I2 cut with the balance re-tuned: fails.

1214 simulations, 0 failed, 31 feasible, 6.9 min.

**Tokens (agy's counts):** 15 model calls, 50.1k input + 293.7k cached + 7.0k output. The old agy v4 session with
subagents had 32 calls and 85.2k + 628.7k + 17.0k.

**Reading:**
- On the same RL 1 state, agy's LLM step was as good as Claude Code's (0.699 vs 0.691).
- Its run reached 0.699 after 1214 simulations, against Claude Code's final 0.702 after 2147.
- The missing second training could only have added to it.
- Without subagents, the session needed half the calls of the old agy run, but still more than this quota allowed.

## Completing the run: a deterministic replay of the missing RL phase (2026-11-06 20:35)
agy's exact MCP calls were taken from its transcript and replayed in the same lane with the same seed (3), through a
driver that builds the experiment exactly as the lane's `mcp_server.py --seed 3` does:
- `warmup(100)`, `train(800)`, `get_status(10)`, its 4 `simulate` designs, `warmup(200)`;
- then the prompt's next step, the **second `train(800)`**, which agy didn't reach.

agy's first `warmup` call had been rejected by the server's argument check (`n` instead of `n_steps`) before it
reached the experiment, so it is left out.

**Verified:** the replay's first 1214 simulations are **identical** to agy's run (maximum absolute difference 0.0
over all parameters, specs and rewards; the same sources and failed flags). So the second training is exactly what
agy's session would have produced. Files: `harness_history_completed_replay.csv`, `replay_tool_calls.jsonl`.

| second `train(800)` (sims 1215–2094) | steps 1–200 | 201–400 | 401–600 | 601–800 |
|---|---|---|---|---|
| best | 0.661 | **0.705** | 0.684 | 0.509 |
| feasible | 7 | 10 | 31 | 93 |

**The completed run's best: FoM 0.7054** (training, simulation 1465):
- 215 µA, 775 µm²;
- UGBW 102.3 MHz (+2.3 %), PM 61.2° (+2.0 %), SR 66 V/µs, gain 556, noise 19.6 mV;
- Cc 0.6 pF.

That's the highest of all harness runs (Claude Code on seed 3: 0.702).

**Not reproducible:** agy's step 4, the stop decision or ≤ 3 more refinements, and its reviewer summary. With UGBW
and PM both at ≈ 2 % margin, the prompt's stop condition ("limited by hard specs with little margin") applies, so
0.7054 is the likely final result.

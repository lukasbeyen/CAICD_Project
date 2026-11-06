# Test run 2026-11-06: harness v3.1 (two RL runs with an educated LLM improvement in between), Claude Code, NOT agy

Claude Code played the orchestrator, `tutor` and `reviewer` by the v3.1 prompts, through a persistent driver around
`TutorExperiment` (seed 123456) that logs the bytes of every tool request and result. **Not an independent
replicate** (the operator knew the earlier sessions). The `setup_rl` call is byte for byte the one of the v3 run, so
the two runs are directly comparable.

| file | content |
|---|---|
| `design_log.md` | the tutor's and the reviewer's `log_entry` |
| `harness_history.csv` | 199 simulations: 16 setup + 5 refine (source `simulate`), 178 `rl` |
| `tool_result_sizes.csv` | bytes of every tool request and result (7 tool calls) |

## The session (199 simulations, the hard budget)
| step | simulations | result |
|---|---|---|
| `setup_rl` (as in v3) | 1–16 | nominal −0.17 (fails UGBW); the best warm-up 0.606 (balanced current moves) |
| `run_rl(80)` | 17–96 | 0.606 → 0.646 (5 improvements: mn5 11, Cc 0.4 pF, Rc 9.7 kΩ, …) |
| **`refine`** (5 designs + a re-centred space) | 97–101 | **0.686**: Cc 0.3 pF + an I2 cut (mn5 10, mp3 12); the cut alone fails UGBW, Cc's UGBW gain makes it pass. mp3/mn4 were at the edges of their ranges → re-centred; 87 transitions kept |
| `run_rl(98)` | 102–199 | no improvement: the design sits on the PM (60.04°) and UGBW (101.3 MHz) limits |

**Final:** FoM **0.686**, 213 µA, 822 µm²; margins PM +0.1 %, UGBW +1.3 %. 124 of 177 distinct designs met all
specs. Pareto: 0.686 (213 µA / 822 µm²) and 0.665 (224 µA / 815 µm², more margin).

## All versions compared (the same turn model, Claude Code / agy test runs)
| | input tokens | turns | tool calls | simulations | best FoM |
|---|---|---|---|---|---|
| v1 (LLM designs; agy) | ≈ 244k | ≈ 38 | 17–30 | 16 | 0.684 |
| v2 (LLM + RL bursts) | ≈ 126k | 53 | 18 | 97 | 0.677 |
| v3 (LLM tutors the RL) | ≈ 30k | 13 | 5 | 146 | 0.650 |
| **v3.1 (+ refine between two RL runs)** | **≈ 46k** | **15** | **7** | **199** | **0.686** |

## Version 3.2 (the final harness) = the first 101 simulations of this run
Brent dropped the second RL run (it found nothing). v3.2's session is setup → `run_rl` → `refine` → end, which is
exactly simulations 1–101 here: **FoM 0.686** (found by `refine`, sim 99), 75 of 101 designs met all specs,
≈ 39k input tokens (the turn model with v3.2's prompts and tool descriptions).

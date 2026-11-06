# Test run 2026-11-06: harness v3 (the LLM tutors the RL), Claude Code playing the agents, NOT agy

Claude Code played the orchestrator, `tutor` and `reviewer` by the v3 prompts. It called the real backend
(`TutorExperiment`, seed 123456) through a persistent driver that behaves like `tutor_mcp_server.py` and logs the
bytes of every tool request and result. **Not an independent replicate:** the operator knew the earlier sessions. On
purpose, the tutor started from the *first* hand design the equations give, which fails UGBW.

| file | content |
|---|---|
| `design_log.md` | the tutor's and the reviewer's `log_entry` |
| `harness_history.csv` | every simulation: 16 by the tutor (nominal + 15 warm-up, source `simulate`), 130 `rl` |
| `tool_result_sizes.csv` | bytes of every tool request and result (**5 tool calls** in the whole session) |

## The session (146 simulations, 5 tool calls)
1. **tutor**, `setup_rl`:
   - the nominal from the equations (Itail ≈ 40 µA, I2 ≈ 100 µA, Cc 0.5 pF, Rc 9.8 kΩ, balance 5), which fails UGBW
     (67 MHz, FoM −0.17);
   - a space of 6 free parameters with 9–11 grid points each (mn4, mn5, mp3, mn1, Cc, Rc), with all L, all W, mn3 and
     mp1 fixed;
   - 15 warm-up designs (one-at-a-time + 3 coupled moves);
   - what the table showed: mn4 is the lever (+1 finger: UGBW +24 %); Cc moves PM (∓7.5 %/0.1 pF); the two balanced
     coupled moves meet all specs (0.599, **0.606**).
2. **tutor**, `run_rl(130)`: 0.606 → **0.650**:
   - the running best 0.616 / 0.634 / 0.650 at 25/50/100 %, from 6 improvements;
   - the parameters touched by the improving designs: mn1 ×5, Rc ×4, mn5 ×2, mp3 ×2, Cc ×1;
   - the final changes relative to the tutor's balanced design: mn5 13 → 11, Cc 0.5 → 0.4 pF, Rc 9.8 → 9.6 kΩ.
3. **reviewer:**
   - the final design: FoM 0.649, 223 µA, 850 µm², PM 65.5° (+9 %), UGBW 105.4 MHz (+5.4 %); no hard spec < 5 %;
   - 88 of 118 distinct designs met all specs.

## Tokens (the same turn model as v1/v2, with the tool descriptions counted)
| | v1 | v2 | **v3** |
|---|---|---|---|
| input tokens | ≈ 244k | ≈ 126k | **≈ 30k** |
| output tokens | ≈ 10k | ≈ 8.5k | ≈ 2.5k |
| model turns | ≈ 38 | 53 | **13** |
| tool calls | 17–30 | 18 | **5** |

## Results compared
| | simulations | best FoM | who found it |
|---|---|---|---|
| v1, agy (Gemini Flash) | 16 | 0.684 | the LLM |
| v2 test | 97 | 0.677 | the LLM (the RL found nothing) |
| **v3 test** | **146** | **0.650** | **the RL** (+0.044 over the tutor's best) |

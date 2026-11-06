# Test run 2026-11-06 14:20: harness v3.2 with the fixed prompts, Claude Code playing tutor + reviewer, NOT agy

After the first real agy session failed (the tutor fenced the RL into a bad region), four prompt fixes were made:
- the netlist values are placeholders;
- check the nominal with your own equations;
- the space must contain what the equations demand;
- the reviewer questions the space.

Then Claude Code played the agents **following only the prompt files**: every value was derived from the
`opamp-design` equations (written out in the tutor's log), with no remembered values or results; no earlier run was
looked at. The caveat stays: the operator can't truly forget the earlier sessions, so this is a disciplined replay,
not an independent agent.

| file | content |
|---|---|
| `design_log.md` | the tutor's and the reviewer's `log_entry` |
| `harness_history.csv` | 101 simulations: 16 setup + 5 refine (`simulate`), 80 `rl` |
| `tool_result_sizes.csv` | bytes of every tool request and result (6 tool calls) |

## The session (101 simulations, 6 tool calls)
| step | sims | best FoM | notes |
|---|---|---|---|
| nominal (equations) | 1 | −0.045 | only UGBW fails (87.8 MHz); calibration: UGBW 0.59×, SR 0.43× the estimate |
| warm-up (15) | 2–16 | 0.656 | mn4 +1 = +18 % UGBW → all specs met; Cc moves PM |
| RL (80) | 17–96 | **0.669** | mn1 11, mn5 11: 211 µA, 867 µm², PM 63.5°, UGBW 100.3 MHz (+0.3 %) |
| refine (5) | 97–101 | 0.669 | the current cuts fail UGBW (mn5 −1 now −8.6 %, not −2.8 %: the sensitivities shifted); the margin moves pass (0.662, 0.641) |

21 of 92 distinct designs met all specs. Pareto: 0.669 (211 µA / 867 µm²), 0.667 (213 µA / 858 µm²).

## Tokens
- **The tool traffic** (measured): 6 calls, ≈ 12 kB of results, ≈ 4.4 kB of requests.
- **agy's real cost**, judging by the first real agy session (7 tool calls, the same pipeline): ≈ 60k input + ≈ 200k
  cached input + ≈ 13k output. Most of it is agy's own system prompt and tool definitions, which are reread on every
  call.

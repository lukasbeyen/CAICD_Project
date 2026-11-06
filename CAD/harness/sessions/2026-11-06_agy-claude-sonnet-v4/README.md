# The real agy session of harness v4 (2026-11-06 16:16, Claude Sonnet 4.6 Thinking, started by Brent)

`agy --new-project --model claude-sonnet-4-6`, with the 4 course tools allowed for the session; the prompt from
`harness/session_prompt.md` plus the start-from-scratch sentence. Harness v4: the course's `mcp_server.py`, the
warm-up drawn around the best design, plain TD3 `train`.

| file | content |
|---|---|
| `main_transcript.jsonl`, `tutor_transcript.jsonl`, `reviewer_transcript.jsonl` | agy's transcripts (`brain/…/transcript.jsonl`): every model call with its tokens, every tool call and result |
| `harness_history.csv` | every simulation: source, reason, parameters, specs, reward |

## Checks
- **Start from scratch: passed.** The tutor read only the two skills, the netlist and agy's own MCP tool-definition
  files (`~/.gemini/antigravity-cli/mcp/cad/*.json`); `AGENTS.md` is loaded automatically. The main agent and the
  reviewer read no files.
- **Budget: passed.** 191 simulations (< 200), 0 failed, 5.8 minutes.
- **Pipeline: passed.** Main → tutor → reviewer.
- **Prompt rules, partly broken:**
  - 10 hand `simulate` calls before the warm-up (the prompt says ≤ 6);
  - the design handed over didn't pass all hard specs (−0.218: UGBW 84 MHz, PM 45°);
  - the returns misreport counts: "fixed over 6 sims" / "6 hand-design" (there were 10);
  - the reviewer calls the compensation zero an "RHP zero" and says the final design has "the same transistors as
    the tutor's nominal" (it doesn't: the nominal is simulation 1).

## The session
| phase | simulations | best reward | what happened |
|---|---|---|---|
| nominal + 9 hand steps | 10 | −0.218 | nominal Cc 2 pF, L 180 nm: UGBW 17 MHz; then Cc ↓, I_tail ↑ (mn3 = 1 finger, so large mirror ratios): 305–629 µA, never all specs |
| `warmup(100)` around −0.218 | 110 | 0.337 | 7 feasible designs, all at ≈ 450 µA |
| `train(60)` | 66 | −1.609 | nothing feasible |
| refining, 5 × `simulate` | 5 | **0.490** | Cc 1.5 → 0.9 pF, Rc 3.8 → 2.8 kΩ (area); the current stays 452 µA |
| reviewer (`get_status`) | 0 | | |

**Final: FoM 0.490**:
- gain 254 (+27 %), UGBW 115.5 MHz, PM 61.5° (+2.5 %), SR 63.6 V/µs, noise 6.6 mV;
- **current 452 µA** (2.3× the target), area 538 µm².

## Tokens (agy's own counts)
| agent | model calls | input | cached input | output |
|---|---|---|---|---|
| main | 5 | 9.5k | 44.8k | 1.7k |
| tutor | 24 | 63.3k | 572.6k | 14.6k |
| reviewer | 3 | 12.4k | 11.4k | 0.8k |
| **total** | **32** | **85.2k** | **628.7k** | **17.0k** |

Compared with the v3.2 agy session (own tools): 58.8k input + 207.5k cached + 13.2k output.

## Why the FoM is low (compared with the Claude Code test run's 0.678)
- **The current was never budgeted.** The tutor chased UGBW with current. mn3 = 1 finger of 0.25 µm makes every
  mirror ratio large, and the nominal path reached 305–629 µA.
- The warm-up then searched around a ≈ 450 µA design. The current term z = (452 − 200)/(452 + 200) = 0.39 is the
  largest FoM loss, and the refining only worked on the area (Cc, Rc).
- The hand phase took 10 simulations and still handed over a failing design; the warm-up had to repair it.

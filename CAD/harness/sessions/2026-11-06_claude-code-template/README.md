# Test run of harness v4 (only the course's tools), played by Claude Code (2026-11-06 15:11)

Claude Code played the tutor and the reviewer by following only the prompt files: `AGENTS.md`, `tutor.md`,
`reviewer.md`, the two skills and the netlist. One `SizingExperiment(123456, 100, 100000)` was kept alive, built as
`mcp_server.py`'s `main()` builds it, and only its 4 tools were called. Caveat: the player had seen earlier sessions
in its context. It derived the nominal from the equations and didn't reuse earlier designs, but it isn't a truly
blind agent; the real check is Brent's agy session.

| file | content |
|---|---|
| `harness_history.csv` | every simulation: source (`simulate` / `reset` / `warmup` / `train`), reason, parameters, specs, reward |
| `tool_calls.jsonl` | the 17 tool calls in order (16 tutor, 1 reviewer) |
| `tool_result_sizes.csv` | request and result bytes per call (the token estimate) |

## The session
| phase | simulations | best reward | what happened |
|---|---|---|---|
| nominal (`simulate`) | 1 | −0.559 | L 180 nm: gain 2028, noise 67 mV, UGBW 71 MHz, PM 57° fail |
| fix 1: all L → 90 nm | 1 | −0.061 | only the noise fails (35 mV): ∝ √(A0·GBW), the gain surplus removed |
| fix 2: pair W 0.5 → 1 µm | 1 | **0.606** | all hard specs met; current 233 µA, area 894 µm² |
| `warmup(100)` around it | 110 (10 resets) | **0.646** | 13 feasible designs; mp1 +1, mn1 +1, wn1 +1 step, mn5 −1 → 214 µA |
| `train(60)` | 66 (6 resets) | 0.646 | no feasible design (the untrained actor's designs are elsewhere) |
| refine round 1: 5 single steps | 5 | 0.662 | Cc 0.5 → 0.4 pF; Rc −1 kΩ costs 7.6 % UGBW (fails) |
| refine round 2: 5 combinations | 5 | **0.678** | Cc 0.4 pF + mp3 −1 + mn5 −1: 207.7 µA, 863 µm², UGBW +0.8 % |
| reviewer (`get_status`) | 0 | | the final design dominates all 22 feasible designs (lowest current and area) |

**189 simulations, 4.1 minutes, no failed simulation. FoM 0.678.**

## Tokens (estimate, the turn model; not measured)
- **≈ 165k model input tokens** (tutor ≈ 160k over 17 turns, reviewer ≈ 6k).
- Assumptions:
  - every turn rereads the prompt files, the skills, the netlist and the 4 tool definitions (2.5 kB), plus all
    earlier calls and results;
  - ≈ 1.2 kB of model output per turn;
  - 4 bytes per token.
- Most of it is the 10 refining `simulate` calls: each is a turn, and each result is a full candidate (≈ 1.2 kB with
  `spec_units`). `warmup` and `train` return `get_status(3)` (≈ 3 kB each).
- For comparison (the same kind of estimate): v3.2 ≈ 39k, v3 ≈ 30k, v1 ≈ 244k.

## What it shows
- The tutor's design steers the RL through the template alone: the warm-up around it found a better design (+0.04)
  within its 100 random draws.
- `train` added nothing within 60 steps: TD3 starts with an untrained actor, and 60 updates are far too few to move
  it to the tutor's region (the TD3 runs needed thousands of simulations).
- The last gain came from the LLM's refining, with sensitivities measured at the best.
- Compared with v3.2:
  - a similar FoM (0.678 vs 0.669–0.686);
  - about 4× the tokens, because refining needs one `simulate` turn per design;
  - all with the course's tools and no code of our own except the warm-up rule.

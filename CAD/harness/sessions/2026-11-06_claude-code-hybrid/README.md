# Test run 2026-11-06: harness v2 (LLM + RL bursts), Claude Code playing the agents, NOT agy

Claude Code played the orchestrator, `designer`, `rl-explorer` and `reviewer` by the v2 prompts. It called the real
backend (`HybridExperiment`, seed 123456) through a persistent driver that behaves like `hybrid_mcp_server.py` and
logs the bytes of every tool request and result. **Not an independent replicate:** the operator knew the earlier
sessions.

| file | content |
|---|---|
| `design_log.md` | the 6 entries the agents wrote with `log_entry` |
| `harness_history.csv` | every simulation: 7 `simulate` (the designer), 90 `rl` (4 bursts) |
| `tool_result_sizes.csv` | bytes of every tool request and result |

## The session (97 simulations)
| step | simulations | result |
|---|---|---|
| designer A+B | 1–3 | first design → **all specs met at sim 2** (both mirror currents scaled, balance kept), FoM 0.622 at sim 3 |
| burst 1 (30) | 4–33 | 0 better; 1 of 30 RL designs met all specs |
| designer C | 34–35 | current cut on both stages, balance kept → FoM 0.660 (215 µA) |
| burst 2 (20) | 36–55 | 0 better |
| designer C | 56 | Cc 0.4 → 0.3 pF (PM headroom → area) → **FoM 0.677** (PM 60.3°, UGBW 104.3 MHz, 215 µA, 831 µm²) |
| burst 3 (20) | 57–76 | 0 better |
| designer C | 77 | mp3 at L = 45 nm with the same S → gain 24 V/V: at 45 nm, S = m·W/L doesn't scale across lengths |
| burst 4 (20) | 78–97 | 0 better; stop rule (2 cycles without improvement) |
| reviewer | – | final sim 56; margins UGBW +4.3 %, PM +0.5 %; cost 7 designer + 90 RL |

## Findings
- **Tokens** (the same turn model as v1, with the tool descriptions counted):
  - ≈ 126k input + 8.5k output tokens, against ≈ 244k for v1 (−48 %), despite 4 cycles (53 turns);
  - orchestrator 28k (v1 ≈ 100k), 4 RL bursts 29k, 4 designer-C phases 39k.
- **The RL bursts found nothing** in 90 simulations (5 RL designs met all specs, best 0.607). A diagnostic (the same
  seeded buffer, a 30-step burst, 2 seeds; not part of the harness):

  | exploration noise σ | improvements | RL designs meeting all specs | median RL reward |
  |---|---|---|---|
  | 0.1 (template) | 0 / 0 | 3 % / 3 % | −1.22 / −1.06 |
  | 0.05 | 0 / 0 | 10 % / 20 % | −0.82 / −0.55 |
  | 0.02 | 0 / 0 | 20 % / 20 % | −0.52 / −0.12 |

  Three causes:
  1. σ 0.1 moves all 20 parameters at once by ~5 % of their range, which breaks the mirror balance.
  2. The actor drifts away from the warm-started best design with every TD3 update of a still-untrained critic (even
     at σ 0.02 the designs move far).
  3. The best design sits on the PM boundary (+0.3°), so almost every local step loses.

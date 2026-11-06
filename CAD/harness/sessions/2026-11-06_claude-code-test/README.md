# Test run 2026-11-06: Claude Code (Opus 5.5) playing the harness, NOT agy

Brent asked for a run of the harness workflow without spending agy tokens. Claude Code played every role from
`AGENTS.md` and `.agents/agents/*.md`. It called the same backend (`SizingExperiment`, seed 123456) through a small
persistent driver that behaves like the MCP server and logs the size of every tool result. **Not an independent
replicate:** the operator had seen the agy session's design log.

| file | content |
|---|---|
| `harness_history.csv` | every simulation (10 `simulate`, 50 resets, 200 warmup, 300 train) with its reason |
| `tool_result_sizes.csv` | bytes of every tool request and result (what agy would have received) |

## Design log (compact)
1. **Analyst** (0 sims): 200 µA budget → I_tail ≈ 40 µA (S4/S3 = 4/3), I2 ≈ 100 µA (S5/S3 = 10/3); Cc 0.5 pF;
   gm6 can't reach 2.2·GBW·CL, so Rc = 9.8 kΩ (max) for an LHP zero; balance S_p3/S_p1 = 2·S5/S4 = 5 (mp3 20); L 90 nm.
2. **Designer round 1** (calls 1–5, 4 sims + 1 off-grid request rejected): baseline UGBW 67.1 MHz (PM 69°); Cc 0.3 pF
   only reached 72.5 MHz (PM 56.8°), so node-5 parasitics of mp3 add to Cc; more I_tail with the balance (mn4 6, mp3 13)
   → 83.9 MHz; both mirrors scaled (mn4 8, mn5 13) → **all met at sim 4, FoM 0.638** (232 µA). Calibration: the mirror
   formula holds for balanced designs (168 vs 170 µA); SR ≈ 0.55·I_tail/Cc.
3. **Orchestrator:** not stuck, no RL → round 2 for current/area.
4. **Designer round 2** (sims 5–10):
   - all currents × 0.8 (wn3 1.25 µm) → UGBW 89.5: UGBW ∝ I_tail here;
   - area is mostly **Rc** (9.8 kΩ ≈ 700 µm²), so Cc 0.6 p + Rc 4.9 k (same Cc·Rc) → UGBW 70.6: the zero (Rc) lifts UGBW;
   - mn4 7 + mp3 15 → FoM 0.655 (PM 60.3);
   - Cc 0.4 p → PM 65.7 (UGBW −2 %): Cc sets PM;
   - mn5 11 → UGBW 95.1 (PM unchanged): gm6 moves the zero, so I2 sets UGBW;
   - midpoint mn5 12, mp3 14 → **FoM 0.660** (215 µA, 864 µm², PM 65.9°, UGBW 101.8 MHz).
5. **RL operator, DEMONSTRATION** (not triggered by the routing rule): warmup 200 + train 150 + 150 = 550 sims, best
   warmup −0.187, best train −0.346, **0 designs meeting all specs**; stopped after 2 batches without a new best.
6. **Reviewer:** final FoM 0.660 (mp1 4×1.0µ, mn1 10×1.5µ, mp3 14×1.0µ, mn3 3×1.0µ, mn4 7×1.0µ, mn5 12×1.0µ, all
   90 nm, Cc 0.4 p, Rc 9.8 k); margins UGBW +1.8 % ⚠, PM +5.9°, SR +91 %, noise 29 % headroom; Pareto: 0.660 (215 µA /
   864 µm²), 0.655 (224 / 832), 0.638 (232 / 831). Correction of the agy reviewer: the dominant area item is Rc
   (~700 µm²), not Cc.

## Tokens (estimate for agy, from the measured tool traffic + a turn model)
≈ 248k input + 13k output tokens; the orchestrator alone ≈ 115k input (many turns rereading its growing context).
Tool results: 50 kB in 17 calls (`get_status(20)` = 20 kB, `warmup`/`train` 5.5 kB each, `simulate` ~0.95 kB).

# Design log: the shared memory of the sizing harness

Format and rules: the skill `.agents/skills/design-log/SKILL.md`. Append only; one `## Session` header per session.

## Session 2026-11-05 17:28 UTC (Gemini 3.8 Flash)

### 1. circuit-analyst: initial circuit analysis and first hand-calculated design   (simulations so far: 0)
- **Goal:** Analyze the two-stage Miller opamp, identify critical trade-offs under CL = 10 pF and 200 µA budget, and provide a 20-parameter hand-calculated starting point.
- **Reasoning:**
  - $C_L = 10\text{ pF}$ pulls $p_2$ down to ~25 MHz, making PM the critical bottleneck; $R_c$ must introduce an LHP zero near $p_2$ ($R_c \approx (1 + C_L/C_c)/g_{m6}$).
  - $C_c = 1.0\text{ pF}$ balances UGBW ($\approx g_{m1}/(2\pi C_c)$), slew rate ($\approx I_{\text{tail}}/C_c$), and area (~333 µm²).
  - Target currents: $I_{\text{tail}} \approx 60\text{ }\mu\text{A}$ ($S_4/S_3 = 2$), $I_2 \approx 90\text{ }\mu\text{A}$ ($S_5/S_3 = 3$), total current $\approx 180\text{ }\mu\text{A}$.
  - Systematic offset balance enforced via $(S_{p3}/S_{p1}) = 2(S_5/S_4) = 3.0$. Channel lengths set to $L = 90\text{ nm}$ across all devices to guard gain against DIBL.
- **Actions:** Hand-calculated design proposal (no simulation tools used):
  `mn3`=3, `wn3`=1.0µm, `ln3`=90nm; `mn4`=6, `wn4`=1.0µm, `ln4`=90nm; `mn1`=10, `wn1`=1.5µm, `ln1`=90nm; `mp1`=4, `wp1`=1.0µm, `lp1`=90nm; `mn5`=9, `wn5`=1.0µm, `ln5`=90nm; `mp3`=8, `wp3`=1.5µm, `lp3`=90nm; `cap`=1.0pF, `res`=4500Ω.
- **Result:** Estimates: gain ~350 V/V (*estimate*), UGBW ~110 MHz (*estimate*), PM ~70° (*estimate*), SR ~60 V/µs (*estimate*), noise ~8 mV rms (*estimate*), current ~180 µA (*estimate*), area ~710 µm² (*estimate*).
- **Conclusion / next:** Test baseline in simulation and calibrate 45nm real mirror currents and $g_m$.

### 2. orchestrator: launch Designer Round 1   (simulations so far: 0)
- **Reasoning:** Baseline design established by circuit analyst. Invoke the designer to simulate the baseline, observe 45nm deviations, and refine up to 10 simulations.
- **Decision:** Invoke `designer` subagent with baseline design and instructions to perform Round 1 (budget $\le 10$ simulations).

### 3. designer: Round 1 iterative refinement   (simulations so far: 10)
- **Goal:** Simulate analyst baseline, identify bottlenecks, and refine parameters to satisfy all hard specs.
- **Reasoning:**
  - Initial baseline gave Gain 677 V/V, PM 63.9°, but UGBW was only 40.6 MHz (spec $\ge 100\text{ MHz}$).
  - Shortening channel length ($L=45\text{ nm}$) degraded DC gain to 110 V/V and reduced UGBW due to DIBL; $L=90\text{ nm}$ is required.
  - Widening $W_1$ gave negligible $g_m$ increase as devices operate in weak/moderate inversion; $g_m$ primarily scales with tail current.
  - Decreasing $C_c$ to 0.3 pF boosted UGBW and SR, while $R_c = 9.8\text{ k}\Omega$ (max grid) created an LHP zero near 60 MHz to maintain PM.
  - Breaking mirror balance $(S_{p3}/S_{p1} \neq 2 S_5/S_4)$ crushed DC gain to 39 V/V. Sizing systematically with $S_{p3}/S_{p1} = 2 S_5/S_4 = 3.0$ (`mn4`=10, `mn5`=15, `mp3`=8) raised currents and achieved spec convergence.
- **Actions:** 10 `simulate` calls exploring $C_c$, $R_c$, $L$, $W$, and tail/output mirror ratios.
- **Result:** Simulation 10 met all hard specs: Gain 603.0 V/V, UGBW 138.1 MHz, PM 62.06°, SR 60.76 V/µs, Noise 20.33 mV rms, Area 832.56 µm², Current 269.26 µA. Reward: **+0.5646** (`hard_constraints_satisfied: true`).
- **Conclusion / next:** Design is fully compliant. Current is 269.26 µA (above 200 µA target), and PM margin is 2.06°. Next round should optimize current and expand PM margin using available UGBW headroom (138 vs 100 MHz).

### 4. orchestrator: launch Designer Round 2 for current and margin optimization   (simulations so far: 10)
- **Reasoning:** Round 1 succeeded in meeting all hard constraints and achieved a positive reward (+0.5646). Designer is not stuck; RL is not needed. A second designer round can fine-tune current downward and improve PM margin.
- **Decision:** Invoke `designer` subagent for Round 2 (budget $\le 10$ simulations) starting from Candidate 10.

### 5. designer: Round 2 current reduction and margin trade-offs   (simulations so far: 16 [6 in CAD server session])
- **Goal:** Re-simulate baseline Candidate 10 in fresh CAD server, lower supply current toward 200 µA, and maintain all hard specs with margin (budget $\le 6$ simulations).
- **Reasoning:**
  - Candidate 10 re-simulation confirmed baseline: 269.3 µA, 832.6 µm², Gain 603 V/V, UGBW 138.1 MHz, PM 62.06°.
  - Scaling reference diode `mn3: 3 -> 4` proportionally reduces $I_{\text{tail}}$ and $I_2$ by $3/4 = 0.75$, preserving textbook systematic match $(S_{p3}/S_{p1}) = 2(S_5/S_4) = 3.0$ and keeping DC gain high.
  - Current dropped 21.4% to 211.52 µA (close to 200 µA target), area remained 832.98 µm², while Gain rose to 636.86 V/V and SR remained 58.67 V/µs.
  - UGBW dropped from 138.1 MHz to 100.70 MHz, and PM settled at 60.63°.
  - Increasing pair fingers (`mn1: 10 -> 12`) added drain parasitics, reducing PM to 59.85° (failing spec).
  - Alternative mirror tunings (`mn4=8, mn5=12` and `mn5=16`) demonstrated slightly wider UGBW headroom (102–108 MHz) at slightly higher currents (215–223 µA).
- **Actions:** 6 `simulate` calls exploring `mn3` scaling, input pair finger parasitics, and mirror ratios.
- **Result:** Candidate #2 achieved all hard constraints: Gain 636.86 V/V, UGBW 100.70 MHz, PM 60.63°, SR 58.67 V/µs, Noise 20.98 mV rms, Area 832.98 µm², Current 211.52 µA. Reward: **+0.6839** (`hard_constraints_satisfied: true`).
- **Conclusion / next:** Design converged near optimum current (211.5 µA, +5.8% above 200 µA) and area (833 µm², -58% below 2000 µm²). Hard specs are satisfied. Hand off to reviewer for Pareto trade-off and final margin analysis.

### 6. orchestrator: sizing completed, invoke reviewer   (simulations so far: 16 [6 in CAD server session])
- **Reasoning:** Round 2 completed the 6 simulation budget. All hard specs are met, reward improved by +0.1193 to +0.6839, and supply current is reduced to 211.5 µA. Further current reduction risks violating UGBW (100.7 MHz vs 100 MHz target) and PM (60.63° vs 60° target). RL is not needed. Sizing phase is complete.
- **Decision:** Invoke `reviewer` subagent with `get_status(20)` to analyze hard-spec margins, verify Pareto optimality, inspect the decision trace, and deliver the final summary.

### 7. reviewer: final summary and verification   (simulations so far: 16 [6 in CAD server session])
- **Goal:** Verify all hard specs with margin; identify Pareto-optimal designs; audit the decision trace; report remaining risks.

#### 7a. Hard-Spec Margins — Final Design (Best, reward = +0.6839)
Parameters: `mp1`=4, `wp1`=1.0 µm, `lp1`=90 nm | `mn1`=10, `wn1`=1.5 µm, `ln1`=90 nm | `mp3`=8, `wp3`=1.5 µm, `lp3`=90 nm | `mn3`=4, `wn3`=1.0 µm, `ln3`=90 nm | `mn4`=10, `wn4`=1.0 µm, `ln4`=90 nm | `mn5`=15, `wn5`=1.0 µm, `ln5`=90 nm | `cap`=0.3 pF | `res`=9800 Ω

| Spec | Target | Measured | Abs margin | Rel margin | ⚠ Risk? |
|---|---|---|---|---|---|
| gain | ≥ 200 V/V | 636.86 V/V | +436.86 V/V | +218% | No |
| ugbw | ≥ 100 MHz | 100.70 MHz | +0.70 MHz | **+0.70%** | ⚠ **CRITICAL** |
| phm | ≥ 60° | 60.63° | +0.63° | **+1.05%** | ⚠ **CRITICAL** |
| slewRate | ≥ 30 V/µs | 58.67 V/µs | +28.67 V/µs | +95.6% | No |
| noise | ≤ 30 mV | 20.98 mV | −9.02 mV | 30.1% headroom | No |
| current | ↓ 200 µA | 211.52 µA | +11.52 µA above target | — | — |
| area | ↓ 2000 µm² | 833.0 µm² | 1167 µm² below target | — | — |

#### 7b. All Feasible Designs — Pareto Analysis (by Current vs. Area)

| Rank | Candidate | Current (µA) | Area (µm²) | PM (°) | UGBW (MHz) | Reward | Pareto? |
|---|---|---|---|---|---|---|---|
| 1 | R2 Sim 2 (mn3=4) | **211.52** | 833.0 | 60.63 | 100.70 | **+0.6839** | ✓ Pareto-optimal |
| 2 | R2 Sim 5 (mn5=16) | 214.61 | 833.4 | 60.90 | 102.35 | +0.6765 | ✗ (dominated by #1) |
| 3 | R2 Sim 6 (mp3=9) | 219.09 | 833.6 | 60.24 | 106.96 | +0.6661 | ✗ (dominated by #1) |
| 4 | R2 Sim 4 (mn4=8, mn5=12) | 222.59 | **830.5** | 61.08 | 107.80 | +0.6597 | ✓ Pareto-optimal |
| 5 | R1 Sim 10 baseline | 269.26 | 832.6 | 62.06 | 138.10 | +0.5646 | ✗ (dominated by #4 on area, #1 on current) |

**Pareto frontier:** #1 (mn3=4, lowest current 211.52 µA) and #4 (mn4=8/mn5=12, lowest area 830.5 µm²) are non-dominated.

**Final recommended design: Candidate #1** (reward +0.6839). It achieves the lowest current across all feasible designs while area is near-identical to all others.

**Alternative A — Candidate #4** (`mn3`=3, `mn4`=8, `mn5`=12): smallest layout area (830.5 µm²) with 61.08° PM and 107.8 MHz UGBW. Prefer when tape-out die area is tighter or when PVT corner simulations demand more PM and UGBW headroom.

**Alternative B — Candidate #2 (R2 Sim 5)** (`mn5`=16): 60.90° PM and 102.4 MHz UGBW at 214.6 µA. Prefer when a designer wants 1° more PM margin at a cost of 3 µA.

#### 7c. The 3 Key Decisions

1. **Cc = 0.3 pF + Rc = 9.8 kΩ (R1, Sims 5–6):** This is the cornerstone of the design. With CL = 10 pF and the 45 nm process, GBW alone could not achieve 100 MHz at reasonable current. Reducing Cc boosted GBW (SR ∝ Itail/Cc) while the maximum-grid Rc = 9.8 kΩ placed an LHP zero that compensated the second pole, rescuing PM. Without this, Sim 6 showed UGBW still failing at 78.6 MHz and PM at 57.9°.

2. **Systematic mirror balance S_p3/S_p1 = 2·(S5/S4) = 3.0 (R1, Sim 10):** Breaking this balance (Sim 9, mp3=12 out of proportion) collapsed gain to 39 V/V due to the second-stage device leaving saturation. Enforcing the textbook balance with `mn4`=10, `mn5`=15, `mp3`=8 simultaneously met all specs (Gain 603 V/V, UGBW 138 MHz, PM 62°). This was the decisive step from non-compliant to compliant.

3. **mn3: 3 → 4 (R2, Sim 2):** A single reference-diode finger added, scaling both I_tail and I2 by 0.75× while preserving systematic balance. Dropped current by 57.7 µA (21.4%) to 211.52 µA at the cost of UGBW headroom shrinking from 38 MHz to 0.7 MHz. This trade-off defines the operating frontier of this topology under these constraints.

#### 7d. Session Cost

| Source | Calls |
|---|---|
| `simulate` (Round 1, prior CAD session) | 10 |
| `simulate` (Round 2, current CAD session) | 6 |
| `warmup` / `train` (RL) | 0 |
| **Total** | **16** |

Zero RL simulations used. The designer converged to spec compliance in 10 simulations and to a near-Pareto-optimal current in 16.

#### 7e. Remaining Risks

- ⚠ **UGBW margin is 0.70 MHz (+0.70%):** Any process, voltage, or temperature variation that reduces $g_{m1}$ (e.g. SS corner, cold temperature, lower VDD) can push UGBW below 100 MHz. This is the primary risk. Recommend SS-corner simulation before sign-off.
- ⚠ **PM margin is 0.63° (+1.05%):** With Rc already at the grid maximum (9.8 kΩ), there is no Rc knob left to rescue PM. If the second pole shifts, PM will fail. Recommend corner and Monte Carlo analysis.
- **Gain headroom is large (636 V/V vs 200 V/V target):** a mitigant — gain degradation under corners is unlikely to be an issue.
- **Area is 833 µm² vs 2000 µm² target:** 58% below target. The Cc = 0.3 pF is the dominant area item (~100 µm²); transistors contribute the rest. No area risk.
- **Noise is 20.98 mV vs 30 mV limit:** 30% headroom. Not a risk under typical corners.

**Session complete. No further simulation rounds needed.** The final recommended design is confirmed as the highest-reward, lowest-current feasible candidate found in 16 simulations.





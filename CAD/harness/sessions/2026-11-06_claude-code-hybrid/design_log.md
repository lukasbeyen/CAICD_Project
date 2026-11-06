
## Session mcp_20261106_122311_956687

### 1. designer (simulations so far: 3)
Phase A+B. Reasoning: with CL = 10 pF, gm6 cannot reach 2.2*GBW*CL on ~100 uA, so PM relies on the LHP zero (Rc = 9.8k, the maximum); UGBW needs gm1, i.e. tail current; the mirror balance Sp3/Sp1 = 2*S5/S4 keeps the gain.
Actions: sim 1 first design from the equations (Itail 40 uA, I2 100 uA, Cc 0.5p, mp3 20); sim 2 mn4 4->8, mn5 10->13, mp3 20->13 (currents scaled, balance kept); sim 3 Cc 0.5p->0.4p.
Result: sim 1 UGBW 67 MHz (fail), currents as the mirror formula predicts (168 uA). Sim 2 all specs met, FoM 0.606, PM 69.6. Sim 3 FoM 0.622: PM 66.2, UGBW 112.7 MHz, 232 uA, 865 um2; Cc mainly moved PM, not UGBW.
Next: current (232 uA > 200) is the main FoM loss; UGBW (+13 %) limits cutting I_tail. Hand the local trade-off to the RL.

### 2. designer (simulations so far: 35)
Phase C after burst 1. RL: 0 of 30 designs beat 0.622. Its exploration noise moves nearly every one of the 20 parameters by about a grid step at once; for small finger counts (mn3 = 3) that changes every mirror current, the balance Sp3/Sp1 = 2*S5/S4 breaks and the gain collapses (21-77 V/V in most RL designs).
Actions: sim 34 mn4 8->7, mp3 13->15 (less tail current, balance kept): FoM 0.639, 224 uA, UGBW 108.4 MHz. Sim 35 mn5 13->12, mp3 15->14 (less second-stage current, balance kept).
Result: see sim 35 in the history.
Next: burst 2 starts from the new best; both designs are now RL experience.

### 3. designer (simulations so far: 56)
Phase C after burst 2. RL: 0 of 20 better, same cause as burst 1 (all parameters move at once, the balance breaks).
Action: sim 56 Cc 0.4p -> 0.3p on the best (sim 35), spending the PM headroom (+5.9 deg) on area.
Result: FoM 0.677, all met: PM 60.3 (tight, +0.3 deg), UGBW 104.3 MHz, 215 uA, 831 um2. Cc moved PM as expected, UGBW slightly up.
Next: burst 3 from this design; PM is now the binding spec, so further area/current cuts need PM back.

### 4. designer (simulations so far: 77)
Phase C after burst 3 (0 of 20 better). Action: sim 77 mp3 L 90n -> 45n with fingers 14 -> 7, keeping S_p3 = m*W/L and halving mp3's gate capacitance, to win PM (binding, +0.3 deg) with the large gain margin.
Result: fails, gain 24 V/V (PM 76.7, 241 uA). At L = 45 nm the PMOS carries far more current than S predicts (short-channel effects), so the balance computed with S breaks across lengths: scaling by S is only valid at equal L. Best stays sim 56 (FoM 0.677).
Next: burst 4; the design looks converged (PM binds every area or current cut).

### 5. designer (simulations so far: 97)
Phase C after burst 4 (0 of 20 better). No simulation: the design is converged at sim 56 (FoM 0.677). PM (+0.3 deg) binds every area or current cut, Rc is at its maximum, and changing L breaks the balance (sim 77). Stop rule: 2 cycles without a better design.

### 6. reviewer (simulations so far: 97)
Final design (sim 56, FoM 0.677): mp1 4x1.0u/90n, mn1 10x1.5u/90n, mp3 14x1.0u/90n, mn3 3x1.0u/90n, mn4 7x1.0u/90n, mn5 12x1.0u/90n, Cc 0.3p, Rc 9.8k.
Margins: gain 661 (+230 %), UGBW 104.3 MHz (+4.3 %, flag), PM 60.3 deg (+0.5 %, flag), SR 62.1 V/us (+107 %), noise 21.7 mV (28 % headroom); 215 uA, 831 um2.
Pareto (10 designs meet all specs): sim 56 alone; it has both the lowest current and the lowest area.
Key decisions: (1) sim 2, the mirror currents scaled with the balance Sp3/Sp1 = 2*S5/S4 kept: all specs met; (2) sims 34-35, the current cut on both stages with the balance kept: 232 -> 215 uA; (3) sim 56, Cc 0.4 -> 0.3p, spending the PM headroom on area.
RL: 4 bursts, 90 sims, 0 improvements, 5 designs meeting all specs (best 0.607). Its noise moves all 20 parameters at once, which breaks the mirror balance in most designs.
Cost: 97 sims = 7 designer + 90 RL.

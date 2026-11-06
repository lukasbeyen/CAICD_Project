
## Session mcp_20261106_125332_513492

### 1. tutor (simulations so far: 146)
Nominal from the equations: Itail ~40 uA (mn4 4), I2 ~100 uA (mn5 10), Cc 0.5p, Rc 9.8k (LHP zero), balance Sp3/Sp1 = 2*S5/S4 = 5 (mp3 20), all L 90n. It fails UGBW (67 MHz, FoM -0.17).
Space: 6 free parameters with 9-11 grid points (mn4 1-9, mn5 5-15, mp3 12-22, mn1 5-15, Cc 0.1-1.0p, Rc 8.8-9.8k); fixed: all L (balance), mn3, all W, mp1.
Warm-up (15, one-at-a-time + 3 coupled): mn4 is the lever (+1 finger: UGBW +24 %, current +12 %; -1 breaks the balance, gain -66 %); Cc moves PM (-/+7.5 % per 0.1 pF) and SR; mn1, mn5, mp3, Rc small alone. Both mirror currents up with the balance kept meet all specs (0.599, 0.606).
RL: 130 sims from 0.606 -> 0.650 (6 improvements; it moved mn1, Rc, mn5, mp3, Cc): mn4 8, mn5 11, mp3 13, Cc 0.4p, Rc 9.6k; 223 uA, 850 um2, PM 65.5, UGBW 105.4 MHz.

### 2. reviewer (simulations so far: 146)
Final design (RL, FoM 0.649): the tutor's balanced warm-up design (mn4 8, mn5 13, mp3 13) with mn5 13 -> 11, Cc 0.5 -> 0.4p, Rc 9.8 -> 9.6k; all other values as the nominal.
Margins: gain 644 (+222 %), UGBW 105.4 MHz (+5.4 %), PM 65.5 deg (+9.2 %), SR 58.1 V/us (+94 %), noise 21.1 mV (30 % headroom); 223 uA, 850 um2. No hard spec under 5 %.
Why the RL's changes work (the tutor's table): mn5 has a small effect on PM and UGBW, so cutting I2 by 15 % saves current almost for free; Cc -0.1 pF costs PM (-7.5 %) but saves area and raises SR, and the balanced design had PM headroom; Rc -200 ohm saves area with little effect.
Pareto (top 5, all RL): FoM 0.649 dominates the others (the same 223 uA, more area).
Cost: 146 simulations = 16 tutor (nominal + 15 warm-up) + 130 RL; 88 of 118 distinct designs met all specs.

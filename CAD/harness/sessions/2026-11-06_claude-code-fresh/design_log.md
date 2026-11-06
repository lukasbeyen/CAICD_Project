
## Session mcp_20261106_141955_232199

### 1. tutor (simulations so far: 101)
Circuit: NMOS pair + PMOS mirror (stage 1), PMOS CS + NMOS sink (stage 2), Cc+Rc Miller. UGBW fights PM (CL 10 pF), UGBW/SR fight current.
Nominal (equations): Itail 50 uA (mn4 5/mn3 3), I2 120 uA (mn5 12), Cc 0.4p (GBW est. 149 MHz), Rc 9.8k (zero; (1+CL/Cc)/gm6 ~14k), balance 4.8 (mp3 19), mn1 10x1.5u, L 90n. Measured: only UGBW fails (87.8 MHz); calibration: UGBW 0.59x, SR 0.43x the estimate.
Space: mn4 1-10, mn5 7-17, mp3 14-24, mn1 5-15, Cc 0.1-0.9p, Rc 8.8-9.8k; L, W, mn3, mp1 fixed.
Sensitivities: mn4 is the UGBW lever (+18 %/finger, current +10 %); Cc moves PM (-9.7/+6.6 % per -/+0.1p); mn5, mp3, mn1, Rc small. mn4 6 meets all specs (0.656).
RL (80): 0.656 -> 0.669 (mn1 11, mn5 11); UGBW binds (+0.3 %).
Refine: current cuts via mn5 failed (mn5 -1 now costs -8.6 % UGBW, not -2.8 %: the sensitivities shifted with the balance). mp3 +1 buys UGBW margin (0.662); Cc 0.5p + mp3 21 buys PM margin (0.641). Best stays 0.669 at 101 sims.

### 2. reviewer (simulations so far: 101)
Final design (RL, FoM 0.669): the nominal with mn4 5 -> 6, mn5 12 -> 11, mn1 10 -> 11.
Margins: gain 631 (+216 %), UGBW 100.3 MHz (+0.3 %, flag), PM 63.5 deg (+5.8 %), SR 58.3 V/us (+94 %), noise 19.6 mV (35 % headroom); 211 uA, 867 um2.
Why it works (the tutor's sensitivities): mn4 +1 is the UGBW lever (+18 %), which turns the nominal's 87.8 MHz into a pass; mn5 -1 gives back part of its +10 % current at a small UGBW/PM cost; mn1 +1 adds a little gm1.
Pareto (all meet the specs): 0.669 (211 uA / 867 um2) and 0.667 (213 uA / 858 um2). A more robust alternative: 0.662 (mp3 20) with UGBW +1.8 %.
Cost: 101 simulations = 16 setup + 80 RL + 5 refine; 21 of 92 distinct designs met all specs.

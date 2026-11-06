
## Session mcp_20261106_131251_462595

### 1. tutor (simulations so far: 199)
Nominal from the equations (Itail 40 uA, I2 100 uA, Cc 0.5p, Rc 9.8k, balance 5, L 90n): fails UGBW (67 MHz, -0.17). Space: mn4, mn5, mp3, mn1, Cc, Rc with 9-11 points; all L, W, mn3, mp1 fixed. Warm-up (15): mn4 is the UGBW lever (+24 %/finger), Cc moves PM (-7.5 %/-0.1p); balanced current moves meet all specs (0.606).
RL run 1 (80): 0.606 -> 0.646 (mn5 11, Cc 0.4p, Rc 9.7k; 223 uA, PM 65.6).
Refine: PM headroom (+5.6 deg) and UGBW (+6 %) to spend, current is the main loss. 5 designs; the winner is Cc 0.3p + an I2 cut (mn5 10, mp3 12) = 0.686 (213 uA, 822 um2): the I2 cut alone fails UGBW (-7.3 %), and Cc's UGBW gain makes it pass. Space re-centred (mp3 was at the edge of 12-22, mn4 near the top of 1-9); 87 transitions kept.
RL run 2 (98): no improvement; the design sits on the PM and UGBW limits. Total 199 sims.

### 2. reviewer (simulations so far: 199)
Final design (FoM 0.686, found by the tutor in refine): the nominal with mn4 8, mn5 10, mp3 12, Cc 0.3p, Rc 9.7k; all L 90n.
Margins: gain 640 (+220 %), UGBW 101.3 MHz (+1.3 %, flag), PM 60.04 deg (+0.1 %, flag), SR 59.9 V/us (+100 %), noise 21.2 mV (29 % headroom); 213 uA, 822 um2.
Why it works (the tutor's table): Cc -0.1p buys UGBW (+2.4 %) and area (-4 %) for PM (-8 %); that UGBW lets the I2 cut (mn5 10, current -4.5 %) pass, which fails alone (UGBW -7.3 %). RL run 1 had found the cheaper second stage (mn5 11) and Rc 9.7k.
Pareto (all meet the specs): 0.686 (213 uA / 822 um2) and 0.665 (224 uA / 815 um2: less area, more current, more margin: PM 60.5, UGBW 105.8).
Risk: PM and UGBW margins < 2 %.
Cost: 199 simulations = 16 setup + 80 RL + 5 refine + 98 RL; 124 of 177 distinct designs met all specs.

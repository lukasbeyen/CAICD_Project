---
name: opamp-design
description: The two-stage Miller opamp of this project - the 20 parameters and their allowed values, the first-order design equations, which parameter moves which spec, and the area formula. Load it before designing or simulating.
---
# The opamp: parameters, equations, knobs

S = m·W/L (m = parallel fingers). Fixed: CL = 10 pF, VDD = 1.2 V, VCM = 0.6 V, Ibias = 30 µA, 45 nm, TT, 27 °C.
**The `.param` values in the netlist are placeholders, not a design:** choose every value yourself, the widths
included.

| parameters | device | role |
|---|---|---|
| `mp1 wp1 lp1` | mp1 + mp2 (PMOS) | mirror load of the input pair |
| `mn1 wn1 ln1` | mn1 + mn2 (NMOS) | input pair (gm1) |
| `mn3 wn3 ln3` | mn3 (NMOS diode) | bias reference, 30 µA |
| `mn4 wn4 ln4` | mn4 | tail source: I_tail ≈ 30 µA · S4/S3 |
| `mp3 wp3 lp3` | mp3 (PMOS) | second stage, common source (gm6) |
| `mn5 wn5 ln5` | mn5 | second-stage sink: I2 ≈ 30 µA · S5/S3 |
| `cap`, `res` | Cc, Rc | Miller compensation with a nulling resistor |

**Allowed values** (SI units; anything else is refused):
- `m*`: integers 1 … 24;
- `w*`: 2.5e-07 … 2.75e-06 in steps of 2.5e-07;
- `l*`: 4.5e-08, 9e-08, 1.35e-07, 1.8e-07;
- `cap`: 1e-13 … 9.9e-12 in steps of 1e-13;
- `res`: 0 … 9800 in steps of 100.

## First-order equations (direction and first estimates)
- **Current:** 30 µA + I_tail + I2.
- **Transconductance:** gm ≈ 2·Id/Vov, or gm/Id ≈ 5–20 S/A; a wider or shorter device has a higher gm at the same
  current.
- **Gain:** A0 = gm1(ro2‖ro4) · gm6(ro6‖ro7), with ro ∝ L/Id: a longer L raises the gain.
- **Unity-gain frequency and second pole:** GBW ≈ gm1/(2πCc); p2 ≈ gm6/(2πCL).
- **Phase margin:** PM ≥ 60° needs p2 ≳ 2.2·GBW, i.e. gm6 ≳ 2.2·gm1·CL/Cc. That's large for the budget, so use the
  zero: it sits at 1/(2πCc(1/gm6 − Rc)), and Rc > 1/gm6 makes it a left-half-plane zero that adds phase
  (Rc ≈ (1 + CL/Cc)/gm6 cancels p2).
- **Slew rate** (rising edge): SR ≈ I_tail/Cc, if mp3 can source I2 + CL·SR.
- **Noise** (integrated output): it falls with gm1 relative to the load's gm and with a larger W·L of the pair and the
  load; it rises with more gain or bandwidth.
- **Balance:** S_p3/S_p1 = 2·S5/S4 puts the output at its DC level; a strong imbalance collapses the gain.
- **Calibrate early:** in 45 nm these are first estimates (short-channel effects make the real values differ); measure
  the error on the first simulations and say so in the `reason`.

## Knobs
| to improve | change | watch out for |
|---|---|---|
| gain | longer L; more gm at the same current | more capacitance, less PM |
| UGBW | gm1 ↑ (I_tail ↑), Cc ↓ | PM ↓, current ↑ |
| PM | Rc → (1 + CL/Cc)/gm6; gm6 ↑ (I2 ↑, wider mp3); Cc ↑ | Cc ↑ costs UGBW, SR, area |
| slew rate | I_tail ↑, Cc ↓ | current ↑, PM ↓ |
| noise | gm1 ↑ vs. the load; larger W·L of the pair and the load | area ↑ |
| current | lower S4/S3 and S5/S3 (a larger mn3) | gm1, gm6 ↓ |
| area | Rc ↓ and Cc ↓ (they dominate); fewer or shorter fingers | Cc ↓ costs PM; Rc ↓ moves the zero |

**Area** (the `area` spec): transistor m·(W·L + 2(W·160 nm + 50 nm·L)), with the pair and the mirror load counted
twice; Cc ≈ 333 µm²/pF; Rc ≈ 71 µm²/kΩ (9.8 kΩ ≈ 700 µm²). The target is 2000 µm².

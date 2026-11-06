---
name: two-stage-opamp-design
description: The circuit of this project (device map, allowed parameter values) and hand-design knowledge - first-order equations, which parameter moves which spec (the knobs), the trade-offs, and the area formula. Use it to make a first design, to diagnose a failing spec, and to choose the next change.
---
# Two-stage Miller opamp: the circuit, the allowed values, equations, knobs and trade-offs

## The circuit (netlist `ngspice_interface/files/input_netlists/TwoStage.cir`, 45 nm PTM models, TT, 27 °C)
`S = m·W/L` is a transistor's size ratio (m = number of parallel fingers).

| parameters | device(s) | role |
|---|---|---|
| `mp1 wp1 lp1` | mp1 + mp2 (PMOS, identical) | current-mirror load of the input pair (mp1 diode-connected) |
| `mn1 wn1 ln1` | mn1 + mn2 (NMOS, identical) | input differential pair |
| `mn3 wn3 ln3` | mn3 (NMOS, diode) | bias reference: carries Ibias = 30 µA, sets the gate of mn4 and mn5 |
| `mn4 wn4 ln4` | mn4 (NMOS) | tail current source: I_tail ≈ 30 µA · S4/S3 |
| `mp3 wp3 lp3` | mp3 (PMOS) | second stage, common source; gate = first-stage output |
| `mn5 wn5 ln5` | mn5 (NMOS) | second-stage current sink: I2 ≈ 30 µA · S5/S3 |
| `cap` | Cc | Miller compensation capacitor, first-stage output → output |
| `res` | Rc | nulling resistor in series with Cc |

Fixed: load CL = 10 pF, VDD = 1.2 V, input common mode 0.6 V, Ibias = 30 µA.

## Allowed values (SI units: m, F, Ω; anything else is rejected by the tools)
- `m*`: integers 1 … 24
- `w*`: 0.25 µm … 2.75 µm in steps of 0.25 µm (2.5e-07 … 2.75e-06)
- `l*`: 45, 90, 135 or 180 nm (4.5e-08, 9e-08, 1.35e-07, 1.8e-07)
- `cap`: 0.1 pF … 9.9 pF in steps of 0.1 pF
- `res`: 0 … 9800 Ω in steps of 100 Ω

Notation: `S = m·W/L` per transistor. Pair = mn1/mn2 (gm1), mirror load = mp1/mp2, second stage = mp3 (gm6) with
the current sink mn5, tail = mn4, bias diode = mn3 (30 µA). CL = 10 pF.

## First-order equations (use them for direction and first estimates)
- **Currents** (current mirrors off the 30 µA bias):
  - I_tail ≈ 30 µA · S4/S3;
  - I2 ≈ 30 µA · S5/S3;
  - supply current ≈ 30 µA + I_tail + I2.
- **Transconductance:** gm ≈ 2·Id / Vov (strong inversion), or gm = (gm/Id)·Id with gm/Id ≈ 5–20 S/A from strong to
  moderate inversion. A wider (or more fingers) / shorter device at the same current has a lower Vov and a higher gm.
- **Gain:** A0 = A1·A2 with A1 = gm1·(ro2 ‖ ro4) and A2 = gm6·(ro6 ‖ ro7), where ro ∝ L/Id. Longer L on the pair,
  the load, mp3 and mn5 raises the gain.
- **Unity-gain frequency:** GBW ≈ gm1 / (2π·Cc).
- **Second pole:** p2 ≈ gm6 / (2π·CL) (when Cc is much larger than the internal node capacitance).
- **Zero:** without Rc, an RHP zero at gm6 / (2π·Cc) costs phase. With the nulling resistor the zero is at
  1 / (2π·Cc·(1/gm6 − Rc)):
  - Rc = 1/gm6 moves it to infinity;
  - Rc > 1/gm6 makes it a **left-half-plane zero**, which adds phase; placed near p2 or the UGBW it can largely
    cancel p2: Rc ≈ (1 + CL/Cc)/gm6.
- **Phase margin:** with the zero at infinity, PM ≥ 60° needs p2 ≳ 2.2·GBW, i.e. gm6 ≳ 2.2·gm1·CL/Cc. With
  CL = 10 pF that is a large gm6 for the current budget: **Rc is the main PM knob here**.
- **Slew rate (measured on the rising edge):**
  - SR ≈ I_tail / Cc, if mp3 can source I2 + CL·SR;
  - the falling edge is limited by I2 / (CL + Cc).
- **Noise** (output noise integrated over 1 Hz–1 THz): it is roughly the input-referred noise density × the gain ×
  the bandwidth. A larger gm1 relative to the load's gm lowers it (thermal), and a larger W·L of the pair and the
  load lowers the 1/f part. More gain or bandwidth raises the integrated output noise.
- **Systematic balance** (textbook): (S_p3 / S_p1) = 2·(S5 / S4) puts the output at its nominal DC level. A strong
  imbalance pushes a second-stage device out of saturation, and the gain collapses.

**Calibrate early.** In this 45 nm process the textbook formulas are only first estimates: channel-length modulation
and short-channel effects make the real mirror currents and the slew rate differ from them by up to ~2×. Use the
first simulations to measure how far off they are, and correct your model (say so in the `reason`).

## The knobs (what to change for which spec)
| to improve | change | watch out for |
|---|---|---|
| gain ↑ | longer L of the pair/load/mp3/mn5; higher gm1 or gm6 at the same current | more capacitance → lower p2 → less PM |
| UGBW ↑ | gm1 ↑ (I_tail ↑, or a wider pair), or Cc ↓ | PM ↓ (GBW moves towards p2); current ↑ |
| PM ↑ | Rc towards (1 + CL/Cc)/gm6 (LHP zero); gm6 ↑ (I2 ↑, wider mp3); Cc ↑ | Cc ↑ lowers UGBW and SR and costs area; I2 ↑ costs current |
| slew rate ↑ | I_tail ↑, or Cc ↓ | current ↑ / PM ↓ |
| noise ↓ | gm1 ↑ vs. the load; larger W·L of the pair and the load; not more gain/bandwidth than needed | area ↑ |
| current ↓ | lower S4/S3 and S5/S3 (e.g. a larger mn3) | gm1 and gm6 ↓ → UGBW, PM, SR ↓ |
| area ↓ | Rc ↓ and Cc ↓ (they dominate: a 9.8 kΩ Rc ≈ 700 µm², 1 pF ≈ 333 µm²); fewer/shorter fingers | Cc ↓ costs PM; Rc ↓ moves the LHP zero |

## Area estimate (the `area` spec)
- Transistor: m · (W·L + 2·(W·160 nm + 50 nm·L)). The pair (mn1) and the mirror load (mp1) count **twice**
  (two devices each).
- Cc: about **333 µm² per pF** (100 µm² per 300 fF).
- Rc: about **71 µm² per kΩ**.
- Target: 2000 µm². A 3 pF Cc alone is half of it; a 9.8 kΩ Rc is about 700 µm².

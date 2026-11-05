Size the two-stage Miller opamp described in AGENTS.md with the CAD tools.

Goal: meet all hard specs (gain, UGBW, phase margin, slew rate, noise) and then make area and supply current as low as
possible, with as few simulations as possible. Aim to stay under 300 simulations in total.

Work as the orchestrator described in AGENTS.md: start a new session header in harness/design_log.md, run the
circuit-analyst, then designer rounds, call the rl-operator only if the designer is stuck, and finish with the
reviewer. Grant each subagent only the MCP tools listed for it in AGENTS.md. Give every simulate/warmup/train call a
reason, append every step to the design log in the format of the design-log skill, and end with the reviewer's final
summary (the final design, the margins, the 3 key decisions, the simulation count).

# Harness session 2026-11-05 (Gemini 3.8 Flash in Antigravity CLI 1.5.1)

A frozen copy of the session's results (the originals are in the git-ignored `runs/`). The reasoning per step is in
`../../design_log.md` (entries 1–7).

| file | content |
|---|---|
| `harness_history_part1.csv` | simulations 1–10 (`runs/mcp_20261105_172708_916291`): analyst design + designer round 1 |
| `harness_history_part2.csv` | simulations 11–16 (`runs/mcp_20261105_174949_803170`): designer round 2, after an agy restart (a new MCP server, so the call numbers start again at 1; its first call re-simulates the round-1 best design) |
| `feasible_netlists/` | the 6 designs that met all hard specs |
| `final_design.cir` | the reviewer's final design: part 2, call 2 (session simulation 12), FoM 0.684 |

Every row of the history: wall time, seconds since that MCP server started (incl. the LLM's thinking time), call
number, source (`simulate` only: the harness decided RL was not needed), the agent's `reason`, the netlist, the 20
parameters, the 7 specs, the reward, `hard_satisfied`, `failed`.

The runtime comparison: `cd CAD && python analysis/harness_vs_rl.py --harness mcp_20261105_172708_916291
mcp_20261105_174949_803170 --rl B_pilr_w_s123456 B_pilr_w_s1 B_pilr_w_s2` (joins the two parts without the pause).

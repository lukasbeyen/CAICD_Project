# The session prompts of the RL → LLM → RL flow

Since the final run, this flow is also the tutor's own prompt (`.agents/agents/tutor.md`), so the final agy run
needs only `../session_prompt.md` (main agent → tutor → reviewer, with subagents). The prompts below are the
evaluated variants: they override the tutor's steps of that time and play every role in one conversation.

| file | what it is |
|---|---|
| `rl_first_evaluated.txt` | **the exact prompt of the evaluation runs** on the unseen seeds 3, 4, 5 (`../sessions/2026-11-06_eval-rl-first-seeds345/`), copied byte for byte from the sessions' transcripts (identical in all three) |
| `llm_first_big_rl_evaluated.txt` | the exact prompt of the comparison flow, LLM first then one big RL, on the same seeds (`../sessions/2026-11-06_eval-llm-first-big-rl-seeds345/`) |
| `rl_first_final.txt` | **the final version for the report**: the same prompt without the polish step `warmup(50)`, and the budget line 2200 → 2100 |
| `rl_first_final_agy.txt` | the same for **agy**, with one operational sentence: no subagents (the main agent plays the tutor and the reviewer), which saves agy's per-subagent system-prompt overhead |

**Why the polish was removed:**
- In the evaluation runs it never produced the final design. All three final designs came from the second
  `train(800)`, before the polish.
- Without it, the runs would have reached the same final designs. Only the later `get_status(10)` lists differ, by
  the polish designs.
- It saves ≈ 55 simulations.
- The final version itself was not re-run.

## The flow
1. **RL:** `warmup(100)` + `train(800)`, TD3 from scratch (≈ 990 simulations).
2. **LLM:** ≤ 5 iterative `simulate` refinements. Each reason estimates the effect on every hard-spec margin and on
   both FoM terms. The agent weighs margin against the FoM itself.
3. **RL:** `warmup(200)` around the best design, then `train(800)`. `train` first pulls the actor to the best design
   (the warm start in `sizing_tools.py`).
4. **LLM:** a judgement stop, else ≤ 3 more refinements.
5. **The reviewer summary.**

Only the course's 4 tools (`mcp_server.py`). The prompt and the skills contain only general knowledge, no values
taken from earlier runs.

## How the evaluation runs were started
The code was `feat/m4-template` at `908d8a6`: the warm-up around the best design, the warm start, the general-only
skills. One copy of `CAD/` per seed, outside the repo, so that parallel runs don't share `no_backup/` (`clean.sh`)
and no earlier results or `CLAUDE.md` can be read:

```bash
rsync -a --exclude runs/ --exclude no_backup/ --exclude harness/sessions/ --exclude solutions/ \
      --exclude tests/ --exclude analysis/ CAD/ ~/harness_lanes/s3/CAD/
mkdir -p ~/harness_lanes/s3/CAD/no_backup
cd ~/harness_lanes/s3/CAD
MCP_TOOL_TIMEOUT=900000 claude --model sonnet --tools "Read,Glob,Grep" --strict-mcp-config \
  --mcp-config '{"mcpServers":{"cad":{"command":"<venv>/bin/python","args":["<lane>/CAD/mcp_server.py","--seed","3"]}}}' \
  --allowedTools "mcp__cad__simulate,mcp__cad__warmup,mcp__cad__train,mcp__cad__get_status,Read,Glob,Grep" \
  --disallowedTools "Read(//<repo>/**)"
```

Then paste the prompt. Seeds 4 and 5 were the same, in `~/harness_lanes/s4` and `s5`. Claude Code 2.1.316 with
Sonnet: no Bash, Write or Edit, no web, no subagents; only the `cad` server.

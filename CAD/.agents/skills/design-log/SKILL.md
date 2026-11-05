---
name: design-log
description: The format of the harness memory harness/design_log.md - how the orchestrator records every decision, its reason and its result, so the next agent and a human reviewer can follow the whole session.
---
# The design log (`harness/design_log.md`)

The design log is the **shared memory** of the harness:
- the orchestrator appends one entry after every subagent call and every decision;
- subagents read the entries they are given;
- a human reviewer reads the whole log to follow the session.

The tools also store every simulated design with its `reason` in `runs/<run_id>/harness_history.csv`. The log is the
summary that explains it.

## Rules
- **Append only.** Never edit or delete earlier entries; correct a mistake in a new entry.
- **Numbers only from tool results**, copied, not estimated. Estimates are labelled *estimate*.
- Every entry mentions the simulation count so far (`get_status().simulator_calls`).
- Start every session with a header: `## Session <date time>`, plus the model in use.

## Entry format
```
### <n>. <agent>: <short title>   (simulations so far: <N>)
- **Goal:** what this step had to achieve.
- **Reasoning:** the circuit argument (equations, sensitivities) behind the decision.
- **Actions:** the tool calls, with the key parameter changes (e.g. "Cc 2.0 → 1.6 pF").
- **Result:** the specs and the reward that came back; which hard specs are met.
- **Conclusion / next:** what was learned and what happens next, and why.
```

## Orchestrator decisions
Write routing decisions as their own short entries, e.g.
```
### 7. orchestrator: designer stuck, call the RL operator   (simulations so far: 46)
- **Reasoning:** 2 rounds without improvement; PM and UGBW trade off against each other at every local change.
- **Decision:** rl-operator with a budget of 400 simulations; pass it entries 3–6.
```

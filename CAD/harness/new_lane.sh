#!/usr/bin/env bash
# Make a clean copy ("lane") of CAD/ for one harness run, outside the repo, so the run can't see earlier runs,
# results or private notes, and parallel runs don't share no_backup/ (clean.sh).
#
# One lane works for both agy and Claude Code, with the same harness: AGENTS.md, the subagents tutor and reviewer,
# the skills opamp-design and rl-tutoring, the cad MCP server and harness/session_prompt.md. Only the command that
# starts the session differs; the script prints both at the end.
#
# Usage, from CAD/:   bash harness/new_lane.sh ~/harness_lanes/final [SEED]
#   SEED     the MCP server's seed (default 123456, the server's own default)
#   PYTHON   the venv's python, if it isn't ../.venv/bin/python:  PYTHON=/path/bin/python bash harness/new_lane.sh ...
set -euo pipefail

if [ $# -lt 1 ]; then echo "usage: bash harness/new_lane.sh LANE_DIR [SEED]"; exit 1; fi
SEED=${2:-123456}
CAD=$(cd "$(dirname "$0")/.." && pwd)                       # this repo's CAD/
PYTHON=${PYTHON:-$(dirname "$CAD")/.venv/bin/python}
mkdir -p "$1"
DST=$(cd "$1" && pwd)/CAD
if [ -e "$DST" ]; then echo "$DST exists already: pick a new lane name"; exit 1; fi

# 1. The copy, without earlier runs, results, transcripts and tests.
rsync -a --exclude runs/ --exclude no_backup/ --exclude harness/sessions/ --exclude solutions/ --exclude tests/ \
      --exclude analysis/ --exclude output_figs/ --exclude __pycache__/ --exclude .pytest_cache/ "$CAD/" "$DST/"
mkdir -p "$DST/no_backup"

# 2. The cad MCP server of this lane, for agy (.agents/mcp_config.json) and Claude Code (.mcp.json).
cat > "$DST/.agents/mcp_config.json" <<EOF
{
  "mcpServers": {
    "cad": {
      "command": "$PYTHON",
      "args": ["$DST/mcp_server.py", "--seed", "$SEED"],
      "cwd": "$DST",
      "env": {"PATH": "$(dirname "$PYTHON"):/usr/local/bin:/usr/bin:/bin"},
      "timeoutSeconds": 600
    }
  }
}
EOF
cp "$DST/.agents/mcp_config.json" "$DST/.mcp.json"

# 3. Claude Code looks for the same files elsewhere: CLAUDE.md (here it only imports AGENTS.md), .claude/skills
#    (a copy of .agents/skills) and .claude/agents (the same tutor and reviewer, with agy's file-reading tool
#    view_file replaced by Claude Code's names for it, plus the cad tools).
echo "@AGENTS.md" > "$DST/CLAUDE.md"
mkdir -p "$DST/.claude/agents"
cp -r "$DST/.agents/skills" "$DST/.claude/skills"
for f in "$DST"/.agents/agents/*.md; do
  sed 's/^tools: \[view_file\]$/tools: Read, Glob, Grep, Skill, mcp__cad__simulate, mcp__cad__warmup, mcp__cad__train, mcp__cad__get_status/' \
      "$f" > "$DST/.claude/agents/$(basename "$f")"
done

cat <<EOF
Lane ready: $DST (seed $SEED)
cd $DST, start ONE of the two, then paste harness/session_prompt.md:

agy --new-project --model claude-sonnet-4-6 \\
  --settings '{"permissions":{"allow":["mcp(cad/simulate)","mcp(cad/warmup)","mcp(cad/train)","mcp(cad/get_status)"]}}'

MCP_TOOL_TIMEOUT=900000 claude --model claude-sonnet-4-6 --strict-mcp-config --mcp-config .mcp.json \\
  --tools "Read,Glob,Grep,Agent,Skill" \\
  --allowedTools "mcp__cad__simulate,mcp__cad__warmup,mcp__cad__train,mcp__cad__get_status,Read,Glob,Grep,Agent,Skill" \\
  --disallowedTools "Read(//$(dirname "$CAD" | sed 's#^/##')/**)"
EOF

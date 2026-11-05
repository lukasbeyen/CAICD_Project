"""Checks of the Antigravity harness files (milestone 4): agy silently ignores a subagent or skill whose frontmatter
is broken, so these catch typos before a session.

Formats (antigravity.google/docs): subagents `.agents/agents/<name>.md` and skills `.agents/skills/<name>/SKILL.md`
with YAML frontmatter (`name`, `description`); `AGENTS.md` at most 24 000 bytes; `.agents/mcp_config.json`.
"""
import json
import os
import re

import yaml

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = os.path.join(CAD, '.agents', 'agents')
SKILLS = os.path.join(CAD, '.agents', 'skills')
MCP_TOOLS = {'simulate', 'warmup', 'train', 'get_status'}


def frontmatter(path):
    text = open(path).read()
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', text, re.S)
    assert match, f'{path}: no YAML frontmatter'
    return yaml.safe_load(match.group(1)), match.group(2)


def test_agents_md_fits_the_rules_budget():
    assert os.path.getsize(os.path.join(CAD, 'AGENTS.md')) <= 24_000


def test_every_subagent_has_name_description_and_a_prompt():
    names = []
    for file in sorted(os.listdir(AGENTS)):
        meta, body = frontmatter(os.path.join(AGENTS, file))
        assert meta['name'] == file[:-3] and meta['description'].strip(), file
        assert meta.get('tools', []) == ['view_file'], file  # documented tool names only (unknown ones can hang)
        assert len(body.split()) > 50, file
        names.append(meta['name'])
    assert names == ['circuit-analyst', 'designer', 'reviewer', 'rl-operator']


def test_every_skill_has_name_and_description():
    for folder in sorted(os.listdir(SKILLS)):
        meta, body = frontmatter(os.path.join(SKILLS, folder, 'SKILL.md'))
        assert meta['name'] == folder and meta['description'].strip(), folder
        assert len(body.split()) > 50, folder


def test_agents_md_names_every_subagent_skill_and_tool():
    text = open(os.path.join(CAD, 'AGENTS.md')).read()
    for name in os.listdir(AGENTS):
        assert f'`{name[:-3]}`' in text, name
    for name in os.listdir(SKILLS):
        assert f'`{name}`' in text, name
    for tool in MCP_TOOLS:
        assert f'`{tool}' in text, tool


def test_mcp_config_starts_this_folders_server():
    server = json.load(open(os.path.join(CAD, '.agents', 'mcp_config.json')))['mcpServers']['cad']
    assert server['args'][-1].endswith('mcp_server.py') and server['cwd'].endswith('CAD')

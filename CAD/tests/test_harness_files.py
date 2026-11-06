"""Checks of the Antigravity harness files (version 2): agy silently ignores a subagent or skill whose frontmatter is
broken, and every byte of AGENTS.md, of an agent prompt and of a loaded skill is re-read on every turn (tokens)."""
import json
import os
import re

import yaml

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = os.path.join(CAD, '.agents', 'agents')
SKILLS = os.path.join(CAD, '.agents', 'skills')
MCP_TOOLS = {'simulate', 'rl_explore', 'get_status', 'log_entry'}


def frontmatter(path):
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', open(path).read(), re.S)
    assert match, f'{path}: no YAML frontmatter'
    return yaml.safe_load(match.group(1)), match.group(2)


def test_the_always_loaded_context_is_small():
    assert os.path.getsize(os.path.join(CAD, 'AGENTS.md')) <= 3500
    for file in os.listdir(AGENTS):
        assert os.path.getsize(os.path.join(AGENTS, file)) <= 2000, file
    for folder in os.listdir(SKILLS):
        assert os.path.getsize(os.path.join(SKILLS, folder, 'SKILL.md')) <= 4500, folder


def test_the_three_agents_have_name_description_tools_and_a_prompt():
    names = []
    for file in sorted(os.listdir(AGENTS)):
        meta, body = frontmatter(os.path.join(AGENTS, file))
        assert meta['name'] == file[:-3] and meta['description'].strip(), file
        assert meta.get('tools', []) == ['view_file'], file  # documented tool names only (unknown ones can hang)
        used = set(re.findall(r'`(\w+)`', body.split('MCP tools:')[1].split('.')[0]))
        assert used and used <= MCP_TOOLS, (file, used)  # only real MCP tools
        names.append(meta['name'])
    assert names == ['designer', 'reviewer', 'rl-explorer']


def test_the_skills_have_name_and_description():
    assert sorted(os.listdir(SKILLS)) == ['hybrid-rl', 'opamp-design']
    for folder in os.listdir(SKILLS):
        meta, body = frontmatter(os.path.join(SKILLS, folder, 'SKILL.md'))
        assert meta['name'] == folder and meta['description'].strip(), folder


def test_agents_md_names_every_agent_skill_and_tool():
    text = open(os.path.join(CAD, 'AGENTS.md')).read()
    for name in ['designer', 'rl-explorer', 'reviewer', 'opamp-design', 'hybrid-rl']:
        assert f'`{name}`' in text, name
    for tool in MCP_TOOLS:
        assert f'`{tool}' in text, tool


def test_the_mcp_config_starts_the_hybrid_server():
    server = json.load(open(os.path.join(CAD, '.agents', 'mcp_config.json')))['mcpServers']['cad']
    assert server['args'][-1].endswith('hybrid_mcp_server.py') and server['cwd'].endswith('CAD')

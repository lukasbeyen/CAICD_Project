"""End-to-end test of tutor_mcp_server.py over stdio, the way Antigravity CLI talks to it (no simulation runs)."""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def talk_to_the_server():
    server = StdioServerParameters(command=sys.executable, args=[os.path.join(CAD, 'tutor_mcp_server.py')], cwd=CAD,
                                   env=dict(os.environ))
    with open(os.devnull, 'w') as quiet:
        async with stdio_client(server, errlog=quiet) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                status = await session.call_tool('get_status', {'k': 3})
                early = await session.call_tool('run_rl', {'n_sims': 10, 'reason': 'test'})
                bad = await session.call_tool('setup_rl', {'nominal': {'mp1': 1.0}, 'search_space': {'mn1': [1.0, 3.0]},
                                                           'warmup': [{'changes': {'mn1': 2.0}, 'purpose': 'test'}]})
                return tools, status, early, bad


def test_the_tutor_server_offers_five_lean_tools():
    tools, status, early, bad = asyncio.run(asyncio.wait_for(talk_to_the_server(), timeout=120))
    assert {tool.name for tool in tools} == {'setup_rl', 'run_rl', 'refine', 'get_status', 'log_entry'}
    sent_every_turn = sum(len(tool.description or '') + len(json.dumps(tool.input_schema)) for tool in tools)
    assert sent_every_turn < 3000, sent_every_turn  # the tool descriptions go to the model on every turn
    assert not status.is_error and json.loads(status.content[0].text)['simulator_calls'] == 0
    assert early.is_error and 'setup_rl' in early.content[0].text  # the RL needs the tutor's setup first
    assert bad.is_error and 'missing parameters' in bad.content[0].text  # an incomplete nominal: a readable error

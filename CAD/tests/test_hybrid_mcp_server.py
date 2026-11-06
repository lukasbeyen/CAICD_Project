"""End-to-end test of hybrid_mcp_server.py over stdio, the way Antigravity CLI talks to it (no simulation runs)."""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def talk_to_the_server():
    server = StdioServerParameters(command=sys.executable, args=[os.path.join(CAD, 'hybrid_mcp_server.py')], cwd=CAD,
                                   env=dict(os.environ))
    with open(os.devnull, 'w') as quiet:
        async with stdio_client(server, errlog=quiet) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                status = await session.call_tool('get_status', {'k': 3})
                early = await session.call_tool('rl_explore', {'n_steps': 10, 'reason': 'test'})
                return tools, status, early


def test_the_hybrid_server_offers_four_lean_tools():
    tools, status, early = asyncio.run(asyncio.wait_for(talk_to_the_server(), timeout=120))
    assert {tool.name for tool in tools} == {'simulate', 'rl_explore', 'get_status', 'log_entry'}
    # the tool descriptions and schemas go to the model on every turn: keep them small
    sent_every_turn = sum(len(tool.description or '') + len(json.dumps(tool.input_schema)) for tool in tools)
    assert sent_every_turn < 3000, sent_every_turn
    assert not status.is_error and json.loads(status.content[0].text)['simulator_calls'] == 0
    # RL before any design: a readable tool error, not a crash
    assert early.is_error and 'simulate first' in early.content[0].text

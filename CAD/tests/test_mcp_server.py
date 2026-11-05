"""End-to-end test of mcp_server.py over stdio, the way a coding agent (Antigravity CLI) talks to it.

Starts the real server as a subprocess with an MCP client, lists the tools and calls two of them. No simulation runs:
get_status only reads counters, and the invalid design is rejected before ngspice.
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def talk_to_the_server():
    server = StdioServerParameters(command=sys.executable, args=[os.path.join(CAD, 'mcp_server.py')], cwd=CAD,
                                   env=dict(os.environ))
    with open(os.devnull, 'w') as quiet:  # the server's stderr (env prints) stays out of the test output
        async with stdio_client(server, errlog=quiet) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                status = await session.call_tool('get_status', {'k': 3})
                invalid = await session.call_tool('simulate', {'parameters': {'mp1': 1.0}, 'reason': 'test'})
                return tools, status, invalid


def result_json(result):
    return json.loads(result.content[0].text)


def test_the_server_offers_the_four_tools_with_a_reason_argument():
    tools, status, invalid = asyncio.run(asyncio.wait_for(talk_to_the_server(), timeout=120))
    assert set(tools) == {'simulate', 'warmup', 'train', 'get_status'}
    for name in ['simulate', 'warmup', 'train']:
        assert 'reason' in tools[name].input_schema['properties'], name
        assert 'reason' not in tools[name].input_schema.get('required', []), name  # optional
    # get_status: a fresh experiment, nothing simulated
    assert not status.is_error
    counters = result_json(status)
    assert counters['simulator_calls'] == 0 and counters['best_candidates'] == []
    assert counters['hard_constraints'] == ['gain', 'noise', 'phm', 'slewRate', 'ugbw']
    # an incomplete design comes back as a tool error the LLM can read (not a crash of the server)
    assert invalid.is_error and 'missing parameters' in invalid.content[0].text

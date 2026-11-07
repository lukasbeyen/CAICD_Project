"""Check the cad MCP server exactly the way agy starts it, before a session (costs no LLM tokens).

Usage, in the folder where you start agy (CAD/ or a lane's CAD/):   python harness/check_mcp.py
It reads .agents/mcp_config.json, starts that command with those args, cwd and PATH, lists the tools and calls
get_status. No simulation runs. If this fails, agy has no cad tools either.
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CONFIG = os.path.join('.agents', 'mcp_config.json')


async def talk_to_the_server(cad):
    server = StdioServerParameters(command=cad['command'], args=cad['args'], cwd=cad['cwd'],
                                   env={**os.environ, **cad.get('env', {})})
    async with stdio_client(server) as (read, write):  # the server's errors (stderr) are printed here
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [tool.name for tool in (await session.list_tools()).tools]
            status = await session.call_tool('get_status', {'k': 1})
            return tools, json.loads(status.content[0].text)


def main():
    if not os.path.isfile(CONFIG):
        sys.exit(f'no {CONFIG} here: run this in the folder where you start agy')
    cad = json.load(open(CONFIG))['mcpServers']['cad']
    print('command:', cad['command'], *cad['args'])
    print('cwd:    ', cad['cwd'])
    for path in [cad['command'], cad['args'][0], cad['cwd']]:
        if not os.path.exists(path):
            sys.exit(f'FAIL: {path} does not exist on this machine: fix {CONFIG} (or make a lane with new_lane.sh)')
    tools, status = asyncio.run(asyncio.wait_for(talk_to_the_server(cad), timeout=120))
    print('tools:  ', tools)
    print('status: ', status['simulator_calls'], 'simulations so far')
    if sorted(tools) != ['get_status', 'simulate', 'train', 'warmup']:
        sys.exit('FAIL: expected the 4 tools simulate, warmup, train, get_status')
    print('OK: agy will get the cad tools from this config')


if __name__ == '__main__':
    main()

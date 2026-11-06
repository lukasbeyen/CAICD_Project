"""The MCP server of harness version 2: the LLM designs, short RL bursts explore around its best design.

The same structure as the course's mcp_server.py (one experiment per process, calls serialized, stdout reserved for
the MCP protocol). The tool docstrings are short on purpose: the model gets them on every turn.
"""

import argparse
from contextlib import redirect_stdout
import os
from pathlib import Path
import sys
from threading import Lock
from typing import Any, Optional, Union

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import StrictFloat, StrictInt

with redirect_stdout(sys.stderr):
    from hybrid_tools import HybridExperiment


def create_server(experiment):
    """Register the 4 tools for one experiment; serialize calls that share its state."""
    server = MCPServer("CAD hybrid sizing", description="Opamp sizing: LLM designs + short TD3 bursts.")
    lock = Lock()

    def call(method, **arguments):
        with lock, redirect_stdout(sys.stderr):
            try:
                return getattr(experiment, method)(**arguments)
            except (ValueError, RuntimeError) as error:
                raise ToolError(str(error)) from error

    @server.tool()
    def simulate(parameters: Optional[dict[str, StrictFloat]] = None, changes: Optional[dict[str, StrictFloat]] = None,
                 base: Union[StrictInt, str] = "best", reason: str = "") -> dict[str, Any]:
        """Simulate one design: all 20 `parameters` (SI units), or only `changes` to `base` ("best" or a simulation
        number). `reason`: hypothesis -> expected effect. Returns specs, reward, hard_constraints_satisfied."""
        return call("simulate", parameters=parameters, changes=changes, base=base, reason=reason)

    @server.tool()
    def rl_explore(n_steps: StrictInt, reason: str = "") -> dict[str, Any]:
        """One TD3 burst of n_steps (1..60) simulations around the current best design, learning from all designs.
        Returns what it changed vs the previous best, and the best reward/specs."""
        return call("rl_explore", n_steps=n_steps, reason=reason)

    @server.tool()
    def get_status(k: StrictInt = 3) -> dict[str, Any]:
        """Counters and the k (1..20) best designs so far. No simulation."""
        return call("get_status", k=k)

    @server.tool()
    def log_entry(agent: str, text: str) -> dict[str, Any]:
        """Append your step to the shared design log (at most 1200 characters)."""
        return call("log_entry", agent=agent, text=text)

    return server


def main():
    parser = argparse.ArgumentParser(description="CAD hybrid sizing MCP server (stdio)")
    parser.add_argument("--seed", type=int, default=123456)
    args = parser.parse_args()
    # the course code resolves model and netlist paths relative to the project folder (CAD/)
    os.chdir(Path(__file__).resolve().parent)
    with redirect_stdout(sys.stderr):
        experiment = HybridExperiment(args.seed)
    create_server(experiment).run(transport="stdio")


if __name__ == "__main__":
    main()

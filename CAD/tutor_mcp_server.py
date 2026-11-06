"""The MCP server of harness version 3: the LLM tutors the RL, the RL optimizes.

The same structure as the course's mcp_server.py. The tool docstrings are short on purpose: the model gets them on
every turn.
"""

import argparse
from contextlib import redirect_stdout
import os
from pathlib import Path
import sys
from threading import Lock
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, StrictFloat, StrictInt

with redirect_stdout(sys.stderr):
    from tutor_tools import TutorExperiment


class WarmupDesign(BaseModel):
    changes: dict[str, StrictFloat]  # relative to the nominal, inside the search space
    purpose: str                      # what this design teaches the RL


def create_server(experiment):
    """Register the 5 tools for one experiment; serialize calls that share its state."""
    server = MCPServer("CAD RL tutor", description="Opamp sizing: the LLM sets up the RL, TD3 optimizes.")
    lock = Lock()

    def call(method, **arguments):
        with lock, redirect_stdout(sys.stderr):
            try:
                return getattr(experiment, method)(**arguments)
            except (ValueError, RuntimeError) as error:
                raise ToolError(str(error)) from error

    @server.tool()
    def setup_rl(nominal: dict[str, StrictFloat], search_space: dict[str, list[StrictFloat]],
                 warmup: list[WarmupDesign], reason: str = "") -> dict[str, Any]:
        """Once: the nominal design (20 values, SI), the RL's search space {name: [low, high]} (others fixed) and
        <= 20 warm-up designs. Simulates them; returns a sensitivity table (spec change in % per design)."""
        return call("setup_rl", nominal=nominal, search_space=search_space,
                    warmup=[item.model_dump() for item in warmup], reason=reason)

    @server.tool()
    def run_rl(n_sims: StrictInt, reason: str = "") -> dict[str, Any]:
        """TD3 alone for n_sims simulations in that space (< 200 in total). Returns the best design (changes vs
        nominal), its spec margins and which parameters its improvements moved."""
        return call("run_rl", n_sims=n_sims, reason=reason)

    @server.tool()
    def refine(designs: list[WarmupDesign], reason: str = "") -> dict[str, Any]:
        """After the RL run, at most 2 rounds: 1-5 reasoned designs (changes vs the current best). Returns their
        sensitivity rows and the new best's margins."""
        return call("refine", designs=[item.model_dump() for item in designs], reason=reason)

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
    parser = argparse.ArgumentParser(description="CAD RL-tutor MCP server (stdio)")
    parser.add_argument("--seed", type=int, default=123456)
    args = parser.parse_args()
    # the course code resolves model and netlist paths relative to the project folder (CAD/)
    os.chdir(Path(__file__).resolve().parent)
    with redirect_stdout(sys.stderr):
        experiment = TutorExperiment(args.seed)
    create_server(experiment).run(transport="stdio")


if __name__ == "__main__":
    main()

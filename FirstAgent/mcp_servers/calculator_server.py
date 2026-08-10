"""MCP server exposing CalculatorSkill operations.

The server communicates with VS Code over standard input/output.
Do not print normal application messages to stdout because stdout is
reserved for MCP protocol messages.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Allow execution as a script while still resolving the workspace package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server import MCPServer
from skills.calculator import calculator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger("calculator-mcp")


mcp = MCPServer("calculator")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two finite numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The sum of a and b.
    """

    logger.info("Calling calculator.add with a=%s, b=%s", a, b)
    return calculator.add(a, b)


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two finite numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The product of a and b.
    """
    logger.info("Calling calculator.multiply with a=%s, b=%s", a, b)

    return calculator.multiply(a, b)


if __name__ == "__main__":
    mcp.run()
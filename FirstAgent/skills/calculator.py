"""Core calculator business logic.

This module contains no MCP-specific code. It can be imported by the
MCP server, unit tests, command-line applications, or other agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Number = int | float


@dataclass(frozen=True)
class CalculatorSkill:
    """Perform basic validated arithmetic operations."""

    name: str = "calculator"
    description: str = "Perform basic arithmetic operations."

    def add(self, a: Number, b: Number) -> Number:
        """Return the sum of two finite numbers."""

        self._validate_number(a, "a")
        self._validate_number(b, "b")
        return a + b

    def multiply(self, a: Number, b: Number) -> Number:
        """Return the product of two finite numbers."""

        self._validate_number(a, "a")
        self._validate_number(b, "b")
        return a * b

    @staticmethod
    def _validate_number(value: Number, parameter_name: str) -> None:
        """Validate that a value is a finite integer or floating-point number."""

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                f"{parameter_name} must be an integer or floating-point number"
            )

        if isinstance(value, float) and not isfinite(value):
            raise ValueError(f"{parameter_name} must be finite")


def get_tool_registry() -> dict[str, object]:
    """Return the legacy workspace-tool registry.

    This function can remain temporarily for compatibility with your
    existing agent.py implementation. New Copilot integrations should
    use the MCP server instead.
    """

    return {
        "calculator.add": calculator.add,
        "calculator.multiply": calculator.multiply,
    }

calculator = CalculatorSkill()
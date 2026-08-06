class CalculatorSkill:
    name = "calculator"
    description = "Performs basic arithmetic operations."
    tool_actions = {
        "add": "Add two numbers.",
        "multiply": "Multiply two numbers."
    }

    def add(self, a: float, b: float) -> float:
        """Return the sum of two numbers."""
        return a + b

    def multiply(self, a: float, b: float) -> float:
        """Return the product of two numbers."""
        return a * b


def get_tool_registry():
    """Return a registry of calculator tool callables."""
    skill = CalculatorSkill()
    return {
        f"{CalculatorSkill.name}.{action}": getattr(skill, action)
        for action in CalculatorSkill.tool_actions
    }

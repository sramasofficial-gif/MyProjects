where import pytest

from agent import SimpleCopilotAgent


def test_use_skill_add():
    agent = SimpleCopilotAgent()
    assert agent.use_skill("calculator", "add", 5, 7) == "Result: 12"


def test_use_skill_multiply():
    agent = SimpleCopilotAgent()
    assert agent.use_skill("calculator", "multiply", 3, 4) == "Result: 12"


def test_unknown_skill_returns_message():
    agent = SimpleCopilotAgent()
    assert agent.use_skill("unknown", "add", 1, 2) == "Skill 'unknown' not found."


def test_unknown_action_returns_message():
    agent = SimpleCopilotAgent()
    assert agent.use_skill("calculator", "subtract", 5, 2) == "Action 'subtract' not found in skill 'calculator'."


def test_tool_registry_contains_fully_qualified_names():
    agent = SimpleCopilotAgent()
    registry = agent.get_tool_registry()
    assert "calculator.add" in registry
    assert "calculator.multiply" in registry


def test_invoke_tool_direct_action():
    agent = SimpleCopilotAgent()
    assert agent.invoke_tool("calculator.add", a=5, b=7) == 12


def test_invoke_tool_root_action():
    agent = SimpleCopilotAgent()
    assert agent.invoke_tool("calculator", action="multiply", a=3, b=4) == 12


def test_invoke_tool_unknown_tool_raises():
    agent = SimpleCopilotAgent()
    with pytest.raises(ValueError, match="Unknown tool: unknown"):
        agent.invoke_tool("unknown", action="add", a=1, b=2)

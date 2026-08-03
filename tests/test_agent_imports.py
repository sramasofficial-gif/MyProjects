import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from FirstAgent.agent import SimpleCopilotAgent
from FirstAgent.skills.calculator import CalculatorSkill


class AgentImportTests(unittest.TestCase):
    def test_simple_agent_responds(self) -> None:
        agent = SimpleCopilotAgent("Agent")
        self.assertEqual(agent.respond("hi"), "Agent says: You said 'hi'")

    def test_skill_agent_uses_calculator(self) -> None:
        agent = SimpleCopilotAgent("Agent")
        self.assertEqual(agent.use_skill("calculator", "add", 5, 7), "Result: 12")
        self.assertEqual(agent.use_skill("calculator", "multiply", 3, 4), "Result: 12")


if __name__ == "__main__":
    unittest.main()

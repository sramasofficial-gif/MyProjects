from typing import Dict

class SimpleCopilotAgent:
    def __init__(self, name="MyCopilot"):
        self.name = name

    def respond(self, user_input: str) -> str:
        return f"{self.name} says: You said '{user_input}'"

class CalculatorSkill:
    def add(self, a: float, b: float) -> float:
        return a + b

    def multiply(self, a: float, b: float) -> float:
        return a * b


class CopilotAgentWithSkills(SimpleCopilotAgent):
    def __init__(self, name="MyCopilot"):
        super().__init__(name)
        self.skills = {"calculator": CalculatorSkill()}

    def use_skill(self, skill_name: str, action: str, *args) -> str:
        skill = self.skills.get(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found."
        method = getattr(skill, action, None)
        if not method:
            return f"Action '{action}' not found in skill '{skill_name}'."
        return f"Result: {method(*args)}"
        

if __name__ == "__main__":
    agent = CopilotAgentWithSkills()
    print(agent.use_skill("calculator", "add", 5, 7))       # Result: 12
    print(agent.use_skill("calculator", "multiply", 3, 4))  # Result: 12


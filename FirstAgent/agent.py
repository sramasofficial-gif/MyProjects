from skills.calculator import CalculatorSkill

class SimpleCopilotAgent:
    def __init__(self, name="MyCopilot"):
        self.name = name
        self.skills = {"calculator": CalculatorSkill()}

    def respond(self, user_input: str) -> str:
        return f"{self.name} says: You said '{user_input}'"

    def use_skill(self, skill_name: str, action: str, *args):
        skill = self.skills.get(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found."
        method = getattr(skill, action, None)
        if not method:
            return f"Action '{action}' not found in skill '{skill_name}'."
        return f"Result: {method(*args)}"


if __name__ == "__main__":
    agent = SimpleCopilotAgent()
    print(agent.respond("Hello Copilot!"))
    print(agent.use_skill("calculator", "add", 5, 7))
    print(agent.use_skill("calculator", "multiply", 3, 4))
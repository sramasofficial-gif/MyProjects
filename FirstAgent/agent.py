from skills.calculator import CalculatorSkill

class SimpleCopilotAgent:
    def __init__(self, name="MyCopilot"):
        self.name = name
        self.skills = {}
        self.register_skill("calculator", CalculatorSkill())

    def register_skill(self, skill_name: str, skill):
        """Register a skill implementation for future use."""
        self.skills[skill_name] = skill

    def respond(self, user_input: str) -> str:
        """Return a simple response for the given user input."""
        return f"{self.name} says: You said '{user_input}'"

    def use_skill(self, skill_name: str, action: str, *args):
        """Invoke a registered skill action with positional arguments."""
        skill = self.skills.get(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found."

        method = getattr(skill, action, None)
        if not method or not callable(method):
            return f"Action '{action}' not found in skill '{skill_name}'."

        try:
            result = method(*args)
        except TypeError as exc:
            return f"Invalid arguments for {skill_name}.{action}: {exc}"

        return f"Result: {result}"

    def get_tool_registry(self):
        """Return a mapping of tool names to callable skill actions."""
        registry = {}
        for skill_name, skill in self.skills.items():
            actions = getattr(skill, "tool_actions", {})
            for action_name in actions:
                action_callable = getattr(skill, action_name, None)
                if callable(action_callable):
                    registry[f"{skill_name}.{action_name}"] = action_callable
        return registry
    
    def invoke_tool(self, tool_name: str, **kwargs):
        """Invoke a tool by name using keyword arguments."""
        registry = self.get_tool_registry()
        if tool_name in registry:
            return registry[tool_name](**kwargs)

        tool = self.skills.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")

        action = kwargs.pop("action", None)
        if not action:
            raise ValueError("Missing required parameter: action")

        method = getattr(tool, action, None)
        if not method or not callable(method):
            raise ValueError(f"Action '{action}' not found in tool '{tool_name}'.")

        return method(**kwargs)

if __name__ == "__main__":
    agent = SimpleCopilotAgent()
    print(agent.respond("Hello Copilot!"))
    print(agent.use_skill("calculator", "add", 5, 7))
    print(agent.use_skill("calculator", "multiply", 3, 4))
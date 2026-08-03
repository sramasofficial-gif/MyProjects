from typing import Dict

class SimpleCopilotAgent:
    def __init__(self, name="MyCopilot"):
        self.name = name

    def respond(self, user_input: str) -> str:
        return f"{self.name} says: You said '{user_input}'"
        

if __name__ == "__main__":
    agent = SimpleCopilotAgent()
    print(agent.respond("Hello Copilot!"))

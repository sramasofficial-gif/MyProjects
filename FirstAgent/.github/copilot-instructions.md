# GitHub Copilot Instructions for FirstAgent

## Project Overview

This repository contains a simple Python-based agent named `SimpleCopilotAgent`.

The agent demonstrates a lightweight skill-based architecture:

- `agent.py` defines the main agent class.
- `skills/calculator.py` defines `CalculatorSkill`.
- `agent.md` documents the agent manifest, skills, usage, and metadata.
- `tests/` contains automated tests.
- `requirements.txt` lists Python dependencies.

The goal of this project is to help users learn how AI agents, skills, tool-like methods, and testable Python modules can be structured.

## Core Design Principles

When generating or modifying code in this repository, follow these principles:

1. Keep the code beginner-friendly and easy to explain.
2. Prefer simple Python classes and functions over complex frameworks.
3. Keep agent logic separate from skill implementation.
4. Do not hardcode unnecessary behavior into `respond`.
5. Skills should be registered through the agent's `self.skills` dictionary.
6. Each skill should expose small, focused methods.
7. Public methods should use type hints.
8. Add docstrings for classes and public methods.
9. Preserve compatibility with standard Python execution using `python agent.py`.
10. Avoid adding external dependencies unless they are truly required.

## Current Architecture

The current agent architecture is:

```text
SimpleCopilotAgent
├── name
├── skills
│   └── calculator
│       ├── add(a, b)
│       └── multiply(a, b)
├── respond(user_input)
└── use_skill(skill_name, action, *args)

## Coding Standards

When writing Python code:

1. Use clear class and method names.
2. Use snake_case for functions, variables, and file names.
3. Use PascalCase for class names.
4. Use f-strings for readable string formatting.
5. Use explicit error messages.
6. Validate skill names and action names before invoking methods.
7. Avoid broad exception handling unless required.
8. Keep functions small and easy to test.
9. Do not introduce global mutable state.

## Testing Standards

When adding or changing behavior:

1. Add or update tests under tests/.
2. Prefer pytest.
3. Test both successful and failure scenarios.
4. Test unknown skill handling.
5. Test unknown action handling.
6. Test each calculator method independently.
7. Maintain simple tests suitable for beginners.

## Documentation Standards

When updating functionality:

1. Update agent.md if skills, usage, or metadata changes.
2. Update README.md if setup or usage changes.
3. Include example commands where useful.
4. Keep documentation concise and practical.

## Copilot Behavior Rules

When assisting with this repository, GitHub Copilot should:

1. Explain changes before applying large refactors.
2. Prefer incremental improvements.
3. Maintain the simple learning-oriented style of the project.
4. Suggest tests whenever adding new skills.
5. Avoid converting the project into a full framework unless explicitly asked.
6. Avoid adding web APIs, databases, LangChain, CrewAI, AutoGen, or MCP unless explicitly requested.
7. If asked to add a new skill, follow the existing CalculatorSkill pattern.

### Example Usage

Expected behavior:

agent = SimpleCopilotAgent()
agent.respond("Hello Copilot!")
agent.use_skill("calculator", "add", 5, 7)
agent.use_skill("calculator", "multiply", 3, 4)

Expected output style:

MyCopilot says: You said 'Hello Copilot!'
Result: 12
Resu*t: 12

## Safe Change Guidance

Before making changes that affect behavior:

1. Inspect agent.py.
2. Inspect the affected file under skills/.
3. Check or create tests under tests/.
4. Update documentation if public behavior changes.
5. Run tests where possible.


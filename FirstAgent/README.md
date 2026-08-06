# FirstAgent

FirstAgent is a simple Python hands-on project that demonstrates a lightweight agent with skill-based actions.

## Project Structure

```text
FirstAgent/
├── agent.py
├── agent.md
├── skills/
│   └── calculator.py
├── tests/
├── requirements.txt
├── AGENTS.md
└── .github/
    ├── copilot-instructions.md
    ├── instructions/
    └── prompts/
```

## Getting Started

Install dependencies and run tests with:

```bash
pip install -r requirements.txt
python -m pytest -q tests/
```

## Copilot Chat Integration

This project exposes tool-style actions for Copilot chat.
Use `agent.invoke_tool("calculator.add", a=5, b=7)` for direct tool invocation.
For the root tool, use `agent.invoke_tool("calculator", action="add", a=5, b=7)`.

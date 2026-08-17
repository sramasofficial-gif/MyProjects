# FirstAgent

FirstAgent is a simple Python hands-on project that demonstrates a lightweight agent with skill-based actions.

## Project Structure

```text
MyProjects/
└── FirstAgent/
    ├── .github/
    │   └── ...
    ├── .vscode/
    │   └── mcp.json
    ├── skills/
    │   ├── __init__.py
    │   └── calculator.py
    ├── mcp_servers/
    │   ├── __init__.py
    │   └── calculator_server.py
    ├── tests/
    │   ├── __init__.py
    │   ├── test_calculator.py
    │   └── test_calculator_mcp.py
    ├── .venv/
    ├── agent.md
    ├── agent.py
    ├── AGENTS.md
    ├── requirements.txt
    └── README.md
```

skills/calculator.py
    Pure calculator business logic

mcp_servers/calculator_server.py
    MCP protocol adapter and tool registration

.vscode/mcp.json
    Tells VS Code how to launch the local MCP server

tests/
    Tests the logic and the MCP tools

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

# Agent Manifest: MyCopilot

## Overview
MyCopilot is a simple agent designed to demonstrate skills integration.
It can echo user input and perform basic calculations.

## Skills
- **CalculatorSkill**
  - `add(a, b)`: Adds two numbers.
  - `multiply(a, b)`: Multiplies two numbers.

## Usage
Run `python agent.py` to start the agent.
Use `agent.use_skill("calculator", "add", 5, 7)` to perform addition.
Use `agent.use_skill("calculator", "multiply", 3, 4)` to perform multiplication.

## Copilot Chat / Tool Integration
The agent also exposes tool-style invocation for Copilot chat.
It supports both:
- `calculator` with `action`, `a`, and `b` parameters
- `calculator.add` and `calculator.multiply` as fully qualified tool names

Example Python usage:
```python
agent.invoke_tool("calculator", action="add", a=5, b=7)
agent.invoke_tool("calculator.add", a=5, b=7)
agent.invoke_tool("calculator.multiply", a=3, b=4)
```

Example Copilot tool payloads:

`calculator` payload:
```json
{
  "tool": "calculator",
  "input": {
    "action": "add",
    "a": 5,
    "b": 7
  }
}
```

`calculator.add` payload:
```json
{
  "tool": "calculator.add",
  "input": {
    "a": 5,
    "b": 7
  }
}
```

`calculator.multiply` payload:
```json
{
  "tool": "calculator.multiply",
  "input": {
    "a": 3,
    "b": 4
  }
}
```

## Metadata
- Version: 0.1
- Author: Ramasubramanian
- Dependencies: See `requirements.txt`

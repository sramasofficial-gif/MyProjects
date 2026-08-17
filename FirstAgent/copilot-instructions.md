# Copilot Instructions

## Agent Overview
This agent provides calculator functionality inside VS Code.

## Directory Structure

my-copilot-agent/
├── agent.py
├── skills/
│   └── calculator.py
├── agent.md
└── requirements.txt


## Skills
- **CalculatorSkill**
  - `add(a, b)`: Adds two numbers.
  - `multiply(a, b)`: Multiplies two numbers.

## Usage
When the user types a request like "calculate add 5 7", call the `add` skill.
When the user types "calculate multiply 3 4", call the `multiply` skill.

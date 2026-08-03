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

## Metadata
- Version: 0.1
- Author: Ramasubramanian
- Dependencies: See `requirements.txt`

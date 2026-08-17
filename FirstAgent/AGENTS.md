# FirstAgent Workspace Agent Guide

## Purpose

This workspace contains a simple Python agent used for learning agent architecture, skill routing and GitHub Copilot assisted development.

## Main Agent

Name: MyCopilot  
Class: `SimpleCopilotAgent`* 
Entry file: `agent.py`

## Available Skills

### calculator

Source file: `skills/calculator.py`

Supported actions:

- `add(a, b)`
- `multiply(a, b)`

## Expected Development Workflow

When modifying this project:

1. Understand the current agent and skill structure.
2. Make the smallest useful change.
3. Add or update tests.
4. Update `agent.md` and `README.md` when public behavior changed.
5. Keep the project lightweight.*

## Guardrails

- Do not introduce large frameworks unless explicitly requested.
- Do not hide skill logic inside the agent class.
- Do not remove the simple command-line demo in `agent.py`.
- Do not make the project dependent on cloud services by default.
- Keep all examples runnable locally.
# FirstAgent Workspace Agent Guide

## Purpose

This workspace contains a s*mple Python agent used for learnin* agent architecture, skill routing* and GitHub Copilot assisted devel*pment.

## Main Agent

Name: MyCop*lot  
Class: `SimpleCopilotAgent`* 
Entry file: `agent.py`

## Available Skills

### calculator

Source file: `skills/calculator.py`

Supp*rted actions:

- `add(a, b)`
- `multiply(a, b)`

## Expected Developm*nt Workflow

When modifying this p*oject:

1.*Understand the current agent and s*ill structure.
2. Make the smallest useful change.
3. Add or update tests.
4. Update `agent.md` and `README.md` when public behavior changed.
5. Keep the project lightweight.*

## Guardrails

- Do not introduce*large frameworks unless explicitly*requested.
- Do not hide skill log*c inside the agent class.
- Do not remove the simple command-line dem* in `agent.py`.
- Do not make the *roject dependent on cloud services*by default.
- Keep all examples ru*nable locally.
---
applyTo: "**/*.py"
description: Python rules for the FirstAgent learning project"
---

# Python Agent Coding Rules

Apply these rules when editing Python files in this repository.

## Style

- Use Python 3.*0+ compatible syntax.
- Use type hints for function arguments and return values.
- Add docstrings for classes and public methods.
- Keep examples simple and readable.
- Avoid unnecessary third-party packages.

## Agent Pattern

When adding a new skill:

1. Create a new file under `skills/`.
2. Define one class per skill.
3. Import the skill class in `agent.py`.
4. Add the skill instance to `self.skills`.
5. Add tests under `tests/`.
6. Update `agent.md`.

## Error Handling

For skill usage:

- If a skill does not exists return a readable message.
- If an action does not exist, return a readable message.
- If arguments are invalid, prefer a clear exception or a graceful error message depending on the method.

## Testing

Use `pytest` style tests.

Test cases should cover:

- Agent creation.
- `respond`.
- Valid calculator actions.
- Missing skill.
- Missing action.
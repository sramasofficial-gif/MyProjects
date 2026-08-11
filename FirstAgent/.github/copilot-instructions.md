# GitHub Copilot Instructions for FirstAgent

# Project Overview

This repository contains an MCP-enabled AI Agent platform.

The solution demonstrates:

- Skill-based architecture
- MCP (Model Context Protocol) servers
- Repository analysis tools
- Amazon Connect flow analysis
- Lambda function analysis
- Terraform analysis
- AI-assisted test generation
- Extensible agent workflows

Primary technologies:

- Python
- MCP / FastMCP
- GitHub Copilot Agent Mode
- Pytest

---

# Current Architecture

```text
MyProjects/
|   
├────── .vscode/
|       └── mcp.json
|  
├────── FirstAgent/
|      │
|      ├── agent.py
|      ├── skills/
|      │
|      ├── ivr_repo/  (Amazon Connect Contact Center Platform Project Repository)
|      |   |
|      │   └── flows   (containing Amazon Connect IVR/contact flow JSON files)
|      |   |
|      │   └── lambda  (containing AWS Lambda TypeScript files)
|      |   |
|      │   └── terraform (containing Terraform script files)
|      |   |
|      │   └── prompts  (containing IVR voice prompt text files)
|      │
|      ├── mcp_servers/
|      │   └── ivr_repo_svc_mcp_server.py
|      │
|      ├── tests/
|      │
|      ├── .github/
|      │   └── copilot-instructions.md
|      │
|      └── .vscode/
|          └── settings.json  (containing custom agent enablement configurations for vs code)
```

---

# Core Design Principles

When generating or modifying code:

1. Keep solutions easy to understand.
2. Prefer modular design.
3. Separate business logic from MCP plumbing.
4. Keep tools focused on a single responsibility.
5. Use type hints.
6. Use clear docstrings.
7. Prefer pure Python implementations.
8. Keep components independently testable.
9. Design for future extension.
10. Avoid unnecessary dependencies.

---

# MCP Server Standards

All MCP tools must:

1. Have clear names.
2. Have descriptive docstrings.
3. Return structured output.
4. Validate inputs.
5. Handle errors gracefully.
6. Produce useful diagnostic information.
7. Be testable outside Copilot.

Tool descriptions must explain:

- What the tool does
- When it should be used
- Expected input
- Expected output

Example:

```python
@mcp.tool()
def analyze_lambda(file_path: str) -> str:
    """
    Analyze AWS Lambda source code and extract:

    - Business logic
    - Dependencies
    - API integrations
    - Error handling
    - Test recommendations
    """
```

---

# Repository Analysis Workflow

Whenever repository analysis is requested:

STEP 1

Use:

find_files()

to discover target files.

STEP 2

Use:

read_file()

to retrieve content.

STEP 3

Identify file type.

STEP 4

Invoke the appropriate MCP tool.

---

# MCP Tool Selection Rules

When the user asks:

"Find a file"

Use:

find_files() : with cf*.json when contact flows are requested.
find_files() : with *.ts when lambda files are requested.
find_files() : with *.tf when Terraform files are requested.

---

"Read a file"

Use:

read_file()

---

"Analyze Lambda"

Use:

analyze_lambda()

---

"Analyze Terraform"

Use:

analyze_terraform()

---

"Analyze Amazon Connect Flow"

Use:

analyze_connect_flow()

---

"Generate Test Cases"

Use:

generate_testcases()

---

"Compare HLD and Flow"

Use:

compare_hld_to_json()

---

"Generate Gap Analysis"

Use:

generate_gap_report()

---

# Mandatory MCP Usage Rules

Do not assume file contents.

Always:

1. Locate files first
2. Read files second
3. Analyze files third

Never skip these steps.

If repository data is required:

Use MCP tools whenever available.

Do not invent repository information.

---

# Coding Standards

1. Use snake_case.
2. Use PascalCase for classes.
3. Use f-strings.
4. Use descriptive identifiers.
5. Keep functions small.
6. Avoid deep nesting.
7. Avoid global mutable state.
8. Prefer composition over inheritance.
9. Keep business logic independent from MCP wrappers.

---

# Testing Standards

Whenever a new tool is added:

1. Add pytest coverage.
2. Test success cases.
3. Test failure cases.
4. Test invalid input.
5. Test edge cases.
6. Verify MCP tool registration.

Required files:

tests/
    test_<tool>.py

---

# Documentation Standards

Whenever a tool changes:

Update:

- README.md
- agent.md
- MCP usage examples

Provide example prompts.

Provide example outputs.

---

# Copilot Behavior Rules

GitHub Copilot should:

1. Prefer MCP tools over assumptions.
2. Use MCP tools to gather repository context.
3. Explain significant changes before applying them.
4. Suggest tests for all new tools.
5. Prefer incremental improvements.
6. Preserve existing architecture unless asked to refactor.
7. Reuse existing MCP patterns before creating new ones.
8. Follow the repository analysis workflow.

---

# Example Tool Workflows

Example 1

User:

Analyze all Lambda functions.

Workflow:

1. find_files()
2. read_file()
3. analyze_lambda()

---

Example 2

User:

Review Terraform deployment.

Workflow:

1. find_files()
2. read_file()
3. analyze_terraform()

---

Example 3

User:

Generate Amazon Connect test cases.

Workflow:

1. find_files()
2. read_file()
3. analyze_connect_flow()
4. generate_testcases()

---

# Safe Change Guidance

Before making repository changes:

1. Inspect affected files.
2. Inspect related MCP tools.
3. Inspect tests.
4. Update documentation.
5. Add missing tests.
6. Preserve backward compatibility where possible.

## Amazon Connect Contact Flow Audit

When the user asks to audit an Amazon Connect contact flow, calculate
complexity, count blocks or edges, identify Lambda dependencies, check
error handling, or assess flow maintainability:

1. Use `find_files` to locate matching JSON contact flow files.
2. Select the file matching the user's request.
3. Call `audit_contact_flow` with the repository-relative path.
4. Present the returned:
   - total blocks
   - total edges
   - McCabe complexity
   - decision complexity
   - Lambda integration count
   - unhandled error block count
   - audit status
   - recommendations

Do not manually calculate these metrics when `audit_contact_flow` is
available.

Use `read_file` only when detailed inspection of individual flow
actions is additionally required.
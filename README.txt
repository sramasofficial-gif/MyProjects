1. Final Target Architecture

VS Code / GitHub Copilot Agent
             |
             | MCP over stdio
             v
+--------------------------------------+
| Repository Analysis MCP Server       |
|                                      |
|  scan_repository                     |
|  analyze_flow                        |
|  review_lambda                       |
|  generate_unit_tests                 |
|  run_unit_tests                      |
|  simulate_flow                       |
|  review_terraform                    |
|  review_prompts                      |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| Application / Orchestration Layer    |
|                                      |
| Repo Scanner                         |
| Flow Analysis Client                 |
| Lambda Review Client                 |
| Unit Test Generator                  |
| Test Execution Service               |
| Flow Simulation Engine               |
| Terraform Analyzer                   |
| Prompt Reviewer                      |
+------------------+-------------------+
                   |
                   v
+--------------------------------------+
| Deterministic analyzers + LLM        |
| Existing REST services               |
| Local Qwen / optional remote model   |
| npm, Jest/Vitest, pytest             |
| Terraform CLI / static analyzers     |
+--------------------------------------+

2. Development Sequence

3. Phase 1 Only: Repository Scanner

Phase 1 objective

Create one MCP tool:
scan_repository

It will:

Accept the repository root from the caller.
Recursively inspect the repository.
Find .json, .ts, .tsx, .tf, and prompt-related files.
Skip generated, dependency, build, and version-control directories.
Prevent traversal outside the requested repository.
Return metadata only.
Not read complete file content yet.
Not call an LLM or analysis service.
Not modify anything.

This is intentionally conservative. Scanning and content analysis should remain separate operations.


Suggested folder structure

FirstAgent/
├── .vscode/
│   └── mcp.json
├── mcp_servers/
│   ├── __init__.py
│   └── repo_analysis_server.py
├── repo_analysis/
│   ├── __init__.py
│   └── scanner.py
└── tests/
    ├── __init__.py
    └── test_scanner.py
	
Better design for the IVR use case

                    MCP Server
                        │
       ┌────────────────┼─────────────────┐
       │                │                 │
       ▼                ▼                 ▼
 discover_files     read_file        call_service
       │                │                 │
 *.json search      JSON content     REST/gRPC/etc.
       │                │                 │
       └─────────────── LLM ──────────────┘
	   

For the SDLC Agent vision, we use this progression:

V1
 ├─ find_files() ✅
 └─ read_file()

V2
 ├─ analyze_lambda()
 └─ analyze_terraform() 

V3
 └─ generate_test_cases() 
 
V4
 └─ repository_summary() 

V5
 └─ multi-file dependency analysis

	
4. Repository Scanner Implementation

repo_analysis/__init__.py

"""Repository analysis application package."""


repo_analysis/scanner.py

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_EXTENSIONS = {
    ".json",
    ".ts",
    ".tsx",
    ".tf",
    ".prompt",
    ".md",
}

DEFAULT_EXCLUDED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".terraform",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "coverage",
    "dist",
    "build",
    "out",
    "target",
}

DEFAULT_EXCLUDED_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    ".terraform.lock.hcl",
}


@dataclass(frozen=True)
class RepositoryFile:
    relative_path: str
    absolute_path: str
    extension: str
    size_bytes: int
    category: str


@dataclass(frozen=True)
class ScanResult:
    repository_root: str
    files: list[RepositoryFile]
    skipped_large_files: list[str]
    skipped_unreadable_files: list[str]
    counts_by_category: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "repository_root": self.repository_root,
            "files": [asdict(file) for file in self.files],
            "skipped_large_files": self.skipped_large_files,
            "skipped_unreadable_files": self.skipped_unreadable_files,
            "counts_by_category": self.counts_by_category,
            "total_files": len(self.files),
        }


def classify_file(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()

    if suffix == ".json":
        return "json"

    if suffix in {".ts", ".tsx"}:
        return "typescript"

    if suffix == ".tf":
        return "terraform"

    if suffix == ".prompt":
        return "prompt"

    if suffix == ".md" and (
        "prompt" in name
        or path.parent.name.lower() in {"prompt", "prompts"}
    ):
        return "prompt"

    return "other"


def resolve_repository_root(repository_root: str) -> Path:
    if not repository_root or not repository_root.strip():
        raise ValueError("repository_root must not be empty")

    root = Path(repository_root).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(
            f"Repository root does not exist: {root}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository root is not a directory: {root}"
        )

    return root


def is_inside_repository(path: Path, repository_root: Path) -> bool:
    try:
        path.resolve().relative_to(repository_root)
        return True
    except ValueError:
        return False


def contains_excluded_directory(
    relative_path: Path,
    excluded_directories: set[str],
) -> bool:
    return any(
        part in excluded_directories
        for part in relative_path.parts[:-1]
    )


def normalize_extensions(
    extensions: Iterable[str] | None,
) -> set[str]:
    if extensions is None:
        return set(DEFAULT_EXTENSIONS)

    normalized: set[str] = set()

    for extension in extensions:
        value = extension.strip().lower()

        if not value:
            continue

        if not value.startswith("."):
            value = f".{value}"

        normalized.add(value)

    if not normalized:
        raise ValueError("At least one valid extension must be supplied")

    return normalized


def scan_repository(
    repository_root: str,
    extensions: Iterable[str] | None = None,
    max_file_size_bytes: int = 1_000_000,
) -> ScanResult:
    if max_file_size_bytes <= 0:
        raise ValueError("max_file_size_bytes must be greater than zero")

    root = resolve_repository_root(repository_root)
    allowed_extensions = normalize_extensions(extensions)

    files: list[RepositoryFile] = []
    skipped_large_files: list[str] = []
    skipped_unreadable_files: list[str] = []

    for candidate in root.rglob("*"):
        try:
            if not candidate.is_file():
                continue

            resolved_candidate = candidate.resolve()

            if not is_inside_repository(resolved_candidate, root):
                continue

            relative_path = resolved_candidate.relative_to(root)

            if contains_excluded_directory(
                relative_path,
                DEFAULT_EXCLUDED_DIRECTORIES,
            ):
                continue

            if candidate.name in DEFAULT_EXCLUDED_FILES:
                continue

            if candidate.suffix.lower() not in allowed_extensions:
                continue

            category = classify_file(candidate)

            if category == "other":
                continue

            file_size = candidate.stat().st_size

            if file_size > max_file_size_bytes:
                skipped_large_files.append(relative_path.as_posix())
                continue

            files.append(
                RepositoryFile(
                    relative_path=relative_path.as_posix(),
                    absolute_path=str(resolved_candidate),
                    extension=candidate.suffix.lower(),
                    size_bytes=file_size,
                    category=category,
                )
            )

        except (OSError, PermissionError):
            try:
                relative = candidate.relative_to(root).as_posix()
            except ValueError:
                relative = str(candidate)

            skipped_unreadable_files.append(relative)

    files.sort(key=lambda item: item.relative_path.lower())
    skipped_large_files.sort()
    skipped_unreadable_files.sort()

    counts_by_category: dict[str, int] = {}

    for file in files:
        counts_by_category[file.category] = (
            counts_by_category.get(file.category, 0) + 1
        )

    return ScanResult(
        repository_root=str(root),
        files=files,
        skipped_large_files=skipped_large_files,
        skipped_unreadable_files=skipped_unreadable_files,
        counts_by_category=counts_by_category,
    )
	
5. MCP Server

mcp_servers/__init__.py

"""MCP server package."""

mcp_servers/repo_analysis_server.py

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from repo_analysis.scanner import scan_repository


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("repo-analysis-mcp")

mcp = FastMCP("RepositoryAnalysis")


@mcp.tool()
def scan_repo(
    repository_root: str,
    extensions: list[str] | None = None,
    max_file_size_bytes: int = 1_000_000,
) -> dict[str, Any]:
    """
    Scan a repository and return supported source and configuration files.

    This tool does not read full file contents and does not modify files.

    Args:
        repository_root:
            Absolute path to the repository to scan.
        extensions:
            Optional extensions such as json, ts, tsx, tf, prompt, and md.
        max_file_size_bytes:
            Maximum accepted size for each discovered file.

    Returns:
        Repository file inventory grouped by analysis category.
    """
    logger.info(
        "Scanning repository root=%s extensions=%s",
        repository_root,
        extensions,
    )

    try:
        result = scan_repository(
            repository_root=repository_root,
            extensions=extensions,
            max_file_size_bytes=max_file_size_bytes,
        )

        response = {
            "status": "success",
            **result.to_dict(),
        }

        logger.info(
            "Repository scan completed root=%s total_files=%s",
            result.repository_root,
            len(result.files),
        )

        return response

    except (
        ValueError,
        FileNotFoundError,
        NotADirectoryError,
        PermissionError,
    ) as exc:
        logger.warning("Repository scan rejected: %s", exc)

        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }

    except Exception as exc:
        logger.exception("Unexpected repository scan failure")

        return {
            "status": "error",
            "error_type": "InternalServerError",
            "message": str(exc),
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
	

6. Unit Tests for the Scanner
tests/test_scanner.py


import json
from pathlib import Path

import pytest

from repo_analysis.scanner import scan_repository


def create_file(
    root: Path,
    relative_path: str,
    content: str = "",
) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_scans_supported_repository_files(tmp_path: Path) -> None:
    create_file(
        tmp_path,
        "flows/main-flow.json",
        json.dumps({"Version": "2019-10-30"}),
    )
    create_file(
        tmp_path,
        "lambdas/customer.ts",
        "export const handler = async () => {};",
    )
    create_file(
        tmp_path,
        "terraform/main.tf",
        'resource "aws_lambda_function" "customer" {}',
    )
    create_file(
        tmp_path,
        "prompts/reviewer.prompt",
        "Review this source code.",
    )
    create_file(
        tmp_path,
        "README.md",
        "# Repository",
    )

    result = scan_repository(str(tmp_path))

    paths = {file.relative_path for file in result.files}

    assert "flows/main-flow.json" in paths
    assert "lambdas/customer.ts" in paths
    assert "terraform/main.tf" in paths
    assert "prompts/reviewer.prompt" in paths
    assert "README.md" not in paths

    assert result.counts_by_category == {
        "json": 1,
        "prompt": 1,
        "terraform": 1,
        "typescript": 1,
    }


def test_skips_node_modules_and_git(tmp_path: Path) -> None:
    create_file(
        tmp_path,
        "node_modules/library/index.ts",
        "export {};",
    )
    create_file(
        tmp_path,
        ".git/config.json",
        "{}",
    )
    create_file(
        tmp_path,
        "src/handler.ts",
        "export const handler = async () => {};",
    )

    result = scan_repository(str(tmp_path))

    paths = {file.relative_path for file in result.files}

    assert paths == {"src/handler.ts"}


def test_skips_large_files(tmp_path: Path) -> None:
    create_file(
        tmp_path,
        "flows/large.json",
        "x" * 101,
    )

    result = scan_repository(
        str(tmp_path),
        max_file_size_bytes=100,
    )

    assert result.files == []
    assert result.skipped_large_files == ["flows/large.json"]


def test_rejects_missing_repository() -> None:
    with pytest.raises(FileNotFoundError):
        scan_repository("repository-that-does-not-exist")


def test_accepts_extensions_without_dot(tmp_path: Path) -> None:
    create_file(tmp_path, "src/handler.ts", "export {};")
    create_file(tmp_path, "flows/main.json", "{}")

    result = scan_repository(
        str(tmp_path),
        extensions=["ts"],
    )

    assert [file.relative_path for file in result.files] == [
        "src/handler.ts"
    ]
	
	
Run the scanner tests from the FirstAgent directory:

python -m pytest tests\test_scanner.py -v


Expected outcome:

	5 passed

7. Update .vscode/mcp.json

Since your working environment is Windows and you already have a project virtual environment, use the same Python executable pattern.

{
  "servers": {
    "repoAnalysisMcp": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "${workspaceFolder}/mcp_servers/repo_analysis_server.py"
      ],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "PYTHONUNBUFFERED": "1"
      },
      "dev": {
        "watch": "mcp_servers/**/*.py"
      }
    }
  }
}

If FirstAgent is only one folder inside a multi-root workspace, retain the named workspace form you used earlier:

{
  "servers": {
    "repoAnalysisMcp": {
      "type": "stdio",
      "command": "${workspaceFolder:MyProjects}/FirstAgent/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "${workspaceFolder:MyProjects}/FirstAgent/mcp_servers/repo_analysis_server.py"
      ],
      "cwd": "${workspaceFolder:MyProjects}/FirstAgent",
      "env": {
        "PYTHONPATH": "${workspaceFolder:MyProjects}/FirstAgent",
        "PYTHONUNBUFFERED": "1"
      },
      "dev": {
        "watch": "mcp_servers/**/*.py"
      }
    }
  }
}


The official configuration reference documents type, command, args, cwd, env, and development watch settings for stdio servers.


8. Verify in VS Code

Open .vscode/mcp.json.
Select Start above repoAnalysisMcp.
Open Copilot Chat.
Select Agent mode.
Select Configure Tools.
Verify the scan_repo tool appears under repoAnalysisMcp.
Invoke:

Using repoAnalysisMcp, scan this repository:

C:\Users\ramasubramanians\OneDrive - HCL TECHNOLOGIES LIMITED\Documents\HS\Training\MyProjects\FirstAgent

Include json, ts, tsx, tf, prompt, and md files.
Do not analyze or modify any file.
Return the files grouped by category.


Visual Studio Code documentation confirms that MCP servers configured in the workspace become available as tools in Agent mode and may require tool invocation approval. Microsoft’s MCP verification guidance similarly uses .vscode/mcp.json, starts the configured server, selects Agent mode, and verifies the server under Configure tools.






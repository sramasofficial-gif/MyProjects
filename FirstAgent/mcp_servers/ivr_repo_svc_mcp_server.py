"""MCP server exposing IVR Repo services operations.

The server communicates with VS Code over standard input/output.
Do not print normal application messages to stdout because stdout is
reserved for MCP protocol messages.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
#from mcp.server.fastmcp import FastMCP
from mcp.server import MCPServer

#mcp = FastMCP("ivr_repo_svc")
mcp = MCPServer("ivr_repo_svc")
# Allow execution as a script while still resolving the workspace package.
# PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROJECT_ROOT = (
    Path(__file__).parent.parent
    / "ivr_repo"
).resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("repoProcessor")

logging.basicConfig(
    level=logging.INFO, stream=sys.stderr
)

@mcp.tool()
def find_files(extension: str = ".json") -> list[str]:
    """
    Find files within repository.
    """

    if not extension.startswith("."):
        extension = "." + extension

    print("FIND_FILES CALLED", file=sys.stderr)
    logger.info(
        "find_files called with extension=%s",
        extension
    )

    #return [
    #    str(f.relative_to(PROJECT_ROOT))
    #    for f in PROJECT_ROOT.rglob(f"*{extension}")
    #    if f.is_file()
    #]
    return {
        "project_root": str(PROJECT_ROOT),
        "extension": extension,
        "files_found": [
            str(path.relative_to(PROJECT_ROOT))
            for path in PROJECT_ROOT.rglob(f"*{extension}")
            if path.is_file()
        ]
    } 


@mcp.tool()
def read_file(relative_path: str) -> str:
    """
    Read repository file.
    """

    path = (PROJECT_ROOT / relative_path).resolve()

    try:
        path.relative_to(PROJECT_ROOT)
    except ValueError:
        raise ValueError("Outside repository")

    return path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


@mcp.tool()
def analyze_lambda(relative_path: str):
    """
    Analyze lambda source file.
    """

    content = read_file(relative_path)

    imports = []

    for line in content.splitlines():

        if line.startswith("import "):
            imports.append(line.strip())

        elif line.startswith("from "):
            imports.append(line.strip())

    return {
        "file": relative_path,
        "lines": len(content.splitlines()),
        "contains_handler":
            "lambda_handler" in content,
        "imports": imports
    }


if __name__ == "__main__":
    mcp.run()
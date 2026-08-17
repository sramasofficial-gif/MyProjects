from mcp.server import MCPServer

from services.repo_tools import (
    find_files,
    read_file
)

from services.flow_audit import (
    audit_contact_flow_file
)

mcp = MCPServer("ivr_repository_agent")

@mcp.tool()
def find_files_tool(extension=".json"):
    return find_files(extension)


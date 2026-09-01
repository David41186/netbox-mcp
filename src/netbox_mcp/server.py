"""Entrypoint for the NetBox MCP server."""

from __future__ import annotations

from mcp.server import MCPServer

from .tools import register_tools

mcp = MCPServer(
    "netbox",
    instructions=(
        "Tools for reading and writing data in a NetBox instance. Start with "
        "netbox_list_endpoints to see what object types are available, and "
        "netbox_get_schema before creating or updating an object."
    ),
)
register_tools(mcp)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

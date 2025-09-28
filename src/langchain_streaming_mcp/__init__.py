"""MySQL MCP Server - A MySQL MCP server with Streamable HTTP using the official Anthropic MCP package."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .mcp_server import MySQLMCPServer
from .mysql_tool import MySQLConnectionConfig, MySQLSchemaTool, MySQLTool

__all__ = [
    "MySQLMCPServer",
    "MySQLTool",
    "MySQLSchemaTool",
    "MySQLConnectionConfig",
]

"""MCP Server integration using the official Anthropic MCP package with Streamable HTTP."""

import asyncio
from collections.abc import Sequence
import logging
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from .mysql_tool import MySQLConnectionConfig, MySQLSchemaTool, MySQLTool

logger = logging.getLogger(__name__)


class MySQLMCPServer:
    """MCP Server that wraps MySQL functionality using Streamable HTTP."""

    def __init__(self, mysql_config: MySQLConnectionConfig | None = None):
        """Initialize the MySQL MCP server.

        Args:
            mysql_config: MySQL connection configuration. Uses environment defaults if None.
        """
        self.mysql_config = mysql_config or MySQLConnectionConfig.from_environment()
        self.mysql_tool = MySQLTool(self.mysql_config)
        self.schema_tool = MySQLSchemaTool(self.mysql_config)

        # Create MCP server with Streamable HTTP
        self.server = Server("mysql-mcp-server")
        self._setup_handlers()
        # Create session manager after handlers are set up
        self.session_manager = StreamableHTTPSessionManager(self.server)

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available MySQL tools."""
            return [
                types.Tool(
                    name="mysql_query",
                    description="Execute MySQL queries safely with automatic result formatting",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to execute",
                            },
                            "database": {
                                "type": "string",
                                "description": "Database name (optional)",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of rows to return (default: 100)",
                                "default": 100,
                            },
                            "fetch_metadata": {
                                "type": "boolean",
                                "description": "Include column metadata in results (default: true)",
                                "default": True,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                types.Tool(
                    name="mysql_schema",
                    description="Inspect MySQL database schema, list databases, tables, and columns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "Database name to inspect (optional)",
                            },
                            "table": {
                                "type": "string",
                                "description": "Specific table name to inspect (optional)",
                            },
                            "include_data_types": {
                                "type": "boolean",
                                "description": "Include column data types (default: true)",
                                "default": True,
                            },
                        },
                        "required": [],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> Sequence[types.TextContent]:
            """Handle tool execution requests."""
            if arguments is None:
                arguments = {}

            try:
                if name == "mysql_query":
                    query = arguments.get("query", "")
                    database = arguments.get("database")
                    limit = arguments.get("limit", 100)
                    fetch_metadata = arguments.get("fetch_metadata", True)

                    result = await self.mysql_tool._arun(
                        query=query,
                        database=database,
                        limit=limit,
                        fetch_metadata=fetch_metadata,
                    )

                    return [types.TextContent(type="text", text=result)]

                elif name == "mysql_schema":
                    database = arguments.get("database")
                    table = arguments.get("table")
                    include_data_types = arguments.get("include_data_types", True)

                    result = await self.schema_tool._arun(
                        database=database,
                        table=table,
                        include_data_types=include_data_types,
                    )

                    return [types.TextContent(type="text", text=result)]

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text", text=f"Error executing {name}: {str(e)}"
                    )
                ]

    async def run_http(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        """Run the MCP server using Streamable HTTP transport.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        import contextlib

        from starlette.applications import Starlette
        from starlette.responses import Response
        import uvicorn

        @contextlib.asynccontextmanager
        async def lifespan(app):
            async with self.session_manager.run():
                yield

        # Create ASGI app with proper session manager integration
        app = Starlette(lifespan=lifespan)

        @app.route("/", methods=["GET", "POST", "OPTIONS"])
        async def handle_request(request):
            scope = request.scope
            receive = request.receive
            send = request._send
            await self.session_manager.handle_request(scope, receive, send)
            return Response()

        # Use uvicorn to run the ASGI app
        config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def close(self) -> None:
        """Clean up resources."""
        await self.mysql_tool.close()
        await self.schema_tool.close()


async def main() -> None:
    """Main entry point for the MCP server."""
    logging.basicConfig(level=logging.INFO)

    # Create and run the MySQL MCP server with Streamable HTTP
    mcp_server = MySQLMCPServer()

    try:
        logger.info(
            "🚀 Starting MySQL MCP Server with Streamable HTTP on http://0.0.0.0:8000"
        )
        await mcp_server.run_http(host="0.0.0.0", port=8000)
    finally:
        await mcp_server.close()


def run() -> None:
    """Entry point for the script command."""
    asyncio.run(main())


if __name__ == "__main__":
    run()

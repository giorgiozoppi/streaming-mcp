"""MySQL query execution tool for the MCP server."""

import asyncio
import logging
from typing import Any

import aiomysql
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class MySQLConnectionConfig(BaseModel):
    """MySQL connection configuration."""

    host: str = Field(default="localhost", description="MySQL host")
    port: int = Field(default=3306, description="MySQL port")
    user: str = Field(default="mcp-user", description="MySQL username")
    password: str = Field(default="mcp-password", description="MySQL password")
    database: str = Field(default="", description="MySQL database name")
    charset: str = Field(default="utf8mb4", description="Character set")
    autocommit: bool = Field(default=True, description="Auto-commit transactions")
    timeout: float = Field(default=30.0, description="Connection timeout in seconds")

    @classmethod
    def from_environment(cls) -> "MySQLConnectionConfig":
        """Create configuration from environment variables.

        Returns:
            MySQLConnectionConfig with values from environment variables.
        """
        import os

        return cls(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "mcp-user"),
            password=os.getenv("MYSQL_PASSWORD", "mcp-password"),
            database=os.getenv("MYSQL_DATABASE", ""),
            charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
            autocommit=os.getenv("MYSQL_AUTOCOMMIT", "true").lower() == "true",
            timeout=float(os.getenv("MYSQL_TIMEOUT", "30.0")),
        )


class MySQLQueryInput(BaseModel):
    """Input schema for MySQL query tool."""

    query: str = Field(..., description="SQL query to execute")
    database: str | None = Field(
        default=None, description="Database name (optional)"
    )
    limit: int = Field(
        default=100, description="Maximum number of rows to return (for SELECT queries)"
    )
    fetch_metadata: bool = Field(
        default=True, description="Include column metadata in results"
    )

    @validator("query")
    def validate_query(cls, v: str) -> str:
        """Validate SQL query for basic safety."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")

        # Basic safety checks
        query_lower = v.lower().strip()

        # Block dangerous operations
        dangerous_patterns = [
            "drop database",
            "drop schema",
            "drop table",
            "truncate table",
            "delete from",
            "format c:",
            "rm -rf",
            "shutdown",
            "system",
            "exec(",
            "xp_cmdshell",
        ]

        for pattern in dangerous_patterns:
            if pattern in query_lower:
                raise ValueError(
                    f"Query contains potentially dangerous pattern: {pattern}"
                )

        return v


class MySQLTool(BaseTool):
    """Tool for executing MySQL queries safely."""

    name: str = "mysql_query"
    description: str = "Execute MySQL queries on localhost with mcp-user. Supports SELECT, INSERT, UPDATE queries with safety restrictions."
    args_schema: type[BaseModel] = MySQLQueryInput

    def __init__(self, config: MySQLConnectionConfig | None = None, **kwargs):
        """Initialize MySQL tool with configuration.

        Args:
            config: MySQL connection configuration. Uses defaults if None.
            **kwargs: Additional arguments for BaseTool.
        """
        super().__init__(**kwargs)
        self._config = config or MySQLConnectionConfig()
        self._connection_pool: aiomysql.Pool | None = None

    @property
    def config(self) -> MySQLConnectionConfig:
        """Get the MySQL configuration."""
        return self._config

    async def _get_connection_pool(self) -> aiomysql.Pool:
        """Get or create connection pool.

        Returns:
            MySQL connection pool.

        Raises:
            Exception: If connection fails.
        """
        if not self._connection_pool:
            try:
                self._connection_pool = await aiomysql.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.user,
                    password=self.config.password,
                    db=self.config.database,
                    charset=self.config.charset,
                    autocommit=self.config.autocommit,
                    # timeout is not a valid parameter for create_pool
                    minsize=1,
                    maxsize=5,
                )
                logger.info(
                    f"Created MySQL connection pool to {self.config.host}:{self.config.port}"
                )
            except Exception as e:
                logger.error(f"Failed to create MySQL connection pool: {e}")
                raise

        return self._connection_pool

    async def _close_connection_pool(self) -> None:
        """Close the connection pool."""
        if self._connection_pool:
            self._connection_pool.close()
            await self._connection_pool.wait_closed()
            self._connection_pool = None
            logger.info("Closed MySQL connection pool")

    async def _execute_query(
        self,
        query: str,
        database: str | None = None,
        limit: int = 100,
        fetch_metadata: bool = True,
    ) -> dict[str, Any]:
        """Execute SQL query and return results.

        Args:
            query: SQL query to execute.
            database: Optional database to use.
            limit: Maximum rows to return.
            fetch_metadata: Whether to include column metadata.

        Returns:
            Dictionary containing query results.
        """
        pool = await self._get_connection_pool()

        async with pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    # Switch database if specified
                    if database:
                        await cursor.execute(f"USE {database}")

                    # Execute the query
                    await cursor.execute(query)

                    # Determine query type
                    query_type = query.strip().upper().split()[0]

                    result = {
                        "query": query,
                        "query_type": query_type,
                        "success": True,
                        "timestamp": asyncio.get_event_loop().time(),
                    }

                    if query_type == "SELECT":
                        # Fetch results for SELECT queries
                        rows = await cursor.fetchmany(limit)

                        result.update(
                            {
                                "rows": [list(row) for row in rows] if rows else [],
                                "row_count": len(rows) if rows else 0,
                                "limited": len(rows) == limit if rows else False,
                            }
                        )

                        # Add column metadata if requested
                        if fetch_metadata and cursor.description:
                            result["columns"] = [
                                {
                                    "name": desc[0],
                                    "type": desc[1].__name__ if desc[1] else "unknown",
                                    "display_size": desc[2],
                                    "internal_size": desc[3],
                                    "precision": desc[4],
                                    "scale": desc[5],
                                    "null_ok": desc[6],
                                }
                                for desc in cursor.description
                            ]

                    elif query_type in ("INSERT", "UPDATE", "DELETE"):
                        # For modification queries, return affected rows
                        result.update(
                            {
                                "affected_rows": cursor.rowcount,
                                "last_insert_id": cursor.lastrowid
                                if hasattr(cursor, "lastrowid")
                                else None,
                            }
                        )

                    elif query_type in ("CREATE", "ALTER", "DROP"):
                        # For DDL queries
                        result.update(
                            {
                                "ddl_executed": True,
                                "message": "DDL statement executed successfully",
                            }
                        )

                    else:
                        # For other queries (SHOW, DESCRIBE, etc.)
                        rows = await cursor.fetchall()
                        result.update(
                            {
                                "rows": [list(row) for row in rows] if rows else [],
                                "row_count": len(rows) if rows else 0,
                            }
                        )

                        if fetch_metadata and cursor.description:
                            result["columns"] = [desc[0] for desc in cursor.description]

                    return result

                except Exception as e:
                    logger.error(f"MySQL query error: {e}")
                    return {
                        "query": query,
                        "success": False,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "timestamp": asyncio.get_event_loop().time(),
                    }

    def _format_result(self, result: dict[str, Any]) -> str:
        """Format query result for display.

        Args:
            result: Query result dictionary.

        Returns:
            Formatted result string.
        """
        if not result.get("success"):
            return f"❌ MySQL Error: {result.get('error', 'Unknown error')}\nQuery: {result.get('query', 'N/A')}"

        query_type = result.get("query_type", "UNKNOWN")
        formatted = f"✅ MySQL {query_type} Query Executed Successfully\n"
        formatted += f"Query: {result.get('query', 'N/A')}\n"

        if query_type == "SELECT":
            row_count = result.get("row_count", 0)
            limited = result.get("limited", False)

            formatted += f"Rows returned: {row_count}"
            if limited:
                formatted += " (limited)"
            formatted += "\n"

            # Add column information
            columns = result.get("columns", [])
            if columns:
                col_names = [
                    col["name"] if isinstance(col, dict) else str(col)
                    for col in columns
                ]
                formatted += f"Columns: {', '.join(col_names)}\n"

            # Add sample rows
            rows = result.get("rows", [])
            if rows:
                formatted += "\nData:\n"
                for i, row in enumerate(rows[:5]):  # Show first 5 rows
                    formatted += f"  Row {i + 1}: {row}\n"

                if len(rows) > 5:
                    formatted += f"  ... and {len(rows) - 5} more rows\n"

        elif query_type in ("INSERT", "UPDATE", "DELETE"):
            affected_rows = result.get("affected_rows", 0)
            formatted += f"Affected rows: {affected_rows}\n"

            last_id = result.get("last_insert_id")
            if last_id:
                formatted += f"Last insert ID: {last_id}\n"

        elif result.get("ddl_executed"):
            formatted += result.get("message", "DDL executed successfully") + "\n"

        else:
            # Other query types
            rows = result.get("rows", [])
            formatted += f"Rows returned: {len(rows)}\n"

            if rows:
                formatted += "Results:\n"
                for i, row in enumerate(rows[:10]):  # Show first 10 rows
                    formatted += f"  {i + 1}. {row}\n"

        return formatted

    async def _arun(
        self,
        query: str,
        database: str | None = None,
        limit: int = 100,
        fetch_metadata: bool = True,
    ) -> str:
        """Asynchronously execute MySQL query."""
        try:
            result = await self._execute_query(query, database, limit, fetch_metadata)
            return self._format_result(result)

        except Exception as e:
            logger.error(f"MySQL tool error: {e}")
            return f"❌ MySQL Tool Error: {str(e)}\nQuery: {query}"

    async def astream_events(
        self,
        input: str,
        config: str | None = None,
        version: str | None = None,
        include_names: bool = True,
        include_types: bool = True,
        include_tags: bool = True,
        exclude_names: list[str] | None = None,
        exclude_types: list[str] | None = None,
        limit: int = 100,
        fetch_metadata: bool = True,
    ):
        """Async generator that streams MySQL query events/results."""
        # Map parameters to expected query/database
        query = input
        database = config

        try:
            result = await self._execute_query(query, database, limit, fetch_metadata)
            # Stream metadata first
            yield {
                "event": "metadata",
                "query": result.get("query"),
                "query_type": result.get("query_type"),
                "columns": result.get("columns", []),
                "success": result.get("success", False),
                "error": result.get("error", None),
            }
            # Stream rows one by one if SELECT
            if result.get("success") and result.get("query_type") == "SELECT":
                for i, row in enumerate(result.get("rows", [])):
                    yield {"event": "row", "index": i, "row": row}
            # Stream summary at the end
            yield {
                "event": "summary",
                "row_count": result.get("row_count", 0),
                "limited": result.get("limited", False),
                "affected_rows": result.get("affected_rows", None),
                "last_insert_id": result.get("last_insert_id", None),
                "ddl_executed": result.get("ddl_executed", False),
                "message": result.get("message", None),
            }
        except Exception as e:
            yield {"event": "error", "error": str(e), "error_type": type(e).__name__}

    def _run(
        self,
        query: str,
        database: str | None = None,
        limit: int = 100,
        fetch_metadata: bool = True,
    ) -> str:
        """Synchronously execute MySQL query."""
        return asyncio.run(self._arun(query, database, limit, fetch_metadata))

    async def close(self) -> None:
        """Close the MySQL tool and cleanup connections."""
        await self._close_connection_pool()


class MySQLSchemaInput(BaseModel):
    """Input schema for MySQL schema inspection tool."""

    database: str | None = Field(
        default=None, description="Database name to inspect"
    )
    table: str | None = Field(
        default=None, description="Specific table name to inspect"
    )
    include_data_types: bool = Field(
        default=True, description="Include column data types"
    )


class MySQLSchemaTool(BaseTool):
    """Tool for inspecting MySQL database schema."""

    name: str = "mysql_schema"
    description: str = (
        "Inspect MySQL database schema, list databases, tables, and columns"
    )
    args_schema: type[BaseModel] = MySQLSchemaInput

    def __init__(self, config: MySQLConnectionConfig | None = None, **kwargs):
        """Initialize MySQL schema tool.

        Args:
            config: MySQL connection configuration.
            **kwargs: Additional arguments for BaseTool.
        """
        super().__init__(**kwargs)
        self._mysql_tool = MySQLTool(config)

    @property
    def mysql_tool(self) -> MySQLTool:
        """Get the MySQL tool."""
        return self._mysql_tool

    async def _arun(
        self,
        database: str | None = None,
        table: str | None = None,
        include_data_types: bool = True,
    ) -> str:
        """Asynchronously inspect MySQL schema."""
        try:
            if not database and not table:
                # List all databases
                result = await self.mysql_tool._execute_query("SHOW DATABASES")
                if result.get("success"):
                    databases = [row[0] for row in result.get("rows", [])]
                    return "📚 Available Databases:\n" + "\n".join(
                        f"  • {db}" for db in databases
                    )
                else:
                    return f"❌ Error listing databases: {result.get('error')}"

            elif database and not table:
                # List tables in database
                query = f"SHOW TABLES FROM {database}"
                result = await self.mysql_tool._execute_query(query)
                if result.get("success"):
                    tables = [row[0] for row in result.get("rows", [])]
                    return f"📋 Tables in database '{database}':\n" + "\n".join(
                        f"  • {table}" for table in tables
                    )
                else:
                    return f"❌ Error listing tables: {result.get('error')}"

            else:
                # Describe specific table
                db_prefix = f"{database}." if database else ""
                query = f"DESCRIBE {db_prefix}{table}"
                result = await self.mysql_tool._execute_query(query, database)

                if result.get("success"):
                    rows = result.get("rows", [])
                    if rows:
                        schema_info = f"🔍 Schema for table '{table}':\n"
                        for row in rows:
                            field, type_, null, key, default, extra = row
                            schema_info += f"  • {field}: {type_}"
                            if key:
                                schema_info += f" ({key})"
                            if null == "NO":
                                schema_info += " NOT NULL"
                            if default is not None:
                                schema_info += f" DEFAULT {default}"
                            if extra:
                                schema_info += f" {extra}"
                            schema_info += "\n"
                        return schema_info
                    else:
                        return f"📋 Table '{table}' has no columns or doesn't exist"
                else:
                    return f"❌ Error describing table: {result.get('error')}"

        except Exception as e:
            return f"❌ MySQL Schema Tool Error: {str(e)}"

    def _run(
        self,
        database: str | None = None,
        table: str | None = None,
        include_data_types: bool = True,
    ) -> str:
        """Synchronously inspect MySQL schema."""
        return asyncio.run(self._arun(database, table, include_data_types))

    async def close(self) -> None:
        """Close the schema tool."""
        await self.mysql_tool.close()


def create_mysql_tools(
    config: MySQLConnectionConfig | None = None,
) -> list[BaseTool]:
    """Create MySQL tools with the given configuration.

    Args:
        config: MySQL connection configuration. Uses defaults if None.

    Returns:
        List of MySQL tools.
    """
    return [MySQLTool(config), MySQLSchemaTool(config)]

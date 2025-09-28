# MySQL MCP Server

A pure MySQL MCP (Model Context Protocol) server using the official Anthropic MCP package with Streamable HTTP transport.

## 🚀 Features

- **Official MCP Package**: Built with the official Anthropic MCP package
- **Streamable HTTP**: Uses MCP Streamable HTTP transport for efficient communication
- **MySQL Integration**: Direct MySQL database access and schema inspection
- **Minimal Dependencies**: Lightweight with only essential dependencies
- **Type Safety**: Full type hints with Pydantic models
- **Production Ready**: Docker support, health checks, and proper error handling
- **Security**: Safe query execution with validation and restrictions

## 📦 Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd streaming-mcp

# Install dependencies
pip install -e .
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up mysql-mcp-server
```

## 🛠️ Usage

### Starting the Server

```bash
# Using the CLI command
mysql-mcp-server

# Using Python module directly
python -m langchain_streaming_mcp.mcp_server
```

The server will start on `http://0.0.0.0:8000` by default.

### Environment Variables

```bash
# MySQL connection settings
MYSQL_HOST=localhost          # MySQL host (default: localhost)
MYSQL_PORT=3306              # MySQL port (default: 3306)
MYSQL_USER=mcp-user          # MySQL username (default: mcp-user)
MYSQL_PASSWORD=mcp-password   # MySQL password (default: mcp-password)
MYSQL_DATABASE=mcp_demo      # MySQL database (default: empty)
```

## 🔧 Available Tools

### mysql_query

Execute MySQL queries safely with automatic result formatting.

**Parameters:**
- `query` (required): SQL query to execute
- `database` (optional): Database name to use
- `limit` (optional): Maximum rows to return (default: 100)
- `fetch_metadata` (optional): Include column metadata (default: true)

**Safety Features:**
- Blocks dangerous operations (DROP, DELETE, etc.)
- Query validation and sanitization
- Result limiting to prevent memory issues

### mysql_schema

Inspect MySQL database schema, list databases, tables, and columns.

**Parameters:**
- `database` (optional): Database name to inspect
- `table` (optional): Specific table to describe
- `include_data_types` (optional): Include data types (default: true)

**Capabilities:**
- List all databases
- List tables in a database
- Describe table structure with data types

## 🐳 Docker Setup

### Quick Start

```bash
# Start MySQL and MCP server
docker-compose up

# Start with Adminer for database management
docker-compose --profile admin up

# Development mode with hot reload
docker-compose --profile dev up mysql-mcp-server-dev

# Run basic connectivity test
docker-compose --profile test up mcp-client
```

### Services

- **mysql**: MySQL 8.0 database with pre-configured mcp-user
- **mysql-mcp-server**: Production MCP server
- **mysql-mcp-server-dev**: Development server with hot reload
- **adminer**: Web-based MySQL management (profile: admin)
- **mcp-client**: Basic connectivity test (profile: test)

### Ports

- `3306`: MySQL database
- `8000`: MCP server (production)
- `8001`: MCP server (development)
- `8080`: Adminer web interface

## 🔒 Security

### Query Safety

The server implements several security measures:

- **Query Validation**: Blocks dangerous SQL patterns
- **Result Limiting**: Prevents large result sets
- **Connection Pooling**: Managed database connections
- **Read-Only Focus**: Designed primarily for safe read operations

### Blocked Operations

- `DROP DATABASE/TABLE`
- `TRUNCATE TABLE`
- `DELETE FROM` (without WHERE clause)
- System commands and stored procedures

## 📝 MCP Protocol

This server implements the official MCP protocol with Streamable HTTP transport:

- **Protocol Version**: Compatible with MCP 1.0+
- **Transport**: Streamable HTTP for efficient communication
- **Tools**: Exposes MySQL functionality as MCP tools
- **Streaming**: Supports real-time communication

## 🏗️ Architecture

```
mysql-mcp-server/
├── MySQLMCPServer          # Main MCP server class
├── MySQLTool              # Query execution tool
├── MySQLSchemaTool        # Schema inspection tool
└── MySQLConnectionConfig  # Database configuration
```

### Key Components

- **StreamableHTTPSessionManager**: Handles MCP protocol communication
- **MySQL Tools**: Safe database interaction tools
- **Connection Pooling**: Efficient database connection management
- **Configuration**: Environment-based configuration

## 🚀 Development

### Setup Development Environment

```bash
# Clone and install
git clone <repository-url>
cd streaming-mcp
pip install -e .

# Run in development mode
python -m langchain_streaming_mcp.mcp_server
```

### Running Tests

```bash
# Start test environment
docker-compose --profile test up

# Test server connectivity
curl http://localhost:8000/
```

### Code Style

- **Type Safety**: Full type hints with MyPy
- **Code Quality**: Ruff linting
- **Minimal Dependencies**: Only essential packages

## 📋 Database Setup

The included `mysql_setup.sql` creates:

- Sample database `mcp_demo`
- Example tables with test data
- Proper user permissions for mcp-user

### Manual Setup

```sql
-- Create database
CREATE DATABASE mcp_demo;

-- Create user
CREATE USER 'mcp-user'@'%' IDENTIFIED BY 'mcp-password';
GRANT SELECT, INSERT, UPDATE ON mcp_demo.* TO 'mcp-user'@'%';

-- Create sample table
USE mcp_demo;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuration

### MySQL Connection

Configure via environment variables or use defaults:

```python
from langchain_streaming_mcp import MySQLConnectionConfig

# From environment
config = MySQLConnectionConfig.from_environment()

# Custom configuration
config = MySQLConnectionConfig(
    host="localhost",
    port=3306,
    user="mcp-user",
    password="mcp-password",
    database="mcp_demo"
)
```

## 📊 Monitoring

### Health Checks

- **HTTP**: `GET /` returns server status
- **Docker**: Built-in health check via curl
- **Connection**: Validates MySQL connectivity

### Logging

- **Structured Logging**: JSON format for production
- **Debug Mode**: Detailed query logging in development
- **Error Handling**: Comprehensive error reporting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## 🆘 Support

- Create an issue for bug reports
- Check Docker logs: `docker-compose logs mysql-mcp-server`
- Verify MySQL connectivity: `docker-compose logs mysql`
- Test with Adminer: `docker-compose --profile admin up`


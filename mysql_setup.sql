-- MySQL setup script for Langchain Streaming MCP
-- This script runs automatically in Docker during container initialization

-- Note: In Docker, the main mcp-user is created by environment variables
-- This script provides additional setup and sample data

-- Grant additional permissions to the mcp-user for both localhost and container access
GRANT CREATE, ALTER, DROP ON *.* TO 'mcp-user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO 'mcp-user'@'%';
GRANT SHOW DATABASES ON *.* TO 'mcp-user'@'%';
GRANT SELECT ON information_schema.* TO 'mcp-user'@'%';

-- Also grant for localhost (in case of local access)
GRANT CREATE, ALTER, DROP ON *.* TO 'mcp-user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO 'mcp-user'@'localhost';
GRANT SHOW DATABASES ON *.* TO 'mcp-user'@'localhost';
GRANT SELECT ON information_schema.* TO 'mcp-user'@'localhost';

-- Grant full access to the demo database (created by environment variables)
GRANT ALL PRIVILEGES ON mcp_demo.* TO 'mcp-user'@'%';
GRANT ALL PRIVILEGES ON mcp_demo.* TO 'mcp-user'@'localhost';

-- Apply the changes
FLUSH PRIVILEGES;

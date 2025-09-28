FROM python:3.11-slim

# Set environment variables
#ENV PYTHONUNBUFFERED=1
#ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
	bash 

# Copy requirements and install Python dependencies
COPY pyproject.toml README.md ./
COPY src/ ./ 

# Install the package
RUN pip install --no-cache-dir -e .
ENV PYTHONPATH=/app
# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the MySQL MCP server
CMD ["mysql-mcp-server"]

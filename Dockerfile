# Use official Playwright Python image with all dependencies pre-installed
# Using Noble (Ubuntu 24.04 LTS) for latest security updates
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server code
COPY server.py .

# Expose MCP server port
EXPOSE 8000

# Run the MCP server with recommended Docker flags
# --init flag is handled by docker-compose/runtime, not in CMD
CMD ["python", "server.py"]

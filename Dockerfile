# Use official Playwright Python image with all dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

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

# Run the MCP server
CMD ["python", "server.py"]

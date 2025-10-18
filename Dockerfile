# Use official Playwright Python image with all browser dependencies
# Ubuntu 24.04 LTS (Noble) base
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

# Set working directory
WORKDIR /app

# Copy requirements file first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium browser (required even with official image)
# The base image includes system dependencies but not the browser itself
RUN playwright install chromium

# Copy MCP server code
COPY server.py .

# Expose MCP server port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the FastMCP server
CMD ["python", "server.py"]


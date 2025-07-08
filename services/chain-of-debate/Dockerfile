# Chain-of-Debate Service Dockerfile for sam.chat
# UltraMCP Supreme Stack
# Generated: 2025-07-08

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (create basic one if it doesn't exist)
RUN echo "fastapi==0.104.1\nuvicorn[standard]==0.24.0\nrequests==2.31.0\npydantic==2.5.0" > requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create data directory
RUN mkdir -p /app/data/debates

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start the application
CMD ["python", "entrypoint.py"]
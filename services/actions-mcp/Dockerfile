FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8010/health/ || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]
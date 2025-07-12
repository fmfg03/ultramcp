# UltraMCP Agent Factory Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for templates and generated agents
RUN mkdir -p /app/templates /app/generated

# Copy service files
COPY agent_factory_service.py .
COPY enhanced_testing_system.py .
COPY agent_quality_validator.py .
COPY comprehensive_test_scenarios.py .
COPY templates/ /app/templates/

# Create default configuration
RUN echo "ULTRAMCP_COD_URL=http://ultramcp-cod-service:8001" > .env && \
    echo "ULTRAMCP_LOCAL_MODELS_URL=http://ultramcp-local-models-orchestrator:8012" >> .env && \
    echo "ULTRAMCP_SCENARIO_URL=http://ultramcp-scenario-testing:8013" >> .env

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8014/health || exit 1

# Expose port
EXPOSE 8014

# Run the service
CMD ["python", "agent_factory_service.py"]
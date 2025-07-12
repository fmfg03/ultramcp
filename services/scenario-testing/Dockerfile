# Scenario Testing Service for UltraMCP CoD
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install scenario framework from git
RUN git clone https://github.com/fmfg03/scenario.git /app/scenario

# Copy CoD testing components
COPY cod_agent_adapter.py .
COPY cod_judge_system.py .
COPY test_scenarios.py .
COPY config.py .

# Install spacy model for NLP analysis
RUN python -m spacy download en_core_web_sm

# Create results directory
RUN mkdir -p /app/results

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8013/health', timeout=5)"

# Expose port for testing API
EXPOSE 8013

# Run the test service
CMD ["python", "-m", "uvicorn", "test_service:app", "--host", "0.0.0.0", "--port", "8013"]
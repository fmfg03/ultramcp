FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download sentence transformers models
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Try to download code models (optional)
RUN python -c "try:\n    from transformers import AutoTokenizer, AutoModel\n    AutoTokenizer.from_pretrained('microsoft/codebert-base')\n    AutoModel.from_pretrained('microsoft/codebert-base')\nexcept: pass"

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 voyage && chown -R voyage:voyage /app
USER voyage

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Expose port
EXPOSE 8010

# Run the application
CMD ["uvicorn", "voyage_service:app", "--host", "0.0.0.0", "--port", "8010"]
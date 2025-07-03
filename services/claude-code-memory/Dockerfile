# =============================================================================
# UltraMCP Claude Code Memory Service
# Advanced semantic code memory with Tree-sitter AST parsing and Qdrant vector search
# =============================================================================

FROM python:3.11-slim

LABEL maintainer="UltraMCP Team"
LABEL description="Claude Code Memory service with semantic code indexing"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Tree-sitter
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Create non-root user
RUN addgroup --gid 1001 --system memory && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group memory

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Tree-sitter language parsers
RUN python -c "
import tree_sitter_languages
# Pre-install common language parsers
languages = ['python', 'javascript', 'typescript', 'rust', 'go', 'java', 'cpp', 'c', 'bash', 'json', 'yaml']
for lang in languages:
    try:
        tree_sitter_languages.get_language(lang)
        print(f'✅ {lang} parser installed')
    except Exception as e:
        print(f'⚠️  {lang} parser failed: {e}')
"

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/indices data/cache data/memory

# Set ownership
RUN chown -R memory:memory /app

# Switch to non-root user
USER memory

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python scripts/health-check.py

# Expose port
EXPOSE 8009

# Environment variables
ENV PYTHONPATH=/app
ENV MEMORY_SERVICE_PORT=8009
ENV QDRANT_URL=http://ultramcp-qdrant:6333
ENV MEMORY_COLLECTION=ultramcp_code_memory
ENV TREE_SITTER_CACHE_DIR=/app/data/cache/tree_sitter
ENV MEMORY_INDEX_DIR=/app/data/indices
ENV LOG_LEVEL=INFO

# Start the service
CMD ["python", "memory_service.py"]
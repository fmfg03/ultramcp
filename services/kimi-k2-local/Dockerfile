FROM nvidia/cuda:11.8-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    vllm \
    torch \
    transformers \
    fastapi \
    uvicorn

# Create app directory
WORKDIR /app

# Copy startup script
COPY start_kimi.sh .
RUN chmod +x start_kimi.sh

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8011/health || exit 1

# Start command
CMD ["./start_kimi.sh"]
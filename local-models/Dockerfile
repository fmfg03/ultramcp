FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Hugging Face CLI
RUN pip3 install --no-cache-dir huggingface_hub[cli]

# Create models directory
RUN mkdir -p /models

# Copy application code
COPY enhanced_model_manager.py .

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting UltraMCP Enhanced Local Models Orchestrator with MiniMax-M1-80k"\n\
echo "📊 GPU Info:"\n\
nvidia-smi || echo "No GPU detected"\n\
echo "🔧 Starting model orchestrator..."\n\
python3 enhanced_model_manager.py' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 8012

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8012/health || exit 1

# Start application
CMD ["/app/start.sh"]
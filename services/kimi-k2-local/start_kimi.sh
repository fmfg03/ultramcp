#!/bin/bash

echo "🧠 Starting Kimi-K2 Local Model Server..."

# Set environment variables
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
export MODEL_NAME="moonshot-ai/Kimi-K2-Instruct"
export HOST="0.0.0.0"
export PORT="8011"
export MAX_MODEL_LEN="128000"

# Check for GPU availability
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    nvidia-smi
else
    echo "⚠️  No NVIDIA GPU detected, using CPU (slower)"
fi

# Download model if not exists
echo "📥 Checking model availability..."
python3 -c "
from transformers import AutoTokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained('$MODEL_NAME')
    print('✅ Model already downloaded')
except:
    print('📦 Downloading model... (this may take a while)')
    tokenizer = AutoTokenizer.from_pretrained('$MODEL_NAME')
    print('✅ Model download complete')
"

# Start vLLM server
echo "🚀 Starting vLLM server on $HOST:$PORT"
python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_NAME" \
    --host "$HOST" \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --disable-log-requests \
    --served-model-name "kimi-k2"
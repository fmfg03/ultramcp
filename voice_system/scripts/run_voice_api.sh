#!/bin/bash

echo "🚀 Starting MCP Voice API Server..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./setup_voice_system.sh first"
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if required files exist
if [ ! -f "voice_api.py" ]; then
    echo "❌ voice_api.py not found!"
    echo "📝 Create the voice system files first"
    exit 1
fi

# Start the API server
echo "📡 Starting FastAPI server on port 8080..."
python3 -m uvicorn voice_api:app --host 0.0.0.0 --port 8080 --reload

echo "✅ Voice API server started!"
echo "🌐 API available at: http://localhost:8080"
echo "📚 Docs available at: http://localhost:8080/docs"

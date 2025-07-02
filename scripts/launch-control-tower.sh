#!/bin/bash

# =============================================================================
# UltraMCP Control Tower Launcher
# =============================================================================

set -e

echo "🎛️ UltraMCP Control Tower Launcher"
echo "=================================="

# Check dependencies
echo "🔍 Checking dependencies..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed"
    exit 1
fi

# Check if Ollama is running
if ! pgrep -f "ollama" > /dev/null; then
    echo "⚠️  Ollama not running - starting local models..."
    ollama serve &
    sleep 3
fi

# Create directories if needed
mkdir -p /root/ultramcp/services/control-tower
mkdir -p /root/ultramcp/logs

echo "✅ Dependencies checked"

# Install backend dependencies
echo "📦 Installing Control Tower backend dependencies..."
cd /root/ultramcp/services/control-tower
if [ ! -d "node_modules" ]; then
    npm install --silent
fi

# Install frontend dependencies  
echo "📦 Installing frontend dependencies..."
cd /root/ultramcp/apps/frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi

echo "✅ Dependencies installed"

# Start services
echo "🚀 Starting Control Tower services..."

# Start backend WebSocket server
echo "🔧 Starting WebSocket server on port 8001..."
cd /root/ultramcp/services/control-tower
npm start &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ WebSocket server running on port 8001"
else
    echo "❌ Failed to start WebSocket server"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend development server
echo "🎨 Starting frontend on port 5173..."
cd /root/ultramcp/apps/frontend
npm run dev -- --port 5173 --host 0.0.0.0 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

# Check if frontend is accessible
if curl -s http://localhost:5173 > /dev/null; then
    echo "✅ Frontend running on port 5173"
else
    echo "❌ Failed to start frontend"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 UltraMCP Control Tower is now running!"
echo ""
echo "📊 Control Tower UI: http://localhost:5173"
echo "🔌 WebSocket API: ws://localhost:8001"
echo "📡 REST API: http://localhost:8001"
echo ""
echo "🎯 Quick Test:"
echo "  make cod-local TOPIC='Test the Control Tower'"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap to clean up processes on exit
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0' INT TERM

# Keep script running
wait
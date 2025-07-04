#!/bin/bash

echo "🎭 Starting Claudia MCP Integration..."

# Change to claudia-mcp directory
cd /root/ultramcp/services/claudia-mcp

echo "1. Starting Chain-of-Debate MCP Server..."
python3 cod_mcp_server.py &
COD_PID=$!

echo "2. Starting Local Models MCP Server..."
python3 local_mcp_server.py &
LOCAL_PID=$!

echo "3. Starting Hybrid Decision MCP Server..."
python3 hybrid_mcp_server.py &
HYBRID_PID=$!

echo "✅ Claudia MCP servers started"
echo "Chain-of-Debate PID: $COD_PID"
echo "Local Models PID: $LOCAL_PID"
echo "Hybrid Decision PID: $HYBRID_PID"

echo ""
echo "Starting Claudia frontend..."
cd /root/ultramcp/apps/frontend
npm run dev -- --port 3001 &
FRONTEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "✅ Complete Claudia system started!"
echo "🎭 Claudia Interface: http://localhost:3001"
echo "📖 To stop servers: kill $COD_PID $LOCAL_PID $HYBRID_PID $FRONTEND_PID"
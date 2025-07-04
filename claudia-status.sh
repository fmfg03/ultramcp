#!/bin/bash

echo "📊 Claudia Integration Status"
echo "============================"

# Check if frontend is running
if curl -s http://localhost:3003 > /dev/null 2>&1; then
    echo "✅ Frontend: Running on http://localhost:3003"
else
    echo "❌ Frontend: Not running"
fi

# Check MCP servers by looking for Python processes
if pgrep -f "cod_mcp_server.py" > /dev/null; then
    echo "✅ Chain-of-Debate MCP Server: Running"
else
    echo "❌ Chain-of-Debate MCP Server: Not running"
fi

if pgrep -f "local_mcp_server.py" > /dev/null; then
    echo "✅ Local Models MCP Server: Running"
else
    echo "❌ Local Models MCP Server: Not running"
fi

if pgrep -f "hybrid_mcp_server.py" > /dev/null; then
    echo "✅ Hybrid Decision MCP Server: Running"
else
    echo "❌ Hybrid Decision MCP Server: Not running"
fi

echo ""
echo "🎭 Access Claudia at: http://localhost:3003"
echo "📖 Use /root/ultramcp/start-claudia.sh to restart"
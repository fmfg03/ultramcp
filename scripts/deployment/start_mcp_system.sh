#!/bin/bash
# MCP Enterprise System Startup

echo "🚀 Starting MCP Enterprise System..."

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# Start services in background
echo "Starting Memory Analyzer..."
python3 sam_memory_analyzer.py &

echo "Starting Orchestration Server..."
python3 mcp_orchestration_server.py &

echo "Starting Webhook System..."
python3 complete_webhook_agent_end_task_system.py &

echo "Starting Monitoring Dashboard..."
python3 mcp_logs_dashboard_system.py &

echo "✅ All services started!"
echo "📊 Monitor logs: tail -f *.log"
echo "🌐 Access frontend: http://65.109.54.94:5174"
echo "🔌 API endpoint: http://65.109.54.94:3000"

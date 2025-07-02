#!/bin/bash

# UltraMCP System Status Check
source "$(dirname "$0")/common.sh"

log_info "system-status" "Checking UltraMCP system status"

echo "🎭 Playwright MCP:"
if is_service_running "playwright.*mcp"; then
    pid=$(pgrep -f 'playwright.*mcp')
    echo "  ✅ Running (PID: $pid)"
else
    echo "  ❌ Not running"
fi

echo ""
echo "🧠 CoD Protocol Service:"
if is_service_running "cod-service"; then
    pid=$(pgrep -f 'cod-service')
    echo "  ✅ Running (PID: $pid)"
else
    echo "  ❌ Not running"
fi

echo ""
echo "💾 System Resources:"
echo "  Memory: $(free -h 2>/dev/null | awk '/^Mem:/ {print $3"/"$2}' || echo 'unknown')"
echo "  Disk: $(df -h . 2>/dev/null | awk 'NR==2 {print $3"/"$2" ("$5" used)"}' || echo 'unknown')"

echo ""
echo "🌐 Network Connectivity:"
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "  ✅ Internet connection active"
else
    echo "  ❌ No internet connection"
fi

echo ""
echo "🔑 Environment Variables:"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "  ✅ OpenAI API key configured"
else
    echo "  ⚠️  OpenAI API key not set"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  ✅ Anthropic API key configured"
else
    echo "  ⚠️  Anthropic API key not set"
fi

echo ""
echo "📊 Recent Activity:"
if [ -f "logs/combined.log" ]; then
    last_entry=$(tail -n 1 logs/combined.log 2>/dev/null)
    if [ -n "$last_entry" ]; then
        last_timestamp=$(echo "$last_entry" | jq -r '.timestamp' 2>/dev/null || echo 'Unable to parse')
        echo "  Last activity: $last_timestamp"
        
        today_count=$(grep "$(date +%Y-%m-%d)" logs/combined.log 2>/dev/null | wc -l)
        echo "  Log entries today: $today_count"
        
        error_count=$(tail -n 100 logs/combined.log 2>/dev/null | grep -c '"level":"error"' || echo 0)
        if [ "$error_count" -gt 0 ]; then
            echo "  ⚠️  Recent errors: $error_count (last 100 entries)"
        else
            echo "  ✅ No recent errors"
        fi
    else
        echo "  ❌ Log file empty"
    fi
else
    echo "  ❌ No log file found"
fi

echo ""
echo "🚀 Available Commands:"
echo "  make help          - Show all available commands"
echo "  make logs          - View recent logs"
echo "  make health-check  - Run comprehensive health check"

log_info "system-status" "Status check complete"
#!/bin/bash

# Claude Code Integration Demo Script
# Demonstrates UltraMCP Hybrid productivity features
source "$(dirname "$0")/common.sh"

echo "🤖 UltraMCP + Claude Code Productivity Demo"
echo "==========================================="
echo ""

log_info "claude-demo" "Starting Claude Code integration demonstration"

# Function to run demo with user interaction
run_demo() {
    local demo_type="$1"
    local description="$2"
    local command="$3"
    
    echo "📋 Demo: $demo_type"
    echo "Description: $description"
    echo "Command: $command"
    echo ""
    
    read -p "Run this demo? [y/N]: " choice
    case $choice in
        [Yy]*)
            echo "🚀 Running: $command"
            echo "================================"
            eval "$command"
            echo ""
            echo "✅ Demo completed. Check results above."
            echo ""
            ;;
        *)
            echo "⏭️  Skipping demo"
            echo ""
            ;;
    esac
}

# Check system status first
echo "🔍 System Status Check"
echo "====================="
make status
echo ""

# Demo 1: Terminal-First AI Chat (80% use case)
run_demo \
    "Terminal-First AI Chat" \
    "Quick AI interaction bypassing complex orchestration" \
    "make chat TEXT='What are the benefits of terminal-first development?'"

# Demo 2: Web Scraping with Playwright
run_demo \
    "Web Scraping" \
    "Extract content from web pages using Playwright MCP" \
    "make web-scrape URL='https://httpbin.org/json'"

# Demo 3: Advanced CoD Protocol Debate (20% use case)
run_demo \
    "Chain-of-Debate Protocol" \
    "Multi-LLM coordination for complex decision making" \
    "make debate TOPIC='Terminal-first vs GUI-first development approaches'"

# Demo 4: Full Research Pipeline
run_demo \
    "Web Research Pipeline" \
    "Combine web scraping with AI analysis" \
    "make research URL='https://httpbin.org/json'"

# Demo 5: Data Analysis
if [ -f "package.json" ]; then
    run_demo \
        "Data Analysis" \
        "Analyze local JSON file with AI insights" \
        "make analyze FILE='package.json'"
fi

# Demo 6: System Monitoring
run_demo \
    "System Health Check" \
    "Comprehensive system status and health monitoring" \
    "make health-check"

# Show available data
echo "📊 Available Data Files"
echo "======================"
if [ -d "data" ]; then
    echo "Recent task results:"
    find data -name "task_*" -type f | head -5 | while read -r file; do
        echo "  📄 $file"
        if [[ "$file" == *.json ]]; then
            echo "      $(jq -r '.task_id // "unknown"' "$file" 2>/dev/null): $(jq -r '.timestamp // "no timestamp"' "$file" 2>/dev/null)"
        fi
    done
else
    echo "No data directory found. Run some demos first!"
fi

echo ""

# Show logs summary
echo "📋 Recent Logs Summary"
echo "======================"
if [ -f "logs/combined.log" ]; then
    echo "Last 5 log entries:"
    tail -n 5 logs/combined.log | jq -r '. | "\(.timestamp) [\(.level)] \(.service): \(.message)"' 2>/dev/null || tail -n 5 logs/combined.log
else
    echo "No logs found. System may not be initialized."
fi

echo ""

# Claude Code integration tips
echo "💡 Claude Code Integration Tips"
echo "==============================="
echo ""
echo "1. **Terminal-First Productivity (80%)**:"
echo "   • Use 'make chat TEXT=\"your question\"' for quick AI interactions"
echo "   • Use 'make web-scrape URL=\"...\"' for web data extraction"
echo "   • Use 'make status' to check system health"
echo ""
echo "2. **Advanced Orchestration (20%)**:"
echo "   • Use 'make debate TOPIC=\"...\"' for complex decisions"
echo "   • Use 'make research URL=\"...\"' for comprehensive analysis"
echo "   • Use 'make analyze FILE=\"...\"' for data insights"
echo ""
echo "3. **Development Workflow**:"
echo "   • Use 'make docker-hybrid' for production-like environment"
echo "   • Use 'make docker-dev' for development with hot reload"
echo "   • Use 'make logs-tail' to monitor system activity"
echo ""
echo "4. **File Management**:"
echo "   • All results stored in 'data/' directory with task IDs"
echo "   • All logs in 'logs/combined.log' in JSON format"
echo "   • Use 'make help' to see all available commands"
echo ""

# Integration verification
echo "🔧 Claude Code Integration Verification"
echo "======================================="
echo ""

# Check if we're running in Claude Code environment
if [ -n "$CLAUDE_CODE" ] || [ -n "$ANTHROPIC_CLI" ]; then
    echo "✅ Running in Claude Code environment"
else
    echo "ℹ️  Not detected as Claude Code environment"
    echo "   This script works in any terminal, optimized for Claude Code"
fi

# Check required tools
tools=("make" "docker" "jq" "curl" "node" "python3")
echo "📋 Tool Availability:"
for tool in "${tools[@]}"; do
    if command -v "$tool" >/dev/null; then
        echo "  ✅ $tool: Available"
    else
        echo "  ❌ $tool: Missing"
    fi
done

echo ""

# Show next steps
echo "🎯 Next Steps for Claude Code Productivity"
echo "=========================================="
echo ""
echo "1. Start the system: make start"
echo "2. Quick AI chat: make chat TEXT='Hello UltraMCP'"
echo "3. Web scraping: make web-scrape URL='https://example.com'"
echo "4. Advanced debate: make debate TOPIC='AI development best practices'"
echo "5. Check status: make status"
echo "6. View logs: make logs"
echo ""
echo "For full command reference: make help"
echo ""

log_success "claude-demo" "Claude Code integration demo completed"

echo "🚀 UltraMCP Hybrid System Ready for Maximum Productivity!"
echo "========================================================="
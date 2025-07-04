#!/bin/bash

# =============================================================================
# UltraMCP System Status Check
# Comprehensive status overview for all system components
# =============================================================================

# Import common functions if available
if [ -f "$(dirname "$0")/common.sh" ]; then
    source "$(dirname "$0")/common.sh"
else
    # Fallback logging function
    log_info() {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $2"
    }
    
    is_service_running() {
        pgrep -f "$1" > /dev/null
    }
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Status indicators
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
}

warning_status() {
    echo -e "${YELLOW}⚠️${NC}"
}

log_info "system-status" "Checking UltraMCP system status"

echo -e "${CYAN}🎯 UltraMCP System Status Report${NC}"
echo "================================="
echo "Time: $(date)"
echo "Directory: $(pwd)"

# Core Dependencies
echo -e "\n${PURPLE}🔧 Core Dependencies${NC}"
printf "%-20s" "Node.js:"
if command -v node &> /dev/null; then
    printf "%s %s\n" "$(check_status 0)" "$(node --version)"
else
    printf "%s Not installed\n" "$(check_status 1)"
fi

printf "%-20s" "Python 3:"
if command -v python3 &> /dev/null; then
    printf "%s %s\n" "$(check_status 0)" "$(python3 --version)"
else
    printf "%s Not installed\n" "$(check_status 1)"
fi

printf "%-20s" "Docker:"
if command -v docker &> /dev/null; then
    printf "%s Installed\n" "$(check_status 0)"
else
    printf "%s Not installed\n" "$(check_status 1)"
fi

printf "%-20s" "Ollama:"
if command -v ollama &> /dev/null; then
    printf "%s Installed\n" "$(check_status 0)"
else
    printf "%s Not available\n" "$(warning_status)"
fi

# UltraMCP Structure
echo -e "\n${PURPLE}🏗️ UltraMCP Structure${NC}"
printf "%-20s" "CLAUDE.md:"
[ -f "CLAUDE.md" ] && printf "%s Present\n" "$(check_status 0)" || printf "%s Missing\n" "$(check_status 1)"

printf "%-20s" "Makefile:"
[ -f "Makefile" ] && printf "%s Present\n" "$(check_status 0)" || printf "%s Missing\n" "$(check_status 1)"

printf "%-20s" "Core Orchestrator:"
[ -f "core/orchestrator/eventBus.js" ] && printf "%s Present\n" "$(check_status 0)" || printf "%s Missing\n" "$(check_status 1)"

printf "%-20s" "HITL System:"
[ -f "services/human-interaction/action_request_adapter.py" ] && printf "%s Present\n" "$(check_status 0)" || printf "%s Missing\n" "$(check_status 1)"

# Legacy MCP Services Check
echo -e "\n${PURPLE}🎭 Legacy MCP Services${NC}"
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

# Docker Services
echo -e "\n${PURPLE}🐳 Docker Services${NC}"
if command -v docker &> /dev/null; then
    running_containers=$(docker ps --format "{{.Names}}" 2>/dev/null)
    container_count=$(echo "$running_containers" | grep -v '^$' | wc -l)
    
    printf "%-20s" "Running Containers:"
    if [ "$container_count" -gt 0 ]; then
        printf "%s %d active\n" "$(check_status 0)" "$container_count"
        echo "$running_containers" | sed 's/^/                     🟢 /'
    else
        printf "%s None running\n" "$(warning_status)"
        echo "                     💡 Use 'make docker-hybrid' to start services"
    fi
else
    printf "%-20s%s Docker not available\n" "Docker Status:" "$(check_status 1)"
fi

# Local LLM Models
echo -e "\n${PURPLE}🤖 Local LLM Models${NC}"
if command -v ollama &> /dev/null; then
    models=$(ollama list 2>/dev/null | grep -v NAME)
    model_count=$(echo "$models" | grep -v '^$' | wc -l)
    
    printf "%-20s" "Available Models:"
    if [ "$model_count" -gt 0 ]; then
        printf "%s %d models\n" "$(check_status 0)" "$model_count"
        echo "$models" | head -3 | sed 's/^/                     🧠 /'
        if [ "$model_count" -gt 3 ]; then
            echo "                     ... and $((model_count - 3)) more"
        fi
    else
        printf "%s No models downloaded\n" "$(warning_status)"
        echo "                     💡 Use 'ollama pull llama3.1' to download models"
    fi
else
    printf "%-20s%s Ollama not installed\n" "Ollama Status:" "$(warning_status)"
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

# Environment Configuration
echo -e "\n${PURPLE}🔑 Environment Configuration${NC}"
printf "%-20s" ".env file:"
if [ -f ".env" ]; then
    printf "%s Present\n" "$(check_status 0)"
else
    printf "%s Missing\n" "$(warning_status)"
    echo "                     💡 Copy from .env.example"
fi

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
    mkdir -p logs 2>/dev/null
fi

# Claude Code Integration Status
echo -e "\n${PURPLE}🤖 Claude Code Integration${NC}"
if [ -f "data/last-claude-session.json" ]; then
    session_info=$(cat data/last-claude-session.json 2>/dev/null)
    if [ -n "$session_info" ]; then
        session_id=$(echo "$session_info" | jq -r '.session_id' 2>/dev/null || echo 'unknown')
        echo "  ✅ Last session: $session_id"
    fi
else
    echo "  💡 No previous Claude session detected"
fi

echo ""
echo "🚀 Available Commands:"
echo "  make help              - Show all available commands"
echo "  make claude-verify     - Full system verification"
echo "  make docker-hybrid     - Start all services"
echo "  make logs              - View recent logs"
echo "  make health-check      - Run comprehensive health check"

echo -e "\n${GREEN}📋 Status check complete${NC}"
log_info "system-status" "Status check complete"
#!/bin/bash

# =============================================================================
# UltraMCP Claude Session Initialization
# Automatic initialization script for every Claude Code session
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Session info
SESSION_ID=$(date +%Y%m%d-%H%M%S)
INIT_LOG="logs/claude-session-$SESSION_ID.log"

echo -e "${CYAN}🚀 Initializing UltraMCP for Claude Code session...${NC}"

# Create session log
mkdir -p logs
echo "$(date): Claude Code session initialized - $SESSION_ID" > "$INIT_LOG"

# Quick system acknowledgment
echo -e "${BLUE}📚 Acknowledging system documentation...${NC}"
if [ -f "CLAUDE.md" ]; then
    echo "✅ CLAUDE.md acknowledged"
    echo "$(date): CLAUDE.md acknowledged" >> "$INIT_LOG"
fi

if [ -f "README.md" ]; then
    echo "✅ README.md acknowledged" 
    echo "$(date): README.md acknowledged" >> "$INIT_LOG"
fi

# Quick MCP services check
echo -e "${BLUE}🔧 Quick MCP services check...${NC}"
SERVICES_STATUS=""

# Check Docker containers
if command -v docker &> /dev/null; then
    RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}" 2>/dev/null | wc -l)
    if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
        echo "✅ $RUNNING_CONTAINERS Docker services running"
        SERVICES_STATUS="$RUNNING_CONTAINERS containers active"
    else
        echo "⚠️  No Docker services running (use 'make docker-hybrid')"
        SERVICES_STATUS="No containers running"
    fi
else
    echo "⚠️  Docker not available"
    SERVICES_STATUS="Docker unavailable"
fi

# Check Ollama (local LLMs)
if command -v ollama &> /dev/null; then
    LOCAL_MODELS=$(ollama list 2>/dev/null | grep -v NAME | wc -l)
    if [ "$LOCAL_MODELS" -gt 0 ]; then
        echo "✅ $LOCAL_MODELS local LLM models available"
    else
        echo "⚠️  No local LLM models (use 'ollama pull llama3.1')"
    fi
else
    echo "⚠️  Ollama not installed (local LLMs unavailable)"
fi

# Environment check
if [ -f ".env" ]; then
    echo "✅ Environment configuration found"
else
    echo "⚠️  No .env file (copy from .env.example)"
fi

# Log session info
echo "$(date): Services status - $SERVICES_STATUS" >> "$INIT_LOG"

# Quick start reminder
echo -e "\n${GREEN}🎯 UltraMCP Ready for Claude Code!${NC}"
echo -e "${CYAN}Essential commands:${NC}"
echo "  make help           - Show all commands"
echo "  make status         - System status"
echo "  make chat TEXT='...' - Quick AI chat"
echo "  make docker-hybrid  - Start all services"
echo ""
echo -e "${YELLOW}💡 Documentation: cat CLAUDE.md${NC}"
echo -e "${YELLOW}📊 Full verification: ./scripts/claude-startup-verification.sh${NC}"

# Save session info for later reference
echo "{\"session_id\":\"$SESSION_ID\",\"timestamp\":\"$(date -Iseconds)\",\"status\":\"initialized\"}" > "data/last-claude-session.json"

echo -e "\n${GREEN}✅ Claude Code session ready - ID: $SESSION_ID${NC}"
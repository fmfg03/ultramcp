#!/bin/bash

# =============================================================================
# Auto Claude Initialization Hook
# This script can be added to .bashrc or .zshrc to auto-run on terminal start
# when in UltraMCP directory
# =============================================================================

# Check if we're in UltraMCP directory and Claude Code might be starting
if [ -f "CLAUDE.md" ] && [ -f "Makefile" ] && [ -d "services" ]; then
    # Check if this looks like a fresh Claude Code session
    if [ ! -f "data/last-claude-session.json" ] || [ $(find data/last-claude-session.json -mmin +60 2>/dev/null | wc -l) -gt 0 ]; then
        echo "🤖 UltraMCP detected - Initializing Claude Code session..."
        ./scripts/claude-session-init.sh
    else
        echo "✅ UltraMCP ready - Session already initialized"
        echo "💡 Run 'make claude-verify' for full verification"
    fi
fi
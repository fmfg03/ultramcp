#!/bin/bash

# =============================================================================
# Setup Claude Code Aliases for UltraMCP
# Creates convenient aliases for Claude Code integration
# =============================================================================

echo "🤖 Setting up Claude Code aliases for UltraMCP..."

# Create alias file
ALIAS_FILE="$HOME/.ultramcp_aliases"

cat > "$ALIAS_FILE" << 'EOF'
# UltraMCP Claude Code Aliases
# Source this file in your .bashrc or .zshrc

# Navigation
alias ultramcp='cd /root/ultramcp'

# Session Management
alias claude-init='make claude-init'
alias claude-verify='make claude-verify'
alias claude-start='make claude-start'

# Quick Commands  
alias ustatus='make status'
alias uhelp='make help'
alias ulogs='make logs-tail'

# AI Operations
alias uchat='make chat TEXT='
alias ulocal='make local-chat TEXT='
alias udebate='make cod-local TOPIC='

# Development
alias ustart='make docker-hybrid'
alias ustop='make docker-down'
alias uhealthcheck='make health-check'

# Quick shortcuts
alias u='make'
alias init='make claude-init'
alias verify='make claude-verify'

echo "🚀 UltraMCP aliases loaded!"
echo "💡 Run 'claude-init' to start your session"
EOF

echo "✅ Aliases created at: $ALIAS_FILE"
echo ""
echo "📝 To activate aliases, add this to your .bashrc or .zshrc:"
echo "source $ALIAS_FILE"
echo ""
echo "🔧 Or run this command to add it automatically:"
echo "echo 'source $ALIAS_FILE' >> ~/.bashrc"
echo ""
echo "💡 After activation, you can use:"
echo "  claude-init    - Initialize Claude session"
echo "  ustatus        - Check system status"  
echo "  uchat 'hello'  - Quick AI chat"
echo "  udebate 'topic' - Local AI debate"
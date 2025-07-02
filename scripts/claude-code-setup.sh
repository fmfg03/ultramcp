#!/bin/bash

# Claude Code Integration Setup Script
# Optimizes UltraMCP for Claude Code productivity
source "$(dirname "$0")/common.sh"

echo "🤖 UltraMCP + Claude Code Setup"
echo "==============================="
echo ""

log_info "claude-setup" "Setting up Claude Code integration"

# Check if Claude Code environment is detected
if [ -n "$CLAUDE_CODE" ] || [ -n "$ANTHROPIC_CLI" ]; then
    echo "✅ Claude Code environment detected"
    log_info "claude-setup" "Claude Code environment detected"
else
    echo "ℹ️  Standard terminal environment (works with Claude Code)"
    log_info "claude-setup" "Standard terminal environment"
fi

echo ""

# Setup system directories
echo "📁 Setting up directories..."
ensure_directory "data/debates"
ensure_directory "data/scrapes" 
ensure_directory "data/research"
ensure_directory "data/analysis"
ensure_directory "logs"

# Check and install dependencies
echo ""
echo "🔧 Checking dependencies..."

# Check Node.js and npm
if command -v node >/dev/null && command -v npm >/dev/null; then
    echo "  ✅ Node.js and npm: Available"
    node_version=$(node --version)
    npm_version=$(npm --version)
    echo "     Node.js: $node_version, npm: $npm_version"
    
    # Install Node.js dependencies if package.json exists
    if [ -f "package.json" ]; then
        echo "  📦 Installing Node.js dependencies..."
        npm install --silent
        echo "     ✅ Node.js dependencies installed"
    fi
else
    echo "  ❌ Node.js/npm: Missing"
    echo "     Install from: https://nodejs.org/"
fi

# Check Python 3
if command -v python3 >/dev/null; then
    echo "  ✅ Python 3: Available"
    python_version=$(python3 --version)
    echo "     $python_version"
    
    # Install Python dependencies
    if [ -f "requirements.txt" ]; then
        echo "  📦 Installing Python dependencies..."
        pip3 install -r requirements.txt --quiet --user
        echo "     ✅ Python dependencies installed"
    fi
else
    echo "  ❌ Python 3: Missing"
    echo "     Install Python 3.8+ from: https://python.org/"
fi

# Check Docker
if command -v docker >/dev/null; then
    echo "  ✅ Docker: Available"
    docker_version=$(docker --version)
    echo "     $docker_version"
    
    # Check Docker Compose
    if docker compose version >/dev/null 2>&1; then
        echo "  ✅ Docker Compose: Available (docker compose)"
        compose_version=$(docker compose version)
        echo "     $compose_version"
    elif command -v docker-compose >/dev/null; then
        echo "  ✅ Docker Compose: Available (docker-compose)"
        compose_version=$(docker-compose --version)
        echo "     $compose_version"
    else
        echo "  ❌ Docker Compose: Missing"
        echo "     Install Docker Compose plugin"
    fi
else
    echo "  ❌ Docker: Missing"
    echo "     Install from: https://docker.com/"
fi

# Check required CLI tools
echo ""
echo "🛠️  Checking CLI tools..."
cli_tools=("jq" "curl" "make")
for tool in "${cli_tools[@]}"; do
    if command -v "$tool" >/dev/null; then
        echo "  ✅ $tool: Available"
    else
        echo "  ❌ $tool: Missing"
        case $tool in
            jq) echo "     Install: brew install jq (macOS) or apt install jq (Ubuntu)" ;;
            curl) echo "     Install: Usually pre-installed on most systems" ;;
            make) echo "     Install: Usually pre-installed, or via build-essential" ;;
        esac
    fi
done

# Setup environment file
echo ""
echo "🔐 Setting up environment configuration..."

if [ ! -f ".env" ]; then
    log_info "claude-setup" "Creating .env file"
    
    cat > .env << EOF
# UltraMCP Hybrid System Configuration
# Generated on $(date -Iseconds)

# Database Configuration
POSTGRES_PASSWORD=ultramcp_secure_$(date +%s)
POSTGRES_DB=ultramcp
POSTGRES_USER=ultramcp

# Redis Configuration  
REDIS_PASSWORD=redis_secure_$(date +%s)

# CoD Protocol Service
COD_SERVICE_PORT=8001

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Security
JWT_SECRET=jwt_secret_$(date +%s)
SESSION_SECRET=session_secret_$(date +%s)

# Development/Production Mode
NODE_ENV=development
PYTHONPATH=/app

# Logging
LOG_LEVEL=info
EOF

    echo "  ✅ Created .env file with secure defaults"
    echo "  ⚠️  Please update API keys in .env file for full functionality"
else
    echo "  ✅ .env file already exists"
fi

# Make scripts executable
echo ""
echo "🔧 Setting up script permissions..."
chmod +x scripts/*.sh
echo "  ✅ All scripts are now executable"

# Verify setup
echo ""
echo "🔍 Verifying setup..."

# Test Makefile
if make help >/dev/null 2>&1; then
    echo "  ✅ Makefile: Working"
else
    echo "  ❌ Makefile: Issues detected"
fi

# Test common script
if [ -f "scripts/common.sh" ] && source scripts/common.sh; then
    echo "  ✅ Common utilities: Working"
else
    echo "  ❌ Common utilities: Issues detected"
fi

# Create Claude Code optimized aliases
echo ""
echo "🚀 Creating Claude Code productivity shortcuts..."

# Create a quick reference file
cat > QUICK_REFERENCE.md << 'EOF'
# UltraMCP Quick Reference for Claude Code

## Most Used Commands (Terminal-First - 80%)
```bash
make chat TEXT="your question"           # Quick AI chat
make web-scrape URL="https://site.com"   # Web scraping  
make status                              # System status
make logs                                # View logs
```

## Advanced Commands (Orchestration - 20%)
```bash
make debate TOPIC="your topic"           # Multi-LLM debate
make research URL="https://site.com"     # Web research + AI
make analyze FILE="data.json"            # Data analysis
```

## System Management
```bash
make start                               # Interactive startup
make docker-hybrid                       # Start optimized stack
make health-check                        # Full health check
```

## Claude Code Integration
```bash
make claude-help                         # Integration guide
make claude-demo                         # Productivity demo
```

All results saved to `data/` directory with task IDs.
All logs in `logs/combined.log` in JSON format.
EOF

echo "  ✅ Created QUICK_REFERENCE.md for easy access"

# Final setup summary
echo ""
echo "✅ UltraMCP + Claude Code Setup Complete!"
echo "========================================"
echo ""
echo "🎯 Next Steps:"
echo "1. Update API keys in .env file (OPENAI_API_KEY, ANTHROPIC_API_KEY)"
echo "2. Run: make start (interactive startup)"
echo "3. Try: make claude-demo (productivity demonstration)"
echo "4. Check: make claude-help (integration guide)"
echo ""
echo "📋 Quick Commands to Try:"
echo "• make chat TEXT='Hello UltraMCP'"
echo "• make web-scrape URL='https://httpbin.org/json'"
echo "• make status"
echo ""
echo "📖 Documentation:"
echo "• CLAUDE.md - Full integration guide"
echo "• QUICK_REFERENCE.md - Command reference"
echo "• make help - All available commands"
echo ""

log_success "claude-setup" "Claude Code integration setup completed successfully"

# Optional: Run a quick test
echo "🧪 Quick System Test"
echo "==================="
read -p "Run a quick system test? [y/N]: " test_choice
case $test_choice in
    [Yy]*)
        echo ""
        echo "Running system status check..."
        make status
        echo ""
        echo "✅ System test completed"
        ;;
    *)
        echo "Skipping system test"
        ;;
esac

echo ""
echo "🚀 Ready for maximum productivity with Claude Code!"
echo "Use 'make claude-help' anytime for guidance."
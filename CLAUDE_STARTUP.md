# 🤖 UltraMCP Claude Code Startup Guide

This guide explains how to set up automatic UltraMCP initialization for every Claude Code session.

## 🚀 Quick Start

### Automatic Session Initialization

Every time you start Claude Code in the UltraMCP directory, run:

```bash
make claude-init
```

This will:
- ✅ Acknowledge all documentation files (CLAUDE.md, README.md, etc.)
- ✅ Check MCP services status
- ✅ Verify Docker containers
- ✅ Check local LLM models
- ✅ Validate environment configuration
- ✅ Create session logs

### Full System Verification

For comprehensive verification (recommended for first time setup):

```bash
make claude-verify
```

This provides:
- 🏗️ Complete structure verification
- 📚 Documentation acknowledgment
- 🔧 All MCP services check
- 🐳 Docker services status
- 📦 Dependencies verification
- ⚙️ Environment configuration
- 🎯 Core orchestrator check
- 🔨 Makefile commands validation
- 🏥 Basic health check
- 📊 Detailed reporting

## 📋 Available Commands

### Session Management
```bash
make claude-init      # Quick session initialization
make claude-verify    # Full system verification
make claude-start     # Init + status check
```

### System Operations
```bash
make status          # Quick system status
make help           # Show all commands
make docker-hybrid  # Start all services
make health-check   # Comprehensive health check
```

### Development Commands
```bash
make chat TEXT="Hello"           # Quick AI chat
make local-chat TEXT="Hello"     # Local LLM chat
make logs-tail                   # Follow live logs
make control-tower              # Launch Control Tower UI
```

## 🔧 Automatic Setup Options

### Option 1: Manual Initialization (Recommended)

Add to your Claude Code workflow:
```bash
# When starting work in UltraMCP
cd /path/to/ultramcp
make claude-init
```

### Option 2: Shell Integration (Advanced)

Add to your `.bashrc` or `.zshrc`:
```bash
# Auto-detect UltraMCP and initialize Claude sessions
if [ -f "./scripts/auto-claude-init.sh" ]; then
    source ./scripts/auto-claude-init.sh
fi
```

### Option 3: Claude Code Configuration

Create a `.clauderc` file in the UltraMCP directory (already provided):
```bash
# This file is automatically sourced by Claude Code
source ./.clauderc
```

## 📊 What Gets Verified

### Structure Check ✅
- All required directories (`apps/`, `services/`, `core/`, etc.)
- Essential files (`CLAUDE.md`, `Makefile`, `package.json`)
- Human-in-the-Loop integration components

### Services Check 🔧
- **Asterisk MCP**: Security service
- **Blockoli MCP**: Code intelligence
- **DeepClaude**: Metacognitive AI
- **Voice System**: Voice processing
- **Control Tower**: WebSocket server
- **Human Interaction**: HITL system

### Dependencies Check 📦
- Node.js and npm
- Python 3 and pip3
- Docker and Docker Compose
- Ollama (local LLMs)
- jq (JSON processing)

### Environment Check ⚙️
- `.env` file configuration
- API keys (OpenAI, Anthropic)
- Database credentials
- System paths

### Docker Services Check 🐳
- Running containers
- Service health
- Port availability
- Resource usage

### Local LLM Check 🤖
- Available Ollama models
- Model sizes and versions
- Download recommendations

## 🎯 Session Information

Each Claude session generates:
- **Session ID**: Unique identifier (format: YYYYMMDD-HHMMSS)
- **Session Log**: `logs/claude-session-{SESSION_ID}.log`
- **Status Report**: `data/startup-verification-{TIMESTAMP}.json`
- **Last Session**: `data/last-claude-session.json`

## 💡 Troubleshooting

### Common Issues

**Missing Dependencies**:
```bash
# Install missing tools
sudo apt-get update
sudo apt-get install jq curl

# For Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

**Environment Configuration**:
```bash
# Copy example configuration
cp .env.example .env

# Edit with your API keys
nano .env
```

**Docker Services Not Running**:
```bash
# Start all services
make docker-hybrid

# Or start specific services
docker-compose up -d postgres redis
```

**No Local Models**:
```bash
# Download recommended models
ollama pull qwen2.5:14b
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
```

### Health Check Issues

If `make claude-verify` shows warnings:
1. Check the recommendations in the output
2. Run `make setup` for first-time initialization
3. Verify Docker installation and permissions
4. Ensure all required files exist

### Service Issues

If MCP services aren't running:
```bash
# Check Docker status
docker ps

# Start hybrid stack
make docker-hybrid

# Check logs for errors
make docker-logs
```

## 🚀 Best Practices

### 1. Start Every Session
Always run initialization when starting Claude Code:
```bash
make claude-init
```

### 2. Verify Before Important Work
For critical tasks, run full verification:
```bash
make claude-verify
```

### 3. Monitor System Health
Regularly check system status:
```bash
make status
make health-check
```

### 4. Keep Documentation Current
The initialization process acknowledges:
- `CLAUDE.md` - Main integration guide
- `README.md` - Project overview
- All other `.md` files in the project

### 5. Use Session Logs
Check session logs for troubleshooting:
```bash
# View latest session log
ls -la logs/claude-session-*.log | tail -1 | xargs cat

# View all startup reports
ls -la data/startup-verification-*.json
```

## 🔄 Integration Workflow

### Typical Claude Code Session:

1. **Start**: `make claude-init`
2. **Verify** (if needed): `make claude-verify`
3. **Work**: Use UltraMCP commands (`make chat`, `make cod-local`, etc.)
4. **Monitor**: `make status` for system health
5. **Debug** (if needed): `make logs-tail` for live monitoring

### Development Workflow:

1. **Initialize**: `make claude-start`
2. **Start Services**: `make docker-hybrid`
3. **Develop**: Code with full MCP stack
4. **Test**: `make health-check`
5. **Deploy**: Use deployment commands

## 📖 Related Documentation

- **CLAUDE.md**: Main Claude Code integration guide
- **README.md**: Complete project overview
- **Makefile**: All available commands
- **docker-compose.hybrid.yml**: Service configuration

## 🎉 Success Indicators

A properly initialized session shows:
- ✅ All structure checks pass
- ✅ Documentation acknowledged
- ✅ Services verified
- ✅ Dependencies available
- ✅ Environment configured
- ✅ Session ID assigned

You're ready to use UltraMCP with Claude Code! 🚀
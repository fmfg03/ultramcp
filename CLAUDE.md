# UltraMCP + Claude Code Integration

This document provides optimized workflows for using UltraMCP Hybrid System with Claude Code to achieve maximum developer productivity.

## Quick Start Commands

The UltraMCP system is designed for terminal-first operation with Claude Code. Use these commands frequently:

### Core System Commands
```bash
# System management
make start           # Interactive startup menu
make status          # Check all services
make logs           # View system logs
make health-check   # Comprehensive health check

# Docker operations
make docker-hybrid  # Start optimized hybrid stack
make docker-dev     # Development mode with hot reload
make docker-logs    # View container logs
```

### AI Operations (80% Terminal-First)
```bash
# Quick AI chat (OpenAI API)
make chat TEXT="Explain quantum computing"

# Local AI chat (5 models available, fully offline)
make local-chat TEXT="Explain quantum computing"

# Enhanced Chain-of-Debate Protocol
make cod-local TOPIC="Should we invest in AI research?"      # 100% local debate
make cod-hybrid TOPIC="Architecture decision for X"         # Mix local + API
make cod-privacy TOPIC="Sensitive business decision"        # Privacy-first mode
make cod-cost-optimized TOPIC="Budget allocation strategy"   # Minimize API costs

# Quick development decisions (local only)
make dev-decision DECISION="React vs Vue for this component?"

# Web research with AI analysis
make research URL="https://anthropic.com"

# Data analysis with AI insights  
make analyze FILE="data/research/report.json"
```

### Enhanced Local LLM Operations (Offline AI)
```bash
# List available local models (5 models: Qwen 2.5 14B, Llama 3.1 8B, etc.)
make local-models

# Direct local model chat (zero cost, maximum privacy)
make local-chat TEXT="Write a Python function to sort data"

# Check local LLM system status
make local-status

# Download additional models
make local-pull MODEL="llama3.2"

# Remove unused models
make local-remove MODEL="old-model"

# Test local model performance
make test-cod-performance
```

# Download new models
make local-pull MODEL="codellama:7b"
```

### Web Automation (Playwright MCP)
```bash
# Web scraping
make web-scrape URL="https://news.ycombinator.com"

# Website testing
make test-site URL="https://example.com"

# Web monitoring
make web-monitor URL="https://api.example.com"
```

## Claude Code Productivity Tips

### 1. Use Terminal Commands for Speed
- **80% of tasks**: Use `make` commands directly in terminal
- **20% of complex workflows**: Use enhanced CoD Protocol for multi-LLM coordination
- **Local-first approach**: Prefer `make cod-local` and `make local-chat` for privacy and zero cost
- **Always prefer**: Terminal commands over complex orchestration

### 2. Efficient File Management
```bash
# View logs quickly
make logs | grep ERROR

# Search specific log entries  
make logs-search QUERY="debate"

# Tail live logs while developing
make logs-tail
```

### 3. Enhanced Development Workflow
```bash
# Start development environment
make docker-dev

# Test with local models (zero cost)
make local-chat TEXT="test my changes"

# Quick development decisions
make dev-decision DECISION="Should I refactor this function?"

# Local-only debates for architecture decisions
make cod-local TOPIC="Microservices vs monolith for this feature"

# Check system health
make health-check
```

### 4. Debugging Commands
```bash
# Check service status
make status

# Check local model availability
make local-status

# View container logs
make docker-logs

# Test local model performance
make test-cod-performance

# Check fallback systems
make fallback-status

# Interactive container access
docker exec -it ultramcp-terminal bash
docker exec -it ultramcp-cod-service bash
```

## API Keys Configuration

Set these environment variables in `.env`:

```bash
# Optional for API-based AI operations (local models work without these)
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=claude-your-key-here

# Note: Local models (make local-chat, make cod-local) work completely offline
# and require no API keys - perfect for privacy and zero cost operation

# Optional for enhanced features
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password
```

## Data Flow Architecture

### Terminal-First Approach (80%)
1. User runs `make local-chat` or `make web-scrape`
2. Script executes directly with minimal overhead
3. Local models process requests offline (zero cost, maximum privacy)
4. Results saved to `data/` directory
5. Logs written to `logs/combined.log`

### Enhanced Local CoD Protocol (Hybrid 20%)
1. User runs `make cod-local` (100% local) or `make cod-hybrid` (mixed)
2. Enhanced orchestrator coordinates multiple local models
3. Intelligent role assignment (CFO, CTO, Analyst, etc.)
4. Local models debate with API models when needed
5. Structured results with privacy scores and cost analysis

## File Structure for Claude Code

When working with Claude Code, focus on these key files:

### Scripts Directory (`/scripts/`)
- `common.sh` - Shared utilities and logging
- `simple-chat.sh` - Direct AI chat via API
- `local-llm-chat.sh` - Local model chat (offline, zero cost)
- `enhanced-cod-terminal.py` - Enhanced CoD Protocol with local models
- `cod-debate.sh` - Original multi-LLM debate
- `playwright-scrape.sh` - Web automation
- `web-research.sh` - Research pipeline
- `analyze-data.sh` - Data analysis with AI
- `implement-local-cod.py` - Local model setup script

### Data Directory (`/data/`)
- `local_cod_debates/` - Enhanced CoD Protocol results with local models
- `local_llm/` - Local model chat results
- `debates/` - Original CoD Protocol results
- `scrapes/` - Web scraping results  
- `research/` - Research reports
- `analysis/` - Data analysis results

### Configuration Files
- `Makefile` - Terminal command interface
- `docker-compose.hybrid.yml` - Optimized Docker stack
- `.env` - Environment configuration
- `requirements.txt` - Python dependencies

## Common Workflows

### 1. Research Workflow
```bash
# Step 1: Scrape content
make web-scrape URL="https://research-site.com"

# Step 2: Analyze with AI
make research URL="https://research-site.com"

# Step 3: Review results
cat data/research/task_*_research.json | jq .summary
```

### 2. Data Analysis Workflow
```bash
# Analyze any file type
make analyze FILE="data.csv"
make analyze FILE="report.json"
make analyze FILE="research.txt"

# View analysis results
make logs | grep "analysis"
```

### 3. Development Workflow
```bash
# Start hybrid system
make docker-hybrid

# Develop in terminal-first mode
make chat TEXT="help me debug this function"

# Test web automation
make web-scrape URL="https://test-site.com"

# Advanced coordination when needed
make debate TOPIC="architecture decision for X"
```

## Performance Optimization

### For Maximum Speed
1. Use `make chat` for quick AI interactions
2. Use `make web-scrape` for simple web data
3. Save `make debate` for complex decisions only

### For Development
1. Use `make docker-dev` for hot reload
2. Use `make logs-tail` to monitor changes
3. Use `make status` to check health

### For Production
1. Use `make docker-hybrid` for optimized stack
2. Use `make backup` for system snapshots
3. Use `make health-check` for monitoring

## Claude Code Best Practices

### 1. Command Patterns
- Always use `make` commands for consistency
- Check `make help` when unsure
- Use `make status` before troubleshooting

### 2. Error Handling
- All scripts include comprehensive error handling
- Check `logs/combined.log` for detailed errors
- Use recovery suggestions provided in error messages

### 3. Data Management
- Results auto-saved with task IDs
- Use `data/` directory for all outputs
- Clean old data with `make clean`

### 4. Service Integration
- CoD Protocol service auto-starts when needed
- Database and Redis auto-configured
- Docker containers auto-restart

## Troubleshooting

### Common Issues

**CoD Service Not Responding**
```bash
make status
make docker-logs
# Restart if needed
make docker-rebuild
```

**Missing Dependencies**
```bash
make setup
pip3 install -r requirements.txt
```

**API Key Issues**
```bash
# Check .env file
cat .env | grep API_KEY
# Update with valid keys
```

**Docker Issues**
```bash
make docker-clean
make docker-rebuild
```

## Integration Examples

### Example 1: Quick Research
```bash
# Claude Code prompt: "Research latest AI trends"
make research URL="https://arxiv.org/list/cs.AI/recent"
```

### Example 2: Data Analysis
```bash
# Claude Code prompt: "Analyze this CSV file"
make analyze FILE="sales_data.csv"
```

### Example 3: Complex Decision
```bash
# Claude Code prompt: "Help decide on architecture"
make debate TOPIC="Microservices vs Monolith for our use case"
```

This integration provides the perfect balance of terminal-first productivity (80%) with advanced AI orchestration capabilities (20%) when needed.
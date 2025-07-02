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
# Quick AI chat (bypasses complex orchestration)
make chat TEXT="Explain quantum computing"

# Advanced multi-LLM debate (uses 20% orchestration)
make debate TOPIC="Should we invest in AI research?"

# Web research with AI analysis
make research URL="https://anthropic.com"

# Data analysis with AI insights  
make analyze FILE="data/research/report.json"
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
- **20% of complex workflows**: Use CoD Protocol for multi-LLM coordination
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

### 3. Development Workflow
```bash
# Start development environment
make docker-dev

# Make changes to scripts...
# Test immediately
make chat TEXT="test my changes"

# Check system health
make health-check
```

### 4. Debugging Commands
```bash
# Check service status
make status

# View container logs
make docker-logs

# Interactive container access
docker exec -it ultramcp-terminal bash
docker exec -it ultramcp-cod-service bash
```

## API Keys Configuration

Set these environment variables in `.env`:

```bash
# Required for AI operations
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=claude-your-key-here

# Optional for enhanced features
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password
```

## Data Flow Architecture

### Terminal-First Approach (80%)
1. User runs `make chat` or `make web-scrape`
2. Script executes directly with minimal overhead
3. Results saved to `data/` directory
4. Logs written to `logs/combined.log`

### Advanced Orchestration (20%)
1. User runs `make debate` or `make research`
2. Script calls CoD Protocol service (port 8001)
3. Multi-LLM coordination for complex analysis
4. Structured results with confidence scores

## File Structure for Claude Code

When working with Claude Code, focus on these key files:

### Scripts Directory (`/scripts/`)
- `common.sh` - Shared utilities and logging
- `simple-chat.sh` - Direct AI chat (80% use case)
- `cod-debate.sh` - Multi-LLM debate (20% use case)
- `playwright-scrape.sh` - Web automation
- `web-research.sh` - Research pipeline
- `analyze-data.sh` - Data analysis with AI

### Data Directory (`/data/`)
- `debates/` - CoD Protocol results
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
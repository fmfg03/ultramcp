# =============================================================================
# UltraMCP Hybrid System - Terminal-First Approach
# =============================================================================

.PHONY: help logs setup clean status

# Default target
help:
	@echo "🚀 UltraMCP Hybrid System"
	@echo ""
	@echo "Core Commands:"
	@echo "  make setup           - Initialize system"
	@echo "  make status          - Check all services"
	@echo "  make logs           - View combined logs (last 100 lines)"
	@echo "  make logs-tail      - Follow live logs"
	@echo "  make clean          - Clean up processes and logs"
	@echo ""
	@echo "AI Operations:"
	@echo "  make chat TEXT='...'           - Simple LLM chat"
	@echo "  make debate TOPIC='...'        - Start CoD Protocol debate"
	@echo "  make research URL='...'        - Web research with Playwright"
	@echo "  make analyze FILE='...'        - Analyze document/data"
	@echo ""
	@echo "System Operations:"
	@echo "  make web-scrape URL='...'      - Scrape website"
	@echo "  make test-site URL='...'       - Test website with Playwright"
	@echo "  make health-check              - Comprehensive system health check"
	@echo "  make backup                    - Create system backup"
	@echo ""
	@echo "Risk Mitigation & Recovery:"
	@echo "  make backup-list               - List available backups"
	@echo "  make rollback SNAPSHOT='...'   - Create rollback plan"
	@echo "  make rollback-execute SNAPSHOT='...' - Execute rollback"
	@echo "  make rollback-dry-run SNAPSHOT='...' - Test rollback"
	@echo "  make fallback-status           - Check fallback systems"
	@echo "  make service-discovery         - Service registry status"
	@echo "  make register-services         - Register core services"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make docker-up                 - Start all Docker services"
	@echo "  make docker-dev                - Start development services"
	@echo "  make docker-down               - Stop all Docker services"  
	@echo "  make docker-logs               - View Docker container logs"
	@echo "  make docker-rebuild            - Rebuild and restart services"
	@echo ""
	@echo "Hybrid System:"
	@echo "  make start                     - Interactive startup menu"
	@echo ""
	@echo "Claude Code Integration:"
	@echo "  make claude-help               - Claude Code integration guide"
	@echo "  make claude-demo               - Run productivity demonstration"

# =============================================================================
# SYSTEM SETUP & MANAGEMENT
# =============================================================================

setup:
	@echo "🔧 Setting up UltraMCP Hybrid System..."
	@mkdir -p logs data/state data/backups scripts
	@mkdir -p data/scrapes data/debates data/monitoring
	@npm install
	@pip3 install -r requirements.txt
	@chmod +x scripts/*.sh
	@echo "✅ System ready"

status:
	@echo "📊 UltraMCP System Status"
	@echo "========================="
	@./scripts/system-status.sh

logs:
	@echo "📋 Last 100 log entries:"
	@tail -n 100 logs/combined.log 2>/dev/null | jq -r '. | "\(.timestamp) [\(.level)] \(.service): \(.message)"' 2>/dev/null || tail -n 100 logs/combined.log 2>/dev/null || echo "No logs found"

logs-tail:
	@echo "📋 Following live logs (Ctrl+C to exit):"
	@tail -f logs/combined.log | jq -r '. | "\(.timestamp) [\(.level)] \(.service): \(.message)"' 2>/dev/null || tail -f logs/combined.log

logs-search:
	@echo "🔍 Searching logs for: $(QUERY)"
	@grep -i "$(QUERY)" logs/combined.log 2>/dev/null | tail -n 50 | jq -r '. | "\(.timestamp) [\(.level)] \(.service): \(.message)"' 2>/dev/null || grep -i "$(QUERY)" logs/combined.log 2>/dev/null | tail -n 50 || echo "No matches found"

clean:
	@echo "🧹 Cleaning up..."
	@pkill -f "ultramcp" 2>/dev/null || true
	@pkill -f "cod-service" 2>/dev/null || true
	@rm -f logs/*.log
	@echo "✅ Cleanup complete"

# =============================================================================
# AI OPERATIONS
# =============================================================================

chat:
	@echo "💬 Starting chat session..."
	@./scripts/simple-chat.sh "$(TEXT)"

debate:
	@echo "🎭 Starting CoD Protocol debate on: $(TOPIC)"
	@./scripts/cod-debate.sh "$(TOPIC)"

research:
	@echo "🔍 Researching: $(URL)"
	@./scripts/web-research.sh "$(URL)"

analyze:
	@echo "🧠 Analyzing: $(FILE)"
	@./scripts/analyze-data.sh "$(FILE)"

# =============================================================================
# WEB OPERATIONS (via Playwright MCP)
# =============================================================================

web-scrape:
	@echo "🕷️ Scraping: $(URL)"
	@./scripts/playwright-scrape.sh "$(URL)"

test-site:
	@echo "🧪 Testing site: $(URL)"
	@./scripts/playwright-test.sh "$(URL)"

web-monitor:
	@echo "👀 Monitoring: $(URL)"
	@./scripts/web-monitor.sh "$(URL)"

# =============================================================================
# SYSTEM OPERATIONS
# =============================================================================

health-check:
	@echo "🏥 Running health check..."
	@./scripts/health-check.sh

backup:
	@echo "💾 Creating system backup..."
	@python3 scripts/rollback-manager.py --backup "Manual backup $(shell date '+%Y-%m-%d %H:%M')"

backup-list:
	@echo "📋 Available backups:"
	@python3 scripts/rollback-manager.py --list-backups

rollback:
	@echo "🔄 Creating rollback plan for: $(SNAPSHOT)"
	@python3 scripts/rollback-manager.py --plan "$(SNAPSHOT)"

rollback-execute:
	@echo "⚠️  Executing rollback to: $(SNAPSHOT)"
	@python3 scripts/rollback-manager.py --rollback "$(SNAPSHOT)"

rollback-dry-run:
	@echo "🧪 Dry run rollback to: $(SNAPSHOT)"
	@python3 scripts/rollback-manager.py --rollback "$(SNAPSHOT)" --dry-run

fallback-status:
	@echo "🛡️ Fallback systems status:"
	@python3 scripts/fallback-manager.py --health

service-discovery:
	@echo "🔍 Service discovery status:"
	@python3 scripts/service-discovery.py --status

register-services:
	@echo "📝 Registering core services..."
	@python3 scripts/service-discovery.py --register-core

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev-start:
	@echo "🚀 Starting development environment..."
	@npm run dev &
	@python3 scripts/cod-service.py --dev &
	@echo "✅ Development environment started"

dev-stop:
	@echo "🛑 Stopping development environment..."
	@pkill -f "npm run dev" 2>/dev/null || true
	@pkill -f "cod-service.py" 2>/dev/null || true
	@echo "✅ Development environment stopped"

# =============================================================================
# DOCKER OPERATIONS
# =============================================================================

docker-build:
	@echo "🐳 Building Docker containers..."
	@docker-compose build

docker-up:
	@echo "🚀 Starting Docker containers..."
	@docker-compose up -d

docker-down:
	@echo "🛑 Stopping Docker containers..."
	@docker-compose down

docker-logs:
	@echo "📋 Docker container logs:"
	@docker-compose logs -f

docker-dev:
	@echo "🔧 Starting development Docker stack..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

docker-hybrid:
	@echo "🎯 Starting UltraMCP Hybrid stack (optimized)..."
	@docker-compose -f docker-compose.hybrid.yml up -d

docker-rebuild:
	@echo "🔄 Rebuilding and restarting Docker services..."
	@docker-compose down
	@docker-compose build --no-cache
	@docker-compose up -d

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	@docker-compose down -v
	@docker system prune -f

# =============================================================================
# HYBRID SYSTEM STARTUP
# =============================================================================

start:
	@echo "🚀 UltraMCP Hybrid System Startup"
	@./scripts/hybrid-startup.sh

# =============================================================================
# CLAUDE CODE INTEGRATION
# =============================================================================

claude-demo:
	@echo "🤖 Running Claude Code integration demo..."
	@./scripts/claude-code-demo.sh

claude-help:
	@echo "💡 Claude Code Integration Help"
	@echo "==============================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make start                     - Interactive system startup"
	@echo "  make claude-demo               - Run productivity demonstration"
	@echo ""
	@echo "Terminal-First Commands (80%):"
	@echo "  make chat TEXT='question'      - Quick AI chat"
	@echo "  make web-scrape URL='...'      - Web scraping"
	@echo "  make status                    - System status"
	@echo ""
	@echo "Advanced Orchestration (20%):"
	@echo "  make debate TOPIC='...'        - Multi-LLM debate"
	@echo "  make research URL='...'        - Web research + AI"
	@echo "  make analyze FILE='...'        - Data analysis"
	@echo ""
	@echo "Development:"
	@echo "  make docker-hybrid             - Optimized stack"
	@echo "  make docker-dev                - Development mode"
	@echo "  make logs-tail                 - Live logs"
	@echo ""
	@echo "📖 Full documentation: cat CLAUDE.md"

claude-setup:
	@echo "🤖 Setting up Claude Code integration..."
	@./scripts/claude-code-setup.sh

claude-test:
	@echo "🧪 Testing Claude Code integration..."
	@make health-check
	@make chat TEXT="Hello from UltraMCP Hybrid System!"
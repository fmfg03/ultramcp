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
	@echo "  make chat TEXT='...'           - Simple LLM chat (OpenAI API)"
	@echo "  make local-chat TEXT='...'     - Local LLM chat (Ollama models)"
	@echo "  make debate TOPIC='...'        - Start CoD Protocol debate"
	@echo "  make research URL='...'        - Web research with Playwright"
	@echo "  make analyze FILE='...'        - Analyze document/data"
	@echo ""
	@echo "🎛️ Control Tower UI:"
	@echo "  make control-tower             - Launch full Control Tower UI"
	@echo "  make control-tower-status      - Check Control Tower status"
	@echo ""
	@echo "Local LLM Operations:"
	@echo "  make local-models              - List available local models (5 models ready)"
	@echo "  make local-pull MODEL='...'    - Download new local model"
	@echo "  make local-remove MODEL='...'  - Remove local model"
	@echo "  make local-status              - Check local LLM system status"
	@echo ""
	@echo "🔍 Code Intelligence (Blockoli):"
	@echo "  make index-project PROJECT='...' NAME='...' - Index project for semantic search"
	@echo "  make code-search QUERY='...' PROJECT='...'  - Semantic code search"
	@echo "  make code-debate TOPIC='...' PROJECT='...'  - Code-intelligent AI debate"
	@echo "  make architecture-analysis FOCUS='...' PROJECT='...' - Architecture analysis"
	@echo "  make pattern-analysis PATTERN='...' PROJECT='...'    - Code pattern analysis"
	@echo "  make intelligent-code-review FILE='...' PROJECT='...' - AI code review"
	@echo "  make setup-code-intelligence   - Setup and test code intelligence"
	@echo ""
	@echo "System Operations:"
	@echo "  make web-scrape URL='...'      - Scrape website"
	@echo "  make test-site URL='...'       - Test website with Playwright"
	@echo "  make health-check              - Comprehensive system health check"
	@echo "  make verify-integration        - Verify all services are integrated (no loose components)"
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
# LOCAL LLM OPERATIONS
# =============================================================================

local-chat:
	@echo "🤖 Starting local LLM chat..."
	@./scripts/local-llm-chat.sh "$(TEXT)"

local-models:
	@echo "📋 Available local models:"
	@ollama list

local-pull:
	@echo "📥 Downloading model: $(MODEL)"
	@ollama pull "$(MODEL)"

local-remove:
	@echo "🗑️ Removing model: $(MODEL)"
	@ollama rm "$(MODEL)"

local-status:
	@echo "🔍 Local LLM system status:"
	@ollama ps

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

verify-integration:
	@echo "🔍 Verifying complete service integration..."
	@./scripts/verify-integration.sh

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

# =============================================================================
# CONTROL TOWER UI
# =============================================================================

control-tower:
	@echo "🎛️ Starting UltraMCP Control Tower..."
	@./scripts/launch-control-tower.sh

control-tower-backend:
	@echo "🔧 Starting Control Tower WebSocket Server..."
	@cd services/control-tower && npm install --silent && npm start

control-tower-frontend:
	@echo "🎨 Starting Control Tower UI..."
	@cd apps/frontend && npm run dev -- --port 5173

control-tower-build:
	@echo "🏗️ Building Control Tower UI..."
	@cd services/control-tower && npm install --silent
	@cd apps/frontend && npm run build

control-tower-status:
	@echo "📊 Control Tower Status:"
	@curl -s http://localhost:8001/api/status 2>/dev/null | jq . || echo "❌ Control Tower backend not running"
	@curl -s http://localhost:5173 >/dev/null 2>&1 && echo "✅ Frontend running on http://localhost:5173" || echo "❌ Frontend not running"
	@make chat TEXT="Hello from UltraMCP Hybrid System!"
# =============================================================================
# ENHANCED COD PROTOCOL WITH LOCAL LLMS
# =============================================================================

# Local model CoD debates
cod-local:
	@echo "🎭 Starting LOCAL-ONLY CoD debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=local_only

cod-hybrid:
	@echo "🎭 Starting HYBRID CoD debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=hybrid

cod-privacy:
	@echo "🔒 Starting PRIVACY-FIRST debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=privacy_first

cod-cost-optimized:
	@echo "💰 Starting COST-OPTIMIZED debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=cost_optimized

# Quick local debates for development
dev-decision:
	@echo "🚀 Quick development decision..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(DECISION)" --mode=local_only --rounds=2

# Claude Code integration
claude-debate:
	@echo "🤖 Claude Code CoD integration..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=hybrid --verbose

# Model performance testing
test-cod-performance:
	@echo "📊 Testing CoD performance with local models..."
	@python3 scripts/enhanced-cod-terminal.py --topic="Test performance and response quality" --mode=local_only --rounds=1

# =============================================================================
# SECURITY COMMANDS - ASTERISK MCP INTEGRATION
# =============================================================================

# Run comprehensive security scan
security-scan:
	@echo "🛡️ Running comprehensive security scan..."
	@python3 services/asterisk-mcp/asterisk_security_client.py --scan-type=codebase --path=.

# Secure code review with multi-layer analysis
secure-code-review FILE:
	@echo "🔍 Secure code review pipeline for $(FILE)..."
	@echo "1. Security vulnerability scanning..."
	@python3 services/asterisk-mcp/asterisk_security_client.py --scan-type=snippet --file="$(FILE)"
	@echo "2. AI-powered security analysis..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=secure_code_review --file="$(FILE)"
	@echo "3. Generating security report..."

# Security-focused CoD Protocol debates
security-debate TOPIC:
	@echo "🔒 Security-focused debate: $(TOPIC)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=security_first --topic="$(TOPIC)" \
		--participants="asterisk:security,deepclaude:analyst,local:qwen2.5:14b,local:deepseek-coder:6.7b"

# Vulnerability analysis debate
vulnerability-analysis FILE:
	@echo "🔍 Vulnerability analysis debate for $(FILE)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=vulnerability_analysis --file="$(FILE)"

# Threat modeling session
threat-modeling SCOPE:
	@echo "🎯 Threat modeling session for $(SCOPE)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=threat_modeling --scope="$(SCOPE)"

# Compliance analysis
compliance-check STANDARD:
	@echo "📋 Compliance check for $(STANDARD)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=compliance_review --standard="$(STANDARD)"

# Secure development workflow
secure-dev-workflow:
	@echo "🛡️ Secure Development Workflow..."
	@echo "1. Running security scan..."
	@make security-scan
	@echo "2. Security posture assessment..."
	@make security-debate TOPIC="Overall codebase security posture"
	@echo "3. Generating security report..."
	@make generate-security-report

# Real-time security monitoring
security-monitor:
	@echo "👁️ Starting real-time security monitoring..."
	@python3 scripts/security-monitor.py --watch=. --continuous=true

# Security health check
security-health-check:
	@echo "🏥 Security health check..."
	@python3 services/asterisk-mcp/asterisk_security_client.py --health-check --path=.

# Generate comprehensive security report
generate-security-report:
	@echo "📊 Generating security report..."
	@python3 scripts/generate-security-report.py --output=data/security_reports/

# Security incident response
security-incident-response INCIDENT:
	@echo "🚨 Security incident response for: $(INCIDENT)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=incident_response --incident="$(INCIDENT)"

# =============================================================================
# SECURE AI DEVELOPMENT COMMANDS
# =============================================================================

# Secure code generation with AI
secure-code-gen REQUIREMENT:
	@echo "🤖 Secure code generation: $(REQUIREMENT)..."
	@echo "1. Generating code with security considerations..."
	@make local-chat TEXT="Generate secure code for: $(REQUIREMENT). Include security best practices, input validation, and error handling."
	@echo "2. Security scanning generated code..."
	@make security-scan
	@echo "3. Security review if needed..."

# AI-powered security training
security-training TOPIC:
	@echo "🎓 AI-powered security training: $(TOPIC)..."
	@make cod-local TOPIC="Security training session: $(TOPIC). Provide comprehensive security education with practical examples."

# Secure architecture review
secure-architecture-review COMPONENT:
	@echo "🏗️ Secure architecture review for $(COMPONENT)..."
	@make security-debate TOPIC="Architecture security review for $(COMPONENT)"

# =============================================================================
# ENTERPRISE SECURITY COMMANDS
# =============================================================================

# SOC2 compliance assessment
soc2-compliance:
	@echo "📋 SOC2 compliance assessment..."
	@make compliance-check STANDARD="SOC2"

# GDPR compliance assessment  
gdpr-compliance:
	@echo "🇪🇺 GDPR compliance assessment..."
	@make compliance-check STANDARD="GDPR"

# ISO27001 compliance assessment
iso27001-compliance:
	@echo "🌐 ISO27001 compliance assessment..."
	@make compliance-check STANDARD="ISO27001"

# HIPAA compliance assessment
hipaa-compliance:
	@echo "🏥 HIPAA compliance assessment..."
	@make compliance-check STANDARD="HIPAA"

# PCI DSS compliance assessment
pci-compliance:
	@echo "💳 PCI DSS compliance assessment..."
	@make compliance-check STANDARD="PCI_DSS"

# Comprehensive compliance audit
compliance-audit:
	@echo "📋 Comprehensive compliance audit..."
	@make soc2-compliance
	@make gdpr-compliance
	@make iso27001-compliance
	@echo "Compliance audit complete. Check data/compliance_reports/"

# =============================================================================
# SECURITY MONITORING & ALERTING
# =============================================================================

# Security dashboard (Claudia integration)
security-dashboard:
	@echo "📊 Opening security dashboard..."
	@echo "Security dashboard available at: http://localhost:3000/security"
	@echo "Use Claudia interface for visual security management"

# Security metrics collection
security-metrics:
	@echo "📈 Collecting security metrics..."
	@python3 scripts/collect-security-metrics.py

# Security alerting setup
security-alerts:
	@echo "🚨 Setting up security alerts..."
	@python3 scripts/setup-security-alerts.py

# Security backup and recovery
security-backup:
	@echo "💾 Security backup..."
	@python3 scripts/security-backup.py

# =============================================================================
# BLOCKOLI CODE INTELLIGENCE COMMANDS
# =============================================================================

# Index project for semantic search
index-project:
	@echo "🔍 Indexing project $(PROJECT) as $(NAME)..."
	@python3 services/blockoli-mcp/blockoli_client.py index "$(PROJECT)" "$(NAME)"

# Semantic code search
code-search:
	@echo "🔍 Semantic search: $(QUERY) in $(PROJECT)"
	@python3 services/blockoli-mcp/blockoli_client.py search "$(QUERY)" "$(PROJECT)"

# Code-intelligent debates
code-debate:
	@echo "🧠 Code-intelligent debate: $(TOPIC)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="$(TOPIC)" --project="$(PROJECT)" --mode=basic

# Architecture analysis with AI
architecture-analysis:
	@echo "🏗️ Architecture analysis: $(FOCUS) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Architecture analysis: $(FOCUS)" --project="$(PROJECT)" --mode=architecture_focused

# Security analysis with code context
code-security-analysis:
	@echo "🛡️ Security analysis: $(TOPIC) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Security analysis: $(TOPIC)" --project="$(PROJECT)" --mode=security_focused

# Code pattern analysis
pattern-analysis:
	@echo "🔍 Pattern analysis: $(PATTERN) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Pattern analysis: $(PATTERN)" --project="$(PROJECT)" --mode=pattern_analysis

# Intelligent code review
intelligent-code-review:
	@echo "🧠 Intelligent code review for $(FILE)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Code review for $(FILE)" --project="$(PROJECT)" --query="$(FILE)" --mode=deep_analysis

# Code similarity analysis
similarity-analysis:
	@echo "🔗 Similarity analysis: $(FUNCTION) in $(PROJECT)"
	@python3 services/blockoli-mcp/blockoli_client.py search "$(FUNCTION)" "$(PROJECT)"

# Refactoring analysis with code intelligence
refactoring-analysis:
	@echo "🔄 Refactoring analysis: $(TOPIC) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Refactoring analysis: $(TOPIC)" --project="$(PROJECT)" --mode=refactoring_focused

# Deep code context analysis
deep-code-analysis:
	@echo "🔬 Deep code analysis: $(TOPIC) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="$(TOPIC)" --project="$(PROJECT)" --mode=deep_analysis

# Blockoli health check
blockoli-health:
	@echo "🏥 Blockoli service health check..."
	@python3 services/blockoli-mcp/blockoli_client.py health

# List indexed projects
list-indexed-projects:
	@echo "📋 Listing indexed projects..."
	@curl -s http://localhost:8080/projects 2>/dev/null | jq . || echo "Blockoli service not available"

# Project statistics
project-stats:
	@echo "📊 Project statistics for $(PROJECT)..."
	@curl -s http://localhost:8080/projects/$(PROJECT)/stats 2>/dev/null | jq . || echo "Project not found or Blockoli service not available"

# =============================================================================
# ENHANCED AI DEVELOPMENT WITH CODE INTELLIGENCE
# =============================================================================

# Combined security + code intelligence
secure-code-intelligence:
	@echo "🛡️ Secure code intelligence analysis..."
	@echo "1. Running security scan..."
	@make security-scan
	@echo "2. Code intelligence security analysis..."
	@make code-security-analysis TOPIC="$(TOPIC)" PROJECT="$(PROJECT)"
	@echo "3. Combined analysis complete"

# Development workflow with code intelligence
dev-workflow-intelligent:
	@echo "🚀 Intelligent development workflow..."
	@echo "1. Indexing current project..."
	@make index-project PROJECT="." NAME="current_project"
	@echo "2. Running code health check..."
	@make health-check
	@echo "3. Code pattern analysis..."
	@make pattern-analysis PATTERN="$(PATTERN)" PROJECT="current_project"
	@echo "4. Development workflow complete"

# AI-powered code review workflow
ai-code-review-workflow:
	@echo "🤖 AI-powered code review workflow..."
	@echo "1. Security scan..."
	@make security-scan
	@echo "2. Intelligent code review..."
	@make intelligent-code-review FILE="$(FILE)" PROJECT="$(PROJECT)"
	@echo "3. Pattern analysis..."
	@make pattern-analysis PATTERN="code quality" PROJECT="$(PROJECT)"
	@echo "4. AI code review complete"

# Complete code intelligence setup
setup-code-intelligence:
	@echo "🔧 Setting up code intelligence..."
	@echo "1. Checking Blockoli service..."
	@make blockoli-health
	@echo "2. Indexing current project..."
	@make index-project PROJECT="." NAME="ultramcp"
	@echo "3. Testing code search..."
	@make code-search QUERY="authentication" PROJECT="ultramcp"
	@echo "✅ Code intelligence setup complete"

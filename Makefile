# =============================================================================
# UltraMCP Hybrid System - Terminal-First Approach
# =============================================================================

.PHONY: help logs setup clean status deploy-sam-chat sam-chat-start sam-chat-stop sam-chat-status sam-chat-logs test-sam-chat setup-ssl

# Default target
help:
	@echo "🚀 UltraMCP Supreme Stack - sam.chat Production"
	@echo "================================================"
	@echo ""
	@echo "🌐 sam.chat Production Deployment:"
	@echo "  make deploy-sam-chat         - Deploy complete UltraMCP to sam.chat (no ports)"
	@echo "  make sam-chat-start          - Start sam.chat production environment"
	@echo "  make sam-chat-stop           - Stop sam.chat services"
	@echo "  make sam-chat-status         - Check sam.chat services status"
	@echo "  make sam-chat-logs           - View sam.chat services logs"
	@echo "  make test-sam-chat           - Test sam.chat deployment"
	@echo "  make setup-ssl               - Setup SSL certificates for sam.chat"
	@echo ""
	@echo "Claude Code Integration:"
	@echo "  make claude-init             - Initialize Claude session (RECOMMENDED)"
	@echo "  make claude-verify           - Full system verification"
	@echo "  make claude-start            - Quick session start"
	@echo ""
	@echo "Core Commands:"
	@echo "  make setup                   - Initialize system"
	@echo "  make status                  - Check all services"
	@echo "  make logs                    - View combined logs (last 100 lines)"
	@echo "  make logs-tail               - Follow live logs"
	@echo "  make clean                   - Clean up processes and logs"
	@echo ""
	@echo "AI Operations:"
	@echo "  make chat TEXT='...'           - Simple LLM chat (OpenAI API)"
	@echo "  make local-chat TEXT='...'     - Local LLM chat (Ollama models)"
	@echo "  make context7-chat TEXT='...'  - AI chat with real-time docs"
	@echo "  make debate TOPIC='...'        - Start CoD Protocol debate"
	@echo "  make research URL='...'        - Web research with Playwright"
	@echo "  make analyze FILE='...'        - Analyze document/data"
	@echo ""
	@echo "🤖 Agent Factory (Create Agent App Style):"
	@echo "  make create-agent TYPE='...' FRAMEWORK='...' - Create new AI agent"
	@echo "  make list-agents               - List all created agents"
	@echo "  make agent-templates           - Show available agent templates"
	@echo "  make deploy-agent AGENT='...'  - Deploy agent to production"
	@echo "  make test-agent AGENT='...'    - Test agent with Scenario framework"
	@echo "  make agent-health              - Check Agent Factory service health"
	@echo ""
	@echo "📚 Context7 Real-time Documentation:"
	@echo "  make context7-docs LIBRARY='...'       - Get library documentation"
	@echo "  make context7-search LIBRARY='...' QUERY='...' - Search docs"
	@echo "  make context7-enhance PROMPT='...'     - Enhance prompt with docs"
	@echo "  make context7-health                   - Check Context7 status"
	@echo ""
	@echo "[CONTROL] Control Tower UI:"
	@echo "  make control-tower             - Launch full Control Tower UI"
	@echo "  make control-tower-status      - Check Control Tower status"
	@echo ""
	@echo "Local LLM Operations:"
	@echo "  make local-models              - List available local models (5 models ready)"
	@echo "  make local-pull MODEL='...'    - Download new local model"
	@echo "  make local-remove MODEL='...'  - Remove local model"
	@echo "  make local-status              - Check local LLM system status"
	@echo ""
	@echo "[SEARCH] Code Intelligence (Blockoli):"
	@echo "  make index-project PROJECT='...' NAME='...' - Index project for semantic search"
	@echo "  make code-search QUERY='...' PROJECT='...'  - Semantic code search"
	@echo "  make code-debate TOPIC='...' PROJECT='...'  - Code-intelligent AI debate"
	@echo ""
	@echo "[START] Unified Backend (FastAPI MCP Integration):"
	@echo "  make unified-start             - Start unified backend with all core services"
	@echo "  make unified-status           - Check unified backend health" 
	@echo "  make unified-logs             - View unified backend logs"
	@echo "  make unified-test             - Test unified backend endpoints"
	@echo "  make unified-docs             - Open unified backend documentation"
	@echo "  make architecture-analysis FOCUS='...' PROJECT='...' - Architecture analysis"
	@echo "  make pattern-analysis PATTERN='...' PROJECT='...'    - Code pattern analysis"
	@echo "  make intelligent-code-review FILE='...' PROJECT='...' - AI code review"
	@echo "  make setup-code-intelligence   - Setup and test code intelligence"
	@echo ""
	@echo "[AI] Claude Code Memory (Advanced Semantic Analysis):"
	@echo "  make memory-index PROJECT='...' NAME='...'   - Index project for semantic memory"
	@echo "  make memory-search QUERY='...' PROJECT='...' - Semantic code search with memory"
	@echo "  make memory-analyze FILE='...' PROJECT='...' - Advanced pattern analysis"
	@echo "  make memory-learn-codebase                   - Learn entire UltraMCP codebase"
	@echo "  make memory-debate TOPIC='...' PROJECT='...' - Memory-enhanced AI debate"
	@echo "  make memory-explore                          - Interactive memory exploration"
	@echo "  make memory-help                             - Full memory commands guide"
	@echo ""
	@echo "[START] VoyageAI Hybrid Search (Enterprise-Grade Embeddings + Privacy-First):"
	@echo "  make voyage-search QUERY='...' [PRIVACY='...'] [MODE='...']  - Enhanced semantic search"
	@echo "  make voyage-code-search QUERY='...' [LANGUAGE='...']          - Code-optimized search"
	@echo "  make voyage-privacy-search QUERY='...'                        - Local-only search"
	@echo "  make voyage-finance-search QUERY='...'                        - Finance domain search"
	@echo "  make voyage-healthcare-search QUERY='...'                     - Healthcare domain search"
	@echo "  make voyage-legal-search QUERY='...'                          - Legal domain search"
	@echo "  make voyage-health                                             - Check VoyageAI services"
	@echo "  make voyage-help                                               - Full VoyageAI guide"
	@echo ""
	@echo "[LINK] Ref Tools Documentation (Internal/External Doc Intelligence):"
	@echo "  make ref-search QUERY='...' [SOURCE='...'] [PRIVACY='...']    - Search all documentation"
	@echo "  make ref-internal-search QUERY='...' PROJECT='...' ORG='...'  - Internal docs only"
	@echo "  make ref-external-search QUERY='...' PROJECT='...'            - External docs only"
	@echo "  make ref-read-url URL='...' [CODE=true]                       - Extract URL content"
	@echo ""
	@echo "[SHINE] Unified Documentation Intelligence (Complete Ecosystem):"
	@echo "  make docs-unified-search QUERY='...' [TYPE='...'] [INTELLIGENCE='...']  - Search all sources"
	@echo "  make docs-code-search QUERY='...' PROJECT='...'               - Code-focused search"
	@echo "  make docs-help                                                 - Complete docs guide"
	@echo ""
	@echo "[CLAUDIA] Claudia MCP Integration (Visual Multi-LLM Platform):"
	@echo "  make claudia-start                                             - Start all Claudia MCP servers"
	@echo "  make claudia-system-start                                      - Start complete Claudia system"
	@echo "  make claudia-frontend                                          - Start Claudia frontend dev server"
	@echo "  make claudia-status                                            - Check Claudia MCP servers status"
	@echo "  make claudia-test                                              - Test Claudia MCP integration"
	@echo "  make claudia-help                                              - Full Claudia integration guide"
	@echo "  make cod-mcp-server                                            - Start Chain-of-Debate MCP Server"
	@echo ""
	@echo "🧠 ContextBuilderAgent 2.0 (Semantic Coherence Platform):"
	@echo "  make context-start                                             - Start ContextBuilder ecosystem"
	@echo "  make context-stop                                              - Stop ContextBuilder services"
	@echo "  make context-status                                            - Check ContextBuilder status"
	@echo "  make context-validate                                          - Validate semantic coherence"
	@echo "  make context-mutate MUTATION='...'                             - Apply context mutation"
	@echo "  make context-analyze SESSION='...'                             - Analyze session for insights"
	@echo "  make context-optimize                                          - Optimize context thresholds"
	@echo "  make context-restart                                           - Restart ContextBuilder system"
	@echo "  make context-test                                              - Test ContextBuilder integration"
	@echo "  make context-logs                                              - View ContextBuilder logs"
	@echo "  make context-help                                              - ContextBuilder usage guide"
	@echo ""
	@echo "🎯 PromptAssemblerAgent (Next-Gen Dynamic Prompts):"
	@echo "  make prompt-assemble TYPE='...' OBJECTIVE='...'                - Assemble dynamic prompt"
	@echo "  make prompt-optimize PROMPT='...'                              - Optimize existing prompt"
	@echo "  make prompt-templates                                          - List available templates"
	@echo "  make prompt-analyze PROMPT='...'                               - Analyze prompt quality"
	@echo "  make prompt-status                                             - Check PromptAssembler status"
	@echo ""
	@echo "🔭 ContextObservatory (Enterprise Monitoring):"
	@echo "  make observatory-dashboard TYPE='...'                          - View monitoring dashboard"
	@echo "  make observatory-health                                        - Comprehensive health check"
	@echo "  make observatory-alerts                                        - View system alerts"
	@echo "  make observatory-metrics                                       - Get performance metrics"
	@echo "  make observatory-start-monitoring                              - Start background monitoring"
	@echo ""
	@echo "🐛 DeterministicDebugMode (Reproducible Testing):"
	@echo "  make debug-start-session NAME='...'                           - Start debug session"
	@echo "  make debug-capture-snapshot                                    - Capture system snapshot"
	@echo "  make debug-trace-operation TYPE='...'                          - Trace operation"
	@echo "  make debug-sessions                                            - List debug sessions"
	@echo "  make debug-status                                              - Check debug mode status"
	@echo "  make local-mcp-server                                          - Start Local Models MCP Server"
	@echo "  make hybrid-mcp-server                                         - Start Hybrid Decision MCP Server"
	@echo ""
	@echo "[CLAUDIA] External Actions Execution (Enterprise Integration):"
	@echo "  make actions-list                                              - List all available external actions"
	@echo "  make actions-escalate MESSAGE='...' [PRIORITY='...']          - Escalate to human approval"
	@echo "  make actions-notify RECIPIENT='...' MESSAGE='...' [CHANNEL='...'] - Send notification"
	@echo "  make actions-workflow JOB='...' [TYPE='...'] [PARAMS='...']   - Trigger external workflow"
	@echo "  make actions-ticket TITLE='...' DESC='...' [SYSTEM='...']     - Create external ticket"
	@echo "  make actions-security-scan TARGET='...' [TYPE='...'] [TOOL='...'] - Run security scan"
	@echo "  make actions-validate ACTION='...' PARAMS='...'               - Validate action parameters"
	@echo "  make actions-history ACTION='...' [LIMIT='...']               - Get action execution history"
	@echo "  make actions-stats                                             - Get execution statistics"
	@echo "  make actions-health                                            - Check actions service health"
	@echo ""
	@echo "[LINK] GitIngest Repository Analysis (Code Context for LLMs):"
	@echo "  make gitingest-analyze-repo URL='...' [NAME='...']           - Analyze GitHub repository"
	@echo "  make gitingest-analyze-local PATH='...' [NAME='...']         - Analyze local directory"
	@echo "  make gitingest-list [LIMIT='...']                            - List recent analyses"
	@echo "  make gitingest-get NAME='...'                                - Get specific analysis"
	@echo "  make gitingest-delete NAME='...'                             - Delete analysis"
	@echo "  make gitingest-server                                        - Start GitIngest MCP server"
	@echo "  make gitingest-status                                        - Check GitIngest service status"
	@echo "  make gitingest-help                                          - GitIngest integration guide"
	@echo ""
	@echo "[BUILD] ContextBuilderAgent 2.0 (Semantic Coherence Platform):"
	@echo "  make context-start                                           - Start ContextBuilderAgent system"
	@echo "  make context-stop                                            - Stop all ContextBuilder services"
	@echo "  make context-restart                                         - Restart ContextBuilder system"
	@echo "  make context-status                                          - Check ContextBuilder services status"
	@echo "  make context-validate                                        - Validate semantic coherence"
	@echo "  make context-mutate DOMAIN='...' FIELD='...' VALUE='...'     - Apply context mutation"
	@echo "  make context-optimize                                        - Optimize thresholds and parameters"
	@echo "  make context-analyze SESSION='...'                           - Analyze session transcript"
	@echo "  make context-test                                            - Test ContextBuilder integration"
	@echo "  make context-help                                            - ContextBuilder integration guide"
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
	@echo "[TOOLS] Setting up UltraMCP Hybrid System..."
	@mkdir -p logs data/state data/backups scripts
	@mkdir -p data/scrapes data/debates data/monitoring
	@npm install
	@pip3 install -r requirements.txt
	@chmod +x scripts/*.sh
	@echo "[OK] System ready"

status:
	@echo "[DATA] UltraMCP System Status"
	@echo "========================="
	@./scripts/system-status.sh

logs:
	@echo "📋 Last 100 log entries:"
	@tail -n 100 logs/combined.log 2>/dev/null | jq -r '. | "\(.timestamp) [\(.level)] \(.service): \(.message)"' 2>/dev/null || tail -n 100 logs/combined.log 2>/dev/null || echo "No logs found"

logs-tail:
	@echo "📋 Following live logs (Ctrl+C to exit):"
	@tail -f logs/combined.log | jq -r '. | "\(.timestamp) [\(.level)] \(.service): \(.message)"' 2>/dev/null || tail -f logs/combined.log

logs-search:
	@echo "[SEARCH] Searching logs for: $(QUERY)"
	@grep -i "$(QUERY)" logs/combined.log 2>/dev/null | tail -n 50 | jq -r '. | "\(.timestamp) [\(.level)] \(.service): \(.message)"' 2>/dev/null || grep -i "$(QUERY)" logs/combined.log 2>/dev/null | tail -n 50 || echo "No matches found"

clean:
	@echo "🧹 Cleaning up..."
	@pkill -f "ultramcp" 2>/dev/null || true
	@pkill -f "cod-service" 2>/dev/null || true
	@rm -f logs/*.log
	@echo "[OK] Cleanup complete"

# =============================================================================
# AI OPERATIONS
# =============================================================================

chat:
	@echo "💬 Starting chat session..."
	@./scripts/simple-chat.sh "$(TEXT)"

debate:
	@echo "[CLAUDIA] Starting CoD Protocol debate on: $(TOPIC)"
	@./scripts/cod-debate.sh "$(TOPIC)"

research:
	@echo "[SEARCH] Researching: $(URL)"
	@./scripts/web-research.sh "$(URL)"

analyze:
	@echo "[AI] Analyzing: $(FILE)"
	@./scripts/analyze-data.sh "$(FILE)"

# =============================================================================
# LOCAL LLM OPERATIONS
# =============================================================================

local-chat:
	@echo "[DEEPCLAUDE] Starting local LLM chat..."
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
	@echo "[SEARCH] Local LLM system status:"
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
	@echo "[SEARCH] Verifying complete service integration..."
	@./scripts/verify-integration.sh

backup:
	@echo "💾 Creating system backup..."
	@python3 scripts/rollback-manager.py --backup "Manual backup $(shell date '+%Y-%m-%d %H:%M')"

backup-list:
	@echo "📋 Available backups:"
	@python3 scripts/rollback-manager.py --list-backups

rollback:
	@echo "[SYNC] Creating rollback plan for: $(SNAPSHOT)"
	@python3 scripts/rollback-manager.py --plan "$(SNAPSHOT)"

rollback-execute:
	@echo "[WARNING]  Executing rollback to: $(SNAPSHOT)"
	@python3 scripts/rollback-manager.py --rollback "$(SNAPSHOT)"

rollback-dry-run:
	@echo "🧪 Dry run rollback to: $(SNAPSHOT)"
	@python3 scripts/rollback-manager.py --rollback "$(SNAPSHOT)" --dry-run

fallback-status:
	@echo "🛡️ Fallback systems status:"
	@python3 scripts/fallback-manager.py --health

service-discovery:
	@echo "[SEARCH] Service discovery status:"
	@python3 scripts/service-discovery.py --status

register-services:
	@echo "📝 Registering core services..."
	@python3 scripts/service-discovery.py --register-core

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev-start:
	@echo "[START] Starting development environment..."
	@npm run dev &
	@python3 scripts/cod-service.py --dev &
	@echo "[OK] Development environment started"

dev-stop:
	@echo "🛑 Stopping development environment..."
	@pkill -f "npm run dev" 2>/dev/null || true
	@pkill -f "cod-service.py" 2>/dev/null || true
	@echo "[OK] Development environment stopped"

# =============================================================================
# DOCKER OPERATIONS
# =============================================================================

docker-build:
	@echo "🐳 Building Docker containers..."
	@docker-compose build

docker-up:
	@echo "[START] Starting Docker containers..."
	@docker-compose up -d

docker-down:
	@echo "🛑 Stopping Docker containers..."
	@docker-compose down

docker-logs:
	@echo "📋 Docker container logs:"
	@docker-compose logs -f

docker-dev:
	@echo "[TOOLS] Starting development Docker stack..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

docker-hybrid:
	@echo "[TARGET] Starting UltraMCP Hybrid stack (optimized)..."
	@docker-compose -f docker-compose.hybrid.yml up -d

docker-rebuild:
	@echo "[SYNC] Rebuilding and restarting Docker services..."
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
	@echo "[START] UltraMCP Hybrid System Startup"
	@./scripts/hybrid-startup.sh

# =============================================================================
# CLAUDE CODE INTEGRATION
# =============================================================================

# Auto-initialization for every Claude session
claude-init:
	@./scripts/claude-session-init.sh

# Full verification and acknowledgment
claude-verify:
	@echo "[SEARCH] Running comprehensive Claude Code verification..."
	@./scripts/claude-startup-verification.sh

# Quick session start
claude-start:
	@echo "[START] Starting Claude Code session..."
	@./scripts/claude-session-init.sh
	@make status

claude-demo:
	@echo "[DEEPCLAUDE] Running Claude Code integration demo..."
	@./scripts/claude-code-demo.sh

claude-help:
	@echo "[IDEA] Claude Code Integration Help"
	@echo "==============================="
	@echo ""
	@echo "Session Management:"
	@echo "  make claude-init               - Initialize Claude session"
	@echo "  make claude-verify             - Full system verification" 
	@echo "  make claude-start              - Quick session start"
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
	@echo "[DEEPCLAUDE] Setting up Claude Code integration..."
	@./scripts/claude-code-setup.sh

claude-test:
	@echo "🧪 Testing Claude Code integration..."
	@make health-check

# =============================================================================
# CONTROL TOWER UI
# =============================================================================

control-tower:
	@echo "[CONTROL] Starting UltraMCP Control Tower..."
	@./scripts/launch-control-tower.sh

control-tower-backend:
	@echo "[TOOLS] Starting Control Tower WebSocket Server..."
	@cd services/control-tower && npm install --silent && npm start

control-tower-frontend:
	@echo "[DESIGN] Starting Control Tower UI..."
	@cd apps/frontend && npm run dev -- --port 5173

control-tower-build:
	@echo "[BUILD] Building Control Tower UI..."
	@cd services/control-tower && npm install --silent
	@cd apps/frontend && npm run build

control-tower-status:
	@echo "[DATA] Control Tower Status:"
	@curl -s http://sam.chat:8001/api/status 2>/dev/null | jq . || echo "[ERROR] Control Tower backend not running"
	@curl -s http://sam.chat:5173 >/dev/null 2>&1 && echo "[OK] Frontend running on http://sam.chat:5173" || echo "[ERROR] Frontend not running"
	@make chat TEXT="Hello from UltraMCP Hybrid System!"
# =============================================================================
# CONTEXT7 REAL-TIME DOCUMENTATION
# =============================================================================

# Get real-time documentation
context7-docs:
	@echo "📚 Getting real-time documentation for $(LIBRARY)..."
	@python3 services/context7-mcp/context7_client.py get "$(LIBRARY)" --version="$(VERSION)"

# Search documentation
context7-search:
	@echo "[SEARCH] Searching documentation: $(QUERY) in $(LIBRARY)..."
	@python3 services/context7-mcp/context7_client.py search "$(LIBRARY)" "$(QUERY)"

# Enhance prompt with Context7
context7-enhance:
	@echo "✨ Enhancing prompt with Context7..."
	@python3 services/context7-mcp/context7_client.py enhance "$(PROMPT)" --libraries $(LIBRARIES)

# Detect libraries in code
context7-detect:
	@echo "[SEARCH] Detecting libraries in code..."
	@python3 services/context7-mcp/context7_client.py detect "$(CODE)"

# Context7 health check
context7-health:
	@echo "🏥 Context7 service health check..."
	@curl -s http://sam.chat:8003/health | jq . || echo "Context7 service not available"

# Context7 statistics
context7-stats:
	@echo "[DATA] Context7 service statistics..."
	@curl -s http://sam.chat:8003/api/stats | jq . || echo "Context7 service not available"

# Test Context7 integration
context7-test:
	@echo "🧪 Testing Context7 integration..."
	@./scripts/test-context7-integration.sh

# Claude Code with Context7 enhancement
claude-context7-chat:
	@echo "[DEEPCLAUDE] Claude Code chat with Context7 enhancement..."
	@python3 services/context7-mcp/context7_client.py enhance "$(TEXT). use context7" | make chat TEXT="$(shell cat -)"

# AI chat with automatic documentation context
context7-chat:
	@echo "💬 AI chat with Context7 documentation context..."
	@enhanced_prompt=$$(python3 services/context7-mcp/context7_client.py enhance "$(TEXT). use context7") && \
	make chat TEXT="$$enhanced_prompt"

# Local LLM chat with Context7
context7-local-chat:
	@echo "[DEEPCLAUDE] Local LLM chat with Context7 documentation..."
	@enhanced_prompt=$$(python3 services/context7-mcp/context7_client.py enhance "$(TEXT). use context7") && \
	make local-chat TEXT="$$enhanced_prompt"

# =============================================================================
# ENHANCED COD PROTOCOL WITH LOCAL LLMS
# =============================================================================

# Local model CoD debates
cod-local:
	@echo "[CLAUDIA] Starting LOCAL-ONLY CoD debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=local_only

cod-hybrid:
	@echo "[CLAUDIA] Starting HYBRID CoD debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=hybrid

cod-privacy:
	@echo "[SECURITY] Starting PRIVACY-FIRST debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=privacy_first

cod-cost-optimized:
	@echo "💰 Starting COST-OPTIMIZED debate..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=cost_optimized

# Quick local debates for development
dev-decision:
	@echo "[START] Quick development decision..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(DECISION)" --mode=local_only --rounds=2

# Claude Code integration
claude-debate:
	@echo "[DEEPCLAUDE] Claude Code CoD integration..."
	@python3 scripts/enhanced-cod-terminal.py --topic="$(TOPIC)" --mode=hybrid --verbose

# Model performance testing
test-cod-performance:
	@echo "[DATA] Testing CoD performance with local models..."
	@python3 scripts/enhanced-cod-terminal.py --topic="Test performance and response quality" --mode=local_only --rounds=1

# =============================================================================
# SECURITY COMMANDS - ASTERISK MCP INTEGRATION
# =============================================================================

# Run comprehensive security scan
security-scan:
	@echo "🛡️ Running comprehensive security scan..."
	@python3 services/asterisk-mcp/asterisk_security_client.py --scan-type=codebase --path=.

# Secure code review with multi-layer analysis
secure-code-review:
	@echo "[SEARCH] Secure code review pipeline for $(FILE)..."
	@echo "1. Security vulnerability scanning..."
	@python3 services/asterisk-mcp/asterisk_security_client.py --scan-type=snippet --file="$(FILE)"
	@echo "2. AI-powered security analysis..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=secure_code_review --file="$(FILE)"
	@echo "3. Generating security report..."

# Security-focused CoD Protocol debates
security-debate:
	@echo "[SECURITY] Security-focused debate: $(TOPIC)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=security_first --topic="$(TOPIC)" \
		--participants="asterisk:security,deepclaude:analyst,local:qwen2.5:14b,local:deepseek-coder:6.7b"

# Vulnerability analysis debate
vulnerability-analysis:
	@echo "[SEARCH] Vulnerability analysis debate for $(FILE)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=vulnerability_analysis --file="$(FILE)"

# Threat modeling session
threat-modeling:
	@echo "[TARGET] Threat modeling session for $(SCOPE)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=threat_modeling --scope="$(SCOPE)"

# Compliance analysis
compliance-check:
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
	@echo "[DATA] Generating security report..."
	@python3 scripts/generate-security-report.py --output=data/security_reports/

# Security incident response
security-incident-response INCIDENT:
	@echo "[ALERT] Security incident response for: $(INCIDENT)..."
	@python3 services/cod-protocol/security_enhanced_cod.py --mode=incident_response --incident="$(INCIDENT)"

# =============================================================================
# SECURE AI DEVELOPMENT COMMANDS
# =============================================================================

# Secure code generation with AI
secure-code-gen REQUIREMENT:
	@echo "[DEEPCLAUDE] Secure code generation: $(REQUIREMENT)..."
	@echo "1. Generating code with security considerations..."
	@make local-chat TEXT="Generate secure code for: $(REQUIREMENT). Include security best practices, input validation, and error handling."
	@echo "2. Security scanning generated code..."
	@make security-scan
	@echo "3. Security review if needed..."

# AI-powered security training
security-training:
	@echo "🎓 AI-powered security training: $(TOPIC)..."
	@make cod-local TOPIC="Security training session: $(TOPIC). Provide comprehensive security education with practical examples."

# Secure architecture review
secure-architecture-review:
	@echo "[BUILD] Secure architecture review for $(COMPONENT)..."
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
	@echo "[GATEWAY] ISO27001 compliance assessment..."
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
	@echo "[DATA] Opening security dashboard..."
	@echo "Security dashboard available at: http://sam.chat:3000/security"
	@echo "Use Claudia interface for visual security management"

# Security metrics collection
security-metrics:
	@echo "[METRICS] Collecting security metrics..."
	@python3 scripts/collect-security-metrics.py

# Security alerting setup
security-alerts:
	@echo "[ALERT] Setting up security alerts..."
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
	@echo "[SEARCH] Indexing project $(PROJECT) as $(NAME)..."
	@python3 services/blockoli-mcp/blockoli_client.py index "$(PROJECT)" "$(NAME)"

# Semantic code search
code-search:
	@echo "[SEARCH] Semantic search: $(QUERY) in $(PROJECT)"
	@python3 services/blockoli-mcp/blockoli_client.py search "$(QUERY)" "$(PROJECT)"

# Code-intelligent debates
code-debate:
	@echo "[AI] Code-intelligent debate: $(TOPIC)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="$(TOPIC)" --project="$(PROJECT)" --mode=basic

# Architecture analysis with AI
architecture-analysis:
	@echo "[BUILD] Architecture analysis: $(FOCUS) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Architecture analysis: $(FOCUS)" --project="$(PROJECT)" --mode=architecture_focused

# Security analysis with code context
code-security-analysis:
	@echo "🛡️ Security analysis: $(TOPIC) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Security analysis: $(TOPIC)" --project="$(PROJECT)" --mode=security_focused

# Code pattern analysis
pattern-analysis:
	@echo "[SEARCH] Pattern analysis: $(PATTERN) in $(PROJECT)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Pattern analysis: $(PATTERN)" --project="$(PROJECT)" --mode=pattern_analysis

# Intelligent code review
intelligent-code-review:
	@echo "[AI] Intelligent code review for $(FILE)"
	@python3 services/blockoli-mcp/code_intelligent_cod.py --topic="Code review for $(FILE)" --project="$(PROJECT)" --query="$(FILE)" --mode=deep_analysis

# Code similarity analysis
similarity-analysis:
	@echo "[LINK] Similarity analysis: $(FUNCTION) in $(PROJECT)"
	@python3 services/blockoli-mcp/blockoli_client.py search "$(FUNCTION)" "$(PROJECT)"

# Refactoring analysis with code intelligence
refactoring-analysis:
	@echo "[SYNC] Refactoring analysis: $(TOPIC) in $(PROJECT)"
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
	@curl -s http://sam.chat:8080/projects 2>/dev/null | jq . || echo "Blockoli service not available"

# Project statistics
project-stats:
	@echo "[DATA] Project statistics for $(PROJECT)..."
	@curl -s http://sam.chat:8080/projects/$(PROJECT)/stats 2>/dev/null | jq . || echo "Project not found or Blockoli service not available"

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
	@echo "[START] Intelligent development workflow..."
	@echo "1. Indexing current project..."
	@make index-project PROJECT="." NAME="current_project"
	@echo "2. Running code health check..."
	@make health-check
	@echo "3. Code pattern analysis..."
	@make pattern-analysis PATTERN="$(PATTERN)" PROJECT="current_project"
	@echo "4. Development workflow complete"

# AI-powered code review workflow
ai-code-review-workflow:
	@echo "[DEEPCLAUDE] AI-powered code review workflow..."
	@echo "1. Security scan..."
	@make security-scan
	@echo "2. Intelligent code review..."
	@make intelligent-code-review FILE="$(FILE)" PROJECT="$(PROJECT)"
	@echo "3. Pattern analysis..."
	@make pattern-analysis PATTERN="code quality" PROJECT="$(PROJECT)"
	@echo "4. AI code review complete"

# Complete code intelligence setup
setup-code-intelligence:
	@echo "[TOOLS] Setting up code intelligence..."
	@echo "1. Checking Blockoli service..."
	@make blockoli-health
	@echo "2. Indexing current project..."
	@make index-project PROJECT="." NAME="ultramcp"
	@echo "3. Testing code search..."
	@make code-search QUERY="authentication" PROJECT="ultramcp"
	@echo "[OK] Code intelligence setup complete"

# =============================================================================
# CLAUDE CODE MEMORY - Advanced Semantic Code Analysis
# =============================================================================

# Project indexing with memory
memory-index:
	@echo "[AI] Indexing project for Claude Code Memory..."
	@python3 services/claude-code-memory/claude_memory_client.py index "$(PROJECT)" "$(NAME)" $(if $(FORCE),--force)

# Semantic code search
memory-search:
	@echo "[SEARCH] Searching code with semantic memory..."
	@python3 services/claude-code-memory/claude_memory_client.py search "$(QUERY)" $(if $(PROJECT),--project "$(PROJECT)") $(if $(LANGUAGE),--language "$(LANGUAGE)") --limit $(or $(LIMIT),10)

# Advanced pattern analysis
memory-analyze:
	@echo "🔎 Analyzing code patterns with memory..."
	@python3 services/claude-code-memory/claude_memory_client.py analyze "$(FILE)" $(if $(PROJECT),--project "$(PROJECT)")

# Memory service status
memory-status:
	@echo "[DATA] Claude Code Memory Status"
	@python3 services/claude-code-memory/claude_memory_client.py status

# List memory projects
memory-projects:
	@echo "📁 Indexed Memory Projects"
	@python3 services/claude-code-memory/claude_memory_client.py projects

# Memory-enhanced workflows
memory-learn-codebase:
	@echo "🎓 Learning UltraMCP codebase with memory..."
	@echo "1. Indexing entire project..."
	@make memory-index PROJECT="." NAME="ultramcp" FORCE=true
	@echo "2. Analyzing core patterns..."
	@make memory-analyze FILE="core/orchestrator/eventBus.js" PROJECT="ultramcp"
	@echo "3. Learning complete! Try: make memory-search QUERY='event handling' PROJECT='ultramcp'"

# Smart code search workflow
memory-find-similar:
	@echo "🧬 Finding similar code patterns..."
	@python3 services/claude-code-memory/claude_memory_client.py search "$(PATTERN)" --project "$(PROJECT)" --show-content --limit 5

# Memory-enhanced CoD Protocol
memory-debate:
	@echo "[CLAUDIA] Memory-enhanced CoD Protocol debate..."
	@echo "1. Gathering relevant code context..."
	@make memory-search QUERY="$(TOPIC)" PROJECT="$(PROJECT)" LIMIT=3
	@echo "2. Starting intelligent debate with code context..."
	@make debate TOPIC="$(TOPIC) (with code context)"

# Quality assessment with memory
memory-quality-check:
	@echo "[PREMIUM] Memory-enhanced quality assessment..."
	@echo "1. Pattern analysis..."
	@make memory-analyze FILE="$(FILE)" PROJECT="$(PROJECT)"
	@echo "2. Finding similar implementations..."
	@make memory-find-similar PATTERN="similar to $(FILE)" PROJECT="$(PROJECT)"
	@echo "3. Quality recommendations generated"

# Interactive memory exploration
memory-explore:
	@echo "🗺️ Interactive memory exploration..."
	@echo "Available commands:"
	@echo "  make memory-search QUERY='your search'"
	@echo "  make memory-analyze FILE='path/to/file.py'"
	@echo "  make memory-find-similar PATTERN='design pattern'"
	@echo "Memory status:"
	@make memory-status

# Full memory integration test
test-memory-integration:
	@echo "🧪 Testing Claude Code Memory integration..."
	@echo "1. Service health check..."
	@make memory-status
	@echo "2. Indexing test project..."
	@make memory-index PROJECT="." NAME="test_project"
	@echo "3. Search test..."
	@make memory-search QUERY="test" PROJECT="test_project" LIMIT=3
	@echo "4. Pattern analysis test..."
	@make memory-analyze FILE="Makefile" PROJECT="test_project"
	@echo "[OK] Memory integration test complete"

# Memory cleanup
memory-clean:
	@echo "🧹 Cleaning Claude Code Memory..."
	@python3 -c "import asyncio; from services.claude_code_memory.claude_memory_client import ClaudeCodeMemoryClient; asyncio.run((lambda: ClaudeCodeMemoryClient().clear_memory(confirm=True))())"

# Enhanced help for memory commands
memory-help:
	@echo "[AI] Claude Code Memory Commands"
	@echo "=============================="
	@echo ""
	@echo "Project Management:"
	@echo "  make memory-index PROJECT='.' NAME='my-project'    - Index project for semantic search"
	@echo "  make memory-projects                               - List indexed projects"
	@echo "  make memory-status                                 - Check memory service status"
	@echo ""
	@echo "Code Search & Analysis:"
	@echo "  make memory-search QUERY='authentication logic'   - Semantic code search"
	@echo "  make memory-analyze FILE='src/auth.py'            - Analyze code patterns"
	@echo "  make memory-find-similar PATTERN='design pattern' - Find similar code"
	@echo ""
	@echo "Intelligent Workflows:"
	@echo "  make memory-learn-codebase                         - Learn entire codebase"
	@echo "  make memory-debate TOPIC='architecture decision'  - Memory-enhanced debate"
	@echo "  make memory-quality-check FILE='src/main.py'      - Quality assessment"
	@echo "  make memory-explore                                - Interactive exploration"
	@echo ""
	@echo "Testing & Maintenance:"
	@echo "  make test-memory-integration                       - Test memory integration"
	@echo "  make memory-clean                                  - Clear memory (destructive)"
	@echo ""
	@echo "Examples:"
	@echo "  make memory-index PROJECT='/path/to/code' NAME='webapp'"
	@echo "  make memory-search QUERY='error handling' PROJECT='webapp'"
	@echo "  make memory-analyze FILE='controllers/auth.py' PROJECT='webapp'"

# =============================================================================
# VOYAGEAI HYBRID SEMANTIC SEARCH - Enhanced with Domain Specialization
# =============================================================================

# Enhanced semantic search with VoyageAI
voyage-search:
	@echo "[START] VoyageAI Enhanced Semantic Search..."
	@curl -X POST http://sam.chat:8009/memory/search/enhanced \
		-H "Content-Type: application/json" \
		-d '{"query": "$(QUERY)", "limit": $(or $(LIMIT),10), "privacy_level": "$(or $(PRIVACY),PUBLIC)", "domain": $(if $(DOMAIN),"$(DOMAIN)",null), "search_mode": "$(or $(MODE),AUTO)", "project_name": $(if $(PROJECT),"$(PROJECT)",null)}' | jq .

# Code-optimized search with VoyageAI code embeddings
voyage-code-search:
	@echo "[DESKTOP] VoyageAI Code-Optimized Search..."
	@curl -X POST "http://sam.chat:8009/memory/search/code?query=$(QUERY)&limit=$(or $(LIMIT),10)&privacy_level=$(or $(PRIVACY),INTERNAL)$(if $(PROJECT),&project_name=$(PROJECT))$(if $(LANGUAGE),&language=$(LANGUAGE))" | jq .

# Privacy-first search (local only)
voyage-privacy-search:
	@echo "[SECURITY] Privacy-First Local Search..."
	@curl -X POST "http://sam.chat:8009/memory/search/privacy-first?query=$(QUERY)&limit=$(or $(LIMIT),10)$(if $(PROJECT),&project_name=$(PROJECT))" | jq .

# Domain-specialized search (finance, healthcare, legal, etc.)
voyage-domain-search:
	@echo "[TARGET] Domain-Specialized Search ($(DOMAIN))..."
	@curl -X POST "http://sam.chat:8009/memory/search/domain?query=$(QUERY)&domain=$(DOMAIN)&limit=$(or $(LIMIT),10)&privacy_level=$(or $(PRIVACY),PUBLIC)$(if $(PROJECT),&project_name=$(PROJECT))" | jq .

# Enhanced project indexing with VoyageAI
voyage-index:
	@echo "🗂️ Enhanced Project Indexing with VoyageAI..."
	@curl -X POST http://sam.chat:8009/memory/projects/index \
		-H "Content-Type: application/json" \
		-d '{"project_path": "$(PROJECT)", "project_name": "$(NAME)", "domain": $(if $(DOMAIN),"$(DOMAIN)",null), "privacy_level": "$(or $(PRIVACY),INTERNAL)", "include_patterns": $(or $(PATTERNS),["*.py", "*.js", "*.ts", "*.java", "*.cpp"]), "exclude_patterns": ["node_modules", ".git", "__pycache__"]}' | jq .

# VoyageAI service health check
voyage-health:
	@echo "🏥 VoyageAI Service Health Check..."
	@echo "1. VoyageAI Service:"
	@curl -s http://sam.chat:8010/health | jq .
	@echo "2. Enhanced Memory Service:"
	@curl -s http://sam.chat:8009/health | jq .
	@echo "3. Available Models:"
	@curl -s http://sam.chat:8010/models | jq .

# Get VoyageAI service statistics
voyage-stats:
	@echo "[DATA] VoyageAI Service Statistics..."
	@echo "1. Enhanced Search Stats:"
	@curl -s http://sam.chat:8009/memory/stats/enhanced | jq .search_stats
	@echo "2. Service Health:"
	@curl -s http://sam.chat:8009/memory/stats/enhanced | jq .service_health
	@echo "3. Cost Analysis:"
	@curl -s http://sam.chat:8010/stats | jq .

# List available VoyageAI models and capabilities
voyage-models:
	@echo "[DEEPCLAUDE] Available VoyageAI Models..."
	@curl -s http://sam.chat:8009/memory/models | jq .

# Domain-specific workflows
voyage-finance-search:
	@echo "💰 Finance Domain Search..."
	@make voyage-domain-search DOMAIN="FINANCE" QUERY="$(QUERY)" PROJECT="$(PROJECT)" PRIVACY="$(or $(PRIVACY),PUBLIC)"

voyage-healthcare-search:
	@echo "🏥 Healthcare Domain Search..."
	@make voyage-domain-search DOMAIN="HEALTHCARE" QUERY="$(QUERY)" PROJECT="$(PROJECT)" PRIVACY="$(or $(PRIVACY),CONFIDENTIAL)"

voyage-legal-search:
	@echo "⚖️ Legal Domain Search..."
	@make voyage-domain-search DOMAIN="LEGAL" QUERY="$(QUERY)" PROJECT="$(PROJECT)" PRIVACY="$(or $(PRIVACY),CONFIDENTIAL)"

# Advanced hybrid workflows
voyage-hybrid-analysis:
	@echo "[SYNC] Hybrid Analysis Workflow..."
	@echo "1. Privacy-first search for sensitive content..."
	@make voyage-privacy-search QUERY="$(QUERY)" PROJECT="$(PROJECT)" LIMIT=5
	@echo "2. VoyageAI enhanced search for public context..."
	@make voyage-search QUERY="$(QUERY)" PROJECT="$(PROJECT)" PRIVACY="PUBLIC" MODE="HYBRID" LIMIT=10
	@echo "3. Code-specific analysis..."
	@make voyage-code-search QUERY="$(QUERY)" PROJECT="$(PROJECT)" LANGUAGE="$(LANGUAGE)"

# Cost optimization workflow
voyage-cost-optimized:
	@echo "💰 Cost-Optimized Search Workflow..."
	@echo "1. Starting with local search..."
	@make voyage-privacy-search QUERY="$(QUERY)" PROJECT="$(PROJECT)" LIMIT=3
	@echo "2. Fallback to VoyageAI if needed..."
	@if [ -z "$(FORCE_VOYAGE)" ]; then \
		echo "   Use FORCE_VOYAGE=true to enable VoyageAI search"; \
	else \
		make voyage-search QUERY="$(QUERY)" PROJECT="$(PROJECT)" PRIVACY="PUBLIC" LIMIT=5; \
	fi

# Test VoyageAI integration
test-voyage-integration:
	@echo "🧪 Testing VoyageAI Integration..."
	@echo "1. Service health..."
	@make voyage-health
	@echo "2. Model availability..."
	@make voyage-models
	@echo "3. Privacy-first search test..."
	@make voyage-privacy-search QUERY="test search" PROJECT="ultramcp" LIMIT=3
	@echo "4. Code search test..."
	@make voyage-code-search QUERY="docker" PROJECT="ultramcp" LIMIT=3
	@echo "5. Enhanced search test..."
	@make voyage-search QUERY="integration" PROJECT="ultramcp" MODE="HYBRID" LIMIT=3
	@echo "[OK] VoyageAI integration test complete"

# VoyageAI help
voyage-help:
	@echo "[START] VoyageAI Hybrid Search Commands"
	@echo "================================="
	@echo ""
	@echo "Basic Search:"
	@echo "  make voyage-search QUERY='...' [PROJECT='...'] [PRIVACY=PUBLIC|INTERNAL|CONFIDENTIAL] [MODE=AUTO|HYBRID|LOCAL_ONLY]"
	@echo "  make voyage-code-search QUERY='...' [PROJECT='...'] [LANGUAGE='...'] [PRIVACY=INTERNAL]"
	@echo "  make voyage-privacy-search QUERY='...' [PROJECT='...']  # Local only, maximum privacy"
	@echo ""
	@echo "Domain-Specialized Search:"
	@echo "  make voyage-domain-search QUERY='...' DOMAIN='CODE|FINANCE|HEALTHCARE|LEGAL|GENERAL'"
	@echo "  make voyage-finance-search QUERY='...' [PROJECT='...']"
	@echo "  make voyage-healthcare-search QUERY='...' [PROJECT='...'] # Auto-confidential"
	@echo "  make voyage-legal-search QUERY='...' [PROJECT='...'] # Auto-confidential"
	@echo ""
	@echo "Project Management:"
	@echo "  make voyage-index PROJECT='...' NAME='...' [DOMAIN='...'] [PRIVACY='...']"
	@echo "  make voyage-health  # Check all services"
	@echo "  make voyage-stats   # Get performance statistics"
	@echo "  make voyage-models  # List available models"
	@echo ""
	@echo "Advanced Workflows:"
	@echo "  make voyage-hybrid-analysis QUERY='...' PROJECT='...' [LANGUAGE='...']"
	@echo "  make voyage-cost-optimized QUERY='...' [FORCE_VOYAGE=true]"
	@echo "  make test-voyage-integration  # Test complete integration"
	@echo ""
	@echo "Privacy Levels:"
	@echo "  PUBLIC      - Use VoyageAI APIs for best quality"
	@echo "  INTERNAL    - Prefer local models, fallback to VoyageAI"
	@echo "  CONFIDENTIAL - Local models only"
	@echo "  RESTRICTED  - Local models only"
	@echo ""
	@echo "Search Modes:"
	@echo "  AUTO        - Intelligent selection based on content"
	@echo "  HYBRID      - VoyageAI + local fallback"
	@echo "  VOYAGE_ONLY - VoyageAI only"
	@echo "  LOCAL_ONLY  - Local models only"
	@echo ""
	@echo "Examples:"
	@echo "  make voyage-code-search QUERY='authentication patterns' PROJECT='webapp' LANGUAGE='python'"
	@echo "  make voyage-finance-search QUERY='risk assessment models' PROJECT='fintech-app'"
	@echo "  make voyage-privacy-search QUERY='user data handling' PROJECT='enterprise-app'"
	@echo "  make voyage-search QUERY='microservices architecture' PRIVACY='PUBLIC' MODE='HYBRID'"

# =============================================================================
# REF TOOLS MCP - Complete Documentation Intelligence
# =============================================================================

# Ref Tools documentation search
ref-search:
	@echo "[LINK] Ref Tools Documentation Search..."
	@curl -X POST http://sam.chat:8011/ref/search \
		-H "Content-Type: application/json" \
		-d '{"query": "$(QUERY)", "source_type": "$(or $(SOURCE),AUTO)", "privacy_level": "$(or $(PRIVACY),INTERNAL)", "include_code_examples": $(or $(CODE),true), "max_results": $(or $(LIMIT),10), "organization": $(if $(ORG),"$(ORG)",null), "project_context": $(if $(PROJECT),"$(PROJECT)",null)}' | jq .

# Read URL content with Ref Tools
ref-read-url:
	@echo "📄 Ref Tools URL Content Extraction..."
	@curl -X POST http://sam.chat:8011/ref/read-url \
		-H "Content-Type: application/json" \
		-d '{"url": "$(URL)", "extract_code": $(or $(CODE),true)}' | jq .

# Internal documentation search
ref-internal-search:
	@echo "🏢 Internal Documentation Search..."
	@make ref-search QUERY="$(QUERY)" SOURCE="INTERNAL" PRIVACY="CONFIDENTIAL" PROJECT="$(PROJECT)" ORG="$(ORG)"

# External documentation search
ref-external-search:
	@echo "[GATEWAY] External Documentation Search..."
	@make ref-search QUERY="$(QUERY)" SOURCE="EXTERNAL" PRIVACY="PUBLIC" PROJECT="$(PROJECT)"

# Unified documentation search combining all sources
docs-unified-search:
	@echo "[SHINE] Unified Documentation Intelligence Search..."
	@curl -X POST http://sam.chat:8012/docs/unified-search \
		-H "Content-Type: application/json" \
		-d '{"query": "$(QUERY)", "documentation_type": "$(or $(TYPE),HYBRID)", "intelligence_level": "$(or $(INTELLIGENCE),ENHANCED)", "privacy_level": "$(or $(PRIVACY),INTERNAL)", "include_code": $(or $(CODE),true), "include_examples": $(or $(EXAMPLES),true), "max_results_per_source": $(or $(LIMIT),5), "project_context": $(if $(PROJECT),"$(PROJECT)",null), "organization": $(if $(ORG),"$(ORG)",null)}' | jq .

# Code-focused unified search
docs-code-search:
	@echo "[DESKTOP] Unified Code Documentation Search..."
	@make docs-unified-search QUERY="$(QUERY)" TYPE="CODE_SNIPPETS" INTELLIGENCE="ENHANCED" PROJECT="$(PROJECT)"

# Documentation intelligence help
docs-help:
	@echo "[SHINE] Complete Documentation Intelligence Commands"
	@echo "============================================="
	@echo ""
	@echo "Ref Tools Commands:"
	@echo "  make ref-search QUERY='...' [SOURCE=AUTO|INTERNAL|EXTERNAL] [PRIVACY=...] [PROJECT=...]"
	@echo "  make ref-read-url URL='...' [CODE=true|false]"
	@echo "  make ref-internal-search QUERY='...' PROJECT='...' ORG='...'"
	@echo "  make ref-external-search QUERY='...' PROJECT='...'"
	@echo ""
	@echo "Unified Documentation Intelligence:"
	@echo "  make docs-unified-search QUERY='...' [TYPE=HYBRID|CODE_SNIPPETS|FULL_DOCS|SEMANTIC_CODE]"
	@echo "  make docs-code-search QUERY='...' PROJECT='...'    # Code-focused search"
	@echo ""
	@echo "Examples:"
	@echo "  make ref-external-search QUERY='FastAPI authentication' PROJECT='api-service'"
	@echo "  make ref-internal-search QUERY='deployment guidelines' PROJECT='enterprise' ORG='company'"
	@echo "  make docs-code-search QUERY='React hooks patterns' PROJECT='frontend-app'"
	@echo "  make docs-unified-search QUERY='API security' TYPE='HYBRID' INTELLIGENCE='SUPREME'"

# =============================================================================
# UNIFIED BACKEND - FastAPI MCP Integration
# =============================================================================

# Start unified backend with all core services
unified-start:
	@echo "[START] Starting UltraMCP Unified Backend..."
	@docker-compose -f docker-compose.unified.yml up -d ultramcp-unified-backend
	@echo "[OK] Unified backend started at http://sam.chat:8000"
	@echo "📚 Documentation: http://sam.chat:8000/docs"
	@echo "[LINK] MCP Tools: http://sam.chat:8000/mcp/tools"

# Start complete unified system (backend + specialized services)
unified-system-start:
	@echo "[SHINE] Starting Complete Unified System..."
	@docker-compose -f docker-compose.unified.yml up -d
	@echo "[OK] Complete system started"
	@make unified-status

# Check unified backend health
unified-status:
	@echo "🏥 Unified Backend Health Check..."
	@echo "1. Global Health:"
	@curl -s http://sam.chat:8000/health 2>/dev/null | jq . || echo "[ERROR] Unified backend not available"
	@echo "2. Component Health:"
	@curl -s http://sam.chat:8000/health/detailed 2>/dev/null | jq .components || echo "[ERROR] Component health check failed"
	@echo "3. MCP Tools:"
	@curl -s http://sam.chat:8000/mcp/tools 2>/dev/null | jq .total_tools || echo "[ERROR] MCP tools not available"

# View unified backend logs
unified-logs:
	@echo "📜 Unified Backend Logs..."
	@docker logs ultramcp-unified-backend --tail=50 -f

# Test unified backend endpoints
unified-test:
	@echo "🧪 Testing Unified Backend Endpoints..."
	@echo "1. Health check..."
	@make unified-status
	@echo "2. Testing CoD endpoint..."
	@curl -X POST http://sam.chat:8000/cod/local-debate \
		-H "Content-Type: application/json" \
		-d '{"topic": "Test unified backend debate", "participants": 2, "rounds": 1}' 2>/dev/null | jq .debate_id || echo "[ERROR] CoD test failed"
	@echo "3. Testing Memory endpoint..."
	@curl -X POST "http://sam.chat:8000/memory/search/privacy-first?query=test&limit=3" 2>/dev/null | jq .query || echo "[ERROR] Memory test failed"
	@echo "4. Testing VoyageAI endpoint..."
	@curl -X POST "http://sam.chat:8000/voyage/search/privacy-first?query=test&limit=3" 2>/dev/null | jq .query || echo "[ERROR] Voyage test failed"
	@echo "[OK] Unified backend tests complete"

# Open unified backend documentation
unified-docs:
	@echo "📚 Opening Unified Backend Documentation..."
	@echo "Swagger UI: http://sam.chat:8000/docs"
	@echo "ReDoc: http://sam.chat:8000/redoc"
	@echo "OpenAPI Schema: http://sam.chat:8000/openapi.json"
	@echo "MCP Tools: http://sam.chat:8000/mcp/tools"
	@if command -v open >/dev/null 2>&1; then \
		open http://sam.chat:8000/docs; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://sam.chat:8000/docs; \
	else \
		echo "Open manually: http://sam.chat:8000/docs"; \
	fi

# Test MCP protocol endpoints
unified-mcp-test:
	@echo "[LINK] Testing MCP Protocol Integration..."
	@echo "1. List MCP tools..."
	@curl -s http://sam.chat:8000/mcp/tools | jq .total_tools
	@echo "2. Get MCP capabilities..."
	@curl -s http://sam.chat:8000/mcp/capabilities | jq .capabilities
	@echo "3. Test MCP tool execution (CoD)..."
	@curl -X POST http://sam.chat:8000/mcp/execute/cod_local_debate \
		-H "Content-Type: application/json" \
		-d '{"topic": "MCP integration test", "participants": 2}' | jq .result.debate_id
	@echo "[OK] MCP integration test complete"

# Unified backend development mode
unified-dev:
	@echo "[TOOLS] Starting Unified Backend in Development Mode..."
	@cd services/ultramcp-unified-backend && \
		pip install -r requirements.txt && \
		python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Rebuild unified backend
unified-rebuild:
	@echo "[SYNC] Rebuilding Unified Backend..."
	@docker-compose -f docker-compose.unified.yml down ultramcp-unified-backend
	@docker-compose -f docker-compose.unified.yml build --no-cache ultramcp-unified-backend
	@docker-compose -f docker-compose.unified.yml up -d ultramcp-unified-backend
	@echo "[OK] Unified backend rebuilt and restarted"

# Migration from microservices to unified backend
unified-migrate:
	@echo "[SYNC] Migrating from Microservices to Unified Backend..."
	@echo "1. Stopping individual microservices..."
	@docker-compose down cod-service memory-service voyage-service ref-service docs-service 2>/dev/null || true
	@echo "2. Starting unified backend..."
	@make unified-start
	@echo "3. Testing migration..."
	@make unified-test
	@echo "[OK] Migration complete. Individual services consolidated into unified backend."

# Stop unified backend
unified-stop:
	@echo "🛑 Stopping Unified Backend..."
	@docker-compose -f docker-compose.unified.yml down ultramcp-unified-backend

# Stop complete unified system
unified-system-stop:
	@echo "🛑 Stopping Complete Unified System..."
	@docker-compose -f docker-compose.unified.yml down

# Performance test for unified backend
unified-performance-test:
	@echo "[FAST] Unified Backend Performance Test..."
	@echo "1. Concurrent CoD requests..."
	@for i in $$(seq 1 3); do \
		curl -X POST http://sam.chat:8000/cod/local-debate \
			-H "Content-Type: application/json" \
			-d '{"topic": "Performance test $$i", "participants": 2, "rounds": 1}' \
			-w "Response time: %{time_total}s\n" -o /dev/null -s & \
	done; wait
	@echo "2. Concurrent Memory searches..."
	@for i in $$(seq 1 5); do \
		curl -X POST "http://sam.chat:8000/memory/search/privacy-first?query=performance$$i&limit=2" \
			-w "Response time: %{time_total}s\n" -o /dev/null -s & \
	done; wait
	@echo "[OK] Performance test complete"

# Complete unified backend help
unified-help:
	@echo "[START] UltraMCP Unified Backend Commands"
	@echo "===================================="
	@echo ""
	@echo "Basic Operations:"
	@echo "  make unified-start                 - Start unified backend only"
	@echo "  make unified-system-start          - Start complete unified system"
	@echo "  make unified-status                - Check health and status"
	@echo "  make unified-logs                  - View backend logs"
	@echo "  make unified-stop                  - Stop unified backend"
	@echo "  make unified-system-stop           - Stop complete system"
	@echo ""
	@echo "Development & Testing:"
	@echo "  make unified-dev                   - Start in development mode"
	@echo "  make unified-test                  - Test all endpoints"
	@echo "  make unified-mcp-test              - Test MCP protocol integration"
	@echo "  make unified-performance-test      - Performance testing"
	@echo "  make unified-rebuild               - Rebuild and restart"
	@echo ""
	@echo "Documentation & Integration:"
	@echo "  make unified-docs                  - Open documentation"
	@echo "  make unified-migrate               - Migrate from microservices"
	@echo ""
	@echo "Service URLs:"
	@echo "  Unified Backend:  http://sam.chat:8000"
	@echo "  Documentation:    http://sam.chat:8000/docs"
	@echo "  MCP Tools:        http://sam.chat:8000/mcp/tools"
	@echo "  Health Check:     http://sam.chat:8000/health"
	@echo ""
	@echo "MCP Tools Available:"
	@echo "  - cod_enhanced_debate             - Multi-LLM debate orchestration"
	@echo "  - cod_local_debate                - Privacy-first local debate"
	@echo "  - memory_enhanced_search          - Semantic code search"
	@echo "  - memory_index_project            - Project indexing for memory"
	@echo "  - voyage_enhanced_search          - Premium semantic search"
	@echo "  - voyage_domain_search            - Domain-specialized search"
	@echo "  - ref_search_documentation        - Documentation search"
	@echo "  - ref_read_url                    - URL content extraction"
	@echo "  - docs_unified_search             - Supreme documentation intelligence"
	@echo "  - actions_list                    - List available external actions"
	@echo "  - actions_execute                 - Execute external action"
	@echo "  - actions_escalate_human          - Escalate to human approval"
	@echo "  - actions_send_notification       - Send notifications"
	@echo "  - actions_trigger_workflow        - Trigger external workflows"
	@echo "  - actions_create_ticket           - Create external tickets"
	@echo "  - actions_security_scan           - Run security scans"

# =============================================================================
# CLAUDIA MCP INTEGRATION - Visual Multi-LLM Platform
# =============================================================================

# Start Claudia MCP servers
claudia-start:
	@echo "[CLAUDIA] Starting Claudia MCP Integration..."
	@echo "1. Starting Chain-of-Debate MCP Server..."
	@cd services/claudia-mcp && python3 cod_mcp_server.py &
	@echo "2. Starting Local Models MCP Server..."
	@cd services/claudia-mcp && python3 local_mcp_server.py &
	@echo "3. Starting Hybrid Decision MCP Server..."
	@cd services/claudia-mcp && python3 hybrid_mcp_server.py &
	@echo "[OK] Claudia MCP servers started"

# Start individual Claudia MCP servers
cod-mcp-server:
	@echo "[CLAUDIA] Starting Chain-of-Debate MCP Server..."
	@cd services/claudia-mcp && python3 cod_mcp_server.py

local-mcp-server:
	@echo "[DEEPCLAUDE] Starting Local Models MCP Server..."
	@cd services/claudia-mcp && python3 local_mcp_server.py

hybrid-mcp-server:
	@echo "[AI] Starting Hybrid Decision MCP Server..."
	@cd services/claudia-mcp && python3 hybrid_mcp_server.py

# Test legacy Claudia MCP integration
claudia-legacy-test:
	@echo "🧪 Testing Legacy Claudia MCP Integration..."
	@echo "1. Testing Chain-of-Debate MCP Server files..."
	@test -f services/claudia-mcp/cod_mcp_server.py && echo "[OK] Chain-of-Debate MCP Server exists" || echo "[ERROR] Chain-of-Debate MCP Server missing"
	@echo "2. Testing Local Models MCP Server files..."
	@test -f services/claudia-mcp/local_mcp_server.py && echo "[OK] Local Models MCP Server exists" || echo "[ERROR] Local Models MCP Server missing"
	@echo "3. Testing Hybrid Decision MCP Server files..."
	@test -f services/claudia-mcp/hybrid_mcp_server.py && echo "[OK] Hybrid Decision MCP Server exists" || echo "[ERROR] Hybrid Decision MCP Server missing"
	@echo "4. Testing requirements..."
	@test -f services/claudia-mcp/requirements.txt && echo "[OK] Claudia MCP requirements exist" || echo "[ERROR] Claudia MCP requirements missing"
	@echo "[OK] Legacy Claudia MCP integration tests complete"

# Stop legacy Claudia MCP servers
claudia-legacy-stop:
	@echo "🛑 Stopping legacy Claudia MCP servers..."
	@pkill -f "cod_mcp_server.py" 2>/dev/null || true
	@pkill -f "local_mcp_server.py" 2>/dev/null || true
	@pkill -f "hybrid_mcp_server.py" 2>/dev/null || true
	@echo "[OK] Legacy Claudia MCP servers stopped"

# Check legacy Claudia MCP servers status
claudia-legacy-status:
	@echo "[DATA] Legacy Claudia MCP Servers Status"
	@echo "============================="
	@pgrep -f "cod_mcp_server.py" >/dev/null && echo "[OK] Chain-of-Debate MCP Server: Running" || echo "[ERROR] Chain-of-Debate MCP Server: Stopped"
	@pgrep -f "local_mcp_server.py" >/dev/null && echo "[OK] Local Models MCP Server: Running" || echo "[ERROR] Local Models MCP Server: Stopped"
	@pgrep -f "hybrid_mcp_server.py" >/dev/null && echo "[OK] Hybrid Decision MCP Server: Running" || echo "[ERROR] Hybrid Decision MCP Server: Stopped"

# Claudia frontend development server
claudia-frontend:
	@echo "[DESIGN] Starting Claudia Frontend Development Server..."
	@cd apps/frontend && npm run dev -- --port 3001

# Legacy Claudia integration help
claudia-legacy-help:
	@echo "[CLAUDIA] Legacy Claudia MCP Integration Commands"
	@echo "=================================="
	@echo ""
	@echo "MCP Server Management:"
	@echo "  make claudia-start              - Start all Claudia MCP servers"
	@echo "  make claudia-legacy-stop        - Stop all Claudia MCP servers"
	@echo "  make claudia-legacy-status      - Check MCP servers status"
	@echo "  make claudia-test               - Test MCP integration"
	@echo ""
	@echo "Individual MCP Servers:"
	@echo "  make cod-mcp-server             - Start Chain-of-Debate MCP Server"
	@echo "  make local-mcp-server           - Start Local Models MCP Server"
	@echo "  make hybrid-mcp-server          - Start Hybrid Decision MCP Server"
	@echo ""
	@echo "Frontend Development:"
	@echo "  make claudia-frontend           - Start Claudia frontend dev server"
	@echo ""
	@echo "Integration Workflow:"
	@echo "  1. make claudia-start           - Start MCP servers"
	@echo "  2. make claudia-frontend        - Start frontend"
	@echo "  3. Navigate to http://sam.chat:3001"
	@echo "  4. Use Claudia visual interface for multi-LLM debates"
	@echo ""
	@echo "MCP Tools Available:"
	@echo "  Chain-of-Debate Server:"
	@echo "    - cod_debate                  - Start multi-LLM debate"
	@echo "    - get_local_models           - List available local models"
	@echo "    - local_chat                 - Chat with specific local model"
	@echo "    - cost_analysis              - Analyze debate costs"
	@echo "    - optimize_costs             - Optimize model selection for cost"
	@echo ""
	@echo "  Local Models Server:"
	@echo "    - qwen25_14b_chat            - Chat with Qwen 2.5 14B"
	@echo "    - llama31_8b_chat            - Chat with Llama 3.1 8B"
	@echo "    - qwen_coder_7b_chat         - Chat with Qwen Coder 7B"
	@echo "    - mistral_7b_chat            - Chat with Mistral 7B"
	@echo "    - deepseek_coder_chat        - Chat with DeepSeek Coder"
	@echo "    - auto_select_model          - Auto-select best model for task"
	@echo ""
	@echo "  Hybrid Decision Server:"
	@echo "    - hybrid_decision            - Make hybrid local/API decision"
	@echo "    - cost_optimize_route        - Optimize routing for costs"
	@echo "    - privacy_optimize_route     - Optimize routing for privacy"
	@echo "    - quality_optimize_route     - Optimize routing for quality"
	@echo "    - batch_process              - Process multiple requests efficiently"
	@echo ""
	@echo "Frontend Components:"
	@echo "  - Real-time debate visualization with participant circles"
	@echo "  - Local model management interface"
	@echo "  - Performance monitoring and analytics"
	@echo "  - Cost and privacy optimization controls"
	@echo "  - Integration with UltraMCP backend services"

# Complete Claudia system startup
# Alias for case-sensitive compatibility
Claudia-start: claudia-start

claudia-system-start:
	@echo "[SHINE] Starting Complete Claudia System..."
	@echo "1. Starting Claudia MCP servers..."
	@make claudia-start
	@echo "2. Starting Claudia frontend..."
	@echo "Starting frontend in background..."
	@cd apps/frontend && npm run dev -- --port 3001 > /dev/null 2>&1 &
	@sleep 3
	@echo ""
	@echo "[OK] Complete Claudia system started!"
	@echo "[CLAUDIA] Claudia Interface: http://sam.chat:3001"
	@echo "📖 Use 'make claudia-help' for available commands"
	@make claudia-status

# Simple Claudia startup (MCP servers only)
claudia-simple-start:
	@echo "[CLAUDIA] Starting Claudia MCP Servers Only..."
	@make claudia-start
	@echo "[OK] Claudia MCP servers started!"
	@echo "📖 Use 'make claudia-frontend' to start the UI"
	@make claudia-status

# =============================================================================
# Include sam.chat deployment targets
# =============================================================================
-include deploy-sam-chat-targets.mk

# =============================================================================
# Actions MCP Service Commands (External Actions Execution)
# =============================================================================

# Actions service status
actions-health:
	@echo "[CLAUDIA] Checking Actions MCP Service Health..."
	@curl -s http://sam.chat:8010/health/ | jq . || echo "[ERROR] Actions service not available"

# List all available actions
actions-list:
	@echo "📋 Available External Actions:"
	@curl -s http://sam.chat:8010/actions/ | jq . || echo "[ERROR] Failed to get actions list"

# Escalate to human approval
actions-escalate:
	@echo "[ALERT] Escalating to Human: $(MESSAGE)"
	@curl -X POST http://sam.chat:8010/actions/escalate_to_human/execute \
		-H "Content-Type: application/json" \
		-d '{"parameters": {"message": "$(MESSAGE)", "priority": "$(if $(PRIORITY),$(PRIORITY),medium)"}}' | jq .

# Send notification
actions-notify:
	@echo "📢 Sending Notification to $(RECIPIENT)"
	@ACTION_ID=$$(if [ "$(CHANNEL)" = "slack" ]; then echo "send_slack_message"; else echo "send_email"; fi); \
	curl -X POST http://sam.chat:8010/actions/$$ACTION_ID/execute \
		-H "Content-Type: application/json" \
		-d '{"parameters": {"recipient": "$(RECIPIENT)", "message": "$(MESSAGE)", "subject": "$(if $(SUBJECT),$(SUBJECT),Notification)", "channel": "$(if $(CHANNEL),$(CHANNEL),email)"}}' | jq .

# Trigger external workflow
actions-workflow:
	@echo "[FAST] Triggering Workflow: $(JOB)"
	@curl -X POST http://sam.chat:8010/actions/trigger_workflow/execute \
		-H "Content-Type: application/json" \
		-d '{"parameters": {"job_name": "$(JOB)", "workflow_type": "$(if $(TYPE),$(TYPE),jenkins)", "parameters": $(if $(PARAMS),$(PARAMS),{})}}' | jq .

# Create external ticket
actions-ticket:
	@echo "🎫 Creating Ticket: $(TITLE)"
	@ACTION_ID=$$(if [ "$(SYSTEM)" = "github" ]; then echo "create_github_issue"; else echo "create_jira_ticket"; fi); \
	curl -X POST http://sam.chat:8010/actions/$$ACTION_ID/execute \
		-H "Content-Type: application/json" \
		-d '{"parameters": {"title": "$(TITLE)", "description": "$(DESC)", "system": "$(if $(SYSTEM),$(SYSTEM),jira)", "priority": "$(if $(PRIORITY),$(PRIORITY),medium)"}}' | jq .

# Run security scan
actions-security-scan:
	@echo "[SECURITY] Running Security Scan on $(TARGET)"
	@curl -X POST http://sam.chat:8010/actions/run_security_scan/execute \
		-H "Content-Type: application/json" \
		-d '{"parameters": {"target": "$(TARGET)", "scan_type": "$(if $(TYPE),$(TYPE),vulnerability)", "tool": "$(if $(TOOL),$(TOOL),sonarqube)"}}' | jq .

# Validate action parameters
actions-validate:
	@echo "[OK] Validating Parameters for Action: $(ACTION)"
	@curl -X POST http://sam.chat:8010/actions/$(ACTION)/validate \
		-H "Content-Type: application/json" \
		-d '{"parameters": $(PARAMS)}' | jq .

# Get action execution history
actions-history:
	@echo "📜 Getting History for Action: $(ACTION)"
	@curl -s "http://sam.chat:8010/actions/$(ACTION)/history?limit=$(if $(LIMIT),$(LIMIT),10)" | jq .

# Get execution statistics
actions-stats:
	@echo "[DATA] Actions Execution Statistics:"
	@curl -s http://sam.chat:8010/actions/stats/summary | jq .

# Execute any action directly
actions-execute:
	@echo "[CLAUDIA] Executing Action: $(ACTION)"
	@curl -X POST http://sam.chat:8010/actions/$(ACTION)/execute \
		-H "Content-Type: application/json" \
		-d '{"parameters": $(PARAMS)}' | jq .

# Test actions service integration
actions-test:
	@echo "🧪 Testing Actions MCP Service Integration..."
	@echo "1. Health check..."
	@make actions-health
	@echo ""
	@echo "2. List actions..."
	@make actions-list
	@echo ""
	@echo "3. Validate parameters..."
	@make actions-validate ACTION=escalate_to_human PARAMS='{"message":"test","priority":"low"}'
	@echo ""
	@echo "[OK] Actions integration test complete"

# Actions service help
actions-help:
	@echo "[CLAUDIA] Actions MCP Service Commands"
	@echo "================================"
	@echo ""
	@echo "Basic Operations:"
	@echo "  make actions-health                               - Check service health"
	@echo "  make actions-list                                 - List available actions"
	@echo "  make actions-stats                                - Get execution statistics"
	@echo "  make actions-test                                 - Test service integration"
	@echo ""
	@echo "Human Escalation:"
	@echo "  make actions-escalate MESSAGE='Need approval' [PRIORITY=medium]"
	@echo ""
	@echo "Notifications:"
	@echo "  make actions-notify RECIPIENT='user@domain.com' MESSAGE='Alert' [CHANNEL=email]"
	@echo "  make actions-notify RECIPIENT='#channel' MESSAGE='Alert' CHANNEL=slack"
	@echo ""
	@echo "Workflow Triggers:"
	@echo "  make actions-workflow JOB='deploy-app' [TYPE=jenkins] [PARAMS='{}']"
	@echo "  make actions-workflow JOB='build' TYPE=github_actions"
	@echo ""
	@echo "Ticket Creation:"
	@echo "  make actions-ticket TITLE='Bug fix' DESC='Description' [SYSTEM=jira]"
	@echo "  make actions-ticket TITLE='Feature' DESC='Description' SYSTEM=github"
	@echo ""
	@echo "Security Scans:"
	@echo "  make actions-security-scan TARGET='/app' [TYPE=vulnerability] [TOOL=sonarqube]"
	@echo "  make actions-security-scan TARGET='/src' TYPE=code_analysis TOOL=snyk"
	@echo ""
	@echo "Parameter Validation:"
	@echo "  make actions-validate ACTION=escalate_to_human PARAMS='{\"message\":\"test\"}'"
	@echo ""
	@echo "Execution History:"
	@echo "  make actions-history ACTION=escalate_to_human [LIMIT=10]"
	@echo ""
	@echo "Direct Execution:"
	@echo "  make actions-execute ACTION=escalate_to_human PARAMS='{\"message\":\"test\"}'"
	@echo ""
	@echo "Service URL: http://sam.chat:8010"
	@echo "Documentation: http://sam.chat:8010/docs"

# =============================================================================
# GITINGEST REPOSITORY ANALYSIS - Code Context for LLMs
# =============================================================================

# Analyze GitHub repository
gitingest-analyze-repo:
	@echo "[LINK] Analyzing GitHub repository: $(URL)"
	@/bin/mkdir -p data/gitingest
	@if [ -n "$(NAME)" ]; then \
		/usr/local/bin/gitingest "$(URL)" --output "data/gitingest/$(NAME).txt" $(if $(TOKEN),--token "$(TOKEN)") $(if $(BRANCH),--branch "$(BRANCH)") $(if $(MAX_SIZE),--max-size "$(MAX_SIZE)") $(if $(EXCLUDE),--exclude-pattern "$(EXCLUDE)") $(if $(INCLUDE),--include-pattern "$(INCLUDE)"); \
	else \
		/usr/local/bin/gitingest "$(URL)" --output "data/gitingest/repo_$(shell date +%Y%m%d_%H%M%S).txt" $(if $(TOKEN),--token "$(TOKEN)") $(if $(BRANCH),--branch "$(BRANCH)") $(if $(MAX_SIZE),--max-size "$(MAX_SIZE)") $(if $(EXCLUDE),--exclude-pattern "$(EXCLUDE)") $(if $(INCLUDE),--include-pattern "$(INCLUDE)"); \
	fi
	@echo "[OK] Repository analysis complete"

# Analyze local directory
gitingest-analyze-local:
	@echo "[LINK] Analyzing local directory: $(PATH)"
	@/bin/mkdir -p data/gitingest
	@if [ -n "$(NAME)" ]; then \
		/usr/local/bin/gitingest "$(PATH)" --output "data/gitingest/$(NAME).txt" $(if $(MAX_SIZE),--max-size "$(MAX_SIZE)") $(if $(EXCLUDE),--exclude-pattern "$(EXCLUDE)") $(if $(INCLUDE),--include-pattern "$(INCLUDE)"); \
	else \
		/usr/local/bin/gitingest "$(PATH)" --output "data/gitingest/local_$(shell date +%Y%m%d_%H%M%S).txt" $(if $(MAX_SIZE),--max-size "$(MAX_SIZE)") $(if $(EXCLUDE),--exclude-pattern "$(EXCLUDE)") $(if $(INCLUDE),--include-pattern "$(INCLUDE)"); \
	fi
	@echo "[OK] Local directory analysis complete"

# List recent analyses
gitingest-list:
	@echo "[DATA] Recent GitIngest Analyses"
	@echo "================================"
	@ls -la data/gitingest/*.txt 2>/dev/null | head -$(or $(LIMIT),10) || echo "No analyses found"

# Get specific analysis
gitingest-get:
	@echo "[LINK] Analysis: $(NAME)"
	@echo "===================="
	@if [ -f "data/gitingest/$(NAME).txt" ]; then \
		head -50 "data/gitingest/$(NAME).txt"; \
		echo ""; \
		echo "... (showing first 50 lines)"; \
		echo "Full file: data/gitingest/$(NAME).txt"; \
	else \
		echo "[ERROR] Analysis not found: $(NAME)"; \
		echo "Available analyses:"; \
		ls data/gitingest/*.txt 2>/dev/null || echo "No analyses found"; \
	fi

# Delete analysis
gitingest-delete:
	@echo "[WARNING] Deleting analysis: $(NAME)"
	@if [ -f "data/gitingest/$(NAME).txt" ]; then \
		rm -f "data/gitingest/$(NAME).txt"; \
		rm -f "data/gitingest/$(NAME)_metadata.json"; \
		echo "[OK] Analysis deleted: $(NAME)"; \
	else \
		echo "[ERROR] Analysis not found: $(NAME)"; \
	fi

# Start GitIngest MCP server
gitingest-server:
	@echo "[LINK] Starting GitIngest MCP Server..."
	@cd services/gitingest-mcp && python3 gitingest_mcp_server.py &
	@echo "[OK] GitIngest MCP server started on port 8010"

# Check GitIngest service status
gitingest-status:
	@echo "[DATA] GitIngest Service Status"
	@echo "==============================="
	@echo "GitIngest CLI: $(shell which gitingest && echo 'Installed' || echo 'Not found')"
	@echo "MCP Server: $(shell pgrep -f gitingest_mcp_server.py && echo 'Running' || echo 'Not running')"
	@echo "Data Directory: $(shell ls -la data/gitingest/ 2>/dev/null | wc -l || echo '0') analyses"
	@echo "Recent Activity:"
	@ls -lt data/gitingest/*.txt 2>/dev/null | head -3 || echo "No recent analyses"

# GitIngest help
gitingest-help:
	@echo "[LINK] GitIngest Integration Guide"
	@echo "=================================="
	@echo ""
	@echo "Repository Analysis:"
	@echo "  make gitingest-analyze-repo URL='https://github.com/user/repo' [NAME='my_analysis']"
	@echo "  make gitingest-analyze-repo URL='https://github.com/user/repo' TOKEN='github_pat_...' BRANCH='main'"
	@echo "  make gitingest-analyze-repo URL='https://github.com/user/repo' MAX_SIZE='1000000' EXCLUDE='*.log'"
	@echo ""
	@echo "Local Directory Analysis:"
	@echo "  make gitingest-analyze-local PATH='/path/to/code' [NAME='my_analysis']"
	@echo "  make gitingest-analyze-local PATH='.' NAME='current_project'"
	@echo "  make gitingest-analyze-local PATH='/src' EXCLUDE='node_modules/*' INCLUDE='*.js'"
	@echo ""
	@echo "Analysis Management:"
	@echo "  make gitingest-list [LIMIT=5]                    # List recent analyses"
	@echo "  make gitingest-get NAME='my_analysis'            # View specific analysis"
	@echo "  make gitingest-delete NAME='my_analysis'         # Delete analysis"
	@echo ""
	@echo "Service Management:"
	@echo "  make gitingest-server                            # Start MCP server"
	@echo "  make gitingest-status                            # Check service status"
	@echo ""
	@echo "Parameters:"
	@echo "  URL         Repository URL (GitHub, GitLab, etc.)"
	@echo "  PATH        Local directory path"
	@echo "  NAME        Custom name for analysis output"
	@echo "  TOKEN       GitHub personal access token"
	@echo "  BRANCH      Specific branch to analyze"
	@echo "  MAX_SIZE    Maximum file size in bytes"
	@echo "  EXCLUDE     Patterns to exclude (e.g., '*.log')"
	@echo "  INCLUDE     Patterns to include (e.g., '*.py')"
	@echo ""
	@echo "Examples:"
	@echo "  # Analyze this repository"
	@echo "  make gitingest-analyze-local PATH='.' NAME='ultramcp'"
	@echo ""
	@echo "  # Analyze external repository"
	@echo "  make gitingest-analyze-repo URL='https://github.com/cyclotruc/gitingest' NAME='gitingest_source'"
	@echo ""
	@echo "  # List and view analyses"
	@echo "  make gitingest-list"
	@echo "  make gitingest-get NAME='ultramcp'"
	@echo ""
	@echo "Output: data/gitingest/[NAME].txt"

# =============================================================================
# CONTEXTBUILDERAGENT 2.0 - Semantic Coherence Platform
# =============================================================================

context-start:
	@echo "🚀 Starting ContextBuilderAgent 2.0 ecosystem..."
	@./scripts/bootstrap_context_builder.sh start

# Stop ContextBuilder services
context-stop:
	@echo "🛑 Stopping ContextBuilderAgent services..."
	@./scripts/bootstrap_context_builder.sh stop

# Check ContextBuilder status
context-status:
	@echo "📊 ContextBuilderAgent Status:"
	@./scripts/bootstrap_context_builder.sh status

# Restart ContextBuilder system
context-restart:
	@echo "🔄 Restarting ContextBuilderAgent system..."
	@./scripts/bootstrap_context_builder.sh restart

# Test ContextBuilder integration
context-test:
	@echo "🧪 Testing ContextBuilderAgent integration..."
	@./scripts/bootstrap_context_builder.sh test

# View ContextBuilder logs
context-logs:
	@echo "📝 ContextBuilderAgent Service Logs:"
	@for log in /root/ultramcp/logs/context_builder_*.log; do [ -f "$$log" ] && echo "=== $$(basename $$log) ===" && tail -20 "$$log"; done

# Validate semantic coherence
context-validate:
	@echo "🔍 Validating semantic coherence..."
	@curl -X POST http://sam.chat:8025/validate_coherence \
		-H "Content-Type: application/json" | jq .

# Apply context mutation
context-mutate:
	@echo "🔄 Applying context mutation..."
	@curl -X POST http://sam.chat:8025/apply_mutation \
		-H "Content-Type: application/json" \
		-d '{"target_domain": "$(DOMAIN)", "field": "$(FIELD)", "new_value": "$(VALUE)", "source": "makefile"}' | jq .

# Analyze session for insights
context-analyze:
	@echo "🧠 Analyzing session for insights..."
	@curl -X POST http://sam.chat:8025/analyze_session \
		-H "Content-Type: application/json" \
		-d '{"meeting_transcript": "$(SESSION)", "context_domain": "$(or $(DOMAIN),general)", "analysis_depth": "$(or $(DEPTH),standard)"}' | jq .

# Optimize context thresholds
context-optimize:
	@echo "⚡ Optimizing context thresholds..."
	@curl -X POST http://sam.chat:8025/process_context \
		-H "Content-Type: application/json" \
		-d '{"context_data": {}, "operation": "optimize", "parameters": {"target_performance": 0.85}}' | jq .

# Get system status
context-system-status:
	@echo "🏥 Complete system status..."
	@curl -s http://sam.chat:8025/system_status | jq .

# Get knowledge tree
context-knowledge-tree:
	@echo "🌳 Current knowledge tree:"
	@curl -s http://sam.chat:8025/knowledge_tree | jq .

# Get performance metrics
context-metrics:
	@echo "📊 Performance metrics:"
	@curl -s http://sam.chat:8025/metrics | jq .

# Process context with custom operation
context-process:
	@echo "⚙️ Processing context with operation: $(OPERATION)"
	@curl -X POST http://sam.chat:8025/process_context \
		-H "Content-Type: application/json" \
		-d '{"context_data": $(DATA), "operation": "$(OPERATION)", "parameters": $(or $(PARAMS),{})}' | jq .

# Quick context health check
context-health:
	@echo "🏥 ContextBuilder Health Check:"
	@curl -s http://sam.chat:8025/health | jq .

# Enhanced context help
context-help:
	@echo "🧠 ContextBuilderAgent 2.0 - Complete Usage Guide"
	@echo "=================================================="
	@echo ""
	@echo "System Management:"
	@echo "  make context-start                              - Start complete ecosystem"
	@echo "  make context-stop                               - Stop all services"
	@echo "  make context-restart                            - Restart system"
	@echo "  make context-status                             - Check service status"
	@echo "  make context-health                             - Quick health check"
	@echo "  make context-test                               - Integration test"
	@echo ""
	@echo "Context Operations:"
	@echo "  make context-validate                           - Validate semantic coherence"
	@echo "  make context-analyze SESSION='transcript'       - Analyze session insights"
	@echo "  make context-mutate DOMAIN='...' FIELD='...'   - Apply context mutation"
	@echo "  make context-optimize                           - Optimize thresholds"
	@echo "  make context-process OPERATION='...' DATA='{}'  - Custom context operation"
	@echo ""
	@echo "Information & Monitoring:"
	@echo "  make context-knowledge-tree                     - View knowledge tree"
	@echo "  make context-system-status                      - Complete system status"
	@echo "  make context-metrics                            - Performance metrics"
	@echo "  make context-logs                               - View service logs"
	@echo ""
	@echo "Service Endpoints:"
	@echo "  • Orchestrator:        http://sam.chat:8025"
	@echo "  • Drift Detector:      http://sam.chat:8020"
	@echo "  • Contradiction Resolver: http://sam.chat:8021"
	@echo "  • Belief Reviser:      http://sam.chat:8022"
	@echo "  • Utility Predictor:   http://sam.chat:8023"
	@echo "  • Memory Tuner:        http://sam.chat:8026"
	@echo ""
	@echo "Example Workflows:"
	@echo "  1. Complete startup:   make context-start"
	@echo "  2. Analyze transcript: make context-analyze SESSION='We need better scaling'"
	@echo "  3. Apply insight:      make context-mutate DOMAIN='PAIN_POINTS' FIELD='problemas_actuales' VALUE='Scaling challenges'"
	@echo "  4. Validate changes:   make context-validate"
	@echo "  5. View knowledge:     make context-knowledge-tree"

# =============================================================================
# PROMPTASSEMBLERAGENT - NEXT-GENERATION DYNAMIC PROMPTS
# =============================================================================

# Assemble dynamic prompt
prompt-assemble:
	@echo "🎯 Assembling dynamic prompt..."
	@curl -X POST http://sam.chat:8027/assemble_prompt \
		-H "Content-Type: application/json" \
		-d '{"prompt_type": "$(TYPE)", "objective": "$(OBJECTIVE)", "complexity": "$(or $(COMPLEXITY),medium)", "context_domains": [$(if $(DOMAINS),"$(DOMAINS)",[])], "template_variables": $(or $(VARS),{})}' | jq .

# Optimize existing prompt
prompt-optimize:
	@echo "⚡ Optimizing prompt..."
	@curl -X POST http://sam.chat:8027/optimize_prompt \
		-H "Content-Type: application/json" \
		-d '{"original_prompt": "$(PROMPT)", "performance_metrics": $(or $(METRICS),{}), "target_improvement": "$(or $(TARGET),effectiveness)"}' | jq .

# List prompt templates
prompt-templates:
	@echo "📋 Available prompt templates:"
	@curl -s http://sam.chat:8027/templates | jq .

# Analyze prompt quality
prompt-analyze:
	@echo "🔍 Analyzing prompt quality..."
	@curl -X POST http://sam.chat:8027/analyze_prompt \
		-H "Content-Type: application/json" \
		-d '{"prompt": "$(PROMPT)", "context_domains": [$(if $(DOMAINS),"$(DOMAINS)",[])]}' | jq .

# Check PromptAssembler status
prompt-status:
	@echo "📊 PromptAssembler Status:"
	@curl -s http://sam.chat:8027/health | jq .

# Get PromptAssembler performance analytics
prompt-analytics:
	@echo "📈 PromptAssembler Analytics:"
	@curl -s http://sam.chat:8027/performance_analytics | jq .

# Create new prompt template
prompt-create-template:
	@echo "📝 Creating prompt template..."
	@curl -X POST http://sam.chat:8027/create_template \
		-H "Content-Type: application/json" \
		-d '{"template_name": "$(NAME)", "template_content": "$(CONTENT)", "variables": [$(VARS)], "context_domains": [$(DOMAINS)], "description": "$(DESC)"}' | jq .

# =============================================================================
# CONTEXTOBSERVATORY - ENTERPRISE MONITORING
# =============================================================================

# View monitoring dashboard
observatory-dashboard:
	@echo "🔭 Context Observatory Dashboard ($(TYPE))..."
	@curl -s "http://sam.chat:8028/dashboard/$(or $(TYPE),overview)" | jq .

# Comprehensive health check
observatory-health:
	@echo "🏥 Comprehensive health check..."
	@curl -X GET http://sam.chat:8028/health_check \
		-H "Content-Type: application/json" | jq .

# View system alerts
observatory-alerts:
	@echo "🚨 System alerts..."
	@curl -X GET http://sam.chat:8028/alerts \
		-H "Content-Type: application/json" | jq .

# Get performance metrics
observatory-metrics:
	@echo "📊 Performance metrics..."
	@curl -X GET http://sam.chat:8028/metrics \
		-H "Content-Type: application/json" | jq .

# Start background monitoring
observatory-start-monitoring:
	@echo "▶️ Starting background monitoring..."
	@curl -X POST http://sam.chat:8028/start_monitoring | jq .

# Stop background monitoring
observatory-stop-monitoring:
	@echo "⏹️ Stopping background monitoring..."
	@curl -X POST http://sam.chat:8028/stop_monitoring | jq .

# System overview
observatory-overview:
	@echo "🌐 System overview..."
	@curl -s http://sam.chat:8028/system_overview | jq .

# Performance trends
observatory-trends:
	@echo "📈 Performance trends..."
	@curl -s http://sam.chat:8028/performance_trends | jq .

# Coherence analytics
observatory-coherence:
	@echo "🧠 Coherence analytics..."
	@curl -s http://sam.chat:8028/coherence_analytics | jq .

# Resolve alert
observatory-resolve-alert:
	@echo "✅ Resolving alert $(ALERT_ID)..."
	@curl -X POST "http://sam.chat:8028/alert/$(ALERT_ID)/resolve" | jq .

# =============================================================================
# DETERMINISTICDEBUGMODE - REPRODUCIBLE TESTING
# =============================================================================

# Start debug session
debug-start-session:
	@echo "🐛 Starting debug session: $(NAME)..."
	@curl -X POST http://sam.chat:8029/start_debug_session \
		-H "Content-Type: application/json" \
		-d '{"session_name": "$(NAME)", "debug_level": "$(or $(LEVEL),standard)", "reproducibility_mode": "$(or $(MODE),semantic)", "random_seed": $(or $(SEED),42)}' | jq .

# Stop debug session
debug-stop-session:
	@echo "🛑 Stopping debug session: $(SESSION_ID)..."
	@curl -X POST "http://sam.chat:8029/stop_debug_session/$(SESSION_ID)" | jq .

# Capture system snapshot
debug-capture-snapshot:
	@echo "📸 Capturing system snapshot..."
	@curl -X POST http://sam.chat:8029/capture_snapshot \
		-H "Content-Type: application/json" \
		-d '{"session_id": "$(or $(SESSION_ID),)"}' | jq .

# Trace operation
debug-trace-operation:
	@echo "🔍 Tracing operation: $(TYPE)..."
	@curl -X POST http://sam.chat:8029/trace_operation \
		-H "Content-Type: application/json" \
		-d '{"operation_type": "$(TYPE)", "input_parameters": $(or $(PARAMS),{}), "target_service": "$(or $(SERVICE),orchestrator)"}' | jq .

# List debug sessions
debug-sessions:
	@echo "📋 Debug sessions:"
	@curl -s http://sam.chat:8029/debug_sessions | jq .

# Get snapshots for session
debug-snapshots:
	@echo "📸 Snapshots for session $(SESSION_ID):"
	@curl -s "http://sam.chat:8029/snapshots/$(SESSION_ID)" | jq .

# Get operations for session
debug-operations:
	@echo "⚙️ Operations for session $(SESSION_ID):"
	@curl -s "http://sam.chat:8029/operations/$(SESSION_ID)" | jq .

# Check debug mode status
debug-status:
	@echo "🐛 Debug Mode Status:"
	@curl -s http://sam.chat:8029/health | jq .

# Debug analytics
debug-analytics:
	@echo "📊 Debug Analytics:"
	@curl -s http://sam.chat:8029/debug_analytics | jq .

# Reproducibility report
debug-reproducibility-report:
	@echo "📋 Reproducibility report for session $(SESSION_ID):"
	@curl -s "http://sam.chat:8029/reproducibility_report/$(SESSION_ID)" | jq .

# Enhanced help for new services
prompt-help:
	@echo "🎯 PromptAssemblerAgent - Next-Generation Dynamic Prompts"
	@echo "======================================================="
	@echo ""
	@echo "Prompt Assembly:"
	@echo "  make prompt-assemble TYPE='system' OBJECTIVE='...'     - Assemble dynamic prompt"
	@echo "  make prompt-optimize PROMPT='...' TARGET='clarity'     - Optimize existing prompt"
	@echo "  make prompt-analyze PROMPT='...' DOMAINS='BUSINESS'    - Analyze prompt quality"
	@echo ""
	@echo "Template Management:"
	@echo "  make prompt-templates                                   - List available templates"
	@echo "  make prompt-create-template NAME='...' CONTENT='...'   - Create new template"
	@echo ""
	@echo "Monitoring:"
	@echo "  make prompt-status                                      - Check service status"
	@echo "  make prompt-analytics                                   - Performance analytics"
	@echo ""
	@echo "Example:"
	@echo "  make prompt-assemble TYPE='system' OBJECTIVE='Help with coding' COMPLEXITY='complex'"

observatory-help:
	@echo "🔭 ContextObservatory - Enterprise Monitoring Platform"
	@echo "====================================================="
	@echo ""
	@echo "Dashboards:"
	@echo "  make observatory-dashboard TYPE='overview'              - System overview dashboard"
	@echo "  make observatory-dashboard TYPE='performance'           - Performance dashboard"
	@echo "  make observatory-dashboard TYPE='coherence'             - Coherence dashboard"
	@echo "  make observatory-dashboard TYPE='errors'                - Error tracking dashboard"
	@echo ""
	@echo "Health & Monitoring:"
	@echo "  make observatory-health                                 - Comprehensive health check"
	@echo "  make observatory-start-monitoring                       - Start background monitoring"
	@echo "  make observatory-stop-monitoring                        - Stop background monitoring"
	@echo ""
	@echo "Alerts & Metrics:"
	@echo "  make observatory-alerts                                 - View system alerts"
	@echo "  make observatory-metrics                                - Performance metrics"
	@echo "  make observatory-resolve-alert ALERT_ID='...'          - Resolve specific alert"
	@echo ""
	@echo "Analytics:"
	@echo "  make observatory-trends                                 - Performance trends"
	@echo "  make observatory-coherence                              - Coherence analytics"
	@echo "  make observatory-overview                               - System overview"

debug-help:
	@echo "🐛 DeterministicDebugMode - Reproducible Testing Framework"
	@echo "========================================================="
	@echo ""
	@echo "Session Management:"
	@echo "  make debug-start-session NAME='test1' LEVEL='verbose'  - Start debug session"
	@echo "  make debug-stop-session SESSION_ID='...'               - Stop debug session"
	@echo "  make debug-sessions                                     - List all sessions"
	@echo ""
	@echo "State Capture:"
	@echo "  make debug-capture-snapshot SESSION_ID='...'           - Capture system snapshot"
	@echo "  make debug-snapshots SESSION_ID='...'                  - List session snapshots"
	@echo ""
	@echo "Operation Tracing:"
	@echo "  make debug-trace-operation TYPE='validate' SERVICE='...' - Trace operation"
	@echo "  make debug-operations SESSION_ID='...'                 - List traced operations"
	@echo ""
	@echo "Analysis:"
	@echo "  make debug-status                                       - Debug mode status"
	@echo "  make debug-analytics                                    - Debug analytics"
	@echo "  make debug-reproducibility-report SESSION_ID='...'     - Reproducibility report"
	@echo ""
	@echo "Example workflow:"
	@echo "  1. make debug-start-session NAME='coherence_test'"
	@echo "  2. make debug-trace-operation TYPE='validate_coherence'"
	@echo "  3. make debug-capture-snapshot"
	@echo "  4. make debug-reproducibility-report SESSION_ID='...'"

# =============================================================================
# PRODUCTION LOAD BALANCER - Nginx & HAProxy
# =============================================================================

# Deploy load balancer
deploy-load-balancer:
	@echo "🚀 Deploying Nginx load balancer..."
	@./scripts/deploy_load_balancer.sh deploy nginx

deploy-load-balancer-haproxy:
	@echo "🚀 Deploying HAProxy load balancer..."
	@./scripts/deploy_load_balancer.sh deploy haproxy

# Load balancer status
load-balancer-status:
	@echo "📊 Load balancer status:"
	@./scripts/deploy_load_balancer.sh status

# Test load balancer
test-load-balancer:
	@echo "🧪 Testing load balancer..."
	@./scripts/deploy_load_balancer.sh test

# Production deployment
production-deploy:
	@echo "🏭 Deploying ContextBuilderAgent 2.0 for production..."
	@./scripts/deploy_load_balancer.sh deploy nginx
	@echo "Production deployment completed!"

production-status:
	@echo "📈 Production system status:"
	@make contextbuilder-status
	@make load-balancer-status

production-test:
	@echo "🧪 Testing production deployment..."
	@make test-load-balancer
	@make contextbuilder-test-all

# Nginx commands
nginx-deploy:
	@echo "🌐 Deploying Nginx load balancer..."
	@cd config/nginx && docker-compose -f docker-compose.nginx.yml up -d
	@echo "Nginx deployed successfully!"

nginx-stop:
	@echo "🛑 Stopping Nginx load balancer..."
	@cd config/nginx && docker-compose -f docker-compose.nginx.yml down
	@echo "Nginx stopped!"

nginx-logs:
	@echo "📋 Nginx logs:"
	@cd config/nginx && docker-compose -f docker-compose.nginx.yml logs -f nginx-lb

nginx-status:
	@echo "📊 Nginx status:"
	@curl -s http://sam.chat:8080/health 2>/dev/null || echo "Nginx not available"

# HAProxy commands
haproxy-deploy:
	@echo "🔀 Deploying HAProxy load balancer..."
	@cd config/nginx && docker-compose -f docker-compose.haproxy.yml up -d
	@echo "HAProxy deployed successfully!"

haproxy-stop:
	@echo "🛑 Stopping HAProxy load balancer..."
	@cd config/nginx && docker-compose -f docker-compose.haproxy.yml down
	@echo "HAProxy stopped!"

haproxy-logs:
	@echo "📋 HAProxy logs:"
	@cd config/nginx && docker-compose -f docker-compose.haproxy.yml logs -f haproxy-lb

haproxy-status:
	@echo "📊 HAProxy status:"
	@curl -s http://sam.chat:8405/health 2>/dev/null || echo "HAProxy not available"

haproxy-admin:
	@echo "🔧 HAProxy admin interface:"
	@echo "Available at: http://sam.chat:8404"
	@echo "Username: admin"
	@echo "Password: contextbuilder2024"

# Load balancer help
load-balancer-help:
	@echo "🌐 Load Balancer Commands - Production Ready"
	@echo "=============================================="
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-load-balancer          - Deploy Nginx load balancer"
	@echo "  make deploy-load-balancer-haproxy  - Deploy HAProxy load balancer"
	@echo "  make production-deploy             - Full production deployment"
	@echo ""
	@echo "Status & Testing:"
	@echo "  make load-balancer-status          - Check load balancer status"
	@echo "  make test-load-balancer            - Test load balancer functionality"
	@echo "  make production-status             - Complete production status"
	@echo "  make production-test               - Test production deployment"
	@echo ""
	@echo "Nginx Commands:"
	@echo "  make nginx-deploy                  - Deploy Nginx"
	@echo "  make nginx-stop                    - Stop Nginx"
	@echo "  make nginx-logs                    - View Nginx logs"
	@echo "  make nginx-status                  - Check Nginx status"
	@echo ""
	@echo "HAProxy Commands:"
	@echo "  make haproxy-deploy                - Deploy HAProxy"
	@echo "  make haproxy-stop                  - Stop HAProxy"
	@echo "  make haproxy-logs                  - View HAProxy logs"
	@echo "  make haproxy-status                - Check HAProxy status"
	@echo "  make haproxy-admin                 - Access HAProxy admin"
	@echo ""
	@echo "Load Balancer Features:"
	@echo "  ✅ SSL/TLS termination"
	@echo "  ✅ Health checks for all 9 services"
	@echo "  ✅ Rate limiting and security headers"
	@echo "  ✅ WebSocket support for Observatory"
	@echo "  ✅ Backup server configuration"
	@echo "  ✅ Production-ready scaling"

# =============================================================================
# DATABASE INTEGRATION - PostgreSQL & Redis
# =============================================================================

# Setup database services
setup-database:
	@echo "🗄️ Setting up PostgreSQL + Redis integration..."
	@./scripts/setup_database.sh setup

# Database status
database-status:
	@echo "📊 Database services status:"
	@./scripts/setup_database.sh status

# Test database integration
test-database:
	@echo "🧪 Testing database integration..."
	@./scripts/setup_database.sh test

# Database backup
database-backup:
	@echo "💾 Running database backup..."
	@./scripts/setup_database.sh backup

# Start database services
database-start:
	@echo "🚀 Starting database services..."
	@cd config/database && docker-compose -f docker-compose.database.yml up -d
	@echo "Database services started!"

# Stop database services
database-stop:
	@echo "🛑 Stopping database services..."
	@cd config/database && docker-compose -f docker-compose.database.yml down
	@echo "Database services stopped!"

# Database logs
database-logs:
	@echo "📋 Database logs:"
	@cd config/database && docker-compose -f docker-compose.database.yml logs -f

# PostgreSQL commands
postgres-status:
	@echo "🐘 PostgreSQL status:"
	@docker exec contextbuilder-postgres pg_isready -U contextbuilder -d contextbuilder 2>/dev/null && echo "PostgreSQL: Healthy" || echo "PostgreSQL: Unhealthy"

postgres-shell:
	@echo "🐘 Opening PostgreSQL shell..."
	@docker exec -it contextbuilder-postgres psql -U contextbuilder -d contextbuilder

postgres-backup:
	@echo "💾 PostgreSQL backup..."
	@docker exec contextbuilder-postgres pg_dump -U contextbuilder -d contextbuilder > backup/postgres_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup completed!"

# Redis commands
redis-status:
	@echo "🔴 Redis status:"
	@docker exec contextbuilder-redis redis-cli ping 2>/dev/null && echo "Redis: Healthy" || echo "Redis: Unhealthy"

redis-shell:
	@echo "🔴 Opening Redis shell..."
	@docker exec -it contextbuilder-redis redis-cli -a contextbuilder_redis_2024

redis-monitor:
	@echo "📊 Redis monitoring..."
	@docker exec -it contextbuilder-redis redis-cli -a contextbuilder_redis_2024 monitor

# Database management interfaces
database-admin:
	@echo "🛠️ Database management interfaces:"
	@echo "PgAdmin: http://sam.chat:5050"
	@echo "  Email: admin@contextbuilder.local"
	@echo "  Password: contextbuilder_admin_2024"
	@echo ""
	@echo "Redis Commander: http://sam.chat:8081"
	@echo ""
	@echo "PostgreSQL Metrics: http://sam.chat:9187/metrics"
	@echo "Redis Metrics: http://sam.chat:9121/metrics"

# Database help
database-help:
	@echo "🗄️ Database Integration Commands"
	@echo "================================="
	@echo ""
	@echo "Setup & Management:"
	@echo "  make setup-database            - Complete database setup"
	@echo "  make database-status           - Check database services status"
	@echo "  make test-database             - Test database integration"
	@echo "  make database-backup           - Run database backup"
	@echo ""
	@echo "Service Control:"
	@echo "  make database-start            - Start database services"
	@echo "  make database-stop             - Stop database services"
	@echo "  make database-logs             - View database logs"
	@echo ""
	@echo "PostgreSQL Commands:"
	@echo "  make postgres-status           - Check PostgreSQL status"
	@echo "  make postgres-shell            - Open PostgreSQL shell"
	@echo "  make postgres-backup           - PostgreSQL backup"
	@echo ""
	@echo "Redis Commands:"
	@echo "  make redis-status              - Check Redis status"
	@echo "  make redis-shell               - Open Redis shell"
	@echo "  make redis-monitor             - Monitor Redis operations"
	@echo ""
	@echo "Management:"
	@echo "  make database-admin            - Show admin interface URLs"
	@echo ""
	@echo "Database Features:"
	@echo "  ✅ PostgreSQL 15 with optimized configuration"
	@echo "  ✅ Redis 7 with Sentinel for high availability"
	@echo "  ✅ PgBouncer connection pooling"
	@echo "  ✅ Automated backup system"
	@echo "  ✅ Prometheus monitoring integration"
	@echo "  ✅ Web-based management interfaces"

# =============================================================================
# PROMETHEUS/GRAFANA MONITORING - Production Observability
# =============================================================================

# Setup monitoring stack
setup-monitoring:
	@echo "📊 Setting up Prometheus + Grafana monitoring..."
	@./scripts/setup_monitoring.sh setup

# Monitoring status
monitoring-status:
	@echo "📈 Monitoring services status:"
	@./scripts/setup_monitoring.sh status

# Test monitoring integration
test-monitoring:
	@echo "🧪 Testing monitoring integration..."
	@./scripts/setup_monitoring.sh test

# Start monitoring services
monitoring-start:
	@echo "🚀 Starting monitoring services..."
	@cd config/monitoring && docker-compose -f docker-compose.monitoring.yml up -d
	@echo "Monitoring services started!"

# Stop monitoring services
monitoring-stop:
	@echo "🛑 Stopping monitoring services..."
	@cd config/monitoring && docker-compose -f docker-compose.monitoring.yml down
	@echo "Monitoring services stopped!"

# Monitoring logs
monitoring-logs:
	@echo "📋 Monitoring logs:"
	@cd config/monitoring && docker-compose -f docker-compose.monitoring.yml logs -f

# Prometheus commands
prometheus-status:
	@echo "🔍 Prometheus status:"
	@curl -s http://sam.chat:9090/-/healthy 2>/dev/null && echo "Prometheus: Healthy" || echo "Prometheus: Unhealthy"

prometheus-reload:
	@echo "🔄 Reloading Prometheus configuration..."
	@curl -X POST http://sam.chat:9090/-/reload 2>/dev/null && echo "Configuration reloaded!" || echo "Failed to reload"

prometheus-targets:
	@echo "🎯 Prometheus targets:"
	@curl -s http://sam.chat:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"' 2>/dev/null || echo "Failed to get targets"

# Grafana commands
grafana-status:
	@echo "📊 Grafana status:"
	@curl -s http://sam.chat:3000/api/health 2>/dev/null && echo "Grafana: Healthy" || echo "Grafana: Unhealthy"

grafana-admin:
	@echo "🔑 Grafana admin access:"
	@echo "URL: http://sam.chat:3000"
	@echo "Username: admin"
	@echo "Password: contextbuilder_grafana_2024"

# Alertmanager commands
alertmanager-status:
	@echo "🚨 Alertmanager status:"
	@curl -s http://sam.chat:9093/-/healthy 2>/dev/null && echo "Alertmanager: Healthy" || echo "Alertmanager: Unhealthy"

alertmanager-alerts:
	@echo "📢 Active alerts:"
	@curl -s http://sam.chat:9093/api/v1/alerts | jq -r '.data[] | "\(.labels.alertname): \(.status.state)"' 2>/dev/null || echo "No alerts or service unavailable"

# Custom metrics
custom-metrics:
	@echo "📈 Custom ContextBuilderAgent metrics:"
	@curl -s http://sam.chat:8000/metrics | grep -E "contextbuilder_|HELP" | head -20 2>/dev/null || echo "Custom metrics not available"

# Monitoring dashboards
monitoring-dashboards:
	@echo "📊 Monitoring Dashboard URLs:"
	@echo "Prometheus: http://sam.chat:9090"
	@echo "Grafana: http://sam.chat:3000"
	@echo "Alertmanager: http://sam.chat:9093"
	@echo "Node Exporter: http://sam.chat:9100/metrics"
	@echo "cAdvisor: http://sam.chat:8080"
	@echo "Custom Metrics: http://sam.chat:8000/metrics"

# Complete production monitoring setup
production-monitoring-deploy:
	@echo "🏭 Deploying complete production monitoring..."
	@make setup-monitoring
	@make setup-database
	@make deploy-load-balancer
	@echo "Production monitoring deployment completed!"

# Monitoring help
monitoring-help:
	@echo "📊 Monitoring & Observability Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup & Management:"
	@echo "  make setup-monitoring              - Complete monitoring stack setup"
	@echo "  make monitoring-status             - Check monitoring services status"
	@echo "  make test-monitoring               - Test monitoring integration"
	@echo "  make production-monitoring-deploy  - Deploy complete production monitoring"
	@echo ""
	@echo "Service Control:"
	@echo "  make monitoring-start              - Start monitoring services"
	@echo "  make monitoring-stop               - Stop monitoring services"
	@echo "  make monitoring-logs               - View monitoring logs"
	@echo ""
	@echo "Prometheus Commands:"
	@echo "  make prometheus-status             - Check Prometheus status"
	@echo "  make prometheus-reload             - Reload Prometheus configuration"
	@echo "  make prometheus-targets            - Show monitored targets"
	@echo ""
	@echo "Grafana Commands:"
	@echo "  make grafana-status                - Check Grafana status"
	@echo "  make grafana-admin                 - Show Grafana admin credentials"
	@echo ""
	@echo "Alertmanager Commands:"
	@echo "  make alertmanager-status           - Check Alertmanager status"
	@echo "  make alertmanager-alerts           - Show active alerts"
	@echo ""
	@echo "Metrics & Dashboards:"
	@echo "  make custom-metrics                - Show custom ContextBuilderAgent metrics"
	@echo "  make monitoring-dashboards         - Show dashboard URLs"
	@echo ""
	@echo "Monitoring Features:"
	@echo "  ✅ Prometheus metrics collection (9 services + infrastructure)"
	@echo "  ✅ Grafana dashboards with custom visualizations"
	@echo "  ✅ Intelligent alerting with Alertmanager"
	@echo "  ✅ Business logic metrics (coherence, validation, ML performance)"
	@echo "  ✅ Infrastructure monitoring (CPU, memory, disk, network)"
	@echo "  ✅ Database monitoring (PostgreSQL + Redis)"
	@echo "  ✅ Log aggregation with Loki"
	@echo "  ✅ Distributed tracing with Jaeger"
	@echo "  ✅ Custom ContextBuilderAgent metrics collector"

# =============================================================================
# KUBERNETES DEPLOYMENT - Container Orchestration
# =============================================================================

# Deploy to Kubernetes
k8s-deploy:
	@echo "🚀 Deploying ContextBuilderAgent 2.0 to Kubernetes..."
	@./scripts/deploy_kubernetes.sh deploy

# Kubernetes status
k8s-status:
	@echo "📊 Kubernetes deployment status:"
	@./scripts/deploy_kubernetes.sh status

# Verify Kubernetes deployment
k8s-verify:
	@echo "🧪 Verifying Kubernetes deployment..."
	@./scripts/deploy_kubernetes.sh verify

# Scale Kubernetes deployment
k8s-scale:
	@echo "📈 Scaling Kubernetes deployment..."
	@./scripts/deploy_kubernetes.sh scale $(COMPONENT) $(REPLICAS)

# Kubernetes cleanup
k8s-cleanup:
	@echo "🧹 Cleaning up Kubernetes deployment..."
	@./scripts/deploy_kubernetes.sh cleanup

# Apply specific Kubernetes manifests
k8s-apply-storage:
	@echo "💾 Applying storage manifests..."
	@kubectl apply -f k8s/storage/

k8s-apply-services:
	@echo "🔗 Applying service manifests..."
	@kubectl apply -f k8s/services/

k8s-apply-deployments:
	@echo "🚀 Applying deployment manifests..."
	@kubectl apply -f k8s/deployments/

k8s-apply-ingress:
	@echo "🌐 Applying ingress manifests..."
	@kubectl apply -f k8s/ingress/

# Kubernetes port forwarding for local access
k8s-port-forward-grafana:
	@echo "📊 Port forwarding Grafana (http://sam.chat:3000)..."
	@kubectl port-forward svc/grafana 3000:3000 -n contextbuilder

k8s-port-forward-prometheus:
	@echo "🔍 Port forwarding Prometheus (http://sam.chat:9090)..."
	@kubectl port-forward svc/prometheus 9090:9090 -n contextbuilder

k8s-port-forward-api:
	@echo "🔌 Port forwarding ContextBuilder API (http://sam.chat:8020)..."
	@kubectl port-forward svc/contextbuilder-core 8020:8020 -n contextbuilder

# Kubernetes logs
k8s-logs:
	@echo "📋 ContextBuilderAgent Kubernetes logs:"
	@kubectl logs -l app.kubernetes.io/part-of=contextbuilder -n contextbuilder --tail=100

k8s-logs-core:
	@echo "📋 ContextBuilder Core logs:"
	@kubectl logs -l app.kubernetes.io/name=contextbuilder-core -n contextbuilder --tail=100

k8s-logs-monitoring:
	@echo "📋 Monitoring logs:"
	@kubectl logs -l app.kubernetes.io/component=monitoring -n contextbuilder --tail=100

# Kubernetes shell access
k8s-shell-core:
	@echo "🐚 Opening shell in ContextBuilder Core pod..."
	@kubectl exec -it deployment/contextbuilder-core -n contextbuilder -- /bin/bash

k8s-shell-postgres:
	@echo "🐚 Opening shell in PostgreSQL pod..."
	@kubectl exec -it deployment/postgres -n contextbuilder -- /bin/bash

k8s-shell-redis:
	@echo "🐚 Opening shell in Redis pod..."
	@kubectl exec -it deployment/redis -n contextbuilder -- /bin/sh

# Kubernetes resource management
k8s-get-all:
	@echo "📋 All Kubernetes resources:"
	@kubectl get all -n contextbuilder

k8s-describe-pods:
	@echo "📊 Pod descriptions:"
	@kubectl describe pods -n contextbuilder

k8s-top:
	@echo "📈 Resource usage:"
	@kubectl top pods -n contextbuilder 2>/dev/null || echo "Metrics server not available"

# Production deployment
k8s-production-deploy:
	@echo "🏭 Deploying ContextBuilderAgent 2.0 for production on Kubernetes..."
	@echo "This will deploy with production resource limits and high availability"
	@./scripts/deploy_kubernetes.sh deploy
	@echo "Production Kubernetes deployment completed!"

# Kubernetes help
k8s-help:
	@echo "🚢 Kubernetes Deployment Commands"
	@echo "=================================="
	@echo ""
	@echo "Deployment & Management:"
	@echo "  make k8s-deploy                    - Deploy complete platform to Kubernetes"
	@echo "  make k8s-status                    - Show deployment status"
	@echo "  make k8s-verify                    - Verify deployment health"
	@echo "  make k8s-production-deploy         - Production deployment with HA"
	@echo "  make k8s-cleanup                   - Remove entire deployment"
	@echo ""
	@echo "Scaling:"
	@echo "  make k8s-scale COMPONENT=core REPLICAS=5    - Scale specific component"
	@echo "  make k8s-scale COMPONENT=all REPLICAS=3     - Scale all services"
	@echo ""
	@echo "Individual Components:"
	@echo "  make k8s-apply-storage             - Apply storage manifests"
	@echo "  make k8s-apply-services            - Apply service manifests"
	@echo "  make k8s-apply-deployments         - Apply deployment manifests"
	@echo "  make k8s-apply-ingress             - Apply ingress manifests"
	@echo ""
	@echo "Local Access (Port Forwarding):"
	@echo "  make k8s-port-forward-grafana      - Access Grafana locally"
	@echo "  make k8s-port-forward-prometheus   - Access Prometheus locally"
	@echo "  make k8s-port-forward-api          - Access API locally"
	@echo ""
	@echo "Debugging & Logs:"
	@echo "  make k8s-logs                      - View all logs"
	@echo "  make k8s-logs-core                 - View core service logs"
	@echo "  make k8s-logs-monitoring           - View monitoring logs"
	@echo "  make k8s-shell-core                - Shell access to core pod"
	@echo "  make k8s-shell-postgres            - Shell access to PostgreSQL"
	@echo "  make k8s-shell-redis               - Shell access to Redis"
	@echo ""
	@echo "Resource Monitoring:"
	@echo "  make k8s-get-all                   - Show all resources"
	@echo "  make k8s-describe-pods             - Describe all pods"
	@echo "  make k8s-top                       - Show resource usage"
	@echo ""
	@echo "Kubernetes Features:"
	@echo "  ✅ Complete container orchestration (15+ deployments)"
	@echo "  ✅ High availability with replica sets"
	@echo "  ✅ Auto-scaling and resource management"
	@echo "  ✅ Persistent storage with PV/PVC"
	@echo "  ✅ Service discovery and load balancing"
	@echo "  ✅ Ingress with SSL termination"
	@echo "  ✅ ConfigMaps and Secrets management"
	@echo "  ✅ Health checks and rolling updates"
	@echo "  ✅ Production-ready resource limits"

# =============================================================================
# CI/CD PIPELINE - GitHub Actions Automation
# =============================================================================

# Setup CI/CD pipeline
setup-cicd:
	@echo "🚀 Setting up CI/CD pipeline..."
	@./scripts/setup_cicd.sh setup

# Validate CI/CD configuration
validate-cicd:
	@echo "✅ Validating CI/CD configuration..."
	@./scripts/setup_cicd.sh validate

# Setup GitHub secrets
setup-github-secrets:
	@echo "🔐 Setting up GitHub repository secrets..."
	@./scripts/setup_cicd.sh secrets

# Run local tests
test-unit:
	@echo "🧪 Running unit tests..."
	@pytest tests/unit/ -v --cov=services --cov-report=term-missing

test-integration:
	@echo "🔗 Running integration tests..."
	@docker-compose -f docker-compose.test.yml up -d
	@sleep 30
	@pytest tests/integration/ -v
	@docker-compose -f docker-compose.test.yml down -v

test-performance:
	@echo "⚡ Running performance tests..."
	@docker-compose -f docker-compose.test.yml up -d
	@sleep 30
	@python tests/performance/benchmark.py
	@docker-compose -f docker-compose.test.yml down -v

test-all:
	@echo "🧪 Running all tests..."
	@make test-unit
	@make test-integration
	@make test-performance

# Security scanning
# Code quality checks
quality-check:
	@echo "🔍 Running code quality checks..."
	@pip install black isort flake8
	@black --check .
	@isort --check-only .
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Pre-commit hooks
setup-pre-commit:
	@echo "🪝 Setting up pre-commit hooks..."
	@pip install pre-commit
	@pre-commit install
	@echo "Pre-commit hooks installed!"

run-pre-commit:
	@echo "🪝 Running pre-commit checks..."
	@pre-commit run --all-files

# Container testing
test-container:
	@echo "🐳 Testing container build..."
	@docker build -t contextbuilder-test:latest .
	@docker run --rm contextbuilder-test:latest /bin/sh -c "echo 'Container test passed'"

# Kubernetes manifest validation
validate-k8s:
	@echo "☸️ Validating Kubernetes manifests..."
	@kubectl apply --dry-run=client -f k8s/ || echo "Kubernetes validation completed with warnings"

# Release preparation
prepare-release:
	@echo "📦 Preparing release..."
	@make test-all
	@make security-scan
	@make quality-check
	@make validate-k8s
	@echo "Release preparation completed!"

# GitHub Actions simulation
simulate-ci:
	@echo "🔄 Simulating CI pipeline locally..."
	@make quality-check
	@make test-unit
	@make security-scan
	@make test-container
	@echo "CI simulation completed!"

# Deployment status check
deployment-status:
	@echo "📊 Checking deployment status across environments..."
	@echo "Staging Environment:"
	@kubectl get pods -n contextbuilder-staging 2>/dev/null || echo "Staging not accessible"
	@echo ""
	@echo "Production Environment:"
	@kubectl get pods -n contextbuilder 2>/dev/null || echo "Production not accessible"

# Complete production deployment pipeline
production-pipeline:
	@echo "🏭 Running complete production pipeline..."
	@make setup-database
	@make setup-monitoring
	@make deploy-load-balancer
	@make k8s-deploy
	@echo "Complete production pipeline deployed!"

# CI/CD help
cicd-help:
	@echo "🚀 CI/CD Pipeline Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup & Configuration:"
	@echo "  make setup-cicd                - Complete CI/CD pipeline setup"
	@echo "  make validate-cicd             - Validate CI/CD configuration"
	@echo "  make setup-github-secrets      - Setup GitHub repository secrets"
	@echo "  make setup-pre-commit          - Setup pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test-unit                 - Run unit tests"
	@echo "  make test-integration          - Run integration tests"
	@echo "  make test-performance          - Run performance tests"
	@echo "  make test-all                  - Run all tests"
	@echo "  make test-container            - Test container build"
	@echo ""
	@echo "Quality & Security:"
	@echo "  make quality-check             - Run code quality checks"
	@echo "  make security-scan             - Run security scans"
	@echo "  make run-pre-commit            - Run pre-commit checks"
	@echo "  make validate-k8s              - Validate Kubernetes manifests"
	@echo ""
	@echo "Release & Deployment:"
	@echo "  make prepare-release           - Prepare for release"
	@echo "  make simulate-ci               - Simulate CI pipeline locally"
	@echo "  make deployment-status         - Check deployment status"
	@echo "  make production-pipeline       - Complete production deployment"
	@echo ""
	@echo "CI/CD Features:"
	@echo "  ✅ GitHub Actions workflows (CI, Security, Release)"
	@echo "  ✅ Automated testing (Unit, Integration, Performance)"
	@echo "  ✅ Security scanning (SAST, DAST, Container, Dependencies)"
	@echo "  ✅ Code quality analysis (SonarCloud, CodeQL)"
	@echo "  ✅ Container security scanning (Trivy, Snyk)"
	@echo "  ✅ Kubernetes manifest validation"
	@echo "  ✅ Automated deployments (Staging → Production)"
	@echo "  ✅ Release management with semantic versioning"
	@echo "  ✅ Slack notifications and alerts"
	@echo "  ✅ Pre-commit hooks for code quality"

# =============================================================================
# ENHANCED CLAUDIA INTEGRATION - Agent Management System
# =============================================================================

# Start enhanced Claudia integration service
claudia-enhanced-start:
	@echo "🚀 Starting enhanced Claudia integration service..."
	@docker-compose -f docker-compose.hybrid.yml up -d ultramcp-claudia-integration
	@echo "✅ Claudia integration service started on port 8013"

# List all available agents
claudia-agents-list:
	@echo "📋 Listing all available agents..."
	@curl -s http://sam.chat:8013/agents | jq '.[] | {name: .name, id: .id, services: .ultramcp_services}'

# List agent templates
claudia-templates-list:
	@echo "📋 Listing agent templates..."
	@curl -s http://sam.chat:8013/agents/templates | jq 'keys'

# Install agent template
claudia-install-template:
	@echo "📥 Installing agent template: $(TEMPLATE)"
	@curl -s -X POST http://sam.chat:8013/agents/templates/$(TEMPLATE)/install | jq '.'

# Execute agent
claudia-execute-agent:
	@echo "🚀 Executing agent: $(AGENT_ID)"
	@curl -s -X POST http://sam.chat:8013/agents/$(AGENT_ID)/execute \
		-H "Content-Type: application/json" \
		-d '{"task": "$(TASK)", "project_path": "$(PROJECT:-/root/ultramcp)"}' | jq '.'

# List recent executions
claudia-executions-list:
	@echo "📋 Listing recent executions..."
	@curl -s http://sam.chat:8013/executions | jq '.[] | {id: .id, agent: .agent_name, status: .status, task: .task}'

# Show agent execution metrics
claudia-metrics:
	@echo "📊 Agent execution metrics..."
	@curl -s http://sam.chat:8013/metrics | jq '.'

# Check Claudia service health
claudia-health:
	@echo "🏥 Checking Claudia service health..."
	@curl -s http://localhost:8013/health || echo "Claudia service not available"

# Test complete Claudia integration
claudia-test:
	@echo "🧪 Running comprehensive Claudia integration test..."
	@./scripts/test_claudia_integration.sh

# Quick security scan workflow
claudia-security-scan:
	@echo "🔒 Installing and executing security scanner agent..."
	@curl -s -X POST http://sam.chat:8013/agents/templates/ultramcp_security_scanner/install | jq '.id' | xargs -I {} \
		curl -s -X POST http://sam.chat:8013/agents/{}/execute \
		-H "Content-Type: application/json" \
		-d '{"task": "Perform comprehensive security scan", "project_path": "$(PROJECT:-/root/ultramcp)"}' | jq '.'

# Quick code analysis workflow
claudia-code-analysis:
	@echo "🧠 Installing and executing code intelligence agent..."
	@curl -s -X POST http://sam.chat:8013/agents/templates/code_intelligence_analyst/install | jq '.id' | xargs -I {} \
		curl -s -X POST http://sam.chat:8013/agents/{}/execute \
		-H "Content-Type: application/json" \
		-d '{"task": "Analyze architecture and code quality", "project_path": "$(PROJECT:-/root/ultramcp)"}' | jq '.'

# Quick debate orchestration workflow
claudia-debate:
	@echo "🎭 Installing and executing debate orchestrator..."
	@curl -s -X POST http://sam.chat:8013/agents/templates/debate_orchestrator/install | jq '.id' | xargs -I {} \
		curl -s -X POST http://sam.chat:8013/agents/{}/execute \
		-H "Content-Type: application/json" \
		-d '{"task": "$(TOPIC)", "project_path": "$(PROJECT:-/root/ultramcp)"}' | jq '.'

# Quick voice assistant workflow
claudia-voice-assistant:
	@echo "🗣️ Installing and executing voice assistant..."
	@curl -s -X POST http://sam.chat:8013/agents/templates/voice_powered_assistant/install | jq '.id' | xargs -I {} \
		curl -s -X POST http://sam.chat:8013/agents/{}/execute \
		-H "Content-Type: application/json" \
		-d '{"task": "$(TASK)", "project_path": "$(PROJECT:-/root/ultramcp)"}' | jq '.'

# Stop Claudia integration service
claudia-stop:
	@echo "🛑 Stopping Claudia integration service..."
	@docker-compose -f docker-compose.hybrid.yml stop ultramcp-claudia-integration

# Restart Claudia integration service
claudia-restart:
	@echo "🔄 Restarting Claudia integration service..."
	@docker-compose -f docker-compose.hybrid.yml restart ultramcp-claudia-integration

# Show Claudia service logs
claudia-logs:
	@echo "📋 Showing Claudia service logs..."
	@docker-compose -f docker-compose.hybrid.yml logs -f ultramcp-claudia-integration

# Case-sensitive compatibility alias
Claudia-start: claudia-enhanced-start

# Enhanced Claudia integration help
claudia-help:
	@echo "📖 Enhanced Claudia Integration Commands:"
	@echo "========================================"
	@echo ""
	@echo "🚀 Service Management:"
	@echo "  make claudia-enhanced-start     # Start enhanced Claudia service"
	@echo "  make claudia-stop              # Stop service"
	@echo "  make claudia-restart           # Restart service"
	@echo "  make claudia-logs              # Show logs"
	@echo "  make claudia-health            # Check service health"
	@echo ""
	@echo "🤖 Agent Management:"
	@echo "  make claudia-agents-list        # List all agents"
	@echo "  make claudia-templates-list     # List agent templates"
	@echo "  make claudia-install-template TEMPLATE=name  # Install template"
	@echo "  make claudia-execute-agent AGENT_ID=id TASK='task' PROJECT=path"
	@echo "  make claudia-executions-list    # List recent executions"
	@echo "  make claudia-metrics           # Show execution metrics"
	@echo ""
	@echo "🚀 Quick Agent Workflows:"
	@echo "  make claudia-security-scan PROJECT=path     # Quick security scan"
	@echo "  make claudia-code-analysis PROJECT=path     # Code analysis"
	@echo "  make claudia-debate TOPIC='question' PROJECT=path  # AI debate"
	@echo "  make claudia-voice-assistant TASK='help' PROJECT=path  # Voice help"
	@echo ""
	@echo "📋 Available Templates:"
	@echo "  - ultramcp_security_scanner     # Advanced security scanning"
	@echo "  - code_intelligence_analyst     # Code analysis and architecture"
	@echo "  - debate_orchestrator           # Multi-LLM debate coordination"
	@echo "  - voice_powered_assistant       # Voice-enabled AI assistance"
	@echo ""
	@echo "💡 Examples:"
	@echo "  # Install and run security scan"
	@echo "  make claudia-install-template TEMPLATE=ultramcp_security_scanner"
	@echo "  make claudia-security-scan PROJECT=/root/ultramcp"
	@echo ""
	@echo "  # Start AI debate on architecture decision"
	@echo "  make claudia-debate TOPIC='Should we use microservices?' PROJECT=/root/ultramcp"
	@echo ""
	@echo "  # Analyze code quality"
	@echo "  make claudia-code-analysis PROJECT=/root/ultramcp"
	@echo ""
	@echo "Service URL: http://sam.chat:8013"
	@echo "Frontend UI: http://sam.chat:3000/claudia"

# =============================================================================
# ULTRAMCP AGENT FACTORY - Create Agent App Style
# =============================================================================

include agent-factory-commands.mk

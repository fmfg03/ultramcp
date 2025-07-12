# UltraMCP WebUI Commands
# Open WebUI integration with UltraMCP services

.PHONY: webui-start webui-stop webui-restart webui-logs webui-health webui-status webui-reset webui-supabase-start webui-supabase-stop webui-supabase-status

# Main WebUI commands
webui-start: ## 🌐 Start UltraMCP WebUI (Open WebUI)
	@echo "🌐 Starting UltraMCP WebUI..."
	@echo "✅ WebUI will be available at http://localhost:3000"
	@mkdir -p ultramcp-pipelines ultramcp-webui-config
	@docker-compose -f docker-compose.hybrid.yml up -d ultramcp-webui
	@echo "🚀 UltraMCP WebUI started successfully!"
	@echo ""
	@echo "🔗 Access your UltraMCP AI Platform at: http://localhost:3000"
	@echo "📚 Features available:"
	@echo "   • Chain-of-Debate Protocol (/cod <topic>)"
	@echo "   • Agent Factory (/create-agent <type>)"
	@echo "   • Research Engine (/research <query>)"
	@echo "   • Security Scanning (/security <target>)"
	@echo "   • Multi-model local AI (5 Ollama models)"
	@echo "   • Advanced pipelines and workflows"

webui-stop: ## 🛑 Stop UltraMCP WebUI
	@echo "🛑 Stopping UltraMCP WebUI..."
	@docker-compose -f docker-compose.hybrid.yml stop ultramcp-webui
	@echo "✅ WebUI stopped"

webui-restart: ## 🔄 Restart UltraMCP WebUI
	@echo "🔄 Restarting UltraMCP WebUI..."
	@make webui-stop
	@sleep 2
	@make webui-start

webui-logs: ## 📋 View WebUI logs
	@echo "📋 UltraMCP WebUI logs (last 50 lines):"
	@docker logs ultramcp-webui --tail=50 --follow

webui-health: ## 🏥 Check WebUI health
	@echo "🏥 UltraMCP WebUI Health Check"
	@echo "==============================="
	@if docker ps --filter "name=ultramcp-webui" --filter "status=running" --quiet | grep -q .; then \
		echo "✅ Container Status: Running"; \
		if curl -s -f http://localhost:3000/health >/dev/null 2>&1; then \
			echo "✅ HTTP Health: Responding"; \
		else \
			echo "❌ HTTP Health: Not responding"; \
		fi; \
		echo ""; \
		echo "🔗 WebUI URL: http://localhost:3000"; \
		echo "📊 Container Stats:"; \
		docker stats ultramcp-webui --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"; \
	else \
		echo "❌ Container Status: Not running"; \
		echo "💡 Start with: make webui-start"; \
	fi

webui-status: ## 📊 Show comprehensive WebUI status
	@echo "📊 UltraMCP WebUI Status Dashboard"
	@echo "=================================="
	@echo ""
	@echo "🐳 Container Status:"
	@docker ps --filter "name=ultramcp-webui" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "❌ Container not found"
	@echo ""
	@echo "🔗 Service Integration Status:"
	@if docker ps --filter "name=ultramcp-webui" --filter "status=running" --quiet | grep -q .; then \
		echo "✅ WebUI Container: Running"; \
		echo "🧪 Testing service connections..."; \
		docker exec ultramcp-webui sh -c "curl -s -f http://ultramcp-unified-docs:8012/health >/dev/null 2>&1 && echo '✅ Unified Docs: Connected' || echo '❌ Unified Docs: Disconnected'"; \
		docker exec ultramcp-webui sh -c "curl -s -f http://ultramcp-claude-memory:8009/health >/dev/null 2>&1 && echo '✅ Claude Memory: Connected' || echo '❌ Claude Memory: Disconnected'"; \
		docker exec ultramcp-webui sh -c "curl -s -f http://ultramcp-cod-service:8001/health >/dev/null 2>&1 && echo '✅ Chain-of-Debate: Connected' || echo '❌ Chain-of-Debate: Disconnected'"; \
	else \
		echo "❌ WebUI Container: Not running"; \
	fi
	@echo ""
	@echo "📁 Pipeline Status:"
	@if [ -d "ultramcp-pipelines" ]; then \
		echo "✅ Pipelines Directory: $(shell ls ultramcp-pipelines/ | wc -l) files"; \
		ls ultramcp-pipelines/ | sed 's/^/   • /'; \
	else \
		echo "❌ Pipelines Directory: Not found"; \
	fi

webui-reset: ## 🔄 Reset WebUI data and configuration
	@echo "🔄 Resetting UltraMCP WebUI..."
	@echo "⚠️  This will delete all WebUI data, configurations, and user accounts!"
	@read -p "Are you sure you want to reset? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@make webui-stop
	@echo "🗑️  Removing WebUI data..."
	@docker volume rm ultramcp-webui-data 2>/dev/null || true
	@rm -rf ultramcp-webui-config/*
	@echo "🔄 Starting fresh WebUI..."
	@make webui-start
	@echo "✅ WebUI reset complete!"

# Pipeline management
webui-pipelines: ## 📚 Show available UltraMCP pipelines
	@echo "📚 UltraMCP Custom Pipelines"
	@echo "============================="
	@echo ""
	@if [ -d "ultramcp-pipelines" ]; then \
		echo "🔧 Available Pipelines:"; \
		for file in ultramcp-pipelines/*.py; do \
			if [ -f "$$file" ]; then \
				echo "   • $$(basename $$file .py)"; \
				grep -o 'class Pipeline:' "$$file" >/dev/null 2>&1 && echo "     ✅ Valid pipeline format" || echo "     ⚠️  Check pipeline format"; \
			fi; \
		done; \
	else \
		echo "❌ Pipelines directory not found"; \
		echo "💡 Run 'make webui-start' to initialize"; \
	fi
	@echo ""
	@echo "🎯 Pipeline Features:"
	@echo "   • UltraMCP Chain-of-Debate Protocol"
	@echo "   • Agent Factory Integration"
	@echo "   • Comprehensive Services Access"
	@echo "   • Research and Analysis Tools"
	@echo "   • Security Scanning Capabilities"

webui-demo: ## 🎬 Run WebUI demonstration
	@echo "🎬 UltraMCP WebUI Demonstration"
	@echo "==============================="
	@echo ""
	@echo "🚀 Starting demonstration sequence..."
	@make webui-health
	@echo ""
	@echo "📝 Demo Instructions:"
	@echo "1. 🌐 Open http://localhost:3000 in your browser"
	@echo "2. 📝 Create an account or sign in"
	@echo "3. 🎭 Try: '/cod Should we invest in AI research?'"
	@echo "4. 🤖 Try: '/create-agent customer-support name=DemoBot'"
	@echo "5. 🔍 Try: '/research artificial intelligence trends'"
	@echo "6. 🔒 Try: '/security scan example.com'"
	@echo "7. ❓ Try: '/help' for all available commands"
	@echo ""
	@echo "✨ Experience the power of UltraMCP's integrated AI platform!"

# Quick access commands
webui-open: ## 🌐 Open WebUI in default browser
	@echo "🌐 Opening UltraMCP WebUI..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:3000; \
	elif command -v open >/dev/null 2>&1; then \
		open http://localhost:3000; \
	else \
		echo "🔗 Please open http://localhost:3000 in your browser"; \
	fi

webui-quick-start: ## ⚡ Quick start WebUI with all services
	@echo "⚡ UltraMCP WebUI Quick Start"
	@echo "============================"
	@echo ""
	@echo "🚀 Starting UltraMCP services..."
	@make docker-hybrid
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@echo ""
	@echo "🌐 Starting WebUI..."
	@make webui-start
	@echo ""
	@echo "✅ UltraMCP WebUI is ready!"
	@make webui-demo

# Help
# Dashboard commands
dashboard-start: ## 📊 Start custom UltraMCP dashboard only
	@echo "📊 Starting UltraMCP Custom Dashboard..."
	@echo "✅ Dashboard will be available at http://localhost:3001"
	@cd ultramcp-dashboard && npm run dev

dashboard-build: ## 🏗️ Build dashboard for production
	@echo "🏗️ Building UltraMCP Dashboard..."
	@cd ultramcp-dashboard && npm run build

dashboard-install: ## 📦 Install dashboard dependencies
	@echo "📦 Installing dashboard dependencies..."
	@cd ultramcp-dashboard && npm install

# Supabase backend integration commands
webui-supabase-start: ## 🗄️ Start WebUI with Supabase backend
	@echo "🗄️ Starting UltraMCP WebUI with Supabase Backend..."
	@echo "✅ WebUI with Supabase will be available at http://localhost:3000"
	@echo "✅ Custom Dashboard will be available at http://localhost:3001"
	@echo "✅ Supabase API Gateway will be available at http://localhost:8000"
	@mkdir -p ultramcp-pipelines ultramcp-webui-config
	@docker-compose -f docker-compose.supabase-webui.yml up -d
	@echo "🚀 UltraMCP WebUI with Supabase started successfully!"
	@echo ""
	@echo "🔗 Access Points:"
	@echo "   🌐 Open WebUI: http://localhost:3000"
	@echo "   📊 Custom Dashboard: http://localhost:3001"
	@echo "   🗄️ Supabase API: http://localhost:8000"
	@echo ""
	@echo "🗄️ Supabase Features:"
	@echo "   • PostgreSQL Database with Vector Extensions"
	@echo "   • Real-time subscriptions and webhooks"
	@echo "   • Authentication and user management"
	@echo "   • File storage with image transformations"
	@echo "   • API Gateway with Kong proxy"
	@echo "   • Complete backend infrastructure"
	@echo ""
	@echo "📊 Custom Dashboard Features:"
	@echo "   • Real-time service monitoring"
	@echo "   • shadcn/ui modern interface"
	@echo "   • Service health analytics"
	@echo "   • Performance metrics"

webui-supabase-stop: ## 🛑 Stop WebUI with Supabase backend
	@echo "🛑 Stopping UltraMCP WebUI with Supabase..."
	@docker-compose -f docker-compose.supabase-webui.yml down
	@echo "✅ WebUI with Supabase stopped"

webui-supabase-status: ## 📊 Show WebUI + Supabase status
	@echo "📊 UltraMCP WebUI + Supabase Status Dashboard"
	@echo "=============================================="
	@echo ""
	@echo "🐳 Container Status:"
	@docker-compose -f docker-compose.supabase-webui.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" || echo "❌ Services not running"
	@echo ""
	@echo "🔗 Service Health Checks:"
	@if docker ps --filter "name=ultramcp-webui" --filter "status=running" --quiet | grep -q .; then \
		echo "✅ Open WebUI: Running on http://localhost:3000"; \
	else \
		echo "❌ Open WebUI: Not running"; \
	fi
	@if docker ps --filter "name=ultramcp-dashboard" --filter "status=running" --quiet | grep -q .; then \
		echo "✅ Custom Dashboard: Running on http://localhost:3001"; \
	else \
		echo "❌ Custom Dashboard: Not running"; \
	fi
	@if docker ps --filter "name=ultramcp-supabase-kong" --filter "status=running" --quiet | grep -q .; then \
		echo "✅ Supabase API Gateway: Running on http://localhost:8000"; \
	else \
		echo "❌ Supabase API Gateway: Not running"; \
	fi
	@if docker ps --filter "name=ultramcp-supabase-db" --filter "status=running" --quiet | grep -q .; then \
		echo "✅ PostgreSQL Database: Running on port 54322"; \
	else \
		echo "❌ PostgreSQL Database: Not running"; \
	fi
	@echo ""
	@echo "🗄️ Database Connection Test:"
	@docker exec ultramcp-supabase-db pg_isready -h localhost -p 5432 -U supabase_admin && echo "✅ Database: Accepting connections" || echo "❌ Database: Connection failed"

webui-help: ## ❓ Show WebUI help and usage
	@echo "❓ UltraMCP WebUI Help"
	@echo "====================="
	@echo ""
	@echo "🌐 Web Interface Commands:"
	@echo "   make webui-start     - Start WebUI (http://localhost:3000)"
	@echo "   make webui-stop      - Stop WebUI"
	@echo "   make webui-restart   - Restart WebUI"
	@echo "   make webui-health    - Check WebUI health"
	@echo "   make webui-status    - Show detailed status"
	@echo "   make webui-logs      - View WebUI logs"
	@echo "   make webui-reset     - Reset WebUI data"
	@echo ""
	@echo "🗄️ Supabase Backend Commands:"
	@echo "   make webui-supabase-start   - Start WebUI with Supabase backend"
	@echo "   make webui-supabase-stop    - Stop WebUI with Supabase backend"
	@echo "   make webui-supabase-status  - Show Supabase + WebUI status"
	@echo ""
	@echo "🎬 Demo & Quick Start:"
	@echo "   make webui-demo      - Show demonstration guide"
	@echo "   make webui-open      - Open WebUI in browser"
	@echo "   make webui-quick-start - Start everything quickly"
	@echo ""
	@echo "🔧 Pipeline Management:"
	@echo "   make webui-pipelines - Show available pipelines"
	@echo ""
	@echo "🎭 Available WebUI Features:"
	@echo "   • Chain-of-Debate Protocol (/cod <topic>)"
	@echo "   • Agent Factory (/create-agent <type>)"
	@echo "   • Research Engine (/research <query>)"
	@echo "   • Analysis Tools (/analyze <data>)"
	@echo "   • Security Scanning (/security <target>)"
	@echo "   • Service Health (/health)"
	@echo "   • Help System (/help)"
	@echo ""
	@echo "🔗 Access: http://localhost:3000"
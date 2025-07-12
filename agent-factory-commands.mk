# =============================================================================
# ULTRAMCP AGENT FACTORY - Create Agent App Style
# =============================================================================

# Agent Factory Service Management
agent-factory-start:
	@echo "🤖 Starting Agent Factory service..."
	@docker-compose -f docker-compose.agent-factory.yml up -d
	@echo "✅ Agent Factory started on port 8014"

agent-factory-stop:
	@echo "🛑 Stopping Agent Factory service..."
	@docker-compose -f docker-compose.agent-factory.yml down
	@echo "✅ Agent Factory stopped"

agent-factory-build:
	@echo "🔧 Building Agent Factory service..."
	@docker-compose -f docker-compose.agent-factory.yml build --no-cache
	@echo "✅ Agent Factory built successfully"

agent-factory-logs:
	@echo "📋 Agent Factory logs:"
	@docker logs ultramcp-agent-factory --tail=50

# Agent Creation Commands
create-agent:
	@echo "🤖 Creating agent: $(TYPE) with framework: $(FRAMEWORK)"
	@python3 scripts/agent-factory-cli.py create "$(TYPE)" --framework "$(FRAMEWORK)" $(if $(NAME),--name "$(NAME)") $(if $(DEPLOY),--deploy) $(if $(NO_TEST),--no-test)

# Quick create commands for common agent types
create-customer-support:
	@make create-agent TYPE="customer-support" FRAMEWORK="ultramcp" DEPLOY=true

create-research-analyst:
	@make create-agent TYPE="research-analyst" FRAMEWORK="langchain" DEPLOY=true

create-code-reviewer:
	@make create-agent TYPE="code-reviewer" FRAMEWORK="ultramcp" DEPLOY=true

create-content-creator:
	@make create-agent TYPE="content-creator" FRAMEWORK="crewai" DEPLOY=true

# Agent Management Commands
list-agents:
	@echo "📋 Listing all created agents..."
	@python3 scripts/agent-factory-cli.py list

agent-templates:
	@echo "📚 Available agent templates..."
	@python3 scripts/agent-factory-cli.py templates

frameworks:
	@echo "🔧 Supported frameworks..."
	@python3 scripts/agent-factory-cli.py frameworks

deploy-agent:
	@echo "🚀 Deploying agent: $(AGENT)"
	@python3 scripts/agent-factory-cli.py deploy "$(AGENT)"

test-agent:
	@echo "🧪 Testing agent: $(AGENT)"
	@python3 scripts/agent-factory-cli.py test "$(AGENT)"

agent-status:
	@echo "📊 Agent status: $(AGENT)"
	@python3 scripts/agent-factory-cli.py status "$(AGENT)"

agent-health:
	@echo "🏥 Agent Factory health check..."
	@python3 scripts/agent-factory-cli.py health

# Agent Testing with Scenario Framework
test-all-agents:
	@echo "🧪 Running comprehensive agent tests..."
	@python3 scripts/agent-factory-cli.py list | grep -o '"agent_id":"[^"]*"' | cut -d'"' -f4 | while read agent_id; do \
		echo "Testing agent: $$agent_id"; \
		python3 scripts/agent-factory-cli.py test "$$agent_id"; \
	done

# Agent Deployment Pipelines
deploy-production-agents:
	@echo "🚀 Deploying all ready agents to production..."
	@echo "1. Customer Support Agent..."
	@make create-customer-support
	@echo "2. Research Analyst Agent..."
	@make create-research-analyst
	@echo "3. Code Reviewer Agent..."
	@make create-code-reviewer
	@echo "✅ Production agents deployed"

# Agent Factory Integration with UltraMCP
agent-factory-integration:
	@echo "🔗 Setting up Agent Factory integration..."
	@echo "1. Starting Agent Factory service..."
	@make agent-factory-start
	@echo "2. Waiting for service to be ready..."
	@sleep 10
	@echo "3. Checking health..."
	@make agent-health
	@echo "4. Loading default templates..."
	@make agent-templates
	@echo "✅ Agent Factory integration complete"

# Development Commands
agent-factory-dev:
	@echo "👨‍💻 Starting Agent Factory in development mode..."
	@docker-compose -f docker-compose.agent-factory.yml up --build

agent-factory-debug:
	@echo "🐛 Debugging Agent Factory..."
	@docker exec -it ultramcp-agent-factory /bin/bash

# Agent Analytics and Monitoring
agent-metrics:
	@echo "📊 Agent Factory metrics..."
	@curl -s http://localhost:8014/agents | jq '.by_status'

agent-performance:
	@echo "⚡ Agent performance statistics..."
	@curl -s http://localhost:8014/health | jq '.ultramcp_services'

# Quick Demo Commands
demo-agent-creation:
	@echo "🎬 Agent Factory Demo - Creating Sample Agents"
	@echo "=============================================="
	@echo ""
	@echo "1. Creating Customer Support Agent (UltraMCP)..."
	@make create-agent TYPE="customer-support" FRAMEWORK="ultramcp" NAME="demo-support"
	@sleep 5
	@echo ""
	@echo "2. Creating Research Analyst (LangChain)..."
	@make create-agent TYPE="research-analyst" FRAMEWORK="langchain" NAME="demo-researcher"
	@sleep 5
	@echo ""
	@echo "3. Listing created agents..."
	@make list-agents
	@echo ""
	@echo "🎉 Demo complete! Check agents at http://localhost:8014"

# Cleanup Commands
clean-agents:
	@echo "🧹 Cleaning up agent deployments..."
	@docker ps | grep "agent-" | awk '{print $$1}' | xargs -r docker stop
	@docker ps -a | grep "agent-" | awk '{print $$1}' | xargs -r docker rm
	@echo "✅ Agent containers cleaned"

# Help Commands
agent-factory-help:
	@echo "🤖 UltraMCP Agent Factory - Create Agent App Style"
	@echo "=================================================="
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make agent-factory-integration  - Complete setup and integration"
	@echo "  make demo-agent-creation        - Run demo with sample agents"
	@echo ""
	@echo "🔧 Service Management:"
	@echo "  make agent-factory-start        - Start the Agent Factory service"
	@echo "  make agent-factory-stop         - Stop the Agent Factory service"
	@echo "  make agent-factory-logs         - View service logs"
	@echo "  make agent-health               - Check service health"
	@echo ""
	@echo "🤖 Agent Creation:"
	@echo "  make create-agent TYPE='customer-support' FRAMEWORK='ultramcp'"
	@echo "  make create-customer-support    - Quick customer support agent"
	@echo "  make create-research-analyst    - Quick research analyst agent"
	@echo "  make create-code-reviewer       - Quick code reviewer agent"
	@echo ""
	@echo "📋 Agent Management:"
	@echo "  make list-agents                - List all created agents"
	@echo "  make agent-templates            - Show available templates"
	@echo "  make frameworks                 - Show supported frameworks"
	@echo "  make deploy-agent AGENT='...'   - Deploy specific agent"
	@echo "  make test-agent AGENT='...'     - Test specific agent"
	@echo ""
	@echo "🔧 Supported Frameworks:"
	@echo "  - ultramcp   : Native UltraMCP with local models + CoD"
	@echo "  - langchain  : LangChain with tools and memory"
	@echo "  - crewai     : CrewAI for multi-agent collaboration"
	@echo "  - autogen    : AutoGen for conversational agents"
	@echo ""
	@echo "💡 Examples:"
	@echo "  # Create and deploy customer support agent"
	@echo "  make create-agent TYPE='customer-support' FRAMEWORK='ultramcp' DEPLOY=true"
	@echo ""
	@echo "  # Create research analyst with custom name"
	@echo "  make create-agent TYPE='research-analyst' FRAMEWORK='langchain' NAME='market-analyst'"
	@echo ""
	@echo "  # Test all created agents"
	@echo "  make test-all-agents"
	@echo ""
	@echo "🌐 Service URLs:"
	@echo "  Agent Factory API: http://localhost:8014"
	@echo "  Agent Health: http://localhost:8014/health"
	@echo "  Templates: http://localhost:8014/templates"
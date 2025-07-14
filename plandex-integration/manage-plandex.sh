#!/bin/bash
# UltraMCP Plandex Management Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

case "${1:-help}" in
    "start")
        log_info "Starting Plandex services..."
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Plandex services started"
        ;;
    "stop")
        log_info "Stopping Plandex services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Plandex services stopped"
        ;;
    "restart")
        log_info "Restarting Plandex services..."
        docker-compose -f "$COMPOSE_FILE" down
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Plandex services restarted"
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        service="${2:-}"
        if [[ -n "$service" ]]; then
            docker-compose -f "$COMPOSE_FILE" logs -f "$service"
        else
            docker-compose -f "$COMPOSE_FILE" logs -f
        fi
        ;;
    "health")
        log_info "Checking Plandex health..."
        
        # Check Plandex core
        if curl -s -f http://localhost:7777/health >/dev/null; then
            log_success "✓ Plandex core is healthy"
        else
            log_error "✗ Plandex core is unhealthy"
        fi
        
        # Check Agent Registry
        if curl -s -f http://localhost:7778/health >/dev/null; then
            log_success "✓ Agent Registry is healthy"
        else
            log_error "✗ Agent Registry is unhealthy"
        fi
        
        # Check Context Bridge
        if curl -s -f http://localhost:7779/health >/dev/null; then
            log_success "✓ Context Bridge is healthy"
        else
            log_error "✗ Context Bridge is unhealthy"
        fi
        ;;
    "agents")
        log_info "Listing registered agents..."
        curl -s http://localhost:7778/agents | jq '.agents[] | {name: .name, type: .type, status: .is_active}'
        ;;
    "plan")
        task="${2:-}"
        if [[ -z "$task" ]]; then
            log_error "Task required. Usage: $0 plan \"<task description>\""
            exit 1
        fi
        
        log_info "Generating plan for: $task"
        curl -X POST http://localhost:7777/plan \
            -H "Content-Type: application/json" \
            -d "{\"task\": \"$task\"}" | jq '.'
        ;;
    "execute")
        plan_id="${2:-}"
        if [[ -z "$plan_id" ]]; then
            log_error "Plan ID required. Usage: $0 execute <plan_id>"
            exit 1
        fi
        
        log_info "Executing plan: $plan_id"
        curl -X POST "http://localhost:7777/execute/$plan_id" | jq '.'
        ;;
    "contexts")
        log_info "Listing active contexts..."
        curl -s http://localhost:7779/contexts | jq '.contexts[] | {id: .id, summary: .summary, created: .createdAt}'
        ;;
    "dashboard")
        log_info "Plandex Integration URLs:"
        echo ""
        echo "🧠 Plandex Core:        http://localhost:7777"
        echo "🤖 Agent Registry:      http://localhost:7778"
        echo "🔗 Context Bridge:      http://localhost:7779"
        echo "🌐 Plandex UI:          http://localhost:7780"
        echo ""
        echo "📝 API Examples:"
        echo "  List agents:    curl http://localhost:7778/agents"
        echo "  Health check:   curl http://localhost:7778/agents/health/check"
        echo "  Create context: curl -X POST http://localhost:7779/context -d '{\"task\":\"test\"}'"
        ;;
    "build")
        log_info "Building Plandex services..."
        docker-compose -f "$COMPOSE_FILE" build
        log_success "Build completed"
        ;;
    "help"|*)
        echo "UltraMCP Plandex Management"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start                    Start Plandex services"
        echo "  stop                     Stop Plandex services"
        echo "  restart                  Restart Plandex services"
        echo "  status                   Show service status"
        echo "  logs [service]           Show logs"
        echo "  health                   Check service health"
        echo "  agents                   List registered agents"
        echo "  plan \"<task>\"            Generate execution plan"
        echo "  execute <plan_id>        Execute a plan"
        echo "  contexts                 List active contexts"
        echo "  dashboard                Show dashboard URLs"
        echo "  build                    Build services"
        echo "  help                     Show this help"
        ;;
esac

#!/bin/bash

# UltraMCP ContextBuilderAgent 2.0 - Bootstrap Script
# Complete initialization of the ContextBuilderAgent ecosystem

set -e

echo "🚀 UltraMCP ContextBuilderAgent 2.0 Bootstrap"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTEXT_DIR="/root/ultramcp/.context"
SERVICES_DIR="/root/ultramcp/services/context-builder-agent"
LOGS_DIR="/root/ultramcp/logs"

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if curl -f "http://sam.chat:$port/health" >/dev/null 2>&1; then
        print_success "$service_name is running on port $port"
        return 0
    else
        print_warning "$service_name is not responding on port $port"
        return 1
    fi
}

# Function to start service
start_service() {
    local service_name=$1
    local script_name=$2
    local port=$3
    
    print_status "Starting $service_name on port $port..."
    
    cd "$SERVICES_DIR"
    nohup python3 -m uvicorn "$script_name:app" --host 0.0.0.0 --port "$port" \
        > "$LOGS_DIR/context_builder_${service_name}.log" 2>&1 &
    
    echo $! > "$LOGS_DIR/context_builder_${service_name}.pid"
    
    # Wait for service to start
    sleep 5
    
    if check_service "$service_name" "$port"; then
        print_success "$service_name started successfully"
    else
        print_error "Failed to start $service_name"
        return 1
    fi
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    cd "$SERVICES_DIR"
    
    if pip3 install -r requirements.txt; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Function to check system prerequisites
check_prerequisites() {
    print_status "Checking system prerequisites..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python 3 is available"
    else
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 is available"
    else
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check Redis (optional)
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis is not running - some features may be limited"
    fi
    
    # Check PostgreSQL (optional)
    if pg_isready -h mcp-database -p 5432 &> /dev/null; then
        print_success "PostgreSQL is available"
    else
        print_warning "PostgreSQL is not available - using fallback storage"
    fi
}

# Function to create directories
create_directories() {
    print_status "Creating necessary directories..."
    
    # Create logs directory
    mkdir -p "$LOGS_DIR"
    
    # Create context subdirectories
    mkdir -p "$CONTEXT_DIR"/{sessions,fragments/{by_agent,by_phase,shared},mutations,versions,observability,integrations}
    mkdir -p "$CONTEXT_DIR/fragments/by_agent"/{sitebuilder,leadscorer,nurturer,crm_sync,paid_campaigns}
    mkdir -p "$CONTEXT_DIR/fragments/by_phase"/{discovery,planning,execution,optimization}
    mkdir -p "$CONTEXT_DIR"/{models,data/training}
    
    print_success "Directory structure created"
}

# Function to validate knowledge tree
validate_knowledge_tree() {
    print_status "Validating knowledge tree structure..."
    
    if [ -f "$CONTEXT_DIR/core/knowledge_tree.yaml" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('$CONTEXT_DIR/core/knowledge_tree.yaml'))" 2>/dev/null; then
            print_success "Knowledge tree is valid YAML"
        else
            print_error "Knowledge tree has invalid YAML syntax"
            return 1
        fi
    else
        print_error "Knowledge tree not found at $CONTEXT_DIR/core/knowledge_tree.yaml"
        return 1
    fi
}

# Function to start all services
start_all_services() {
    print_status "Starting ContextBuilderAgent services..."
    
    # Service definitions: name, script, port
    declare -a services=(
        "context_drift_detector context_drift_detector 8020"
        "contradiction_resolver contradiction_resolver 8021"
        "belief_reviser belief_reviser 8022"
        "utility_predictor utility_predictor 8023"
        "orchestrator context_builder_orchestrator 8025"
        "memory_tuner context_memory_tuner 8026"
        "prompt_assembler prompt_assembler_agent 8027"
        "observatory context_observatory 8028"
        "debug_mode deterministic_debug_mode 8029"
    )
    
    for service_def in "${services[@]}"; do
        read -r name script port <<< "$service_def"
        start_service "$name" "$script" "$port"
        sleep 2
    done
}

# Function to test system integration
test_integration() {
    print_status "Testing system integration..."
    
    # Test orchestrator health
    if curl -f "http://sam.chat:8025/health" >/dev/null 2>&1; then
        print_success "Orchestrator is responding"
    else
        print_error "Orchestrator is not responding"
        return 1
    fi
    
    # Test knowledge tree access
    if curl -f "http://sam.chat:8025/knowledge_tree" >/dev/null 2>&1; then
        print_success "Knowledge tree is accessible"
    else
        print_warning "Knowledge tree access issue"
    fi
    
    # Test system status
    if curl -f "http://sam.chat:8025/system_status" >/dev/null 2>&1; then
        print_success "System status is accessible"
    else
        print_warning "System status access issue"
    fi
}

# Function to create sample session data
create_sample_data() {
    print_status "Creating sample session data..."
    
    cat > "$CONTEXT_DIR/sessions/sample_session_insights.yaml" << 'EOF'
# Sample Session Insights
session_id: "sample_session_001"
timestamp: "2025-07-04T06:30:00Z"
source: "bootstrap_sample"

insights:
  pain_points_explicit:
    - content: "Difficulty scaling current infrastructure"
      confidence: 0.9
      source: "sample_data"
      timestamp: "2025-07-04T06:30:00Z"
      
  objetivos_declarados:
    - content: "Achieve 99.9% uptime for critical services"
      confidence: 0.8
      source: "sample_data"
      timestamp: "2025-07-04T06:30:00Z"
      
  senales_oportunidad:
    - content: "Growing demand for AI-enhanced solutions"
      confidence: 0.7
      source: "sample_data"
      timestamp: "2025-07-04T06:30:00Z"

proposed_mutations:
  - mutation_id: "add_scaling_challenge"
    type: "ADD_INSIGHT"
    target_domain: "PAIN_POINTS.problemas_actuales"
    confidence: 0.9
    requires_cod_validation: false
    new_value: "Infrastructure scaling challenges"
    source: "sample_session"
EOF

    print_success "Sample session data created"
}

# Function to show final status
show_final_status() {
    echo ""
    echo "🎯 ContextBuilderAgent 2.0 Bootstrap Complete"
    echo "============================================="
    echo ""
    
    echo "📊 Service Status:"
    check_service "Context Drift Detector" 8020
    check_service "Contradiction Resolver" 8021
    check_service "Belief Reviser" 8022
    check_service "Utility Predictor" 8023
    check_service "Orchestrator" 8025
    check_service "Memory Tuner" 8026
    check_service "Prompt Assembler" 8027
    check_service "Context Observatory" 8028
    check_service "Debug Mode" 8029
    
    echo ""
    echo "🔗 Available Endpoints:"
    echo "  • Orchestrator:        http://sam.chat:8025"
    echo "  • System Status:       http://sam.chat:8025/system_status"
    echo "  • Knowledge Tree:      http://sam.chat:8025/knowledge_tree"
    echo "  • Prompt Assembler:    http://sam.chat:8027"
    echo "  • Context Observatory: http://sam.chat:8028"
    echo "  • Debug Mode:          http://sam.chat:8029"
    echo "  • Health Check:        http://sam.chat:8025/health"
    echo ""
    echo "📁 Key Directories:"
    echo "  • Context Root:        $CONTEXT_DIR"
    echo "  • Services:            $SERVICES_DIR"
    echo "  • Logs:                $LOGS_DIR"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Test the system:    curl http://sam.chat:8025/health"
    echo "  2. View knowledge:     curl http://sam.chat:8025/knowledge_tree"
    echo "  3. Process context:    curl -X POST http://sam.chat:8025/process_context"
    echo "  4. Monitor logs:       tail -f $LOGS_DIR/context_builder_*.log"
    echo ""
}

# Function to stop all services
stop_services() {
    print_status "Stopping ContextBuilderAgent services..."
    
    for pid_file in "$LOGS_DIR"/context_builder_*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill "$pid" 2>/dev/null; then
                print_success "Stopped service with PID $pid"
            fi
            rm -f "$pid_file"
        fi
    done
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [start|stop|restart|status|test]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all ContextBuilderAgent services"
    echo "  stop      - Stop all ContextBuilderAgent services"
    echo "  restart   - Restart all ContextBuilderAgent services"
    echo "  status    - Show status of all services"
    echo "  test      - Run integration tests"
    echo ""
}

# Main execution
main() {
    case "${1:-start}" in
        "start")
            print_status "Starting ContextBuilderAgent 2.0 bootstrap..."
            check_prerequisites
            create_directories
            validate_knowledge_tree
            install_dependencies
            start_all_services
            create_sample_data
            test_integration
            show_final_status
            ;;
        "stop")
            stop_services
            print_success "All services stopped"
            ;;
        "restart")
            stop_services
            sleep 3
            "$0" start
            ;;
        "status")
            echo "ContextBuilderAgent Service Status:"
            check_service "Context Drift Detector" 8020
            check_service "Contradiction Resolver" 8021
            check_service "Belief Reviser" 8022
            check_service "Utility Predictor" 8023
            check_service "Orchestrator" 8025
            check_service "Memory Tuner" 8026
            check_service "Prompt Assembler" 8027
            check_service "Context Observatory" 8028
            check_service "Debug Mode" 8029
            ;;
        "test")
            test_integration
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Handle Ctrl+C
trap 'print_warning "Bootstrap interrupted"; stop_services; exit 130' INT

# Run main function
main "$@"
#!/bin/bash

# =============================================================================
# UltraMCP Claude Startup Verification Script
# Comprehensive startup verification for every Claude session
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

header() {
    echo -e "\n${PURPLE}================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================================${NC}\n"
}

# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

verify_ultramcp_structure() {
    header "🏗️  ULTRAMCP STRUCTURE VERIFICATION"
    
    local required_dirs=(
        "apps/backend"
        "apps/frontend" 
        "core/orchestrator"
        "services/control-tower"
        "services/human-interaction"
        "services/asterisk-mcp"
        "services/blockoli-mcp"
        "services/deepclaude"
        "services/voice-system"
        "scripts"
        "data"
        "logs"
        "database/schemas"
    )
    
    local required_files=(
        "CLAUDE.md"
        "README.md"
        "Makefile"
        "package.json"
        "requirements.txt"
        "docker-compose.hybrid.yml"
        ".env.example"
    )
    
    log "Checking directory structure..."
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            success "Directory: $dir"
        else
            error "Missing directory: $dir"
        fi
    done
    
    log "Checking required files..."
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            success "File: $file"
        else
            error "Missing file: $file"
        fi
    done
}

acknowledge_documentation() {
    header "📚 DOCUMENTATION ACKNOWLEDGMENT"
    
    local docs=(
        "CLAUDE.md"
        "README.md"
    )
    
    for doc in "${docs[@]}"; do
        if [ -f "$doc" ]; then
            log "Acknowledging $doc..."
            echo "📖 Content summary for $doc:"
            head -10 "$doc" | sed 's/^/   /'
            success "Acknowledged: $doc"
        else
            warning "Documentation file not found: $doc"
        fi
    done
    
    # Check for additional MD files
    local md_files=$(find . -name "*.md" -type f | head -10)
    if [ -n "$md_files" ]; then
        info "Additional documentation files found:"
        echo "$md_files" | sed 's/^/   📄 /'
    fi
}

verify_mcp_services() {
    header "🔧 MCP SERVICES VERIFICATION"
    
    local services=(
        "asterisk-mcp:Asterisk Security Service"
        "context7-mcp:Context7 Real-time Documentation"
        "blockoli-mcp:Blockoli Code Intelligence"
        "deepclaude:DeepClaude Metacognitive Service"
        "voice-system:Voice Processing System"
        "control-tower:Control Tower WebSocket Server"
        "human-interaction:Human-in-the-Loop Services"
    )
    
    for service_info in "${services[@]}"; do
        local service_dir=$(echo $service_info | cut -d: -f1)
        local service_name=$(echo $service_info | cut -d: -f2)
        
        log "Checking $service_name..."
        
        if [ -d "services/$service_dir" ]; then
            success "Service directory: services/$service_dir"
            
            # Check for service files
            if [ -f "services/$service_dir/Dockerfile" ]; then
                success "  Dockerfile found"
            else
                warning "  Dockerfile missing"
            fi
            
            if [ -f "services/$service_dir/requirements.txt" ]; then
                success "  Python requirements found"
            elif [ -f "services/$service_dir/package.json" ]; then
                success "  Node.js package.json found"
            else
                warning "  No dependency file found"
            fi
            
            # Check main service file
            local main_files=(
                "services/$service_dir/*.py"
                "services/$service_dir/*.js"
                "services/$service_dir/src/index.js"
            )
            
            local found_main=false
            for pattern in "${main_files[@]}"; do
                if ls $pattern 1> /dev/null 2>&1; then
                    success "  Main service file found"
                    found_main=true
                    break
                fi
            done
            
            if [ "$found_main" = false ]; then
                warning "  No main service file found"
            fi
        else
            error "Service directory missing: services/$service_dir"
        fi
    done
}

check_docker_services() {
    header "🐳 DOCKER SERVICES CHECK"
    
    if command -v docker &> /dev/null; then
        success "Docker is installed"
        
        if command -v docker-compose &> /dev/null; then
            success "Docker Compose is installed"
            
            # Check if services are running
            log "Checking running containers..."
            local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -v NAMES)
            
            if [ -n "$running_containers" ]; then
                info "Running containers:"
                echo "$running_containers" | sed 's/^/   🟢 /'
            else
                warning "No Docker containers currently running"
                info "Use 'make docker-hybrid' to start services"
            fi
        else
            error "Docker Compose not installed"
        fi
    else
        error "Docker not installed"
    fi
}

verify_dependencies() {
    header "📦 DEPENDENCIES VERIFICATION"
    
    # Check Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version)
        success "Node.js: $node_version"
    else
        error "Node.js not installed"
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version)
        success "npm: $npm_version"
    else
        error "npm not installed"
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version)
        success "Python: $python_version"
    else
        error "Python 3 not installed"
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        local pip_version=$(pip3 --version)
        success "pip3: $pip_version"
    else
        error "pip3 not installed"
    fi
    
    # Check Ollama (for local LLMs)
    if command -v ollama &> /dev/null; then
        success "Ollama installed (local LLMs available)"
        
        # Check running models
        local ollama_models=$(ollama list 2>/dev/null | grep -v NAME | wc -l)
        if [ "$ollama_models" -gt 0 ]; then
            info "$ollama_models local models available"
        else
            warning "No local models downloaded"
        fi
    else
        warning "Ollama not installed (local LLMs unavailable)"
    fi
    
    # Check jq
    if command -v jq &> /dev/null; then
        success "jq installed (JSON processing)"
    else
        warning "jq not installed (recommended for log parsing)"
    fi
}

check_environment_config() {
    header "🔧 ENVIRONMENT CONFIGURATION"
    
    if [ -f ".env" ]; then
        success ".env file exists"
        
        # Check for important environment variables
        local env_vars=(
            "OPENAI_API_KEY"
            "ANTHROPIC_API_KEY"
            "POSTGRES_PASSWORD"
            "REDIS_PASSWORD"
        )
        
        for var in "${env_vars[@]}"; do
            if grep -q "^$var=" .env; then
                local value=$(grep "^$var=" .env | cut -d= -f2)
                if [ -n "$value" ] && [ "$value" != "your-key-here" ]; then
                    success "  $var configured"
                else
                    warning "  $var not configured"
                fi
            else
                warning "  $var not found in .env"
            fi
        done
    else
        warning ".env file not found"
        if [ -f ".env.example" ]; then
            info "Use 'cp .env.example .env' to create configuration"
        fi
    fi
}

verify_core_orchestrator() {
    header "🎯 CORE ORCHESTRATOR VERIFICATION"
    
    local core_files=(
        "core/orchestrator/eventBus.js"
        "core/orchestrator/index.js"
        "apps/backend/src/index.js"
        "apps/backend/package.json"
    )
    
    for file in "${core_files[@]}"; do
        if [ -f "$file" ]; then
            success "Core file: $file"
        else
            error "Missing core file: $file"
        fi
    done
    
    # Check for HITL integration
    if [ -f "services/human-interaction/action_request_adapter.py" ]; then
        success "Human-in-the-Loop integration available"
    else
        warning "HITL integration not found"
    fi
}

check_makefile_commands() {
    header "🔨 MAKEFILE COMMANDS VERIFICATION"
    
    if [ -f "Makefile" ]; then
        success "Makefile found"
        
        local important_commands=(
            "help"
            "status"
            "setup"
            "chat"
            "local-chat"
            "health-check"
            "docker-hybrid"
            "start"
        )
        
        log "Checking important make commands..."
        for cmd in "${important_commands[@]}"; do
            if grep -q "^$cmd:" Makefile; then
                success "  make $cmd"
            else
                warning "  make $cmd not found"
            fi
        done
    else
        error "Makefile not found"
    fi
}

run_basic_health_check() {
    header "🏥 BASIC HEALTH CHECK"
    
    # Check if health-check script exists
    if [ -f "scripts/health-check.sh" ]; then
        log "Running basic health check..."
        if ./scripts/health-check.sh; then
            success "Health check passed"
        else
            warning "Health check found issues"
        fi
    else
        warning "Health check script not found"
    fi
    
    # Check logs directory
    if [ -d "logs" ]; then
        success "Logs directory exists"
        
        if [ -f "logs/combined.log" ]; then
            local log_size=$(du -h logs/combined.log | cut -f1)
            info "Combined log size: $log_size"
        else
            info "No combined log file yet"
        fi
    else
        mkdir -p logs
        success "Created logs directory"
    fi
    
    # Check data directory
    if [ -d "data" ]; then
        success "Data directory exists"
    else
        mkdir -p data
        success "Created data directory"
    fi
}

display_quick_start_guide() {
    header "🚀 QUICK START GUIDE"
    
    echo -e "${BLUE}Essential Commands:${NC}"
    echo "  make help                    - Show all available commands"
    echo "  make status                  - Check system status"
    echo "  make setup                   - Initialize system"
    echo "  make docker-hybrid           - Start Docker services"
    echo "  make chat TEXT='Hello'       - Quick AI chat"
    echo "  make local-chat TEXT='Hello' - Local LLM chat"
    echo "  make health-check            - Run health check"
    echo ""
    echo -e "${BLUE}Development:${NC}"
    echo "  make start                   - Interactive startup"
    echo "  make logs-tail               - Follow live logs"
    echo "  make control-tower           - Launch Control Tower UI"
    echo ""
    echo -e "${BLUE}Advanced:${NC}"
    echo "  make cod-local TOPIC='...'   - Local AI debate"
    echo "  make security-scan           - Security analysis"
    echo "  make code-search QUERY='...' - Code intelligence"
    echo ""
    echo -e "${YELLOW}📖 Documentation: cat CLAUDE.md${NC}"
}

generate_startup_report() {
    header "📊 STARTUP VERIFICATION REPORT"
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="data/startup-verification-$(date +%Y%m%d-%H%M%S).json"
    
    # Create basic report
    cat > "$report_file" << EOF
{
  "timestamp": "$timestamp",
  "verification_results": {
    "structure_check": "completed",
    "documentation_check": "completed",
    "services_check": "completed",
    "dependencies_check": "completed",
    "environment_check": "completed",
    "health_check": "completed"
  },
  "status": "verification_completed",
  "recommendations": [
    "Run 'make setup' if this is first time setup",
    "Run 'make docker-hybrid' to start services",
    "Check 'make status' for current system status",
    "Review CLAUDE.md for detailed usage instructions"
  ]
}
EOF
    
    success "Startup report saved: $report_file"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    clear
    
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║    🤖 ULTRAMCP CLAUDE STARTUP VERIFICATION                  ║"
    echo "║                                                              ║"
    echo "║    Comprehensive system check for every Claude session      ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    local start_time=$(date +%s)
    
    # Run all verification steps
    verify_ultramcp_structure
    acknowledge_documentation
    verify_mcp_services
    check_docker_services
    verify_dependencies
    check_environment_config
    verify_core_orchestrator
    check_makefile_commands
    run_basic_health_check
    
    # Generate report
    generate_startup_report
    
    # Display quick start guide
    display_quick_start_guide
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo -e "\n${GREEN}🎉 UltraMCP startup verification completed in ${duration}s${NC}"
    echo -e "${CYAN}💡 Run 'make help' for available commands${NC}"
    echo -e "${CYAN}📖 Check CLAUDE.md for detailed documentation${NC}\n"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
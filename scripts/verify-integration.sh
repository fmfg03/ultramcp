#!/bin/bash

# UltraMCP Supreme Stack - Complete Integration Verification Script
# Ensures all services are properly integrated with no loose components

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/integration-verification.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Logging function
log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
    echo -e "$1"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

log_header() {
    log "${PURPLE}🔍 $1${NC}"
}

# Error tracking
ERRORS=0
WARNINGS=0

# Service definitions
declare -A SERVICES=(
    ["backend"]="3001"
    ["cod-service"]="8001"
    ["asterisk-mcp"]="8002"
    ["blockoli"]="8003"
    ["voice-system"]="8004"
    ["deepclaude"]="8006"
    ["control-tower"]="8007"
)

declare -A SERVICE_PATHS=(
    ["backend"]="apps/backend"
    ["cod-service"]="services/chain-of-debate"
    ["asterisk-mcp"]="services/asterisk-mcp"
    ["blockoli"]="services/blockoli-mcp"
    ["voice-system"]="services/voice-system"
    ["deepclaude"]="services/deepclaude"
    ["control-tower"]="services/control-tower"
)

# Function to check if a port is available
check_port() {
    local port=$1
    if command -v nc >/dev/null 2>&1; then
        nc -z sam.chat "$port" 2>/dev/null
    elif command -v telnet >/dev/null 2>&1; then
        timeout 3 telnet sam.chat "$port" 2>/dev/null | grep -q "Connected"
    else
        # Fallback using /dev/tcp
        (echo >/dev/tcp/sam.chat/"$port") 2>/dev/null
    fi
}

# Function to check service health via HTTP
check_service_health() {
    local service=$1
    local port=$2
    local health_endpoint="http://sam.chat:$port/health"
    
    if command -v curl >/dev/null 2>&1; then
        curl -s -f --connect-timeout 5 "$health_endpoint" >/dev/null
    elif command -v wget >/dev/null 2>&1; then
        wget -q -T 5 -O /dev/null "$health_endpoint" 2>/dev/null
    else
        # Fallback to port check
        check_port "$port"
    fi
}

# Header
clear
log_header "═══════════════════════════════════════════════════════════════"
log_header "🎛️  UltraMCP Supreme Stack - Integration Verification"
log_header "═══════════════════════════════════════════════════════════════"
log_info "Timestamp: $TIMESTAMP"
log_info "Project Root: $PROJECT_ROOT"
log_info "Log File: $LOG_FILE"
log_header "═══════════════════════════════════════════════════════════════"

# 1. File Structure Verification
log_header "📁 Verifying File Structure and Components"

# Check Docker Compose files
log_info "Checking Docker orchestration files..."
if [[ -f "$PROJECT_ROOT/docker-compose.hybrid.yml" ]]; then
    log_success "Docker Compose hybrid configuration found"
    
    # Verify all services are defined in Docker Compose
    for service in "${!SERVICES[@]}"; do
        # Map service names to Docker Compose service names
        compose_service_name="$service"
        case $service in
            "backend") compose_service_name="ultramcp-terminal" ;;
            "cod-service") compose_service_name="ultramcp-cod-service" ;;
            "asterisk-mcp") compose_service_name="ultramcp-asterisk-mcp" ;;
            "blockoli") compose_service_name="ultramcp-blockoli" ;;
            "voice-system") compose_service_name="ultramcp-voice" ;;
            "deepclaude") compose_service_name="ultramcp-deepclaude" ;;
            "control-tower") compose_service_name="ultramcp-control-tower" ;;
        esac
        
        if grep -q "$compose_service_name" "$PROJECT_ROOT/docker-compose.hybrid.yml"; then
            log_success "Service '$service' found in Docker Compose"
        else
            log_error "Service '$service' NOT found in Docker Compose (looking for $compose_service_name)"
            ((ERRORS++))
        fi
    done
else
    log_error "Docker Compose hybrid configuration missing"
    ((ERRORS++))
fi

# Check service directories and files
log_info "Checking service file structure..."
for service in "${!SERVICE_PATHS[@]}"; do
    service_path="${SERVICE_PATHS[$service]}"
    full_path="$PROJECT_ROOT/$service_path"
    
    if [[ -d "$full_path" ]]; then
        log_success "Service directory exists: $service_path"
        
        # Check for Dockerfile
        if [[ -f "$full_path/Dockerfile" ]]; then
            log_success "Dockerfile found for $service"
        else
            log_warning "Dockerfile missing for $service"
            ((WARNINGS++))
        fi
        
        # Check for requirements/package files
        if [[ -f "$full_path/requirements.txt" ]] || [[ -f "$full_path/package.json" ]]; then
            log_success "Dependencies file found for $service"
        else
            log_warning "Dependencies file missing for $service"
            ((WARNINGS++))
        fi
        
        # Check for main service file
        case $service in
            "backend")
                if [[ -f "$full_path/src/index.js" ]]; then
                    log_success "Main service file found for $service"
                else
                    log_error "Main service file missing for $service"
                    ((ERRORS++))
                fi
                ;;
            "control-tower")
                if [[ -f "$full_path/control_tower_service.js" ]]; then
                    log_success "Main service file found for $service"
                else
                    log_error "Main service file missing for $service"
                    ((ERRORS++))
                fi
                ;;
            "asterisk-mcp")
                if [[ -f "$full_path/asterisk_security_service.py" ]] || [[ -f "$full_path/entrypoint.py" ]]; then
                    log_success "Main service file found for $service"
                else
                    log_error "Main service file missing for $service"
                    ((ERRORS++))
                fi
                ;;
            "voice-system")
                if [[ -f "$full_path/voice_service.py" ]] || [[ -f "$full_path/entrypoint.py" ]]; then
                    log_success "Main service file found for $service"
                else
                    log_error "Main service file missing for $service"
                    ((ERRORS++))
                fi
                ;;
            *)
                if [[ -f "$full_path/${service}_service.py" ]] || [[ -f "$full_path/entrypoint.py" ]]; then
                    log_success "Main service file found for $service"
                else
                    log_error "Main service file missing for $service"
                    ((ERRORS++))
                fi
                ;;
        esac
    else
        log_error "Service directory missing: $service_path"
        ((ERRORS++))
    fi
done

# 2. Database Schema Verification
log_header "🗄️  Verifying Database Integration"

if [[ -f "$PROJECT_ROOT/database/schemas/init.sql" ]]; then
    log_success "Database schema file found"
    
    # Check if schema includes all services
    schema_content=$(cat "$PROJECT_ROOT/database/schemas/init.sql")
    for service in "${!SERVICES[@]}"; do
        if [[ "$service" == "backend" ]]; then continue; fi
        
        # Convert service name to expected table pattern
        case $service in
            "cod-service") table_pattern="cod_debates" ;;
            "asterisk-mcp") table_pattern="security_scans" ;;
            "blockoli") table_pattern="blockoli_projects" ;;
            "voice-system") table_pattern="voice_sessions" ;;
            "deepclaude") table_pattern="deepclaude_reasoning" ;;
            "control-tower") table_pattern="control_tower_orchestrations" ;;
        esac
        
        if echo "$schema_content" | grep -q "$table_pattern"; then
            log_success "Database tables defined for $service"
        else
            log_warning "Database tables missing for $service"
            ((WARNINGS++))
        fi
    done
else
    log_error "Database schema file missing"
    ((ERRORS++))
fi

# 3. Environment Configuration Verification
log_header "⚙️  Verifying Environment Configuration"

if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
    log_success "Environment template found"
    
    env_content=$(cat "$PROJECT_ROOT/.env.example")
    
    # Check service URL configurations
    for service in "${!SERVICES[@]}"; do
        # Map service names to environment variable patterns
        case $service in
            "backend") 
                # Backend doesn't need a service URL config
                log_success "Environment config found for $service (not needed)"
                ;;
            "cod-service")
                if echo "$env_content" | grep -q "COD_SERVICE_URL"; then
                    log_success "Environment config found for $service"
                else
                    log_warning "Environment config missing for $service"
                    ((WARNINGS++))
                fi
                ;;
            "asterisk-mcp")
                if echo "$env_content" | grep -q "ASTERISK_SERVICE_URL"; then
                    log_success "Environment config found for $service"
                else
                    log_warning "Environment config missing for $service"
                    ((WARNINGS++))
                fi
                ;;
            "blockoli")
                if echo "$env_content" | grep -q "BLOCKOLI_SERVICE_URL"; then
                    log_success "Environment config found for $service"
                else
                    log_warning "Environment config missing for $service"
                    ((WARNINGS++))
                fi
                ;;
            "voice-system")
                if echo "$env_content" | grep -q "VOICE_SERVICE_URL"; then
                    log_success "Environment config found for $service"
                else
                    log_warning "Environment config missing for $service"
                    ((WARNINGS++))
                fi
                ;;
            "deepclaude")
                if echo "$env_content" | grep -q "DEEPCLAUDE_SERVICE_URL"; then
                    log_success "Environment config found for $service"
                else
                    log_warning "Environment config missing for $service"
                    ((WARNINGS++))
                fi
                ;;
            "control-tower")
                if echo "$env_content" | grep -q "CONTROL_TOWER_URL"; then
                    log_success "Environment config found for $service"
                else
                    log_warning "Environment config missing for $service"
                    ((WARNINGS++))
                fi
                ;;
        esac
    done
else
    log_error "Environment template file missing"
    ((ERRORS++))
fi

# 4. API Gateway Integration Verification
log_header "🌐 Verifying API Gateway Integration"

backend_index="$PROJECT_ROOT/apps/backend/src/index.js"
if [[ -f "$backend_index" ]]; then
    log_success "Backend API Gateway file found"
    
    backend_content=$(cat "$backend_index")
    
    # Check for http-proxy-middleware import
    if echo "$backend_content" | grep -q "http-proxy-middleware"; then
        log_success "Proxy middleware imported in API Gateway"
    else
        log_error "Proxy middleware missing in API Gateway"
        ((ERRORS++))
    fi
    
    # Check for service proxy routes
    api_routes=("security" "blockoli" "voice" "deepclaude" "cod" "orchestrate")
    for route in "${api_routes[@]}"; do
        if echo "$backend_content" | grep -q "/api/$route"; then
            log_success "API route configured for $route"
        else
            log_error "API route missing for $route"
            ((ERRORS++))
        fi
    done
    
    # Check for health aggregation endpoint
    if echo "$backend_content" | grep -q "/api/health"; then
        log_success "Health aggregation endpoint configured"
    else
        log_error "Health aggregation endpoint missing"
        ((ERRORS++))
    fi
    
else
    log_error "Backend API Gateway file missing"
    ((ERRORS++))
fi

# 5. Service Connectivity Check (if services are running)
log_header "🔌 Checking Service Connectivity (if running)"

running_services=0
for service in "${!SERVICES[@]}"; do
    port="${SERVICES[$service]}"
    
    if check_port "$port"; then
        log_success "Service $service is running on port $port"
        ((running_services++))
        
        # Try to check health endpoint
        if check_service_health "$service" "$port"; then
            log_success "Health check passed for $service"
        else
            log_warning "Health check failed for $service (may not be fully ready)"
            ((WARNINGS++))
        fi
    else
        log_info "Service $service not running on port $port (expected if not started)"
    fi
done

if [[ $running_services -gt 0 ]]; then
    log_info "Found $running_services running services"
else
    log_info "No services currently running - this is normal if not started"
fi

# 6. Cross-Service Integration Check
log_header "🔗 Verifying Cross-Service Integration"

# Check if Control Tower has orchestration endpoints
control_tower_service="$PROJECT_ROOT/services/control-tower/control_tower_service.js"
if [[ -f "$control_tower_service" ]]; then
    ct_content=$(cat "$control_tower_service")
    
    orchestration_endpoints=("orchestrate/debate" "orchestrate/security-analysis" "orchestrate/voice-debate")
    for endpoint in "${orchestration_endpoints[@]}"; do
        if echo "$ct_content" | grep -q "$endpoint"; then
            log_success "Control Tower orchestration endpoint: $endpoint"
        else
            log_error "Control Tower missing endpoint: $endpoint"
            ((ERRORS++))
        fi
    done
else
    log_error "Control Tower service file missing for integration check"
    ((ERRORS++))
fi

# Check if services have integration capabilities
integration_checks=(
    "blockoli:code_intelligent_cod.py"
    "voice-system:voice_service.py"
    "deepclaude:deepclaude_service.py"
    "asterisk-mcp:asterisk_security_service.py"
)

for check in "${integration_checks[@]}"; do
    service=$(echo "$check" | cut -d: -f1)
    file=$(echo "$check" | cut -d: -f2)
    service_path="${SERVICE_PATHS[$service]}"
    full_file_path="$PROJECT_ROOT/$service_path/$file"
    
    if [[ -f "$full_file_path" ]]; then
        log_success "Integration service file found: $service/$file"
    else
        log_error "Integration service file missing: $service/$file"
        ((ERRORS++))
    fi
done

# 7. Make Commands Integration Check
log_header "⚡ Verifying Make Commands Integration"

makefile="$PROJECT_ROOT/Makefile"
if [[ -f "$makefile" ]]; then
    log_success "Makefile found"
    
    makefile_content=$(cat "$makefile")
    
    # Check for service-specific commands
    service_commands=("docker-hybrid" "status" "health-check" "cod-local" "local-chat")
    for cmd in "${service_commands[@]}"; do
        if echo "$makefile_content" | grep -q "^$cmd:"; then
            log_success "Make command available: $cmd"
        else
            log_warning "Make command missing: $cmd"
            ((WARNINGS++))
        fi
    done
else
    log_error "Makefile missing"
    ((ERRORS++))
fi

# Final Summary
log_header "═══════════════════════════════════════════════════════════════"
log_header "📊 Integration Verification Results"
log_header "═══════════════════════════════════════════════════════════════"

total_checks=$((ERRORS + WARNINGS))
if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    log_success "🎉 PERFECT INTEGRATION: All services are properly integrated!"
    log_success "✅ No loose components found"
    log_success "✅ All services have proper orchestration"
    log_success "✅ API Gateway routing is complete"
    log_success "✅ Database schemas are comprehensive"
    log_success "✅ Environment configuration is complete"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    log_warning "⚠️  MOSTLY INTEGRATED: $WARNINGS warnings found"
    log_info "Warnings are typically non-critical issues"
    log_info "System should function properly with these warnings"
    exit 0
else
    log_error "💥 INTEGRATION ISSUES: $ERRORS critical errors, $WARNINGS warnings"
    log_error "❌ Some components may be loose or improperly integrated"
    log_error "🔧 Fix these errors before deployment"
    
    log_info ""
    log_info "Common fixes:"
    log_info "1. Ensure all Dockerfiles exist for each service"
    log_info "2. Add missing API routes to backend/src/index.js"
    log_info "3. Complete database schema definitions"
    log_info "4. Add missing environment variables"
    log_info "5. Implement missing health check endpoints"
    
    exit 1
fi

log_header "═══════════════════════════════════════════════════════════════"
log_info "Verification completed at $(date '+%Y-%m-%d %H:%M:%S')"
log_info "Detailed log saved to: $LOG_FILE"
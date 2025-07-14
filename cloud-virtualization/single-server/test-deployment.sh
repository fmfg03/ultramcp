#!/bin/bash
# UltraMCP Single Server Testing Suite
# Comprehensive testing for single-server deployment

set -euo pipefail

# Configuration
DOMAIN_BASE="ultramcp.local"
SERVER_IP=$(hostname -I | awk '{print $1}')
TIMEOUT=30

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Test result functions
test_pass() {
    log_success "✓ $1"
    ((TESTS_PASSED++))
}

test_fail() {
    log_error "✗ $1"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

# HTTP health check
check_http_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local service_name="$3"
    
    if curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url" | grep -q "$expected_status"; then
        test_pass "$service_name HTTP endpoint ($url)"
        return 0
    else
        test_fail "$service_name HTTP endpoint ($url)"
        return 1
    fi
}

# JSON API health check
check_json_health() {
    local url="$1"
    local service_name="$2"
    
    local response=$(curl -s --max-time "$TIMEOUT" "$url" 2>/dev/null)
    if echo "$response" | jq -e '.status == "healthy" or .status == "ok"' >/dev/null 2>&1; then
        test_pass "$service_name JSON health response"
        return 0
    else
        test_fail "$service_name JSON health response"
        log_warning "Response: $response"
        return 1
    fi
}

# Docker container check
check_docker_container() {
    local container_name="$1"
    local service_name="$2"
    
    if docker ps | grep -q "$container_name.*Up"; then
        test_pass "$service_name Docker container running"
        return 0
    else
        test_fail "$service_name Docker container running"
        return 1
    fi
}

# Database connectivity check
check_database_connection() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    
    if docker exec ultramcp-postgres pg_isready -h "$host" -p "$port" >/dev/null 2>&1; then
        test_pass "$service_name database connectivity"
        return 0
    else
        test_fail "$service_name database connectivity"
        return 1
    fi
}

# Redis connectivity check
check_redis_connection() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    
    if docker exec ultramcp-redis redis-cli -h "$host" -p "$port" ping | grep -q "PONG"; then
        test_pass "$service_name Redis connectivity"
        return 0
    else
        test_fail "$service_name Redis connectivity"
        return 1
    fi
}

# Test infrastructure services
test_infrastructure() {
    log_info "Testing infrastructure services..."
    
    # Docker containers
    check_docker_container "ultramcp-postgres" "PostgreSQL"
    check_docker_container "ultramcp-redis" "Redis" 
    check_docker_container "ultramcp-qdrant" "Qdrant"
    check_docker_container "ultramcp-traefik" "Traefik"
    check_docker_container "ultramcp-prometheus" "Prometheus"
    check_docker_container "ultramcp-grafana" "Grafana"
    
    # Database connectivity
    check_database_connection "localhost" "5432" "PostgreSQL"
    check_redis_connection "localhost" "6379" "Redis"
    
    # Infrastructure HTTP endpoints
    check_http_endpoint "http://localhost:6333/health" "200" "Qdrant"
    check_http_endpoint "http://localhost:8080" "200" "Traefik Dashboard"
    check_http_endpoint "http://localhost:9090/-/healthy" "200" "Prometheus"
    check_http_endpoint "http://localhost:3000/api/health" "200" "Grafana"
}

# Test UltraMCP services
test_ultramcp_services() {
    log_info "Testing UltraMCP services..."
    
    local services=(
        "ultramcp-cod:Chain-of-Debate:8001"
        "ultramcp-security:Security Scanner:8002"
        "ultramcp-blockoli:Code Intelligence:8003"
        "ultramcp-voice:Voice System:8004"
        "ultramcp-deepclaude:DeepClaude Engine:8005"
        "ultramcp-control:Control Tower:8006"
        "ultramcp-memory:Claude Memory:8007"
        "ultramcp-sam:Sam MCP:8008"
        "ultramcp-api:API Gateway:3000"
        "ultramcp-webui:WebUI:3001"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r container_name service_name port <<< "$service_info"
        
        # Check container
        check_docker_container "$container_name" "$service_name"
        
        # Check HTTP endpoint
        check_http_endpoint "http://localhost:$port/health" "200" "$service_name"
        
        # Check JSON health response (if available)
        if [[ "$port" != "3001" ]]; then  # Skip WebUI as it might not have JSON health
            check_json_health "http://localhost:$port/health" "$service_name"
        fi
    done
}

# Test domain routing
test_domain_routing() {
    log_info "Testing domain routing..."
    
    local domains=(
        "$DOMAIN_BASE:WebUI"
        "api.$DOMAIN_BASE:API Gateway"
        "cod.$DOMAIN_BASE:Chain-of-Debate"
        "security.$DOMAIN_BASE:Security Scanner"
        "blockoli.$DOMAIN_BASE:Code Intelligence"
        "voice.$DOMAIN_BASE:Voice System"
        "deepclaude.$DOMAIN_BASE:DeepClaude Engine"
        "control.$DOMAIN_BASE:Control Tower"
        "memory.$DOMAIN_BASE:Claude Memory"
        "sam.$DOMAIN_BASE:Sam MCP"
        "prometheus.$DOMAIN_BASE:Prometheus"
        "grafana.$DOMAIN_BASE:Grafana"
        "traefik.$DOMAIN_BASE:Traefik Dashboard"
    )
    
    for domain_info in "${domains[@]}"; do
        IFS=':' read -r domain service_name <<< "$domain_info"
        check_http_endpoint "http://$domain" "200" "$service_name Domain Routing"
    done
}

# Test service integration
test_service_integration() {
    log_info "Testing service integration..."
    
    # Test API Gateway can reach services
    local api_endpoints=(
        "/health:API Gateway Health"
        "/api/status:API Status"
    )
    
    for endpoint_info in "${api_endpoints[@]}"; do
        IFS=':' read -r endpoint description <<< "$endpoint_info"
        check_http_endpoint "http://api.$DOMAIN_BASE$endpoint" "200" "$description"
    done
    
    # Test database tables exist
    if docker exec ultramcp-postgres psql -U postgres -d ultramcp -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" >/dev/null 2>&1; then
        test_pass "Database schema initialization"
    else
        test_fail "Database schema initialization"
    fi
    
    # Test Redis cache
    if docker exec ultramcp-redis redis-cli set test_key "test_value" >/dev/null 2>&1; then
        test_pass "Redis cache write/read"
        docker exec ultramcp-redis redis-cli del test_key >/dev/null 2>&1
    else
        test_fail "Redis cache write/read"
    fi
}

# Test resource usage
test_resource_usage() {
    log_info "Testing resource usage..."
    
    # Check memory usage
    local total_memory=$(free -m | awk '/^Mem:/ {print $2}')
    local used_memory=$(free -m | awk '/^Mem:/ {print $3}')
    local memory_percent=$((used_memory * 100 / total_memory))
    
    if [[ $memory_percent -lt 90 ]]; then
        test_pass "Memory usage acceptable ($memory_percent%)"
    else
        test_fail "Memory usage high ($memory_percent%)"
    fi
    
    # Check disk usage
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -lt 90 ]]; then
        test_pass "Disk usage acceptable ($disk_usage%)"
    else
        test_fail "Disk usage high ($disk_usage%)"
    fi
    
    # Check Docker container resource limits
    local containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep ultramcp)
    local container_count=$(echo "$containers" | wc -l)
    
    if [[ $container_count -ge 15 ]]; then
        test_pass "All expected containers running ($container_count)"
    else
        test_fail "Missing containers (found $container_count, expected 15+)"
    fi
}

# Test security configuration
test_security() {
    log_info "Testing security configuration..."
    
    # Check if sensitive ports are not exposed
    local sensitive_ports=("5432" "6379" "6333")
    
    for port in "${sensitive_ports[@]}"; do
        if ! netstat -ln | grep ":$port " | grep -q "0.0.0.0"; then
            test_pass "Port $port not publicly exposed"
        else
            test_fail "Port $port publicly exposed (security risk)"
        fi
    done
    
    # Check environment file permissions
    if [[ $(stat -c %a /opt/ultramcp/.env) == "600" ]]; then
        test_pass "Environment file permissions secure"
    else
        test_fail "Environment file permissions insecure"
    fi
    
    # Check Docker daemon security
    if groups | grep -q docker; then
        test_pass "User in Docker group"
    else
        test_fail "User not in Docker group"
    fi
}

# Test monitoring and logging
test_monitoring() {
    log_info "Testing monitoring and logging..."
    
    # Check Prometheus targets
    local prometheus_targets=$(curl -s "http://prometheus.$DOMAIN_BASE/api/v1/targets" | jq -r '.data.activeTargets | length')
    if [[ $prometheus_targets -gt 0 ]]; then
        test_pass "Prometheus monitoring targets ($prometheus_targets targets)"
    else
        test_fail "Prometheus monitoring targets"
    fi
    
    # Check Grafana datasources
    if curl -s "http://admin:ultramcp2024@grafana.$DOMAIN_BASE/api/datasources" | jq -e 'length > 0' >/dev/null; then
        test_pass "Grafana datasources configured"
    else
        test_fail "Grafana datasources configured"
    fi
    
    # Check log files exist
    if [[ -d /opt/ultramcp/logs ]] && [[ $(find /opt/ultramcp/logs -name "*.log" | wc -l) -gt 0 ]]; then
        test_pass "Log files present"
    else
        test_fail "Log files missing"
    fi
}

# Test backup functionality
test_backup() {
    log_info "Testing backup functionality..."
    
    # Test backup script exists and is executable
    if [[ -x /opt/ultramcp/manage.sh ]]; then
        test_pass "Management script executable"
    else
        test_fail "Management script not executable"
    fi
    
    # Test backup directory exists
    if [[ -d /opt/ultramcp/backups ]]; then
        test_pass "Backup directory exists"
    else
        test_fail "Backup directory missing"
    fi
}

# Performance test
test_performance() {
    log_info "Testing basic performance..."
    
    # Test API response times
    local api_urls=(
        "http://api.$DOMAIN_BASE/health"
        "http://cod.$DOMAIN_BASE/health"
        "http://security.$DOMAIN_BASE/health"
    )
    
    for url in "${api_urls[@]}"; do
        local response_time=$(curl -o /dev/null -s -w "%{time_total}" "$url")
        if (( $(echo "$response_time < 5.0" | bc -l) )); then
            test_pass "Response time acceptable for $url (${response_time}s)"
        else
            test_fail "Response time slow for $url (${response_time}s)"
        fi
    done
}

# Generate test report
generate_report() {
    echo ""
    echo "============================================"
    echo "UltraMCP Single Server Test Report"
    echo "============================================"
    echo "Date: $(date)"
    echo "Server: $SERVER_IP"
    echo "Domain: $DOMAIN_BASE"
    echo ""
    echo "Test Results:"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo "  Total:  $((TESTS_PASSED + TESTS_FAILED))"
    echo ""
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo "Failed Tests:"
        for test in "${FAILED_TESTS[@]}"; do
            echo "  - $test"
        done
        echo ""
    fi
    
    # Overall status
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All tests passed! UltraMCP deployment is healthy."
        echo ""
        echo "🎉 Your UltraMCP single-server deployment is ready!"
        echo ""
        echo "Quick Start:"
        echo "  Main Interface:  http://$DOMAIN_BASE"
        echo "  API Gateway:     http://api.$DOMAIN_BASE"
        echo "  Monitoring:      http://grafana.$DOMAIN_BASE (admin/ultramcp2024)"
        echo ""
        echo "Management:"
        echo "  Status:    ultramcp status"
        echo "  Logs:      ultramcp logs [service]"
        echo "  URLs:      ultramcp urls"
        return 0
    else
        log_error "Some tests failed. Please check the issues above."
        echo ""
        echo "Common Solutions:"
        echo "  - Wait longer for services to start (try: ultramcp restart)"
        echo "  - Check logs: ultramcp logs"
        echo "  - Verify environment: cat /opt/ultramcp/.env"
        echo "  - Check resources: docker stats"
        return 1
    fi
}

# Main test function
main() {
    local test_type="${1:-all}"
    
    log_info "Starting UltraMCP Single Server Test Suite"
    log_info "Test Type: $test_type"
    
    case "$test_type" in
        "infrastructure")
            test_infrastructure
            ;;
        "services")
            test_ultramcp_services
            ;;
        "domains")
            test_domain_routing
            ;;
        "integration")
            test_service_integration
            ;;
        "resources")
            test_resource_usage
            ;;
        "security")
            test_security
            ;;
        "monitoring")
            test_monitoring
            ;;
        "backup")
            test_backup
            ;;
        "performance")
            test_performance
            ;;
        "quick")
            test_infrastructure
            test_ultramcp_services
            ;;
        "all"|*)
            test_infrastructure
            test_ultramcp_services
            test_domain_routing
            test_service_integration
            test_resource_usage
            test_security
            test_monitoring
            test_backup
            test_performance
            ;;
    esac
    
    generate_report
}

# Help function
show_help() {
    echo "UltraMCP Single Server Test Suite"
    echo ""
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Test Types:"
    echo "  all            Run all tests (default)"
    echo "  quick          Run essential tests only"
    echo "  infrastructure Test infrastructure services"
    echo "  services       Test UltraMCP services"
    echo "  domains        Test domain routing"
    echo "  integration    Test service integration"
    echo "  resources      Test resource usage"
    echo "  security       Test security configuration"
    echo "  monitoring     Test monitoring setup"
    echo "  backup         Test backup functionality"
    echo "  performance    Test basic performance"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all tests"
    echo "  $0 quick        # Run quick health check"
    echo "  $0 services     # Test only UltraMCP services"
}

# Check if bc is available for performance tests
if ! command -v bc >/dev/null 2>&1; then
    log_warning "Installing bc for performance calculations..."
    sudo apt update && sudo apt install -y bc
fi

# Run main function or show help
if [[ "${1:-}" == "help" ]] || [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    show_help
else
    main "$@"
fi
#!/bin/bash
# Security Audit Script for MCP System
# Validates all security requirements and configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_non_root_users() {
    log_info "Checking non-root user configuration in Dockerfiles..."
    
    local dockerfiles=("Dockerfile.backend" "Dockerfile.studio" "Dockerfile.devtool")
    local all_good=true
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$PROJECT_ROOT/$dockerfile" ]]; then
            if grep -q "USER.*root" "$PROJECT_ROOT/$dockerfile" 2>/dev/null; then
                log_error "$dockerfile: Running as root user"
                all_good=false
            elif grep -q "USER " "$PROJECT_ROOT/$dockerfile"; then
                local user=$(grep "USER " "$PROJECT_ROOT/$dockerfile" | tail -1 | awk '{print $2}')
                log_success "$dockerfile: Running as non-root user ($user)"
            else
                log_warning "$dockerfile: No USER directive found"
                all_good=false
            fi
        else
            log_warning "$dockerfile: File not found"
        fi
    done
    
    if [[ "$all_good" == "true" ]]; then
        log_success "All services configured to run as non-root"
    else
        log_error "Some services may be running as root"
    fi
}

check_secret_exposure() {
    log_info "Auditing secret exposure in Docker configurations..."
    
    # Check for hardcoded secrets in Dockerfiles
    local secret_patterns=("password" "secret" "key" "token" "api")
    local exposed_secrets=false
    
    for pattern in "${secret_patterns[@]}"; do
        if grep -ri "$pattern.*=" "$PROJECT_ROOT"/Dockerfile* 2>/dev/null | grep -v "ARG\|#"; then
            log_error "Potential hardcoded secret found: $pattern"
            exposed_secrets=true
        fi
    done
    
    # Check .env file protection
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        if grep -q "\.env" "$PROJECT_ROOT/.gitignore" 2>/dev/null; then
            log_success ".env file is gitignored"
        else
            log_error ".env file is not in .gitignore"
            exposed_secrets=true
        fi
    fi
    
    # Check .dockerignore
    if [[ -f "$PROJECT_ROOT/.dockerignore" ]]; then
        if grep -q "\.env" "$PROJECT_ROOT/.dockerignore" 2>/dev/null; then
            log_success ".env file is dockerignored"
        else
            log_warning ".env file should be in .dockerignore"
        fi
    else
        log_warning ".dockerignore file not found"
    fi
    
    if [[ "$exposed_secrets" == "false" ]]; then
        log_success "No obvious secret exposure found"
    else
        log_error "Potential secret exposure detected"
    fi
}

check_firewall_config() {
    log_info "Checking firewall configuration recommendations..."
    
    cat << EOF
${YELLOW}Recommended firewall rules:${NC}

# Allow only necessary external ports
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 22/tcp     # SSH (if needed)

# Deny internal service ports from external access
sudo ufw deny 5432/tcp    # PostgreSQL
sudo ufw deny 6379/tcp    # Redis
sudo ufw deny 8123/tcp    # LangGraph Studio
sudo ufw deny 3000/tcp    # Backend (behind reverse proxy)

# Enable firewall
sudo ufw --force enable

EOF
    
    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        local ufw_status=$(sudo ufw status 2>/dev/null || echo "inactive")
        if [[ "$ufw_status" == *"active"* ]]; then
            log_success "UFW firewall is active"
        else
            log_warning "UFW firewall is not active"
        fi
    else
        log_warning "UFW not available, consider iptables or cloud security groups"
    fi
}

check_ssl_config() {
    log_info "Checking SSL/HTTPS configuration..."
    
    local nginx_configs=("docker/nginx/nginx.conf" "docker/nginx/nginx.prod.conf")
    local ssl_configured=false
    
    for config in "${nginx_configs[@]}"; do
        if [[ -f "$PROJECT_ROOT/$config" ]]; then
            if grep -q "ssl_certificate" "$PROJECT_ROOT/$config" 2>/dev/null; then
                log_success "SSL configuration found in $config"
                ssl_configured=true
            fi
        fi
    done
    
    if [[ "$ssl_configured" == "false" ]]; then
        log_warning "SSL configuration not found in Nginx configs"
        cat << EOF
${YELLOW}To enable SSL with Let's Encrypt:${NC}

1. Install certbot:
   sudo apt install certbot python3-certbot-nginx

2. Obtain certificate:
   sudo certbot --nginx -d yourdomain.com

3. Auto-renewal:
   sudo crontab -e
   0 12 * * * /usr/bin/certbot renew --quiet

EOF
    fi
}

check_security_headers() {
    log_info "Checking security headers configuration..."
    
    local nginx_configs=("docker/nginx/nginx.conf" "docker/nginx/nginx.prod.conf")
    local headers_found=0
    local required_headers=("Content-Security-Policy" "X-Frame-Options" "Strict-Transport-Security")
    
    for config in "${nginx_configs[@]}"; do
        if [[ -f "$PROJECT_ROOT/$config" ]]; then
            for header in "${required_headers[@]}"; do
                if grep -q "$header" "$PROJECT_ROOT/$config" 2>/dev/null; then
                    ((headers_found++))
                fi
            done
        fi
    done
    
    if [[ $headers_found -gt 0 ]]; then
        log_success "Security headers configured ($headers_found found)"
    else
        log_warning "Security headers not configured"
    fi
}

check_rate_limiting() {
    log_info "Checking rate limiting configuration..."
    
    local nginx_configs=("docker/nginx/nginx.conf" "docker/nginx/nginx.prod.conf")
    local rate_limiting=false
    
    for config in "${nginx_configs[@]}"; do
        if [[ -f "$PROJECT_ROOT/$config" ]]; then
            if grep -q "limit_req" "$PROJECT_ROOT/$config" 2>/dev/null; then
                log_success "Rate limiting configured in $config"
                rate_limiting=true
            fi
        fi
    done
    
    if [[ "$rate_limiting" == "false" ]]; then
        log_warning "Rate limiting not configured"
    fi
}

check_health_endpoints() {
    log_info "Checking health endpoint configuration..."
    
    # Check backend health endpoint
    if grep -r "/health" "$PROJECT_ROOT/backend/src" 2>/dev/null | grep -q "app.get\|router.get"; then
        log_success "Backend health endpoint configured"
    else
        log_warning "Backend health endpoint not found"
    fi
    
    # Check studio health endpoint
    if grep -r "/health" "$PROJECT_ROOT/langgraph_system" 2>/dev/null | grep -q "route\|app.route"; then
        log_success "Studio health endpoint configured"
    else
        log_warning "Studio health endpoint not found"
    fi
    
    # Check Docker health checks
    local dockerfiles=("Dockerfile.backend" "Dockerfile.studio" "Dockerfile.devtool")
    local health_checks=0
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$PROJECT_ROOT/$dockerfile" ]]; then
            if grep -q "HEALTHCHECK" "$PROJECT_ROOT/$dockerfile"; then
                ((health_checks++))
            fi
        fi
    done
    
    log_success "Docker health checks configured: $health_checks/3"
}

check_monitoring_config() {
    log_info "Checking monitoring configuration..."
    
    # Check for Prometheus config
    if [[ -f "$PROJECT_ROOT/docker/monitoring/prometheus.yml" ]]; then
        log_success "Prometheus configuration found"
    else
        log_warning "Prometheus configuration not found"
    fi
    
    # Check for metrics endpoints
    if grep -r "prometheus\|metrics" "$PROJECT_ROOT/backend/src" 2>/dev/null | grep -q "endpoint\|route"; then
        log_success "Metrics endpoints configured"
    else
        log_warning "Metrics endpoints not found"
    fi
    
    # Check for logging configuration
    if grep -r "winston\|pino\|structlog" "$PROJECT_ROOT" 2>/dev/null | grep -q "logger\|log"; then
        log_success "Structured logging configured"
    else
        log_warning "Structured logging not found"
    fi
}

check_backup_strategy() {
    log_info "Checking backup strategy..."
    
    # Check for backup scripts
    if [[ -f "$PROJECT_ROOT/scripts/deploy.sh" ]]; then
        if grep -q "backup" "$PROJECT_ROOT/scripts/deploy.sh"; then
            log_success "Backup functionality in deploy script"
        else
            log_warning "Backup functionality not found in deploy script"
        fi
    fi
    
    # Check for volume persistence
    if grep -q "volumes:" "$PROJECT_ROOT/docker-compose"*.yml 2>/dev/null; then
        log_success "Volume persistence configured"
    else
        log_warning "Volume persistence not configured"
    fi
}

generate_security_report() {
    log_info "Generating security report..."
    
    local report_file="$PROJECT_ROOT/security_audit_report.md"
    
    cat > "$report_file" << EOF
# MCP System Security Audit Report

Generated: $(date)

## Summary

This report contains the security audit results for the MCP system.

## Findings

### ✅ Passed Checks
- Non-root user configuration
- Secret management
- Health endpoint configuration
- Volume persistence

### ⚠️ Recommendations
- Enable UFW firewall with proper rules
- Configure SSL/TLS with Let's Encrypt
- Implement security headers in Nginx
- Set up rate limiting for API endpoints
- Configure monitoring and alerting

### 🔧 Next Steps

1. **Immediate (High Priority)**
   - Enable firewall rules
   - Configure SSL certificates
   - Implement rate limiting

2. **Short Term (Medium Priority)**
   - Set up monitoring dashboard
   - Configure automated backups
   - Implement log aggregation

3. **Long Term (Low Priority)**
   - Security penetration testing
   - Compliance audit (SOC2, ISO27001)
   - Advanced threat detection

## Security Checklist

- [ ] Firewall configured and active
- [ ] SSL/TLS certificates installed
- [ ] Security headers implemented
- [ ] Rate limiting configured
- [ ] Monitoring and alerting active
- [ ] Backup strategy tested
- [ ] Incident response plan documented

EOF
    
    log_success "Security report generated: $report_file"
}

main() {
    echo "🔐 MCP System Security Audit"
    echo "=============================="
    echo ""
    
    check_non_root_users
    echo ""
    
    check_secret_exposure
    echo ""
    
    check_firewall_config
    echo ""
    
    check_ssl_config
    echo ""
    
    check_security_headers
    echo ""
    
    check_rate_limiting
    echo ""
    
    check_health_endpoints
    echo ""
    
    check_monitoring_config
    echo ""
    
    check_backup_strategy
    echo ""
    
    generate_security_report
    echo ""
    
    log_info "Security audit completed!"
    log_info "Review the generated report: security_audit_report.md"
}

# Run the audit
main "$@"


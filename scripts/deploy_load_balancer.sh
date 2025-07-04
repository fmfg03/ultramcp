#!/bin/bash

# UltraMCP ContextBuilderAgent 2.0 - Load Balancer Deployment Script
# Automated deployment of Nginx/HAProxy load balancing for production

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config/nginx"
LOGS_DIR="$PROJECT_ROOT/logs"
SSL_DIR="$CONFIG_DIR/ssl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check OpenSSL for SSL certificate generation
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is not installed"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create SSL certificates
create_ssl_certificates() {
    log "Creating SSL certificates..."
    
    mkdir -p "$SSL_DIR"
    
    # Generate self-signed certificate for development
    if [[ ! -f "$SSL_DIR/contextbuilder.crt" || ! -f "$SSL_DIR/contextbuilder.key" ]]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/contextbuilder.key" \
            -out "$SSL_DIR/contextbuilder.crt" \
            -subj "/C=US/ST=State/L=City/O=UltraMCP/CN=contextbuilder.ultramcp.local"
        
        # Create PEM file for HAProxy
        cat "$SSL_DIR/contextbuilder.crt" "$SSL_DIR/contextbuilder.key" > "$SSL_DIR/contextbuilder.pem"
        
        success "SSL certificates created"
    else
        log "SSL certificates already exist"
    fi
}

# Setup directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$LOGS_DIR/nginx"
    mkdir -p "$CONFIG_DIR/static"
    mkdir -p "$CONFIG_DIR/ssl"
    
    # Create simple index.html for static content
    cat > "$CONFIG_DIR/static/index.html" <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>UltraMCP ContextBuilderAgent 2.0</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .content { margin: 20px 0; }
        .service { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .status { color: #27ae60; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 UltraMCP ContextBuilderAgent 2.0</h1>
        <p>Next-Generation Semantic Coherence Platform</p>
    </div>
    
    <div class="content">
        <h2>Available Services</h2>
        
        <div class="service">
            <h3>Core Context Builder</h3>
            <p>Endpoint: <code>/api/context/</code></p>
            <p>Status: <span class="status">Load Balanced</span></p>
        </div>
        
        <div class="service">
            <h3>Belief Reviser</h3>
            <p>Endpoint: <code>/api/belief/</code></p>
            <p>Status: <span class="status">Load Balanced</span></p>
        </div>
        
        <div class="service">
            <h3>Contradiction Resolver</h3>
            <p>Endpoint: <code>/api/contradiction/</code></p>
            <p>Status: <span class="status">Active</span></p>
        </div>
        
        <div class="service">
            <h3>Utility Predictor</h3>
            <p>Endpoint: <code>/api/utility/</code></p>
            <p>Status: <span class="status">Active</span></p>
        </div>
        
        <div class="service">
            <h3>Context Drift Detector</h3>
            <p>Endpoint: <code>/api/drift/</code></p>
            <p>Status: <span class="status">Active</span></p>
        </div>
        
        <div class="service">
            <h3>Prompt Assembler</h3>
            <p>Endpoint: <code>/api/prompt/</code></p>
            <p>Status: <span class="status">Active</span></p>
        </div>
        
        <div class="service">
            <h3>Context Observatory</h3>
            <p>Endpoint: <code>/api/observatory/</code></p>
            <p>Status: <span class="status">Active</span></p>
        </div>
        
        <div class="service">
            <h3>Deterministic Debug</h3>
            <p>Endpoint: <code>/api/debug/</code></p>
            <p>Status: <span class="status">Active</span></p>
        </div>
        
        <div class="service">
            <h3>Context Memory Tuner</h3>
            <p>Endpoint: <code>/api/memory/</code></p>
            <p>Status: <span class="status">Active</span></p>
        </div>
    </div>
    
    <div class="content">
        <h2>System Information</h2>
        <p>Load Balancer: Nginx + HAProxy</p>
        <p>Services: 9 Microservices</p>
        <p>Health Check: <a href="/health">/health</a></p>
        <p>Status: <a href="/nginx_status">/nginx_status</a></p>
    </div>
</body>
</html>
EOF
    
    success "Directories setup completed"
}

# Deploy with Nginx
deploy_nginx() {
    log "Deploying with Nginx load balancer..."
    
    cd "$CONFIG_DIR"
    
    # Pull latest images
    docker-compose -f docker-compose.nginx.yml pull
    
    # Start services
    docker-compose -f docker-compose.nginx.yml up -d
    
    # Wait for services to start
    sleep 30
    
    # Check health
    if curl -f http://sam.chat:8080/health &> /dev/null; then
        success "Nginx load balancer deployed successfully"
        log "Services available at:"
        log "  - HTTP: http://sam.chat"
        log "  - HTTPS: https://sam.chat"
        log "  - Status: http://sam.chat:8080/status"
        log "  - Health: http://sam.chat:8080/health"
    else
        error "Nginx load balancer deployment failed"
        return 1
    fi
}

# Deploy with HAProxy
deploy_haproxy() {
    log "Deploying with HAProxy load balancer..."
    
    # Create HAProxy Docker Compose
    cat > "$CONFIG_DIR/docker-compose.haproxy.yml" <<EOF
version: '3.8'

services:
  haproxy-lb:
    image: haproxy:2.8-alpine
    container_name: ultramcp-contextbuilder-haproxy
    ports:
      - "80:80"
      - "443:443"
      - "8404:8404"  # Admin interface
      - "8405:8405"  # Health check
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - ./ssl:/etc/ssl/certs:ro
      - ../logs/haproxy:/var/log/haproxy
    networks:
      - contextbuilder-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://sam.chat:8405/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  contextbuilder-network:
    external: true
EOF
    
    cd "$CONFIG_DIR"
    
    # Create network if it doesn't exist
    docker network create contextbuilder-network 2>/dev/null || true
    
    # Start HAProxy
    docker-compose -f docker-compose.haproxy.yml up -d
    
    # Wait for services to start
    sleep 10
    
    # Check health
    if curl -f http://sam.chat:8405/health &> /dev/null; then
        success "HAProxy load balancer deployed successfully"
        log "Services available at:"
        log "  - HTTP: http://sam.chat"
        log "  - HTTPS: https://sam.chat"
        log "  - Admin: http://sam.chat:8404"
        log "  - Health: http://sam.chat:8405/health"
    else
        error "HAProxy load balancer deployment failed"
        return 1
    fi
}

# Test load balancer
test_load_balancer() {
    log "Testing load balancer..."
    
    # Test health endpoint
    if curl -f http://sam.chat/health &> /dev/null; then
        success "Health check passed"
    else
        error "Health check failed"
        return 1
    fi
    
    # Test API endpoints
    local endpoints=("/api/context/" "/api/belief/" "/api/contradiction/" "/api/utility/" "/api/drift/" "/api/prompt/" "/api/observatory/" "/api/debug/" "/api/memory/")
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f "http://sam.chat${endpoint}health" &> /dev/null; then
            success "Endpoint ${endpoint} is accessible"
        else
            warning "Endpoint ${endpoint} is not accessible"
        fi
    done
}

# Show status
show_status() {
    log "Load Balancer Status:"
    echo
    
    # Show running containers
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(nginx|haproxy|contextbuilder)"
    
    echo
    log "Service Health:"
    
    # Check each service
    local services=("8020" "8022" "8024" "8025" "8026" "8027" "8028" "8029" "8030")
    
    for port in "${services[@]}"; do
        if curl -f "http://sam.chat:${port}/health" &> /dev/null 2>&1; then
            echo -e "  Port ${port}: ${GREEN}✓ Healthy${NC}"
        else
            echo -e "  Port ${port}: ${RED}✗ Unhealthy${NC}"
        fi
    done
}

# Main deployment function
main() {
    local lb_type="${1:-nginx}"
    
    log "Starting ContextBuilderAgent 2.0 Load Balancer Deployment"
    log "Load Balancer Type: $lb_type"
    
    check_prerequisites
    setup_directories
    create_ssl_certificates
    
    case "$lb_type" in
        "nginx")
            deploy_nginx
            ;;
        "haproxy")
            deploy_haproxy
            ;;
        *)
            error "Invalid load balancer type: $lb_type"
            echo "Usage: $0 [nginx|haproxy]"
            exit 1
            ;;
    esac
    
    test_load_balancer
    show_status
    
    success "Load balancer deployment completed successfully!"
    log "You can now access the ContextBuilderAgent 2.0 platform at http://sam.chat"
}

# Command line interface
case "${1:-help}" in
    "deploy")
        main "${2:-nginx}"
        ;;
    "status")
        show_status
        ;;
    "test")
        test_load_balancer
        ;;
    "help"|*)
        echo "UltraMCP ContextBuilderAgent 2.0 - Load Balancer Deployment"
        echo
        echo "Usage: $0 [command] [options]"
        echo
        echo "Commands:"
        echo "  deploy [nginx|haproxy]  Deploy load balancer (default: nginx)"
        echo "  status                  Show load balancer status"
        echo "  test                    Test load balancer functionality"
        echo "  help                    Show this help message"
        echo
        echo "Examples:"
        echo "  $0 deploy nginx         Deploy with Nginx"
        echo "  $0 deploy haproxy       Deploy with HAProxy"
        echo "  $0 status               Check status"
        echo "  $0 test                 Test services"
        ;;
esac
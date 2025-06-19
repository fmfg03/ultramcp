#!/bin/bash
# Docker Volume Fix Script
# Fixes volume mounting issues in Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

cleanup_docker() {
    log_info "Cleaning up Docker environment..."
    
    # Stop and remove containers
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Remove problematic volumes
    docker volume rm supermcp_backend_temp 2>/dev/null || true
    docker volume rm supermcp_backend_logs 2>/dev/null || true
    docker volume rm supermcp_backend_uploads 2>/dev/null || true
    docker volume rm supermcp_studio_exports 2>/dev/null || true
    
    # Prune unused volumes
    docker volume prune -f 2>/dev/null || true
    
    log_success "Docker environment cleaned"
}

fix_permissions() {
    log_info "Fixing file permissions..."
    
    # Ensure current user owns the project directory
    sudo chown -R $USER:$USER . 2>/dev/null || true
    
    # Fix permissions for key directories
    chmod 755 . 2>/dev/null || true
    chmod -R 755 backend/ 2>/dev/null || true
    chmod -R 755 langgraph_system/ 2>/dev/null || true
    chmod -R 755 mcp-devtool-client/ 2>/dev/null || true
    chmod -R 755 docker/ 2>/dev/null || true
    chmod -R 755 scripts/ 2>/dev/null || true
    
    # Fix keys directory
    if [[ -d "keys" ]]; then
        chmod 755 keys/
        chmod 644 keys/* 2>/dev/null || true
    fi
    
    log_success "Permissions fixed"
}

check_docker_daemon() {
    log_info "Checking Docker daemon..."
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running or accessible"
        log_info "Try: sudo systemctl start docker"
        return 1
    fi
    
    log_success "Docker daemon is running"
}

check_disk_space() {
    log_info "Checking disk space..."
    
    local available=$(df . | tail -1 | awk '{print $4}')
    local available_gb=$((available / 1024 / 1024))
    
    if [[ $available_gb -lt 2 ]]; then
        log_warning "Low disk space: ${available_gb}GB available"
        log_info "Consider cleaning up: docker system prune -a"
    else
        log_success "Sufficient disk space: ${available_gb}GB available"
    fi
}

create_required_directories() {
    log_info "Creating required directories..."
    
    local dirs=("logs" "uploads" "temp" "keys" "docker/nginx" "docker/postgres" "docker/redis")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        fi
        
        # Ensure proper permissions
        chmod 755 "$dir" 2>/dev/null || true
        
        # Create .gitkeep if directory is empty
        if [[ -z "$(ls -A "$dir" 2>/dev/null)" ]]; then
            touch "$dir/.gitkeep"
        fi
    done
}

test_docker_compose() {
    log_info "Testing Docker Compose configuration..."
    
    # Validate docker-compose.yml
    if docker-compose config >/dev/null 2>&1; then
        log_success "Docker Compose configuration is valid"
    else
        log_error "Docker Compose configuration has errors"
        docker-compose config
        return 1
    fi
    
    # Check for conflicting ports
    local ports=("3000" "5173" "8123" "8124" "5432" "6379")
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_warning "Port $port is already in use"
        fi
    done
}

generate_env_file() {
    log_info "Generating .env file if missing..."
    
    if [[ ! -f ".env" ]]; then
        cat > .env << 'EOF'
# MCP System Environment Configuration
NODE_ENV=development

# Database
POSTGRES_PASSWORD=postgres_secure_password
MCP_DB_PASSWORD=mcp_secure_password

# Redis
REDIS_PASSWORD=redis_secure_password

# Security
JWT_SECRET=your_jwt_secret_key_here
SESSION_SECRET=your_session_secret_key_here
STUDIO_SECRET=your_studio_secret_here

# API Keys (optional)
LANGWATCH_API_KEY=
PERPLEXITY_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# MCP Configuration
MCP_API_KEYS=dev-key-123,test-key-456

# Frontend URLs
VITE_API_BASE_URL=http://localhost:3000
VITE_STUDIO_BASE_URL=http://localhost:8123
VITE_WS_BASE_URL=ws://localhost:3000
EOF
        log_success "Created .env file"
    else
        log_success ".env file already exists"
    fi
}

main() {
    echo "🔧 Docker Volume Fix"
    echo "===================="
    echo ""
    
    check_docker_daemon || exit 1
    echo ""
    
    cleanup_docker
    echo ""
    
    fix_permissions
    echo ""
    
    create_required_directories
    echo ""
    
    check_disk_space
    echo ""
    
    generate_env_file
    echo ""
    
    test_docker_compose || exit 1
    echo ""
    
    log_success "Docker volume fixes completed!"
    log_info "You can now run: docker-compose up --build"
    echo ""
    log_info "If you still have issues, try:"
    log_info "  1. sudo systemctl restart docker"
    log_info "  2. docker system prune -a"
    log_info "  3. Reboot the system"
}

main "$@"


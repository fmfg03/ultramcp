#!/bin/bash
# UltraMCP Single Server Deployment
# Complete virtualization testing on one server

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SERVER_IP=$(hostname -I | awk '{print $1}')
DOMAIN_BASE="ultramcp.local"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        log_info "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# System requirements check
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot determine OS version"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]] && [[ "$ID" != "debian" ]]; then
        log_warning "This script is optimized for Ubuntu/Debian. Other distros may require modifications."
    fi
    
    # Check resources
    local total_mem=$(free -m | awk '/^Mem:/ {print $2}')
    local total_disk=$(df / | awk 'NR==2 {print int($4/1024/1024)}')
    local cpu_cores=$(nproc)
    
    log_info "System Resources:"
    log_info "  CPU Cores: $cpu_cores"
    log_info "  Memory: ${total_mem}MB"
    log_info "  Disk Space: ${total_disk}GB available"
    
    # Minimum requirements
    if [[ $total_mem -lt 8192 ]]; then
        log_warning "Recommended minimum: 8GB RAM (found ${total_mem}MB)"
    fi
    
    if [[ $total_disk -lt 50 ]]; then
        log_warning "Recommended minimum: 50GB disk space (found ${total_disk}GB)"
    fi
    
    if [[ $cpu_cores -lt 4 ]]; then
        log_warning "Recommended minimum: 4 CPU cores (found $cpu_cores)"
    fi
    
    log_success "System requirements check completed"
}

# Install required packages
install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package lists
    sudo apt update
    
    # Install essential packages
    sudo apt install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        jq \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        python3 \
        python3-pip \
        nodejs \
        npm
    
    log_success "System dependencies installed"
}

# Install Docker and Docker Compose
install_docker() {
    log_info "Installing Docker..."
    
    # Remove old versions
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Install Docker Compose standalone
    local compose_version="2.24.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/v${compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker installed successfully"
    log_warning "Please log out and back in for Docker group membership to take effect"
}

# Install LXD for sandboxing
install_lxd() {
    log_info "Installing LXD for container sandboxing..."
    
    # Install LXD via snap
    sudo snap install lxd
    
    # Add user to lxd group
    sudo usermod -a -G lxd $USER
    
    log_success "LXD installed successfully"
    log_info "Run 'sudo lxd init' to initialize LXD after logging back in"
}

# Setup directory structure
setup_directories() {
    log_info "Setting up UltraMCP directory structure..."
    
    # Create main directories
    mkdir -p /opt/ultramcp/{data,logs,config,backups,secrets}
    mkdir -p /opt/ultramcp/data/{postgres,redis,qdrant,grafana,prometheus}
    mkdir -p /opt/ultramcp/services
    
    # Set permissions
    sudo chown -R $USER:$USER /opt/ultramcp
    chmod 700 /opt/ultramcp/secrets
    
    log_success "Directory structure created"
}

# Create single-server docker-compose
create_docker_compose() {
    log_info "Creating single-server Docker Compose configuration..."
    
    cat > /opt/ultramcp/docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Reverse Proxy
  traefik:
    image: traefik:v3.0
    container_name: ultramcp-traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./config/traefik:/etc/traefik
      - ./data/traefik:/data
    command:
      - --api.dashboard=true
      - --api.insecure=true
      - --providers.docker=true
      - --providers.docker.exposedByDefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --log.level=INFO
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.traefik.loadbalancer.server.port=8080"

  # Core Infrastructure
  postgres:
    image: postgres:15-alpine
    container_name: ultramcp-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=ultramcp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-ultramcp_secure_password}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ../database/schemas/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d ultramcp"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - ultramcp

  redis:
    image: redis:7-alpine
    container_name: ultramcp-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD:-ultramcp_redis_password}
    volumes:
      - ./data/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ultramcp

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: ultramcp-qdrant
    restart: unless-stopped
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - ultramcp

  # UltraMCP Services
  chain-of-debate:
    image: ultramcp/chain-of-debate:latest
    container_name: ultramcp-cod
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - NODE_ENV=production
      - PORT=8001
    volumes:
      - ./data/cod:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 15s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.cod.rule=Host(`cod.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.cod.loadbalancer.server.port=8001"
    depends_on:
      - postgres
      - redis

  asterisk-security:
    image: ultramcp/asterisk-security:latest
    container_name: ultramcp-security
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - PORT=8002
    volumes:
      - ./data/security:/app/data
      - ./logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock:ro
    privileged: true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 15s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.security.rule=Host(`security.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.security.loadbalancer.server.port=8002"
    depends_on:
      - postgres
      - redis

  blockoli-intelligence:
    image: ultramcp/blockoli-intelligence:latest
    container_name: ultramcp-blockoli
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - PORT=8003
    volumes:
      - ./data/blockoli:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 15s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.blockoli.rule=Host(`blockoli.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.blockoli.loadbalancer.server.port=8003"
    depends_on:
      - postgres
      - redis

  voice-system:
    image: ultramcp/voice-system:latest
    container_name: ultramcp-voice
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - PORT=8004
    volumes:
      - ./data/voice:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 15s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.voice.rule=Host(`voice.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.voice.loadbalancer.server.port=8004"
    depends_on:
      - postgres
      - redis

  deepclaude-engine:
    image: ultramcp/deepclaude-engine:latest
    container_name: ultramcp-deepclaude
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - PORT=8005
    volumes:
      - ./data/deepclaude:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 6G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 20s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.deepclaude.rule=Host(`deepclaude.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.deepclaude.loadbalancer.server.port=8005"
    depends_on:
      - postgres
      - redis

  control-tower:
    image: ultramcp/control-tower:latest
    container_name: ultramcp-control
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - PORT=8006
    volumes:
      - ./data/control:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
      interval: 30s
      timeout: 15s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.control.rule=Host(`control.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.control.loadbalancer.server.port=8006"
    depends_on:
      - postgres
      - redis

  claude-memory:
    image: ultramcp/claude-memory:latest
    container_name: ultramcp-memory
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - QDRANT_URL=http://qdrant:6333
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - PORT=8007
    volumes:
      - ./data/memory:/app/data
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8007/health"]
      interval: 30s
      timeout: 15s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.memory.rule=Host(`memory.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.memory.loadbalancer.server.port=8007"
    depends_on:
      - postgres
      - redis
      - qdrant

  sam-mcp:
    image: ultramcp/sam-mcp:latest
    container_name: ultramcp-sam
    restart: unless-stopped
    environment:
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - PORT=8008
    volumes:
      - ./data/sam:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 15s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.sam.rule=Host(`sam.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.sam.loadbalancer.server.port=8008"
    depends_on:
      - postgres
      - redis

  # API Gateway
  backend-api:
    image: ultramcp/backend-api:latest
    container_name: ultramcp-api
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - PORT=3000
      - POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD:-ultramcp_secure_password}@postgres:5432/ultramcp
      - REDIS_URL=redis://:${REDIS_PASSWORD:-ultramcp_redis_password}@redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    volumes:
      - ./data/api:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.api.loadbalancer.server.port=3000"
    depends_on:
      - postgres
      - redis

  # Frontend
  webui:
    image: ultramcp/webui:latest
    container_name: ultramcp-webui
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=http://api.${DOMAIN_BASE:-ultramcp.local}
    volumes:
      - ./data/webui:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.webui.rule=Host(`${DOMAIN_BASE:-ultramcp.local}`) || Host(`www.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.webui.loadbalancer.server.port=3001"

  # Monitoring
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: ultramcp-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./data/prometheus:/prometheus
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.prometheus.loadbalancer.server.port=9090"

  grafana:
    image: grafana/grafana:10.2.0
    container_name: ultramcp-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-ultramcp2024}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./data/grafana:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - ultramcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN_BASE:-ultramcp.local}`)"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"
    depends_on:
      - prometheus

networks:
  ultramcp:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF

    log_success "Docker Compose configuration created"
}

# Create environment file
create_env_file() {
    log_info "Creating environment configuration..."
    
    cat > /opt/ultramcp/.env << EOF
# UltraMCP Single Server Configuration
# Generated on $(date)

# Server Configuration
SERVER_IP=$SERVER_IP
DOMAIN_BASE=$DOMAIN_BASE

# Database Passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
GRAFANA_PASSWORD=ultramcp2024

# Supabase Configuration (Update these with your values)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# API Keys (Optional - add your keys here)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Service Configuration
NODE_ENV=production
LOG_LEVEL=info
ENABLE_MONITORING=true
EOF

    chmod 600 /opt/ultramcp/.env
    log_success "Environment file created at /opt/ultramcp/.env"
    log_warning "Please update Supabase credentials in /opt/ultramcp/.env"
}

# Create monitoring configuration
create_monitoring_config() {
    log_info "Creating monitoring configuration..."
    
    mkdir -p /opt/ultramcp/config/{prometheus,grafana/datasources,grafana/dashboards}
    
    # Prometheus configuration
    cat > /opt/ultramcp/config/prometheus.yml << 'EOF'
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'ultramcp-services'
    static_configs:
      - targets:
          - 'chain-of-debate:8001'
          - 'asterisk-security:8002'
          - 'blockoli-intelligence:8003'
          - 'voice-system:8004'
          - 'deepclaude-engine:8005'
          - 'control-tower:8006'
          - 'claude-memory:8007'
          - 'sam-mcp:8008'
          - 'backend-api:3000'
          - 'webui:3001'
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'infrastructure'
    static_configs:
      - targets:
          - 'postgres:5432'
          - 'redis:6379'
          - 'qdrant:6333'
EOF

    # Grafana datasource
    cat > /opt/ultramcp/config/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    log_success "Monitoring configuration created"
}

# Create management scripts
create_management_scripts() {
    log_info "Creating management scripts..."
    
    # Main management script
    cat > /opt/ultramcp/manage.sh << 'EOF'
#!/bin/bash
# UltraMCP Single Server Management Script

set -euo pipefail

COMPOSE_FILE="/opt/ultramcp/docker-compose.yml"
ENV_FILE="/opt/ultramcp/.env"

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

# Load environment
if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE"
fi

case "${1:-help}" in
    "start")
        log_info "Starting UltraMCP services..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        log_success "Services started"
        ;;
    "stop")
        log_info "Stopping UltraMCP services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting UltraMCP services..."
        docker-compose -f "$COMPOSE_FILE" down
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        log_success "Services restarted"
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
        log_info "Checking service health..."
        services=(
            "postgres:5432"
            "redis:6379"
            "qdrant:6333"
            "chain-of-debate:8001"
            "asterisk-security:8002"
            "blockoli-intelligence:8003"
            "voice-system:8004"
            "deepclaude-engine:8005"
            "control-tower:8006"
            "claude-memory:8007"
            "sam-mcp:8008"
            "backend-api:3000"
            "webui:3001"
            "prometheus:9090"
            "grafana:3000"
        )
        
        healthy=0
        total=${#services[@]}
        
        for service in "${services[@]}"; do
            name=$(echo "$service" | cut -d':' -f1)
            port=$(echo "$service" | cut -d':' -f2)
            
            if docker exec "ultramcp-${name}" nc -z localhost "$port" 2>/dev/null; then
                log_success "✓ $name is healthy"
                ((healthy++))
            else
                log_error "✗ $name is unhealthy"
            fi
        done
        
        log_info "Health check: $healthy/$total services healthy"
        ;;
    "urls")
        log_info "UltraMCP Service URLs:"
        echo ""
        echo "🌐 Main Services:"
        echo "  WebUI:              http://${DOMAIN_BASE:-ultramcp.local}"
        echo "  API Gateway:        http://api.${DOMAIN_BASE:-ultramcp.local}"
        echo ""
        echo "🔧 UltraMCP Services:"
        echo "  Chain of Debate:    http://cod.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Security Scanner:   http://security.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Code Intelligence:  http://blockoli.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Voice System:       http://voice.${DOMAIN_BASE:-ultramcp.local}"
        echo "  DeepClaude Engine:  http://deepclaude.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Control Tower:      http://control.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Claude Memory:      http://memory.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Sam MCP:            http://sam.${DOMAIN_BASE:-ultramcp.local}"
        echo ""
        echo "📊 Monitoring:"
        echo "  Prometheus:         http://prometheus.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Grafana:            http://grafana.${DOMAIN_BASE:-ultramcp.local}"
        echo "  Traefik Dashboard:  http://traefik.${DOMAIN_BASE:-ultramcp.local}"
        echo ""
        echo "💡 Add these to your /etc/hosts file:"
        echo "  ${SERVER_IP:-127.0.0.1} ${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} api.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} cod.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} security.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} blockoli.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} voice.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} deepclaude.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} control.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} memory.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} sam.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} prometheus.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} grafana.${DOMAIN_BASE:-ultramcp.local}"
        echo "  ${SERVER_IP:-127.0.0.1} traefik.${DOMAIN_BASE:-ultramcp.local}"
        ;;
    "backup")
        log_info "Creating backup..."
        backup_dir="/opt/ultramcp/backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        # Backup volumes
        docker run --rm \
            -v ultramcp_postgres-data:/source:ro \
            -v "$backup_dir:/backup" \
            alpine tar czf /backup/postgres_data.tar.gz -C /source .
            
        docker run --rm \
            -v ultramcp_redis-data:/source:ro \
            -v "$backup_dir:/backup" \
            alpine tar czf /backup/redis_data.tar.gz -C /source .
            
        # Backup configuration
        cp -r /opt/ultramcp/config "$backup_dir/"
        cp /opt/ultramcp/.env "$backup_dir/"
        
        log_success "Backup created: $backup_dir"
        ;;
    "update")
        service="${2:-}"
        if [[ -n "$service" ]]; then
            log_info "Updating service: $service"
            docker-compose -f "$COMPOSE_FILE" pull "$service"
            docker-compose -f "$COMPOSE_FILE" up -d "$service"
        else
            log_info "Updating all services..."
            docker-compose -f "$COMPOSE_FILE" pull
            docker-compose -f "$COMPOSE_FILE" up -d
        fi
        log_success "Update completed"
        ;;
    "help"|*)
        echo "UltraMCP Single Server Management"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start              Start all services"
        echo "  stop               Stop all services"
        echo "  restart            Restart all services"
        echo "  status             Show service status"
        echo "  logs [service]     Show logs (all or specific service)"
        echo "  health             Check service health"
        echo "  urls               Show service URLs"
        echo "  backup             Create backup"
        echo "  update [service]   Update services"
        echo "  help               Show this help"
        ;;
esac
EOF

    chmod +x /opt/ultramcp/manage.sh
    
    # Create symlink for global access
    sudo ln -sf /opt/ultramcp/manage.sh /usr/local/bin/ultramcp
    
    log_success "Management scripts created"
}

# Update hosts file for local domains
update_hosts() {
    log_info "Updating /etc/hosts for local domains..."
    
    # Backup existing hosts file
    sudo cp /etc/hosts /etc/hosts.backup.$(date +%Y%m%d_%H%M%S)
    
    # Remove existing UltraMCP entries
    sudo sed -i '/# UltraMCP/d' /etc/hosts
    
    # Add new entries
    cat << EOF | sudo tee -a /etc/hosts > /dev/null

# UltraMCP Local Services
$SERVER_IP $DOMAIN_BASE
$SERVER_IP api.$DOMAIN_BASE
$SERVER_IP cod.$DOMAIN_BASE
$SERVER_IP security.$DOMAIN_BASE
$SERVER_IP blockoli.$DOMAIN_BASE
$SERVER_IP voice.$DOMAIN_BASE
$SERVER_IP deepclaude.$DOMAIN_BASE
$SERVER_IP control.$DOMAIN_BASE
$SERVER_IP memory.$DOMAIN_BASE
$SERVER_IP sam.$DOMAIN_BASE
$SERVER_IP prometheus.$DOMAIN_BASE
$SERVER_IP grafana.$DOMAIN_BASE
$SERVER_IP traefik.$DOMAIN_BASE
EOF

    log_success "Hosts file updated"
}

# Deploy services
deploy_services() {
    log_info "Deploying UltraMCP services..."
    
    cd /opt/ultramcp
    
    # Start services
    docker-compose --env-file .env up -d
    
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check health
    /opt/ultramcp/manage.sh health
    
    log_success "Deployment completed!"
    log_info "Run 'ultramcp urls' to see all service URLs"
}

# Main deployment function
main() {
    log_info "Starting UltraMCP Single Server Deployment"
    log_info "Server IP: $SERVER_IP"
    log_info "Domain Base: $DOMAIN_BASE"
    
    case "${1:-full}" in
        "install")
            check_root
            check_requirements
            install_dependencies
            install_docker
            install_lxd
            log_success "Installation completed. Please log out and back in, then run: $0 setup"
            ;;
        "setup")
            setup_directories
            create_docker_compose
            create_env_file
            create_monitoring_config
            create_management_scripts
            update_hosts
            log_success "Setup completed. Edit /opt/ultramcp/.env with your Supabase credentials, then run: $0 deploy"
            ;;
        "deploy")
            deploy_services
            ;;
        "full")
            check_root
            check_requirements
            install_dependencies
            install_docker
            install_lxd
            setup_directories
            create_docker_compose
            create_env_file
            create_monitoring_config
            create_management_scripts
            update_hosts
            log_warning "Installation completed. Please:"
            log_warning "1. Log out and back in (for Docker group membership)"
            log_warning "2. Edit /opt/ultramcp/.env with your Supabase credentials"
            log_warning "3. Run: $0 deploy"
            ;;
        *)
            echo "UltraMCP Single Server Deployment"
            echo ""
            echo "Usage: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  full       Complete installation, setup, and instructions"
            echo "  install    Install dependencies only"
            echo "  setup      Setup configuration only"
            echo "  deploy     Deploy services only"
            ;;
    esac
}

# Run main function
main "$@"
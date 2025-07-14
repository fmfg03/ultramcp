#!/bin/bash
# UltraMCP Docker Swarm Deployment Script
# Deploy and manage UltraMCP services across Docker Swarm cluster

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.swarm.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Docker Swarm is initialized
check_swarm() {
    if ! docker info | grep -q "Swarm: active"; then
        log_error "Docker Swarm is not initialized on this node"
        log_info "Initialize Swarm with: docker swarm init"
        exit 1
    fi
    log_success "Docker Swarm is active"
}

# Create required directories
create_directories() {
    log_info "Creating required directories..."
    
    local dirs=(
        "/opt/ultramcp/data/postgres"
        "/opt/ultramcp/data/redis"
        "/opt/ultramcp/data/qdrant"
        "/opt/ultramcp/data/traefik"
        "/opt/ultramcp/data/prometheus"
        "/opt/ultramcp/data/grafana"
        "/opt/ultramcp/configs"
        "/opt/ultramcp/secrets"
        "/opt/ultramcp/logs"
        "/opt/ultramcp/backups"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    # Set proper permissions
    chmod 700 /opt/ultramcp/secrets
    chmod 755 /opt/ultramcp/data/*
    
    log_success "Directories created successfully"
}

# Create Docker secrets
create_secrets() {
    log_info "Creating Docker secrets..."
    
    # Generate random passwords if not provided
    POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}"
    REDIS_PASSWORD="${REDIS_PASSWORD:-$(openssl rand -base64 32)}"
    GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-ultramcp2024}"
    
    # Create secrets
    echo "$POSTGRES_PASSWORD" | docker secret create postgres_password - 2>/dev/null || log_warning "postgres_password secret already exists"
    echo "$REDIS_PASSWORD" | docker secret create redis_password - 2>/dev/null || log_warning "redis_password secret already exists"
    
    # API keys (optional)
    if [ -n "${OPENAI_API_KEY:-}" ]; then
        echo "$OPENAI_API_KEY" | docker secret create openai_api_key - 2>/dev/null || log_warning "openai_api_key secret already exists"
    fi
    
    if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
        echo "$ANTHROPIC_API_KEY" | docker secret create anthropic_api_key - 2>/dev/null || log_warning "anthropic_api_key secret already exists"
    fi
    
    # Save passwords to file for reference
    cat > /opt/ultramcp/secrets/passwords.txt << EOF
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD
Generated at: $(date)
EOF
    
    chmod 600 /opt/ultramcp/secrets/passwords.txt
    log_success "Secrets created successfully"
}

# Label nodes for service placement
label_nodes() {
    log_info "Labeling nodes for service placement..."
    
    # Get current node ID
    CURRENT_NODE=$(docker info --format '{{.Swarm.NodeID}}')
    
    # Label current node as manager with all capabilities
    docker node update --label-add postgres=true "$CURRENT_NODE"
    docker node update --label-add redis=true "$CURRENT_NODE"
    docker node update --label-add qdrant=true "$CURRENT_NODE"
    docker node update --label-add monitoring=true "$CURRENT_NODE"
    docker node update --label-add security=true "$CURRENT_NODE"
    docker node update --label-add cpu_intensive=true "$CURRENT_NODE"
    docker node update --label-add memory_intensive=true "$CURRENT_NODE"
    docker node update --label-add ai_intensive=true "$CURRENT_NODE"
    docker node update --label-add media=true "$CURRENT_NODE"
    docker node update --label-add zone=primary "$CURRENT_NODE"
    
    log_success "Node labeling completed"
}

# Create monitoring configurations
create_monitoring_configs() {
    log_info "Creating monitoring configurations..."
    
    # Prometheus configuration
    cat > /opt/ultramcp/configs/prometheus.yml << 'EOF'
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']

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

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'docker-swarm'
    dockerswarm_sd_configs:
      - host: unix:///var/run/docker.sock
        role: tasks
    relabel_configs:
      - source_labels: [__meta_dockerswarm_task_state]
        regex: running
        action: keep
      - source_labels: [__meta_dockerswarm_service_label_prometheus_job]
        target_label: job
        regex: (.+)
EOF

    # Create Prometheus configuration as Docker config
    docker config create prometheus_config /opt/ultramcp/configs/prometheus.yml 2>/dev/null || log_warning "prometheus_config already exists"
    
    # Grafana datasources
    mkdir -p /opt/ultramcp/configs/grafana/{datasources,dashboards}
    
    cat > /opt/ultramcp/configs/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Grafana dashboards configuration
    cat > /opt/ultramcp/configs/grafana/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'UltraMCP'
    orgId: 1
    folder: 'UltraMCP'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    log_success "Monitoring configurations created"
}

# Create environment file for Docker Compose
create_env_file() {
    log_info "Creating environment file..."
    
    cat > "$PROJECT_ROOT/.env" << EOF
# UltraMCP Docker Swarm Environment
COMPOSE_PROJECT_NAME=ultramcp

# Service Domains
WEBUI_DOMAIN=${WEBUI_DOMAIN:-ultramcp.local}
API_DOMAIN=${API_DOMAIN:-api.ultramcp.local}
COD_DOMAIN=${COD_DOMAIN:-cod.ultramcp.local}
SECURITY_DOMAIN=${SECURITY_DOMAIN:-security.ultramcp.local}
BLOCKOLI_DOMAIN=${BLOCKOLI_DOMAIN:-blockoli.ultramcp.local}
VOICE_DOMAIN=${VOICE_DOMAIN:-voice.ultramcp.local}
DEEPCLAUDE_DOMAIN=${DEEPCLAUDE_DOMAIN:-deepclaude.ultramcp.local}
CONTROL_DOMAIN=${CONTROL_DOMAIN:-control.ultramcp.local}
MEMORY_DOMAIN=${MEMORY_DOMAIN:-memory.ultramcp.local}
SAM_DOMAIN=${SAM_DOMAIN:-sam.ultramcp.local}
GRAFANA_DOMAIN=${GRAFANA_DOMAIN:-grafana.ultramcp.local}

# SSL Configuration
ACME_EMAIL=${ACME_EMAIL:-admin@ultramcp.local}

# Database Passwords (read from secrets)
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-ultramcp2024}

# Supabase Configuration
SUPABASE_URL=${SUPABASE_URL:-https://your-project.supabase.co}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-your-anon-key}

# Frontend Configuration
FRONTEND_URL=${FRONTEND_URL:-https://ultramcp.local}

# Environment
NODE_ENV=production
LOG_LEVEL=info
EOF

    chmod 600 "$PROJECT_ROOT/.env"
    log_success "Environment file created"
}

# Deploy the stack
deploy_stack() {
    log_info "Deploying UltraMCP stack to Docker Swarm..."
    
    cd "$PROJECT_ROOT"
    
    # Deploy the stack
    docker stack deploy \
        --compose-file "$COMPOSE_FILE" \
        --with-registry-auth \
        ultramcp
    
    log_success "Stack deployment initiated"
    
    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check service status
    docker stack services ultramcp
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    local services=(
        "postgres"
        "redis"
        "qdrant"
        "traefik"
        "chain-of-debate"
        "asterisk-security"
        "blockoli-intelligence"
        "voice-system"
        "deepclaude-engine"
        "control-tower"
        "claude-memory"
        "sam-mcp"
        "backend-api"
        "webui"
        "prometheus"
        "grafana"
    )
    
    local healthy=0
    local total=${#services[@]}
    
    for service in "${services[@]}"; do
        local replicas=$(docker service ls --filter name=ultramcp_$service --format "{{.Replicas}}")
        if [[ "$replicas" =~ ^[0-9]+/[0-9]+$ ]]; then
            local running=$(echo "$replicas" | cut -d'/' -f1)
            local desired=$(echo "$replicas" | cut -d'/' -f2)
            if [ "$running" -eq "$desired" ] && [ "$running" -gt 0 ]; then
                log_success "Service $service: $replicas (healthy)"
                ((healthy++))
            else
                log_warning "Service $service: $replicas (not ready)"
            fi
        else
            log_error "Service $service: unknown status"
        fi
    done
    
    log_info "Health check complete: $healthy/$total services healthy"
    
    if [ "$healthy" -eq "$total" ]; then
        log_success "All services are healthy!"
        show_urls
    else
        log_warning "Some services are not healthy. Check logs with: docker service logs ultramcp_<service>"
    fi
}

# Show service URLs
show_urls() {
    log_info "UltraMCP services are available at:"
    echo ""
    echo "🌐 Main Interface:"
    echo "  WebUI:        https://${WEBUI_DOMAIN:-ultramcp.local}"
    echo "  API Gateway:  https://${API_DOMAIN:-api.ultramcp.local}"
    echo ""
    echo "🔧 Services:"
    echo "  Chain of Debate:    https://${COD_DOMAIN:-cod.ultramcp.local}"
    echo "  Security Scanner:   https://${SECURITY_DOMAIN:-security.ultramcp.local}"
    echo "  Code Intelligence:  https://${BLOCKOLI_DOMAIN:-blockoli.ultramcp.local}"
    echo "  Voice System:       https://${VOICE_DOMAIN:-voice.ultramcp.local}"
    echo "  DeepClaude Engine:  https://${DEEPCLAUDE_DOMAIN:-deepclaude.ultramcp.local}"
    echo "  Control Tower:      https://${CONTROL_DOMAIN:-control.ultramcp.local}"
    echo "  Claude Memory:      https://${MEMORY_DOMAIN:-memory.ultramcp.local}"
    echo "  Sam MCP:            https://${SAM_DOMAIN:-sam.ultramcp.local}"
    echo ""
    echo "📊 Monitoring:"
    echo "  Grafana:      https://${GRAFANA_DOMAIN:-grafana.ultramcp.local}"
    echo "  Traefik:      http://localhost:8080"
    echo ""
    echo "🔑 Default Credentials:"
    echo "  Grafana: admin / ultramcp2024"
    echo ""
    echo "📝 Logs: docker service logs ultramcp_<service>"
    echo "📊 Status: docker stack services ultramcp"
}

# Remove the stack
remove_stack() {
    log_warning "Removing UltraMCP stack..."
    docker stack rm ultramcp
    log_success "Stack removed"
}

# Scale services
scale_service() {
    local service="$1"
    local replicas="$2"
    
    if [ -z "$service" ] || [ -z "$replicas" ]; then
        log_error "Usage: scale <service> <replicas>"
        exit 1
    fi
    
    log_info "Scaling service ultramcp_$service to $replicas replicas..."
    docker service scale "ultramcp_$service=$replicas"
    log_success "Service scaled successfully"
}

# Update service
update_service() {
    local service="$1"
    local image="$2"
    
    if [ -z "$service" ]; then
        log_error "Usage: update <service> [image]"
        exit 1
    fi
    
    if [ -n "$image" ]; then
        log_info "Updating service ultramcp_$service with image $image..."
        docker service update --image "$image" "ultramcp_$service"
    else
        log_info "Updating service ultramcp_$service..."
        docker service update --force "ultramcp_$service"
    fi
    
    log_success "Service update initiated"
}

# Backup data
backup_data() {
    log_info "Creating backup..."
    
    local backup_dir="/opt/ultramcp/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup volumes
    tar czf "$backup_dir/postgres_data.tar.gz" -C /opt/ultramcp/data postgres
    tar czf "$backup_dir/redis_data.tar.gz" -C /opt/ultramcp/data redis
    tar czf "$backup_dir/qdrant_data.tar.gz" -C /opt/ultramcp/data qdrant
    tar czf "$backup_dir/grafana_data.tar.gz" -C /opt/ultramcp/data grafana
    
    # Backup configs
    cp -r /opt/ultramcp/configs "$backup_dir/"
    
    # Backup secrets (encrypted)
    if [ -f /opt/ultramcp/secrets/passwords.txt ]; then
        cp /opt/ultramcp/secrets/passwords.txt "$backup_dir/"
    fi
    
    log_success "Backup created: $backup_dir"
}

# Show usage
usage() {
    echo "UltraMCP Docker Swarm Deployment Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  init              Initialize Swarm and deploy stack"
    echo "  deploy            Deploy the stack"
    echo "  remove            Remove the stack"
    echo "  status            Show service status"
    echo "  health            Check service health"
    echo "  scale <svc> <n>   Scale a service"
    echo "  update <svc> [img] Update a service"
    echo "  logs <service>    Show service logs"
    echo "  backup            Backup all data"
    echo "  urls              Show service URLs"
    echo ""
    echo "Examples:"
    echo "  $0 init"
    echo "  $0 scale chain-of-debate 5"
    echo "  $0 update webui ultramcp/webui:v2.0"
    echo "  $0 logs backend-api"
}

# Main command handling
main() {
    case "${1:-}" in
        "init")
            check_swarm
            create_directories
            create_secrets
            label_nodes
            create_monitoring_configs
            create_env_file
            deploy_stack
            sleep 60
            check_health
            ;;
        "deploy")
            check_swarm
            deploy_stack
            ;;
        "remove")
            remove_stack
            ;;
        "status")
            docker stack services ultramcp
            ;;
        "health")
            check_health
            ;;
        "scale")
            scale_service "$2" "$3"
            ;;
        "update")
            update_service "$2" "$3"
            ;;
        "logs")
            if [ -z "${2:-}" ]; then
                log_error "Service name required"
                exit 1
            fi
            docker service logs -f "ultramcp_$2"
            ;;
        "backup")
            backup_data
            ;;
        "urls")
            show_urls
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
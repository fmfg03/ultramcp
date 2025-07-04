#!/bin/bash

# UltraMCP ContextBuilderAgent 2.0 - Monitoring Setup Script
# Automated Prometheus + Grafana + Alertmanager Deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config/monitoring"
LOGS_DIR="$PROJECT_ROOT/logs"

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
    
    # Check available ports
    local ports=(9090 3000 9093 9100 8080 9115 9113 3100 16686 8000)
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            warning "Port $port is already in use"
        fi
    done
    
    success "Prerequisites check passed"
}

# Setup directories
setup_directories() {
    log "Setting up monitoring directories..."
    
    mkdir -p "$CONFIG_DIR/grafana/dashboards/system"
    mkdir -p "$CONFIG_DIR/grafana/dashboards/infrastructure"
    mkdir -p "$CONFIG_DIR/grafana/dashboards/business"
    mkdir -p "$CONFIG_DIR/grafana/dashboards/performance"
    mkdir -p "$CONFIG_DIR/templates"
    mkdir -p "$LOGS_DIR/monitoring"
    
    success "Directories created"
}

# Create Grafana dashboards
create_grafana_dashboards() {
    log "Creating Grafana dashboards..."
    
    # System Overview Dashboard
    cat > "$CONFIG_DIR/grafana/dashboards/system/contextbuilder-overview.json" <<'EOF'
{
  "dashboard": {
    "id": null,
    "title": "ContextBuilderAgent 2.0 - System Overview",
    "tags": ["contextbuilder", "system"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "contextbuilder_service_health",
            "legendFormat": "{{service}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "contextbuilder_service_response_time_seconds",
            "legendFormat": "{{service}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Coherence Score",
        "type": "gauge",
        "targets": [
          {
            "expr": "contextbuilder_coherence_score_average",
            "legendFormat": "Coherence Score"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Active Alerts",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(contextbuilder_observatory_alert_count)",
            "legendFormat": "Total Alerts"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF

    # Infrastructure Dashboard
    cat > "$CONFIG_DIR/grafana/dashboards/infrastructure/infrastructure-overview.json" <<'EOF'
{
  "dashboard": {
    "id": null,
    "title": "ContextBuilderAgent 2.0 - Infrastructure",
    "tags": ["contextbuilder", "infrastructure"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "System Load",
        "type": "graph",
        "targets": [
          {
            "expr": "node_load1",
            "legendFormat": "Load 1m"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "Memory Usage %"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Database Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "contextbuilder_database_connections",
            "legendFormat": "Connections"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Redis Memory",
        "type": "stat",
        "targets": [
          {
            "expr": "contextbuilder_redis_memory_usage_bytes",
            "legendFormat": "Redis Memory"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF

    success "Grafana dashboards created"
}

# Create additional monitoring configuration files
create_monitoring_configs() {
    log "Creating additional monitoring configuration files..."
    
    # Blackbox Exporter configuration
    cat > "$CONFIG_DIR/blackbox.yml" <<'EOF'
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: []
      method: GET
      headers:
        Host: localhost
      no_follow_redirects: false
      fail_if_ssl: false
      fail_if_not_ssl: false
      preferred_ip_protocol: "ip4"
EOF

    # Loki configuration
    cat > "$CONFIG_DIR/loki.yml" <<'EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

analytics:
  reporting_enabled: false
EOF

    # Promtail configuration
    cat > "$CONFIG_DIR/promtail.yml" <<'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

  - job_name: contextbuilder-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: contextbuilder
          __path__: /var/log/contextbuilder/*.log
EOF

    success "Monitoring configuration files created"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    cd "$CONFIG_DIR"
    
    # Pull latest images
    docker-compose -f docker-compose.monitoring.yml pull
    
    # Start monitoring services
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # Wait for services to start
    log "Waiting for monitoring services to start..."
    sleep 30
    
    # Check Prometheus health
    local prometheus_health=0
    for i in {1..10}; do
        if curl -f http://localhost:9090/-/healthy &> /dev/null; then
            prometheus_health=1
            break
        fi
        log "Waiting for Prometheus to be ready... ($i/10)"
        sleep 5
    done
    
    if [[ $prometheus_health -eq 0 ]]; then
        error "Prometheus failed to start"
        return 1
    fi
    
    # Check Grafana health
    local grafana_health=0
    for i in {1..10}; do
        if curl -f http://localhost:3000/api/health &> /dev/null; then
            grafana_health=1
            break
        fi
        log "Waiting for Grafana to be ready... ($i/10)"
        sleep 5
    done
    
    if [[ $grafana_health -eq 0 ]]; then
        error "Grafana failed to start"
        return 1
    fi
    
    success "Monitoring stack deployed successfully"
}

# Configure alerting
configure_alerting() {
    log "Configuring alerting..."
    
    # Test Alertmanager connection
    if curl -f http://localhost:9093/-/healthy &> /dev/null; then
        success "Alertmanager is healthy"
    else
        warning "Alertmanager is not responding"
    fi
    
    # Reload Prometheus configuration
    if curl -X POST http://localhost:9090/-/reload &> /dev/null; then
        success "Prometheus configuration reloaded"
    else
        warning "Failed to reload Prometheus configuration"
    fi
    
    log "Alerting configuration completed"
}

# Test monitoring integration
test_monitoring() {
    log "Testing monitoring integration..."
    
    # Test Prometheus targets
    local prometheus_targets=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets | length')
    log "Prometheus monitoring $prometheus_targets targets"
    
    # Test Grafana datasources
    local grafana_datasources=$(curl -s -u admin:contextbuilder_grafana_2024 http://localhost:3000/api/datasources | jq -r '. | length')
    log "Grafana has $grafana_datasources datasources configured"
    
    # Test custom metrics collector
    if curl -f http://localhost:8000/metrics &> /dev/null; then
        success "Custom metrics collector is working"
    else
        warning "Custom metrics collector is not responding"
    fi
    
    # Test service health monitoring
    log "Testing service health monitoring..."
    local healthy_services=0
    for service in contextbuilder_core belief_reviser prompt_assembler; do
        if curl -f "http://localhost:9090/api/v1/query?query=contextbuilder_service_health{service=\"$service\"}" &> /dev/null; then
            ((healthy_services++))
        fi
    done
    
    log "Monitoring $healthy_services services"
    success "Monitoring integration test completed"
}

# Show status
show_status() {
    log "Monitoring Services Status:"
    echo
    
    # Show running containers
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "contextbuilder-(prometheus|grafana|alertmanager|node-exporter|cadvisor)"
    
    echo
    log "Service Health:"
    
    # Prometheus
    if curl -f http://localhost:9090/-/healthy &> /dev/null; then
        echo -e "  Prometheus: ${GREEN}✓ Healthy${NC}"
    else
        echo -e "  Prometheus: ${RED}✗ Unhealthy${NC}"
    fi
    
    # Grafana
    if curl -f http://localhost:3000/api/health &> /dev/null; then
        echo -e "  Grafana: ${GREEN}✓ Healthy${NC}"
    else
        echo -e "  Grafana: ${RED}✗ Unhealthy${NC}"
    fi
    
    # Alertmanager
    if curl -f http://localhost:9093/-/healthy &> /dev/null; then
        echo -e "  Alertmanager: ${GREEN}✓ Healthy${NC}"
    else
        echo -e "  Alertmanager: ${RED}✗ Unhealthy${NC}"
    fi
    
    echo
    log "Access URLs:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000 (admin/contextbuilder_grafana_2024)"
    echo "  Alertmanager: http://localhost:9093"
    echo "  Custom Metrics: http://localhost:8000/metrics"
}

# Main setup function
main() {
    local action="${1:-setup}"
    
    case "$action" in
        "setup")
            log "Setting up ContextBuilderAgent 2.0 Monitoring Stack"
            check_prerequisites
            setup_directories
            create_grafana_dashboards
            create_monitoring_configs
            deploy_monitoring
            configure_alerting
            test_monitoring
            show_status
            success "Monitoring setup completed successfully!"
            ;;
        "status")
            show_status
            ;;
        "test")
            test_monitoring
            ;;
        "help"|*)
            echo "UltraMCP ContextBuilderAgent 2.0 - Monitoring Setup"
            echo
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  setup     Complete monitoring setup (default)"
            echo "  status    Show monitoring services status"
            echo "  test      Test monitoring integration"
            echo "  help      Show this help message"
            echo
            echo "Monitoring Stack includes:"
            echo "  - Prometheus for metrics collection"
            echo "  - Grafana for visualization"
            echo "  - Alertmanager for alert management"
            echo "  - Node Exporter for system metrics"
            echo "  - cAdvisor for container metrics"
            echo "  - Blackbox Exporter for service health"
            echo "  - Loki for log aggregation"
            echo "  - Jaeger for distributed tracing"
            echo "  - Custom metrics collector for ContextBuilderAgent"
            ;;
    esac
}

# Run main function
main "$@"
#!/bin/bash
# UltraMCP Linux Sandbox Manager
# LXD Container Management for UltraMCP Services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/configs"
LOG_FILE="/var/log/ultramcp-sandbox.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_PREFIX="ultramcp"
NETWORK_NAME="ultramcp-network"
STORAGE_POOL="ultramcp-pool"
BASE_IMAGE="ubuntu:22.04"

# Default resource limits
DEFAULT_CPU="2"
DEFAULT_MEMORY="2GiB"
DEFAULT_DISK="10GiB"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if LXD is installed and initialized
check_lxd() {
    if ! command -v lxc &> /dev/null; then
        log_error "LXD is not installed. Please install with: sudo snap install lxd"
        exit 1
    fi
    
    if ! lxc info &> /dev/null; then
        log_error "LXD is not initialized. Please run: sudo lxd init"
        exit 1
    fi
    
    log_success "LXD is installed and initialized"
}

# Initialize UltraMCP sandbox environment
init_environment() {
    log_info "Initializing UltraMCP sandbox environment..."
    
    # Create storage pool if it doesn't exist
    if ! lxc storage list | grep -q "$STORAGE_POOL"; then
        lxc storage create "$STORAGE_POOL" dir source="/var/lib/lxd/storage-pools/$STORAGE_POOL"
        log_success "Created storage pool: $STORAGE_POOL"
    else
        log_info "Storage pool $STORAGE_POOL already exists"
    fi
    
    # Create network if it doesn't exist
    if ! lxc network list | grep -q "$NETWORK_NAME"; then
        lxc network create "$NETWORK_NAME" \
            ipv4.address=10.10.10.1/24 \
            ipv4.nat=true \
            ipv4.dhcp=true \
            ipv6.address=none
        log_success "Created network: $NETWORK_NAME"
    else
        log_info "Network $NETWORK_NAME already exists"
    fi
    
    # Create profile for UltraMCP containers
    if ! lxc profile list | grep -q "ultramcp-profile"; then
        lxc profile create ultramcp-profile
        
        # Configure the profile
        cat > /tmp/ultramcp-profile.yaml << EOF
config:
  limits.cpu: "$DEFAULT_CPU"
  limits.memory: "$DEFAULT_MEMORY"
  security.nesting: "true"
  security.privileged: "false"
  user.user-data: |
    #cloud-config
    packages:
      - docker.io
      - docker-compose
      - curl
      - wget
      - git
      - python3
      - python3-pip
    runcmd:
      - systemctl enable docker
      - systemctl start docker
      - usermod -aG docker ubuntu
description: UltraMCP container profile
devices:
  eth0:
    network: $NETWORK_NAME
    type: nic
  root:
    path: /
    pool: $STORAGE_POOL
    size: $DEFAULT_DISK
    type: disk
  docker:
    path: /var/lib/docker
    pool: $STORAGE_POOL
    size: 5GiB
    type: disk
name: ultramcp-profile
EOF
        
        lxc profile edit ultramcp-profile < /tmp/ultramcp-profile.yaml
        rm /tmp/ultramcp-profile.yaml
        
        log_success "Created UltraMCP profile"
    else
        log_info "UltraMCP profile already exists"
    fi
    
    log_success "Environment initialization completed"
}

# Create a new sandbox container
create_sandbox() {
    local service_name="$1"
    local cpu_limit="${2:-$DEFAULT_CPU}"
    local memory_limit="${3:-$DEFAULT_MEMORY}"
    local disk_size="${4:-$DEFAULT_DISK}"
    
    if [ -z "$service_name" ]; then
        log_error "Service name is required"
        return 1
    fi
    
    local container_name="${CONTAINER_PREFIX}-${service_name}-sandbox"
    
    # Check if container already exists
    if lxc list | grep -q "$container_name"; then
        log_warning "Container $container_name already exists"
        return 1
    fi
    
    log_info "Creating sandbox container: $container_name"
    
    # Launch container with UltraMCP profile
    lxc launch "$BASE_IMAGE" "$container_name" --profile ultramcp-profile
    
    # Override resource limits if specified
    if [ "$cpu_limit" != "$DEFAULT_CPU" ]; then
        lxc config set "$container_name" limits.cpu "$cpu_limit"
    fi
    
    if [ "$memory_limit" != "$DEFAULT_MEMORY" ]; then
        lxc config set "$container_name" limits.memory "$memory_limit"
    fi
    
    if [ "$disk_size" != "$DEFAULT_DISK" ]; then
        lxc config device override "$container_name" root size="$disk_size"
    fi
    
    # Wait for container to be ready
    log_info "Waiting for container to start..."
    lxc exec "$container_name" -- cloud-init status --wait
    
    # Configure container
    configure_container "$container_name" "$service_name"
    
    # Register with Supabase
    register_sandbox_in_supabase "$container_name" "$service_name"
    
    log_success "Sandbox $container_name created successfully"
    
    # Show container info
    show_container_info "$container_name"
}

# Configure container for UltraMCP service
configure_container() {
    local container_name="$1"
    local service_name="$2"
    
    log_info "Configuring container $container_name for service $service_name"
    
    # Update packages
    lxc exec "$container_name" -- apt update
    lxc exec "$container_name" -- apt upgrade -y
    
    # Install additional packages
    lxc exec "$container_name" -- apt install -y \
        htop \
        vim \
        jq \
        python3-pip \
        nodejs \
        npm
    
    # Create UltraMCP directory
    lxc exec "$container_name" -- mkdir -p /opt/ultramcp
    
    # Copy service-specific configuration
    if [ -f "$CONFIG_DIR/docker-compose.${service_name}.yml" ]; then
        lxc file push "$CONFIG_DIR/docker-compose.${service_name}.yml" \
            "$container_name/opt/ultramcp/docker-compose.yml"
        log_info "Copied service configuration for $service_name"
    else
        log_warning "No specific configuration found for $service_name, using default"
        # Create a basic docker-compose file
        create_default_compose "$container_name" "$service_name"
    fi
    
    # Create environment file
    create_env_file "$container_name" "$service_name"
    
    # Install Python dependencies
    lxc exec "$container_name" -- pip3 install supabase python-dotenv requests
    
    # Create monitoring script
    create_monitoring_script "$container_name"
    
    # Configure port forwarding
    configure_port_forwarding "$container_name" "$service_name"
    
    # Start the service
    lxc exec "$container_name" -- bash -c "cd /opt/ultramcp && docker-compose up -d"
    
    log_success "Container $container_name configured successfully"
}

# Create default docker-compose configuration
create_default_compose() {
    local container_name="$1"
    local service_name="$2"
    
    cat > /tmp/docker-compose-default.yml << EOF
version: '3.8'

services:
  ${service_name}:
    image: ultramcp/${service_name}:latest
    container_name: ${service_name}-service
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - SERVICE_NAME=${service_name}
      - POSTGRES_URL=\${POSTGRES_URL}
      - REDIS_URL=\${REDIS_URL}
      - SUPABASE_URL=\${SUPABASE_URL}
      - SUPABASE_ANON_KEY=\${SUPABASE_ANON_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ultramcp-network

networks:
  ultramcp-network:
    driver: bridge
EOF

    lxc file push /tmp/docker-compose-default.yml \
        "$container_name/opt/ultramcp/docker-compose.yml"
    rm /tmp/docker-compose-default.yml
}

# Create environment file for container
create_env_file() {
    local container_name="$1"
    local service_name="$2"
    
    # Get container IP
    local container_ip=$(lxc info "$container_name" | grep "inet:" | head -1 | awk '{print $2}' | cut -d'/' -f1)
    
    cat > /tmp/container.env << EOF
# UltraMCP Container Environment
SERVICE_NAME=${service_name}
CONTAINER_NAME=${container_name}
CONTAINER_IP=${container_ip}

# Supabase Configuration
SUPABASE_URL=${SUPABASE_URL:-https://your-project.supabase.co}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-your-anon-key}

# Database Configuration
POSTGRES_URL=postgresql://postgres:password@postgres:5432/ultramcp
REDIS_URL=redis://redis:6379

# Service Configuration
PORT=8080
LOG_LEVEL=info
NODE_ENV=production

# Monitoring
ENABLE_MONITORING=true
METRICS_ENABLED=true
EOF

    lxc file push /tmp/container.env "$container_name/opt/ultramcp/.env"
    rm /tmp/container.env
}

# Configure port forwarding
configure_port_forwarding() {
    local container_name="$1"
    local service_name="$2"
    
    # Get the next available port
    local host_port=$(get_next_available_port)
    
    # Add proxy device for port forwarding
    lxc config device add "$container_name" "${service_name}-port" proxy \
        listen=tcp:0.0.0.0:${host_port} \
        connect=tcp:127.0.0.1:8080
    
    log_info "Port forwarding configured: Host port $host_port -> Container port 8080"
    
    # Store port mapping
    echo "${container_name}:${host_port}" >> /var/lib/lxd/ultramcp-ports.txt
}

# Get next available port
get_next_available_port() {
    local start_port=8080
    local port=$start_port
    
    while [ $port -lt 9000 ]; do
        if ! netstat -ln | grep -q ":$port "; then
            echo $port
            return
        fi
        ((port++))
    done
    
    # If no port found, use a random high port
    echo $((RANDOM + 10000))
}

# Create monitoring script for container
create_monitoring_script() {
    local container_name="$1"
    
    cat > /tmp/monitor.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import time
import os
from datetime import datetime

def check_service_health():
    try:
        response = requests.get('http://localhost:8080/health', timeout=5)
        return {
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'response_time': response.elapsed.total_seconds(),
            'status_code': response.status_code
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def report_status():
    health = check_service_health()
    
    # Log to file
    with open('/opt/ultramcp/logs/health.log', 'a') as f:
        f.write(f"{datetime.utcnow().isoformat()} {json.dumps(health)}\n")
    
    print(json.dumps(health, indent=2))

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('/opt/ultramcp/logs', exist_ok=True)
    report_status()
EOF

    lxc file push /tmp/monitor.py "$container_name/opt/ultramcp/monitor.py"
    lxc exec "$container_name" -- chmod +x /opt/ultramcp/monitor.py
    rm /tmp/monitor.py
    
    # Create systemd timer for monitoring
    cat > /tmp/monitor.service << EOF
[Unit]
Description=UltraMCP Service Monitor
After=docker.service

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/ultramcp
ExecStart=/opt/ultramcp/monitor.py
StandardOutput=journal
StandardError=journal
EOF

    cat > /tmp/monitor.timer << EOF
[Unit]
Description=Run service monitor every 2 minutes
Requires=ultramcp-monitor.service

[Timer]
OnBootSec=120
OnUnitActiveSec=120
Unit=ultramcp-monitor.service

[Install]
WantedBy=timers.target
EOF

    lxc file push /tmp/monitor.service "$container_name/etc/systemd/system/ultramcp-monitor.service"
    lxc file push /tmp/monitor.timer "$container_name/etc/systemd/system/ultramcp-monitor.timer"
    
    lxc exec "$container_name" -- systemctl daemon-reload
    lxc exec "$container_name" -- systemctl enable ultramcp-monitor.timer
    lxc exec "$container_name" -- systemctl start ultramcp-monitor.timer
    
    rm /tmp/monitor.service /tmp/monitor.timer
}

# Register sandbox in Supabase
register_sandbox_in_supabase() {
    local container_name="$1"
    local service_name="$2"
    
    if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_ANON_KEY:-}" ]; then
        log_warning "Supabase credentials not provided, skipping registration"
        return
    fi
    
    local container_ip=$(lxc info "$container_name" | grep "inet:" | head -1 | awk '{print $2}' | cut -d'/' -f1)
    local host_port=$(grep "$container_name:" /var/lib/lxd/ultramcp-ports.txt | cut -d':' -f2)
    
    log_info "Registering sandbox $container_name in Supabase..."
    
    python3 << EOF
import requests
import json

try:
    supabase_url = "$SUPABASE_URL"
    supabase_key = "$SUPABASE_ANON_KEY"
    
    instance_data = {
        "name": "$container_name",
        "type": "sandbox",
        "provider": "local",
        "region": "local-datacenter",
        "instance_id": "$container_name",
        "status": "running",
        "specs": {
            "cpu": 2,
            "memory": 2048,
            "disk": 10
        },
        "metadata": {
            "ip_address": "$container_ip",
            "service": "$service_name",
            "host_port": "$host_port",
            "sandbox_type": "lxd",
            "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        }
    }
    
    response = requests.post(
        f"{supabase_url}/rest/v1/cloud_instances",
        headers={
            "apikey": supabase_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        json=instance_data
    )
    
    if response.status_code in [200, 201]:
        print("Successfully registered sandbox in Supabase")
    else:
        print(f"Failed to register: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Error registering sandbox: {e}")
EOF
}

# List all UltraMCP sandboxes
list_sandboxes() {
    log_info "UltraMCP Sandboxes:"
    echo
    
    local containers=$(lxc list -c n,s,4,m,P --format csv | grep "^$CONTAINER_PREFIX")
    
    if [ -z "$containers" ]; then
        log_info "No UltraMCP sandboxes found"
        return
    fi
    
    printf "%-25s %-10s %-15s %-10s %-10s\n" "NAME" "STATUS" "IP ADDRESS" "MEMORY" "HOST PORT"
    echo "--------------------------------------------------------------------------------"
    
    while IFS=',' read -r name status ip memory processes; do
        local host_port=$(grep "$name:" /var/lib/lxd/ultramcp-ports.txt 2>/dev/null | cut -d':' -f2 || echo "N/A")
        printf "%-25s %-10s %-15s %-10s %-10s\n" "$name" "$status" "$ip" "$memory" "$host_port"
    done <<< "$containers"
}

# Show detailed information about a container
show_container_info() {
    local container_name="$1"
    
    if [ -z "$container_name" ]; then
        log_error "Container name is required"
        return 1
    fi
    
    if ! lxc list | grep -q "$container_name"; then
        log_error "Container $container_name not found"
        return 1
    fi
    
    log_info "Container Information: $container_name"
    echo
    
    # Basic info
    lxc info "$container_name"
    
    echo
    echo "Port Mappings:"
    local host_port=$(grep "$container_name:" /var/lib/lxd/ultramcp-ports.txt 2>/dev/null | cut -d':' -f2 || echo "N/A")
    if [ "$host_port" != "N/A" ]; then
        echo "  Host port $host_port -> Container port 8080"
        echo "  Service URL: http://localhost:$host_port"
    fi
    
    echo
    echo "Resource Usage:"
    lxc exec "$container_name" -- df -h / 2>/dev/null || echo "  Unable to get disk usage"
    lxc exec "$container_name" -- free -h 2>/dev/null || echo "  Unable to get memory usage"
}

# Stop a sandbox
stop_sandbox() {
    local container_name="$1"
    
    if [ -z "$container_name" ]; then
        log_error "Container name is required"
        return 1
    fi
    
    log_info "Stopping sandbox: $container_name"
    
    # Stop services first
    lxc exec "$container_name" -- bash -c "cd /opt/ultramcp && docker-compose down" 2>/dev/null || true
    
    # Stop container
    lxc stop "$container_name"
    
    log_success "Sandbox $container_name stopped"
}

# Start a sandbox
start_sandbox() {
    local container_name="$1"
    
    if [ -z "$container_name" ]; then
        log_error "Container name is required"
        return 1
    fi
    
    log_info "Starting sandbox: $container_name"
    
    # Start container
    lxc start "$container_name"
    
    # Wait for it to be ready
    sleep 10
    
    # Start services
    lxc exec "$container_name" -- bash -c "cd /opt/ultramcp && docker-compose up -d"
    
    log_success "Sandbox $container_name started"
}

# Delete a sandbox
delete_sandbox() {
    local container_name="$1"
    local force="${2:-false}"
    
    if [ -z "$container_name" ]; then
        log_error "Container name is required"
        return 1
    fi
    
    if [ "$force" != "true" ]; then
        read -p "Are you sure you want to delete $container_name? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "Deletion cancelled"
            return 0
        fi
    fi
    
    log_warning "Deleting sandbox: $container_name"
    
    # Stop first if running
    if lxc list | grep "$container_name" | grep -q "RUNNING"; then
        stop_sandbox "$container_name"
    fi
    
    # Delete container
    lxc delete "$container_name"
    
    # Remove port mapping
    sed -i "/$container_name:/d" /var/lib/lxd/ultramcp-ports.txt 2>/dev/null || true
    
    log_success "Sandbox $container_name deleted"
}

# Execute command in sandbox
exec_sandbox() {
    local container_name="$1"
    shift
    local command="$*"
    
    if [ -z "$container_name" ]; then
        log_error "Container name is required"
        return 1
    fi
    
    if [ -z "$command" ]; then
        # Interactive shell
        lxc exec "$container_name" -- bash
    else
        # Execute command
        lxc exec "$container_name" -- bash -c "$command"
    fi
}

# Show logs from a sandbox
logs_sandbox() {
    local container_name="$1"
    local service="${2:-all}"
    
    if [ -z "$container_name" ]; then
        log_error "Container name is required"
        return 1
    fi
    
    if [ "$service" = "all" ]; then
        # Show all logs
        lxc exec "$container_name" -- bash -c "cd /opt/ultramcp && docker-compose logs -f"
    else
        # Show specific service logs
        lxc exec "$container_name" -- bash -c "cd /opt/ultramcp && docker-compose logs -f $service"
    fi
}

# Clean up stopped containers and unused resources
cleanup() {
    log_info "Cleaning up unused resources..."
    
    # Remove stopped containers
    local stopped_containers=$(lxc list -c n,s --format csv | grep "^$CONTAINER_PREFIX.*,STOPPED" | cut -d',' -f1)
    
    for container in $stopped_containers; do
        read -p "Remove stopped container $container? (y/N): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            delete_sandbox "$container" true
        fi
    done
    
    log_success "Cleanup completed"
}

# Show usage
usage() {
    echo "UltraMCP Linux Sandbox Manager"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  init                                Initialize LXD environment"
    echo "  create <service> [cpu] [memory] [disk]  Create new sandbox"
    echo "  list                               List all sandboxes"
    echo "  info <container>                   Show container information"
    echo "  start <container>                  Start a sandbox"
    echo "  stop <container>                   Stop a sandbox"
    echo "  delete <container> [force]         Delete a sandbox"
    echo "  exec <container> [command]         Execute command in sandbox"
    echo "  logs <container> [service]         Show sandbox logs"
    echo "  cleanup                            Clean up unused resources"
    echo
    echo "Examples:"
    echo "  $0 init"
    echo "  $0 create chain-of-debate 4 4GiB 20GiB"
    echo "  $0 start ultramcp-security-sandbox"
    echo "  $0 exec ultramcp-cod-sandbox 'docker ps'"
    echo "  $0 logs ultramcp-cod-sandbox chain-of-debate"
}

# Main command handling
main() {
    # Create log file if it doesn't exist
    touch "$LOG_FILE"
    
    case "${1:-}" in
        "init")
            check_lxd
            init_environment
            ;;
        "create")
            check_lxd
            create_sandbox "$2" "$3" "$4" "$5"
            ;;
        "list")
            list_sandboxes
            ;;
        "info")
            show_container_info "$2"
            ;;
        "start")
            start_sandbox "$2"
            ;;
        "stop")
            stop_sandbox "$2"
            ;;
        "delete")
            delete_sandbox "$2" "$3"
            ;;
        "exec")
            shift
            exec_sandbox "$@"
            ;;
        "logs")
            logs_sandbox "$2" "$3"
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
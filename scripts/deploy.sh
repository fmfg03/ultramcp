#!/bin/bash
# MCP System Deployment Script
# Handles deployment across different environments

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
ENV_FILE="$PROJECT_ROOT/.env"

# Default values
ENVIRONMENT="development"
COMPOSE_FILE="docker-compose.yml"
BUILD_CACHE="true"
PULL_IMAGES="true"
VERBOSE="false"

# Functions
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

show_help() {
    cat << EOF
MCP System Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    up          Start the MCP system
    down        Stop the MCP system
    restart     Restart the MCP system
    build       Build all Docker images
    logs        Show logs from all services
    status      Show status of all services
    clean       Clean up unused Docker resources
    backup      Backup database and volumes
    restore     Restore from backup
    scale       Scale services horizontally
    health      Check health of all services

Options:
    -e, --env ENV           Environment (development|production|test) [default: development]
    -f, --file FILE         Docker compose file [default: auto-detected]
    -v, --verbose           Verbose output
    -h, --help              Show this help message
    --no-cache              Build without cache
    --no-pull               Don't pull latest images
    --detach                Run in detached mode

Examples:
    $0 up                           # Start development environment
    $0 -e production up             # Start production environment
    $0 -e production scale backend=3 # Scale backend to 3 instances
    $0 logs backend                 # Show backend logs
    $0 backup                       # Backup database
    $0 clean                        # Clean unused resources

EOF
}

detect_environment() {
    if [[ -f "$ENV_FILE" ]]; then
        local env_from_file=$(grep "^NODE_ENV=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ -n "$env_from_file" ]]; then
            ENVIRONMENT="$env_from_file"
        fi
    fi
    
    case "$ENVIRONMENT" in
        "development"|"dev")
            ENVIRONMENT="development"
            COMPOSE_FILE="docker-compose.dev.yml"
            ;;
        "production"|"prod")
            ENVIRONMENT="production"
            COMPOSE_FILE="docker-compose.prod.yml"
            ;;
        "test"|"testing")
            ENVIRONMENT="test"
            COMPOSE_FILE="docker-compose.test.yml"
            ;;
        *)
            ENVIRONMENT="development"
            COMPOSE_FILE="docker-compose.yml"
            ;;
    esac
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check compose file exists
    if [[ ! -f "$PROJECT_ROOT/$COMPOSE_FILE" ]]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_environment() {
    log_info "Setting up environment for: $ENVIRONMENT"
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/uploads"
    mkdir -p "$PROJECT_ROOT/temp"
    mkdir -p "$PROJECT_ROOT/keys"
    
    # Set permissions
    chmod 755 "$PROJECT_ROOT/logs"
    chmod 755 "$PROJECT_ROOT/uploads"
    chmod 755 "$PROJECT_ROOT/temp"
    chmod 700 "$PROJECT_ROOT/keys"
    
    # Copy environment file if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
            log_warning "Created .env file from .env.example. Please review and update it."
        else
            log_warning "No .env file found. Please create one with required environment variables."
        fi
    fi
    
    log_success "Environment setup completed"
}

docker_compose_cmd() {
    local cmd="docker-compose"
    if docker compose version &> /dev/null; then
        cmd="docker compose"
    fi
    
    local compose_args="-f $PROJECT_ROOT/$COMPOSE_FILE"
    
    if [[ "$VERBOSE" == "true" ]]; then
        compose_args="$compose_args --verbose"
    fi
    
    echo "$cmd $compose_args"
}

cmd_up() {
    log_info "Starting MCP system in $ENVIRONMENT mode..."
    
    local compose_cmd=$(docker_compose_cmd)
    local up_args="up"
    
    if [[ "$1" != "--foreground" ]]; then
        up_args="$up_args -d"
    fi
    
    if [[ "$BUILD_CACHE" == "false" ]]; then
        up_args="$up_args --build --no-cache"
    else
        up_args="$up_args --build"
    fi
    
    if [[ "$PULL_IMAGES" == "true" ]]; then
        log_info "Pulling latest images..."
        $compose_cmd pull
    fi
    
    $compose_cmd $up_args
    
    if [[ "$1" != "--foreground" ]]; then
        log_success "MCP system started successfully"
        log_info "Services are running in the background"
        log_info "Use '$0 logs' to view logs"
        log_info "Use '$0 status' to check service status"
    fi
}

cmd_down() {
    log_info "Stopping MCP system..."
    
    local compose_cmd=$(docker_compose_cmd)
    $compose_cmd down
    
    log_success "MCP system stopped"
}

cmd_restart() {
    log_info "Restarting MCP system..."
    cmd_down
    sleep 2
    cmd_up
}

cmd_build() {
    log_info "Building MCP system images..."
    
    local compose_cmd=$(docker_compose_cmd)
    local build_args="build"
    
    if [[ "$BUILD_CACHE" == "false" ]]; then
        build_args="$build_args --no-cache"
    fi
    
    if [[ "$PULL_IMAGES" == "true" ]]; then
        build_args="$build_args --pull"
    fi
    
    $compose_cmd $build_args
    
    log_success "Build completed"
}

cmd_logs() {
    local service="$1"
    local compose_cmd=$(docker_compose_cmd)
    
    if [[ -n "$service" ]]; then
        log_info "Showing logs for service: $service"
        $compose_cmd logs -f "$service"
    else
        log_info "Showing logs for all services"
        $compose_cmd logs -f
    fi
}

cmd_status() {
    log_info "Checking service status..."
    
    local compose_cmd=$(docker_compose_cmd)
    $compose_cmd ps
    
    echo ""
    log_info "Service health checks:"
    
    # Check individual service health
    local services=("mcp-backend" "mcp-devtool" "mcp-studio" "mcp-database" "mcp-redis")
    
    for service in "${services[@]}"; do
        local container_name="${service}"
        if [[ "$ENVIRONMENT" == "development" ]]; then
            container_name="${service}-dev"
        elif [[ "$ENVIRONMENT" == "production" ]]; then
            container_name="${service}-prod"
        fi
        
        if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
            local health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
            if [[ "$health" == "healthy" ]]; then
                echo -e "  ${GREEN}✓${NC} $service: healthy"
            elif [[ "$health" == "unhealthy" ]]; then
                echo -e "  ${RED}✗${NC} $service: unhealthy"
            else
                echo -e "  ${YELLOW}?${NC} $service: running (no health check)"
            fi
        else
            echo -e "  ${RED}✗${NC} $service: not running"
        fi
    done
}

cmd_clean() {
    log_info "Cleaning up Docker resources..."
    
    # Remove stopped containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    read -p "Remove unused volumes? This may delete data! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    # Remove unused networks
    docker network prune -f
    
    log_success "Cleanup completed"
}

cmd_backup() {
    log_info "Creating backup..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    local compose_cmd=$(docker_compose_cmd)
    local db_container="mcp-database"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        db_container="mcp-database-dev"
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        db_container="mcp-database-prod"
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "$db_container"; then
        log_info "Backing up database..."
        docker exec "$db_container" pg_dumpall -U postgres > "$backup_dir/database.sql"
        log_success "Database backup created: $backup_dir/database.sql"
    else
        log_warning "Database container not running, skipping database backup"
    fi
    
    # Backup volumes
    log_info "Backing up volumes..."
    docker run --rm -v mcp_postgres_data:/data -v "$backup_dir":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
    docker run --rm -v mcp_redis_data:/data -v "$backup_dir":/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
    
    # Backup configuration
    log_info "Backing up configuration..."
    cp "$ENV_FILE" "$backup_dir/.env" 2>/dev/null || true
    cp -r "$PROJECT_ROOT/keys" "$backup_dir/" 2>/dev/null || true
    
    log_success "Backup completed: $backup_dir"
}

cmd_restore() {
    local backup_dir="$1"
    
    if [[ -z "$backup_dir" ]]; then
        log_error "Please specify backup directory"
        exit 1
    fi
    
    if [[ ! -d "$backup_dir" ]]; then
        log_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    log_warning "This will restore from backup and may overwrite existing data!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi
    
    log_info "Restoring from backup: $backup_dir"
    
    # Stop services
    cmd_down
    
    # Restore database
    if [[ -f "$backup_dir/database.sql" ]]; then
        log_info "Restoring database..."
        # Start only database
        local compose_cmd=$(docker_compose_cmd)
        $compose_cmd up -d mcp-database
        sleep 10
        
        # Restore database
        docker exec -i mcp-database psql -U postgres < "$backup_dir/database.sql"
        log_success "Database restored"
    fi
    
    # Restore volumes
    if [[ -f "$backup_dir/postgres_data.tar.gz" ]]; then
        log_info "Restoring PostgreSQL data..."
        docker run --rm -v mcp_postgres_data:/data -v "$backup_dir":/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
    fi
    
    if [[ -f "$backup_dir/redis_data.tar.gz" ]]; then
        log_info "Restoring Redis data..."
        docker run --rm -v mcp_redis_data:/data -v "$backup_dir":/backup alpine tar xzf /backup/redis_data.tar.gz -C /data
    fi
    
    # Restore configuration
    if [[ -f "$backup_dir/.env" ]]; then
        log_info "Restoring environment configuration..."
        cp "$backup_dir/.env" "$ENV_FILE"
    fi
    
    if [[ -d "$backup_dir/keys" ]]; then
        log_info "Restoring keys..."
        cp -r "$backup_dir/keys" "$PROJECT_ROOT/"
    fi
    
    log_success "Restore completed"
    log_info "Starting services..."
    cmd_up
}

cmd_scale() {
    local scale_args="$1"
    
    if [[ -z "$scale_args" ]]; then
        log_error "Please specify scaling configuration (e.g., backend=3)"
        exit 1
    fi
    
    log_info "Scaling services: $scale_args"
    
    local compose_cmd=$(docker_compose_cmd)
    $compose_cmd up -d --scale "$scale_args"
    
    log_success "Scaling completed"
}

cmd_health() {
    log_info "Performing comprehensive health check..."
    
    # Check Docker system
    log_info "Docker system info:"
    docker system df
    
    echo ""
    
    # Check service status
    cmd_status
    
    echo ""
    
    # Check service endpoints
    log_info "Checking service endpoints..."
    
    local endpoints=(
        "http://sam.chat:3000/health:Backend"
        "http://sam.chat:5173:DevTool"
        "http://sam.chat:8123/health:Studio"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_info" | cut -d':' -f1)
        local service=$(echo "$endpoint_info" | cut -d':' -f2)
        
        if curl -f -s "$endpoint" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $service: $endpoint"
        else
            echo -e "  ${RED}✗${NC} $service: $endpoint"
        fi
    done
    
    echo ""
    log_success "Health check completed"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        --no-cache)
            BUILD_CACHE="false"
            shift
            ;;
        --no-pull)
            PULL_IMAGES="false"
            shift
            ;;
        --detach)
            DETACH="true"
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Get command
COMMAND="$1"
shift || true

# Main execution
cd "$PROJECT_ROOT"

detect_environment
check_prerequisites
setup_environment

case "$COMMAND" in
    "up"|"start")
        cmd_up "$@"
        ;;
    "down"|"stop")
        cmd_down
        ;;
    "restart")
        cmd_restart
        ;;
    "build")
        cmd_build
        ;;
    "logs")
        cmd_logs "$@"
        ;;
    "status"|"ps")
        cmd_status
        ;;
    "clean")
        cmd_clean
        ;;
    "backup")
        cmd_backup
        ;;
    "restore")
        cmd_restore "$@"
        ;;
    "scale")
        cmd_scale "$@"
        ;;
    "health")
        cmd_health
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac


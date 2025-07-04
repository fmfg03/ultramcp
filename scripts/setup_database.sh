#!/bin/bash

# UltraMCP ContextBuilderAgent 2.0 - Database Setup Script
# Automated PostgreSQL + Redis Integration Setup

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config/database"
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
    
    # Check if ports are available
    local ports=(5432 6379 26379 5050 8081 6432 9187 9121)
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            warning "Port $port is already in use"
        fi
    done
    
    success "Prerequisites check passed"
}

# Setup directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$CONFIG_DIR/backup"
    mkdir -p "$CONFIG_DIR/logs"
    mkdir -p "$CONFIG_DIR/scripts"
    mkdir -p "$LOGS_DIR/postgres"
    mkdir -p "$LOGS_DIR/redis"
    
    success "Directories created"
}

# Create backup script
create_backup_script() {
    log "Creating backup script..."
    
    cat > "$CONFIG_DIR/scripts/backup.sh" <<'EOF'
#!/bin/bash

# Database backup script
BACKUP_DIR="/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump -h postgres -U contextbuilder -d contextbuilder > "$BACKUP_DIR/contextbuilder_${TIMESTAMP}.sql"

# Redis backup
redis-cli -h redis -p 6379 -a contextbuilder_redis_2024 --rdb "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
EOF
    
    chmod +x "$CONFIG_DIR/scripts/backup.sh"
    success "Backup script created"
}

# Deploy database services
deploy_database() {
    log "Deploying database services..."
    
    cd "$CONFIG_DIR"
    
    # Pull latest images
    docker-compose -f docker-compose.database.yml pull
    
    # Start services
    docker-compose -f docker-compose.database.yml up -d
    
    # Wait for services to start
    log "Waiting for services to start..."
    sleep 30
    
    # Check PostgreSQL health
    local postgres_health=0
    for i in {1..10}; do
        if docker exec contextbuilder-postgres pg_isready -U contextbuilder -d contextbuilder &> /dev/null; then
            postgres_health=1
            break
        fi
        log "Waiting for PostgreSQL to be ready... ($i/10)"
        sleep 5
    done
    
    if [[ $postgres_health -eq 0 ]]; then
        error "PostgreSQL failed to start"
        return 1
    fi
    
    # Check Redis health
    local redis_health=0
    for i in {1..10}; do
        if docker exec contextbuilder-redis redis-cli ping &> /dev/null; then
            redis_health=1
            break
        fi
        log "Waiting for Redis to be ready... ($i/10)"
        sleep 5
    done
    
    if [[ $redis_health -eq 0 ]]; then
        error "Redis failed to start"
        return 1
    fi
    
    success "Database services deployed successfully"
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    # Run database initialization
    if docker exec contextbuilder-postgres psql -U contextbuilder -d contextbuilder -c "SELECT 'Database initialized successfully!' AS status;" &> /dev/null; then
        success "Database initialized successfully"
    else
        error "Database initialization failed"
        return 1
    fi
    
    # Test Redis connection
    if docker exec contextbuilder-redis redis-cli ping | grep -q "PONG"; then
        success "Redis connection test passed"
    else
        error "Redis connection test failed"
        return 1
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up database monitoring..."
    
    # Test PostgreSQL exporter
    local postgres_exporter_health=0
    for i in {1..5}; do
        if curl -f http://localhost:9187/metrics &> /dev/null; then
            postgres_exporter_health=1
            break
        fi
        log "Waiting for PostgreSQL exporter... ($i/5)"
        sleep 3
    done
    
    if [[ $postgres_exporter_health -eq 1 ]]; then
        success "PostgreSQL exporter is healthy"
    else
        warning "PostgreSQL exporter is not responding"
    fi
    
    # Test Redis exporter
    local redis_exporter_health=0
    for i in {1..5}; do
        if curl -f http://localhost:9121/metrics &> /dev/null; then
            redis_exporter_health=1
            break
        fi
        log "Waiting for Redis exporter... ($i/5)"
        sleep 3
    done
    
    if [[ $redis_exporter_health -eq 1 ]]; then
        success "Redis exporter is healthy"
    else
        warning "Redis exporter is not responding"
    fi
}

# Test database integration
test_database_integration() {
    log "Testing database integration..."
    
    # Test PostgreSQL operations
    log "Testing PostgreSQL operations..."
    
    # Create test table
    docker exec contextbuilder-postgres psql -U contextbuilder -d contextbuilder -c "
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );
    " &> /dev/null
    
    # Insert test data
    docker exec contextbuilder-postgres psql -U contextbuilder -d contextbuilder -c "
        INSERT INTO test_table (name) VALUES ('Test Record');
    " &> /dev/null
    
    # Query test data
    local pg_result=$(docker exec contextbuilder-postgres psql -U contextbuilder -d contextbuilder -t -c "
        SELECT COUNT(*) FROM test_table;
    " 2>/dev/null | xargs)
    
    if [[ "$pg_result" -gt 0 ]]; then
        success "PostgreSQL operations test passed"
    else
        error "PostgreSQL operations test failed"
        return 1
    fi
    
    # Clean up test table
    docker exec contextbuilder-postgres psql -U contextbuilder -d contextbuilder -c "
        DROP TABLE IF EXISTS test_table;
    " &> /dev/null
    
    # Test Redis operations
    log "Testing Redis operations..."
    
    # Set test key
    docker exec contextbuilder-redis redis-cli -a contextbuilder_redis_2024 set test_key "test_value" &> /dev/null
    
    # Get test key
    local redis_result=$(docker exec contextbuilder-redis redis-cli -a contextbuilder_redis_2024 get test_key 2>/dev/null)
    
    if [[ "$redis_result" == "test_value" ]]; then
        success "Redis operations test passed"
    else
        error "Redis operations test failed"
        return 1
    fi
    
    # Clean up test key
    docker exec contextbuilder-redis redis-cli -a contextbuilder_redis_2024 del test_key &> /dev/null
    
    # Test Redis Streams (for Semantic Coherence Bus)
    log "Testing Redis Streams..."
    
    # Add stream entry
    docker exec contextbuilder-redis redis-cli -a contextbuilder_redis_2024 xadd coherence_stream "*" event_type "test" data "test_data" &> /dev/null
    
    # Read stream entries
    local stream_result=$(docker exec contextbuilder-redis redis-cli -a contextbuilder_redis_2024 xlen coherence_stream 2>/dev/null)
    
    if [[ "$stream_result" -gt 0 ]]; then
        success "Redis Streams test passed"
    else
        error "Redis Streams test failed"
        return 1
    fi
    
    # Clean up test stream
    docker exec contextbuilder-redis redis-cli -a contextbuilder_redis_2024 del coherence_stream &> /dev/null
}

# Show status
show_status() {
    log "Database Services Status:"
    echo
    
    # Show running containers
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "contextbuilder-(postgres|redis|pgadmin|redis-commander)"
    
    echo
    log "Service Health:"
    
    # PostgreSQL
    if docker exec contextbuilder-postgres pg_isready -U contextbuilder -d contextbuilder &> /dev/null; then
        echo -e "  PostgreSQL: ${GREEN}✓ Healthy${NC}"
    else
        echo -e "  PostgreSQL: ${RED}✗ Unhealthy${NC}"
    fi
    
    # Redis
    if docker exec contextbuilder-redis redis-cli ping &> /dev/null; then
        echo -e "  Redis: ${GREEN}✓ Healthy${NC}"
    else
        echo -e "  Redis: ${RED}✗ Unhealthy${NC}"
    fi
    
    # Connection Pooler
    if nc -z localhost 6432 &> /dev/null; then
        echo -e "  PgBouncer: ${GREEN}✓ Healthy${NC}"
    else
        echo -e "  PgBouncer: ${RED}✗ Unhealthy${NC}"
    fi
    
    echo
    log "Management Interfaces:"
    echo "  PgAdmin: http://localhost:5050"
    echo "  Redis Commander: http://localhost:8081"
    echo "  PostgreSQL Metrics: http://localhost:9187/metrics"
    echo "  Redis Metrics: http://localhost:9121/metrics"
}

# Main setup function
main() {
    local action="${1:-setup}"
    
    case "$action" in
        "setup")
            log "Setting up ContextBuilderAgent 2.0 Database Integration"
            check_prerequisites
            setup_directories
            create_backup_script
            deploy_database
            initialize_database
            setup_monitoring
            test_database_integration
            show_status
            success "Database setup completed successfully!"
            ;;
        "status")
            show_status
            ;;
        "test")
            test_database_integration
            ;;
        "backup")
            log "Running database backup..."
            "$CONFIG_DIR/scripts/backup.sh"
            ;;
        "help"|*)
            echo "UltraMCP ContextBuilderAgent 2.0 - Database Setup"
            echo
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  setup     Complete database setup (default)"
            echo "  status    Show database services status"
            echo "  test      Test database integration"
            echo "  backup    Run database backup"
            echo "  help      Show this help message"
            echo
            echo "Services included:"
            echo "  - PostgreSQL 15 with optimized configuration"
            echo "  - Redis 7 with Sentinel for high availability"
            echo "  - PgBouncer for connection pooling"
            echo "  - PgAdmin for database management"
            echo "  - Redis Commander for Redis management"
            echo "  - Prometheus exporters for monitoring"
            echo "  - Automated backup system"
            ;;
    esac
}

# Run main function
main "$@"
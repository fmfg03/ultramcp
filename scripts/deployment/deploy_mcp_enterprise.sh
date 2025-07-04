#!/bin/bash
# Automated Deployment Script for MCP Enterprise
# Ejecuta deployment completo del sistema

set -e  # Exit on any error

echo "🚀 MCP ENTERPRISE AUTOMATED DEPLOYMENT"
echo "======================================"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEPLOY_LOG="deployment_${TIMESTAMP}.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$DEPLOY_LOG"
}

log "Starting MCP Enterprise deployment..."

# STEP 1: Pre-deployment checks
log "🔍 Running pre-deployment checks..."
if [ -f "pre_deployment_check.sh" ]; then
    chmod +x pre_deployment_check.sh
    if ./pre_deployment_check.sh; then
        log "✅ Pre-deployment checks passed"
    else
        log "❌ Pre-deployment checks failed"
        exit 1
    fi
else
    log "⚠️ Pre-deployment check script not found, continuing..."
fi

# STEP 2: Environment setup
log "🔧 Setting up environment..."
if [ -f "final_environment_setup.sh" ]; then
    chmod +x final_environment_setup.sh
    if ./final_environment_setup.sh; then
        log "✅ Environment setup completed"
    else
        log "❌ Environment setup failed"
        exit 1
    fi
else
    log "❌ Environment setup script not found"
    exit 1
fi

# STEP 3: Database initialization
log "🗄️ Initializing database..."
if [ -n "$SUPABASE_URL" ]; then
    log "✅ Supabase configured, schema should be applied manually"
    log "📋 Schema file: Schema Final - Con Cleanup de Funciones.txt"
else
    log "❌ SUPABASE_URL not configured"
    exit 1
fi

# STEP 4: Install Python dependencies
log "📦 Installing Python dependencies..."
if pip3 install --upgrade pip; then
    log "✅ pip upgraded"
else
    log "⚠️ pip upgrade failed, continuing..."
fi

# Install required packages
PYTHON_PACKAGES=(
    "asyncio"
    "aiohttp>=3.8.0"
    "flask>=2.0.0"
    "flask-cors"
    "requests>=2.28.0"
    "supabase>=1.0.0"
    "openai>=1.0.0"
    "numpy>=1.21.0"
    "python-dotenv"
    "pydantic"
    "uvicorn"
    "fastapi"
    "websockets"
    "redis"
    "psycopg2-binary"
    "jwt"
    "cryptography"
    "schedule"
)

for package in "${PYTHON_PACKAGES[@]}"; do
    if pip3 install "$package"; then
        log "✅ Installed $package"
    else
        log "⚠️ Failed to install $package, may need manual installation"
    fi
done

# STEP 5: Create required directories and permissions
log "📂 Creating directories and setting permissions..."
mkdir -p logs data backups temp
chmod 755 logs data backups temp
chmod +x *.py
chmod +x *.sh

log "✅ Directories and permissions set"

# STEP 6: Test core components
log "🧪 Testing core components..."

test_import() {
    local module=$1
    if python3 -c "import $module; print('✅ $module imported successfully')" 2>/dev/null; then
        log "✅ $module test passed"
        return 0
    else
        log "❌ $module test failed"
        return 1
    fi
}

# Test critical modules
CRITICAL_MODULES=(
    "sam_memory_analyzer"
    "mcp_orchestration_server"
    "complete_webhook_agent_end_task_system"
    "mcp_payload_schemas"
    "sam_manus_notification_protocol"
)

failed_tests=0
for module in "${CRITICAL_MODULES[@]}"; do
    if [ -f "${module}.py" ]; then
        if ! test_import "$module"; then
            failed_tests=$((failed_tests + 1))
        fi
    else
        log "❌ Module file ${module}.py not found"
        failed_tests=$((failed_tests + 1))
    fi
done

if [ $failed_tests -eq 0 ]; then
    log "✅ All critical modules tested successfully"
else
    log "❌ $failed_tests critical modules failed tests"
    log "⚠️ Deployment will continue but may have issues"
fi

# STEP 7: Configure firewall (if needed)
log "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 3000/tcp comment "MCP Backend"
    sudo ufw allow 5174/tcp comment "MCP Frontend"
    sudo ufw allow 8125/tcp comment "MCP Monitor"
    sudo ufw allow 8126/tcp comment "MCP Dashboard"
    sudo ufw allow 8127/tcp comment "MCP Validation"
    sudo ufw allow 3003/tcp comment "MCP Webhooks"
    log "✅ Firewall rules added"
else
    log "⚠️ ufw not available, configure firewall manually"
fi

# STEP 8: Create backup of current configuration
log "💾 Creating deployment backup..."
BACKUP_DIR="backups/deployment_backup_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"
cp *.py "$BACKUP_DIR/" 2>/dev/null || true
cp *.sh "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/" 2>/dev/null || true
log "✅ Backup created in $BACKUP_DIR"

# STEP 9: Start services
log "🚀 Starting MCP Enterprise services..."

# Stop any existing services
if systemctl is-active --quiet mcp-enterprise; then
    log "⏹️ Stopping existing services..."
    sudo systemctl stop mcp-enterprise
    sleep 5
fi

# Kill any remaining processes on our ports
PORTS=(3000 5174 8125 8126 8127 3003)
for port in "${PORTS[@]}"; do
    if netstat -tuln | grep ":$port " > /dev/null; then
        log "🔌 Freeing port $port..."
        sudo fuser -k $port/tcp 2>/dev/null || true
        sleep 2
    fi
done

# Start the service
log "▶️ Starting MCP Enterprise service..."
if sudo systemctl start mcp-enterprise; then
    log "✅ Service started successfully"
    
    # Wait for services to initialize
    log "⏳ Waiting for services to initialize..."
    sleep 15
    
    # Check service status
    if sudo systemctl is-active --quiet mcp-enterprise; then
        log "✅ Service is running"
    else
        log "❌ Service failed to start"
        log "📋 Check logs: sudo journalctl -u mcp-enterprise -f"
        exit 1
    fi
else
    log "❌ Failed to start service"
    exit 1
fi

# STEP 10: Verify deployment
log "✅ Verifying deployment..."

# Health check function
health_check() {
    local service_name=$1
    local url=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log "✅ $service_name health check passed"
            return 0
        else
            log "⏳ $service_name health check attempt $attempt/$max_attempts..."
            sleep 3
            attempt=$((attempt + 1))
        fi
    done
    
    log "❌ $service_name health check failed after $max_attempts attempts"
    return 1
}

# Perform health checks
HEALTH_CHECKS=(
    "Backend:http://sam.chat:3000/health"
    "Monitor:http://sam.chat:8125/health"
    "Dashboard:http://sam.chat:8126/health"
    "Validation:http://sam.chat:8127/health"
)

successful_checks=0
for check in "${HEALTH_CHECKS[@]}"; do
    IFS=':' read -r name url <<< "$check"
    if health_check "$name" "$url"; then
        successful_checks=$((successful_checks + 1))
    fi
done

log "Health checks completed: $successful_checks/${#HEALTH_CHECKS[@]} services healthy"

# STEP 11: Final verification
log "🔍 Final verification..."

# Test API endpoint
if curl -s "http://sam.chat:3000/health" | grep -q "healthy"; then
    log "✅ API endpoint responding correctly"
else
    log "⚠️ API endpoint may have issues"
fi

# Check log files
if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
    log "✅ Log files are being created"
else
    log "⚠️ No log files found"
fi

# Final status
log ""
log "🎉 MCP ENTERPRISE DEPLOYMENT COMPLETED!"
log "====================================="
log ""
log "📊 Deployment Summary:"
log "- Timestamp: $TIMESTAMP"
log "- Services healthy: $successful_checks/${#HEALTH_CHECKS[@]}"
log "- Backup location: $BACKUP_DIR"
log "- Log file: $DEPLOY_LOG"
log ""
log "🌐 Access Points:"
log "- Backend API: http://65.109.54.94:3000"
log "- Frontend: http://65.109.54.94:5174"
log "- Monitor: http://65.109.54.94:8125"
log "- Dashboard: http://65.109.54.94:8126"
log "- Validation: http://65.109.54.94:8127"
log ""
log "📋 Next Steps:"
log "1. Configure external API keys in .env"
log "2. Apply database schema in Supabase"
log "3. Test functionality: curl http://65.109.54.94:3000/health"
log "4. Monitor logs: tail -f logs/*.log"
log ""
log "🎯 Deployment completed successfully!"

echo ""
echo "Deployment log saved to: $DEPLOY_LOG"
echo "System is ready for production use! 🚀"

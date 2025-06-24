#!/bin/bash
# Final Environment Setup para MCP Enterprise
# Configuración completa para producción

echo "🔧 MCP ENTERPRISE FINAL SETUP"
echo "============================="

cd /root/supermcp

# 1. CREAR .env COMPLETO PARA PRODUCCIÓN
echo "📝 Creating production .env..."

cat > .env << 'EOF'
# =============================================================================
# MCP ENTERPRISE PRODUCTION CONFIGURATION
# =============================================================================

# Supabase Configuration (PRODUCTION READY)
SUPABASE_URL=https://bvhhkmdlfpcebecmxshd.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ2aGhrbWRsZnBjZWJlY214c2hkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMzQyNjQzNCwiZXhwIjoyMDQ5MDAyNDM0fQ.TiJmDmqn-3TlPkv7F52HFZ7vZWGfRlNqcVFRo4q5brQ
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ2aGhrbWRsZnBjZWJlY214c2hkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM0MjY0MzQsImV4cCI6MjA0OTAwMjQzNH0.iHR5YG1UhLDrOL47eFqzUUo10O3gxl-rSFXe4VNdqWQ

# External APIs (PLACEHOLDER - Configurar con keys reales)
FIRECRAWL_API_KEY=fc-0332219c1d1f49febd63e06d57e6c953
TELEGRAM_BOT_TOKEN=1771877784:AAFVzasxpqDI-rWZnGOuP4MusR8QwNOFRzg
NOTION_TOKEN=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
GITHUB_TOKEN=ghp_

# OpenAI Configuration
OPENAI_API_KEY=sk-placeholder-configure-with-real-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4096

# System Configuration
NODE_ENV=production
DEBUG=false
LOG_LEVEL=info
ENVIRONMENT=production

# Server Ports
PORT=3000
FRONTEND_PORT=5174
WEBHOOK_PORT=3003
MONITOR_PORT=8125
DASHBOARD_PORT=8126
VALIDATION_PORT=8127

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/mcp_enterprise

# Redis Configuration  
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0

# Security Configuration
JWT_SECRET=mcp-enterprise-jwt-secret-2024-production
JWT_EXPIRATION=24h
JWT_REFRESH_EXPIRATION=7d
ENCRYPTION_KEY=mcp-enterprise-encryption-key-32-chars-prod
WEBHOOK_SECRET=mcp-webhook-secret-2024-production

# Rate Limiting
RATE_LIMIT_WINDOW=15m
RATE_LIMIT_MAX_REQUESTS=1000
RATE_LIMIT_SKIP_SUCCESSFUL=true

# Webhook Configuration
WEBHOOK_RETRY_ATTEMPTS=5
WEBHOOK_TIMEOUT=30000
WEBHOOK_BACKOFF_STRATEGY=exponential

# Agent Configuration
MAX_CONCURRENT_AGENTS=1000
MAX_TASKS_PER_AGENT=10
AGENT_TIMEOUT=300
TASK_TIMEOUT=600

# Memory Configuration
MEMORY_CACHE_SIZE=1000
MEMORY_CACHE_TTL=3600
MEMORY_COMPRESSION_THRESHOLD=1024

# Monitoring Configuration
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30
LOG_RETENTION_DAYS=30

# Email Configuration (para notificaciones)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=francisco@yourdomain.com

# Server Information
SERVER_HOST=65.109.54.94
SERVER_NAME=mcp-enterprise-production
VERSION=2.0.0
EOF

echo "✅ .env created with production settings"

# 2. CREAR DIRECTORIO DE LOGS
echo "📂 Creating logs directory..."
mkdir -p logs
mkdir -p data
mkdir -p backups
chmod 755 logs data backups

# 3. CONFIGURAR LOGROTATE
echo "🔄 Setting up log rotation..."
sudo tee /etc/logrotate.d/mcp-enterprise > /dev/null << 'EOF'
/root/supermcp/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload mcp-enterprise || true
    endscript
}
EOF

# 4. CREAR SYSTEMD SERVICE
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/mcp-enterprise.service > /dev/null << 'EOF'
[Unit]
Description=MCP Enterprise System
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/supermcp
Environment=PYTHONPATH=/root/supermcp
ExecStart=/root/supermcp/start_mcp_enterprise.sh
Restart=always
RestartSec=10
StandardOutput=append:/root/supermcp/logs/system.log
StandardError=append:/root/supermcp/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# 5. CREAR SCRIPT DE STARTUP PRINCIPAL
echo "🚀 Creating main startup script..."
cat > start_mcp_enterprise.sh << 'EOF'
#!/bin/bash
# MCP Enterprise System Startup Script

echo "🚀 STARTING MCP ENTERPRISE SYSTEM"
echo "================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment loaded"
else
    echo "❌ .env file not found"
    exit 1
fi

# Create necessary directories
mkdir -p logs data backups
echo "✅ Directories created"

# Function to start service with logging
start_service() {
    local service_name=$1
    local script_name=$2
    local port=$3
    
    echo "Starting $service_name on port $port..."
    python3 "$script_name" > "logs/${service_name}.log" 2>&1 &
    local pid=$!
    echo $pid > "logs/${service_name}.pid"
    echo "✅ $service_name started (PID: $pid)"
    sleep 2
}

# Start core services
echo "🧠 Starting Memory Analyzer..."
start_service "memory-analyzer" "sam_memory_analyzer.py" $PORT

echo "🎯 Starting Orchestration Server..."  
start_service "orchestration" "mcp_orchestration_server.py" $PORT

echo "🔗 Starting Webhook System..."
start_service "webhook" "complete_webhook_agent_end_task_system.py" $WEBHOOK_PORT

echo "👀 Starting Active Monitoring..."
start_service "monitor" "mcp_active_webhook_monitoring.py" $MONITOR_PORT

echo "📊 Starting Dashboard..."
start_service "dashboard" "mcp_logs_dashboard_system.py" $DASHBOARD_PORT

echo "✅ Starting Validation System..."
start_service "validation" "mcp_task_validation_offline_system.py" $VALIDATION_PORT

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Health check
echo "🏥 Performing health checks..."
services_ok=0

check_service() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
        services_ok=$((services_ok + 1))
    else
        echo "❌ $name is not responding"
    fi
}

check_service "Memory Analyzer" "http://localhost:$PORT/health"
check_service "Active Monitor" "http://localhost:$MONITOR_PORT/health"  
check_service "Dashboard" "http://localhost:$DASHBOARD_PORT/health"
check_service "Validation" "http://localhost:$VALIDATION_PORT/health"

echo ""
echo "🎉 MCP ENTERPRISE SYSTEM STARTED!"
echo "================================"
echo "Services running: $services_ok/4"
echo ""
echo "🌐 Access Points:"
echo "Frontend:    http://65.109.54.94:5174"
echo "Backend:     http://65.109.54.94:3000"
echo "Monitor:     http://65.109.54.94:8125"
echo "Dashboard:   http://65.109.54.94:8126"
echo "Validation:  http://65.109.54.94:8127"
echo ""
echo "📊 Logs location: /root/supermcp/logs/"
echo "📋 Monitor: tail -f logs/*.log"
echo ""

# Keep script running
while true; do
    sleep 60
    # Optional: Add health monitoring here
done
EOF

chmod +x start_mcp_enterprise.sh

# 6. RELOAD SYSTEMD
sudo systemctl daemon-reload
sudo systemctl enable mcp-enterprise

echo ""
echo "✅ FINAL SETUP COMPLETED!"
echo "========================"
echo ""
echo "🎯 Next steps:"
echo "1. Run pre-deployment check: ./pre_deployment_check.sh"
echo "2. Start system: sudo systemctl start mcp-enterprise"
echo "3. Check status: sudo systemctl status mcp-enterprise"
echo "4. View logs: tail -f logs/*.log"
echo ""

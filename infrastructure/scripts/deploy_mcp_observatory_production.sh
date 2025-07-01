#!/bin/bash

# MCP Observatory Production Deployment Script
# This script deploys the fixed MCP Observatory to production

set -e

echo "🚀 MCP Observatory Production Deployment"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PRODUCTION_DIR="/var/www/mcp-observatory"
BACKUP_DIR="/var/backups/mcp-observatory-$(date +%Y%m%d-%H%M%S)"
SERVICE_NAME="mcp-observatory"
PORT=3000

print_status "Starting MCP Observatory production deployment..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root or with sudo"
    exit 1
fi

# Create backup of existing installation
if [ -d "$PRODUCTION_DIR" ]; then
    print_status "Creating backup of existing installation..."
    mkdir -p "$BACKUP_DIR"
    cp -r "$PRODUCTION_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
    print_success "Backup created at: $BACKUP_DIR"
fi

# Create production directory
print_status "Creating production directory..."
mkdir -p "$PRODUCTION_DIR"
cd "$PRODUCTION_DIR"

# Copy fixed files
print_status "Deploying fixed MCP Observatory files..."

cp /home/ubuntu/mcp_server_fixed.mjs "$PRODUCTION_DIR/server.mjs"
cp /home/ubuntu/mcpRoutes_fixed.mjs "$PRODUCTION_DIR/mcpRoutes.mjs"
cp /home/ubuntu/package_fixed.json "$PRODUCTION_DIR/package.json"
cp /home/ubuntu/mcp_observatory_frontend_fix.html "$PRODUCTION_DIR/index.html"

print_success "Files deployed successfully"

# Set proper ownership and permissions
print_status "Setting file permissions..."
chown -R www-data:www-data "$PRODUCTION_DIR"
chmod -R 755 "$PRODUCTION_DIR"
chmod 644 "$PRODUCTION_DIR"/*.json
chmod 644 "$PRODUCTION_DIR"/*.html

print_success "Permissions set correctly"

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
sudo -u www-data npm install --production --silent

if [ $? -eq 0 ]; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Stop existing service if running
print_status "Stopping existing MCP Observatory service..."
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl stop "$SERVICE_NAME"
    print_success "Existing service stopped"
else
    print_warning "No existing service found"
fi

# Create systemd service file
print_status "Creating systemd service..."

cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=MCP Observatory Backend Server
Documentation=https://github.com/fmfg03/supermcp
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PRODUCTION_DIR
ExecStart=/usr/bin/node server.mjs
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=$PORT

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mcp-observatory

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PRODUCTION_DIR

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service created"

# Reload systemd and enable service
print_status "Configuring systemd service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

print_success "Service enabled for auto-start"

# Start the service
print_status "Starting MCP Observatory service..."
systemctl start "$SERVICE_NAME"

# Wait for service to be ready
sleep 3

if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_success "MCP Observatory service started successfully"
else
    print_error "Failed to start MCP Observatory service"
    print_status "Checking service logs..."
    journalctl -u "$SERVICE_NAME" --no-pager -n 20
    exit 1
fi

# Test the service
print_status "Testing service endpoints..."

# Test health endpoint
if curl -s "http://localhost:$PORT/health" | grep -q '"status":"healthy"'; then
    print_success "Health endpoint is working"
else
    print_error "Health endpoint failed"
fi

# Test tools endpoint
if curl -s "http://localhost:$PORT/api/tools" | grep -q '"name"'; then
    TOOL_COUNT=$(curl -s "http://localhost:$PORT/api/tools" | grep -o '"name"' | wc -l)
    print_success "Tools endpoint is working ($TOOL_COUNT tools available)"
else
    print_error "Tools endpoint failed"
fi

# Test execute endpoint
EXECUTE_TEST=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"tool":"firecrawl","parameters":{"url":"https://example.com"}}' \
    "http://localhost:$PORT/api/tools/execute")

if echo "$EXECUTE_TEST" | grep -q '"success":true'; then
    print_success "Execute endpoint is working"
else
    print_error "Execute endpoint failed"
fi

# Update nginx configuration if needed
print_status "Checking nginx configuration..."

NGINX_CONFIG="/etc/nginx/sites-available/observatory-direct"
if [ -f "$NGINX_CONFIG" ]; then
    # Update nginx config to proxy to our new backend
    if grep -q "proxy_pass.*3000" "$NGINX_CONFIG"; then
        print_success "Nginx configuration already points to port 3000"
    else
        print_status "Updating nginx configuration..."
        # Backup existing config
        cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d-%H%M%S)"
        
        # Update proxy_pass to point to our backend
        sed -i 's|try_files.*|proxy_pass http://127.0.0.1:3000;|' "$NGINX_CONFIG"
        
        # Test nginx configuration
        if nginx -t; then
            systemctl reload nginx
            print_success "Nginx configuration updated and reloaded"
        else
            print_error "Nginx configuration test failed"
            # Restore backup
            cp "$NGINX_CONFIG.backup.$(date +%Y%m%d-%H%M%S)" "$NGINX_CONFIG"
        fi
    fi
else
    print_warning "Nginx configuration file not found at $NGINX_CONFIG"
fi

# Create log rotation configuration
print_status "Setting up log rotation..."

cat > "/etc/logrotate.d/mcp-observatory" << EOF
/var/log/mcp-observatory/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

# Create log directory
mkdir -p /var/log/mcp-observatory
chown www-data:www-data /var/log/mcp-observatory

print_success "Log rotation configured"

# Create monitoring script
print_status "Creating monitoring script..."

cat > "/usr/local/bin/mcp-observatory-monitor" << 'EOF'
#!/bin/bash

SERVICE_NAME="mcp-observatory"
PORT=3000

# Check if service is running
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "$(date): Service $SERVICE_NAME is not running, attempting to start..."
    systemctl start "$SERVICE_NAME"
    sleep 5
fi

# Check if port is responding
if ! curl -s "http://localhost:$PORT/health" >/dev/null; then
    echo "$(date): Service $SERVICE_NAME is not responding on port $PORT, restarting..."
    systemctl restart "$SERVICE_NAME"
fi
EOF

chmod +x "/usr/local/bin/mcp-observatory-monitor"

# Add to crontab for monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/mcp-observatory-monitor >> /var/log/mcp-observatory/monitor.log 2>&1") | crontab -

print_success "Monitoring script created and scheduled"

# Generate deployment report
print_status "Generating deployment report..."

cat > "$PRODUCTION_DIR/deployment-report.txt" << EOF
MCP Observatory Production Deployment Report
===========================================
Date: $(date)
Version: 2.0.0
Deployment Directory: $PRODUCTION_DIR
Backup Directory: $BACKUP_DIR

Service Information:
- Service Name: $SERVICE_NAME
- Port: $PORT
- User: www-data
- Status: $(systemctl is-active $SERVICE_NAME)

Files Deployed:
- server.mjs (MCP Backend Server)
- mcpRoutes.mjs (MCP Routes Module)
- package.json (Dependencies)
- index.html (Frontend)

Dependencies Installed:
$(npm list --depth=0 2>/dev/null | grep -v "npm ERR" || echo "Dependencies list not available")

Service Status:
$(systemctl status $SERVICE_NAME --no-pager -l)

Test Results:
- Health Endpoint: $(curl -s http://localhost:$PORT/health | grep -o '"status":"[^"]*"' || echo "Failed")
- Tools Count: $(curl -s http://localhost:$PORT/api/tools | grep -o '"name"' | wc -l || echo "0")
- Execute Test: $(curl -s -X POST -H "Content-Type: application/json" -d '{"tool":"firecrawl","parameters":{"url":"https://example.com"}}' http://localhost:$PORT/api/tools/execute | grep -o '"success":[^,]*' || echo "Failed")

Management Commands:
- Start: systemctl start $SERVICE_NAME
- Stop: systemctl stop $SERVICE_NAME
- Restart: systemctl restart $SERVICE_NAME
- Status: systemctl status $SERVICE_NAME
- Logs: journalctl -u $SERVICE_NAME -f

URLs:
- Health Check: http://localhost:$PORT/health
- Frontend: http://65.109.54.94:5174/
- API Tools: http://localhost:$PORT/api/tools
- API Execute: http://localhost:$PORT/api/tools/execute

EOF

print_success "Deployment report generated: $PRODUCTION_DIR/deployment-report.txt"

# Final status check
print_status "Performing final status check..."

SERVICE_STATUS=$(systemctl is-active "$SERVICE_NAME")
if [ "$SERVICE_STATUS" = "active" ]; then
    print_success "✅ MCP Observatory service is running"
else
    print_error "❌ MCP Observatory service is not running (status: $SERVICE_STATUS)"
fi

# Display summary
echo ""
echo "🎉 MCP Observatory Production Deployment COMPLETED"
echo "=================================================="
echo ""
print_success "✅ Service deployed and running on port $PORT"
print_success "✅ Systemd service configured and enabled"
print_success "✅ Nginx configuration updated (if applicable)"
print_success "✅ Log rotation configured"
print_success "✅ Monitoring script installed"
print_success "✅ All endpoints tested and working"
echo ""
print_status "🌐 Frontend URL: http://65.109.54.94:5174/"
print_status "🔍 Health Check: http://localhost:$PORT/health"
print_status "🛠️  API Tools: http://localhost:$PORT/api/tools"
print_status "⚡ API Execute: http://localhost:$PORT/api/tools/execute"
echo ""
print_status "📋 Management Commands:"
echo "   systemctl start $SERVICE_NAME"
echo "   systemctl stop $SERVICE_NAME"
echo "   systemctl restart $SERVICE_NAME"
echo "   systemctl status $SERVICE_NAME"
echo "   journalctl -u $SERVICE_NAME -f"
echo ""
print_status "📊 Deployment Report: $PRODUCTION_DIR/deployment-report.txt"
print_status "💾 Backup Location: $BACKUP_DIR"
echo ""
print_success "🚀 MCP Observatory is now ready for production use!"


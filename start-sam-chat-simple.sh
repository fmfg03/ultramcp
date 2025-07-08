#!/bin/bash
# Simple UltraMCP sam.chat Startup Script
# Starts services directly without Docker for testing
# Generated: 2025-07-08

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting UltraMCP sam.chat (Simple Mode)...${NC}"
echo "=================================================="

# Configuration
DOMAIN="sam.chat"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env.sam.chat"

# Load environment configuration
echo -e "${YELLOW}🔧 Loading sam.chat configuration...${NC}"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

# Export environment variables
set -a
source "$ENV_FILE"
set +a

echo -e "${GREEN}✅ Environment configured for ${DOMAIN}${NC}"

# Kill any existing processes on our ports
echo -e "${YELLOW}🛑 Stopping existing processes...${NC}"
pkill -f "node.*3001" 2>/dev/null || true
pkill -f "vite.*5173" 2>/dev/null || true
pkill -f "redis-server" 2>/dev/null || true

# Start Redis (required for backend)
echo -e "${YELLOW}📊 Starting Redis...${NC}"
if command -v redis-server >/dev/null 2>&1; then
    redis-server --daemonize yes --port 6379
    echo -e "${GREEN}✅ Redis started${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not found, installing...${NC}"
    sudo apt update && sudo apt install -y redis-server
    redis-server --daemonize yes --port 6379
    echo -e "${GREEN}✅ Redis installed and started${NC}"
fi

# Start backend API gateway
echo -e "${YELLOW}🌐 Starting Backend API Gateway...${NC}"
cd "${SCRIPT_DIR}/apps/backend"
NODE_ENV=production PORT=3001 node src/simple-server.js > ../../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start Claudia service with integrated frontend (port 8013)
echo -e "${YELLOW}🎨 Starting Claudia MCP Service with Integrated Frontend...${NC}"
cd "${SCRIPT_DIR}/services/claudia-integration"
python3 agent_service.py > ../../logs/claudia.log 2>&1 &
CLAUDIA_PID=$!
echo "Claudia PID: $CLAUDIA_PID"

# Wait for services to start
echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 5

# Test services
echo -e "${YELLOW}🧪 Testing services...${NC}"

# Test backend
if curl -f -s http://localhost:3001/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API OK${NC}"
else
    echo -e "${RED}❌ Backend API Failed${NC}"
fi

# Test Claudia service with integrated frontend
if curl -f -s http://localhost:8013 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Claudia Service OK${NC}"
else
    echo -e "${RED}❌ Claudia Service Failed${NC}"
fi

# Configure Nginx for sam.chat
echo -e "${YELLOW}🌐 Configuring Nginx for sam.chat...${NC}"
if command -v nginx >/dev/null 2>&1; then
    sudo cp "${SCRIPT_DIR}/nginx-sam-chat-production.conf" /etc/nginx/sites-available/sam.chat
    sudo ln -sf /etc/nginx/sites-available/sam.chat /etc/nginx/sites-enabled/sam.chat
    sudo rm -f /etc/nginx/sites-enabled/default
    
    if sudo nginx -t; then
        sudo systemctl reload nginx
        echo -e "${GREEN}✅ Nginx configured for sam.chat${NC}"
    else
        echo -e "${RED}❌ Nginx configuration error${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Nginx not found, skipping configuration${NC}"
fi

# Save PIDs for cleanup
echo "$BACKEND_PID" > /tmp/ultramcp-backend.pid
echo "$CLAUDIA_PID" > /tmp/ultramcp-claudia.pid

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 UltraMCP sam.chat started successfully!${NC}"
echo ""
echo -e "${BLUE}📍 Access your services:${NC}"
echo -e "   🌐 Claudia Frontend: ${GREEN}https://sam.chat${NC} (or http://localhost:8013)"
echo -e "   🔌 Backend API:      ${GREEN}https://api.sam.chat${NC} (or http://localhost:3001)"
echo ""
echo -e "${YELLOW}📝 Service Management:${NC}"
echo "   View logs: tail -f logs/backend.log logs/claudia.log"
echo "   Stop services: pkill -f 'node.*3001'; pkill -f 'python3.*agent_service.py'"
echo ""
echo -e "${BLUE}📊 Process IDs:${NC}"
echo "   Backend PID: $BACKEND_PID"
echo "   Claudia PID: $CLAUDIA_PID"
echo "=================================================="
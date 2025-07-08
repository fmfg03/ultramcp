#!/bin/bash
# UltraMCP sam.chat Deployment Script
# Starts the complete sam.chat production environment
# Generated: 2025-07-08

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="sam.chat"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env.sam.chat"

echo -e "${BLUE}🚀 UltraMCP sam.chat Deployment Starting...${NC}"
echo "=================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check service health
check_service_health() {
    local service_url="$1"
    local service_name="$2"
    
    echo -n "Checking ${service_name}... "
    if curl -f -s "$service_url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url="$1"
    local name="$2"
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for ${name} to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ${name} is ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ ${name} failed to start after ${max_attempts} attempts${NC}"
    return 1
}

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

if ! command_exists nginx; then
    echo -e "${RED}❌ Nginx is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites satisfied${NC}"

# Load environment configuration
echo -e "${YELLOW}🔧 Loading sam.chat configuration...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

# Copy environment file
cp "$ENV_FILE" "${SCRIPT_DIR}/.env"
echo -e "${GREEN}✅ Environment configured for ${DOMAIN}${NC}"

# Stop any existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose -f docker-compose.sam.chat.yml down --remove-orphans 2>/dev/null || true

# Clean up old images (optional)
echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker system prune -f

# Build and start services
echo -e "${YELLOW}🏗️  Building and starting sam.chat services...${NC}"
docker compose -f docker-compose.sam.chat.minimal.yml up -d --build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start Docker services${NC}"
    exit 1
fi

# Wait for core services to be ready
echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"

# Wait for Redis
wait_for_service "http://localhost:6379" "Redis"

# Wait for backend API
wait_for_service "http://localhost:3001/health" "Backend API Gateway"

# Wait for frontend
wait_for_service "http://localhost:5173/health" "Frontend"

# Configure Nginx for sam.chat
echo -e "${YELLOW}🌐 Configuring Nginx for sam.chat...${NC}"

# Backup existing nginx config
if [ -f /etc/nginx/nginx.conf ]; then
    sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d%H%M%S)
fi

# Copy sam.chat nginx configuration
sudo cp nginx-sam-chat-production.conf /etc/nginx/sites-available/sam.chat
sudo ln -sf /etc/nginx/sites-available/sam.chat /etc/nginx/sites-enabled/sam.chat

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if sudo nginx -t; then
    echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded with sam.chat configuration${NC}"
else
    echo -e "${RED}❌ Nginx configuration is invalid${NC}"
    exit 1
fi

# Health checks
echo -e "${YELLOW}🏥 Running health checks...${NC}"

sleep 5

# Check all services
SERVICES=(
    "http://localhost:5173/health:Frontend"
    "http://localhost:3001/health:Backend API"
    "http://localhost:8001:Chain-of-Debate"
    "http://localhost:8002:Asterisk Security"
    "http://localhost:8003:Blockoli Intelligence"
    "http://localhost:8004:Voice System"
    "http://localhost:8005:Memory Service"
    "http://localhost:8006:DeepClaude"
    "http://localhost:8007:Control Tower"
    "http://localhost:8013:Claudia Integration"
)

ALL_HEALTHY=true
for service in "${SERVICES[@]}"; do
    IFS=':' read -r url name <<< "$service"
    if ! check_service_health "$url" "$name"; then
        ALL_HEALTHY=false
    fi
done

# Display status
echo ""
echo "=================================================="
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}🎉 UltraMCP sam.chat deployment successful!${NC}"
    echo ""
    echo -e "${BLUE}📍 Access your services:${NC}"
    echo -e "   🌐 Frontend: ${GREEN}https://sam.chat${NC}"
    echo -e "   🔌 API:      ${GREEN}https://api.sam.chat${NC}"
    echo -e "   🎛️  Studio:   ${GREEN}https://studio.sam.chat${NC}"
    echo -e "   🔭 Observatory: ${GREEN}https://observatory.sam.chat${NC}"
    echo ""
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "   1. Configure DNS to point sam.chat subdomains to this server"
    echo "   2. Install SSL certificates with: sudo certbot --nginx"
    echo "   3. Update Nginx config to enable HTTPS redirects"
    echo ""
    echo -e "${BLUE}📊 Monitor services:${NC}"
    echo "   docker-compose -f docker-compose.sam.chat.yml logs -f"
    echo "   docker-compose -f docker-compose.sam.chat.yml ps"
else
    echo -e "${RED}⚠️  Some services are not healthy${NC}"
    echo "Check logs with: docker-compose -f docker-compose.sam.chat.yml logs"
fi

echo "=================================================="

# Display container status
echo -e "${BLUE}📋 Container Status:${NC}"
docker-compose -f docker-compose.sam.chat.yml ps

echo ""
echo -e "${GREEN}✅ sam.chat deployment script completed${NC}"
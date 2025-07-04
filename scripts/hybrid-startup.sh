#!/bin/bash

# UltraMCP Hybrid System Startup Script
# Terminal-first approach with Docker orchestration
source "$(dirname "$0")/common.sh"

echo "🚀 UltraMCP Hybrid System Startup"
echo "=================================="
echo ""

# Check prerequisites
log_info "hybrid-startup" "Checking system prerequisites"

# Check Docker
if ! command -v docker >/dev/null; then
    handle_error "hybrid-startup" "DOCKER_NOT_FOUND" "Docker not installed" '["Install Docker", "Add Docker to PATH", "Verify Docker service is running"]'
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose >/dev/null && ! docker compose version >/dev/null 2>&1; then
    handle_error "hybrid-startup" "DOCKER_COMPOSE_NOT_FOUND" "Docker Compose not available" '["Install Docker Compose plugin", "Use docker-compose binary", "Update Docker to latest version"]'
    exit 1
fi

# Detect Docker Compose command
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

log_info "hybrid-startup" "Using Docker Compose command: $DOCKER_COMPOSE"

# Check .env file
if [ ! -f ".env" ]; then
    log_info "hybrid-startup" "Creating .env file from template"
    
    # Create .env with secure defaults
    cat > .env << EOF
# UltraMCP Hybrid System Configuration
# Generated on $(date -Iseconds)

# Database Configuration
POSTGRES_PASSWORD=ultramcp_secure_$(date +%s)
POSTGRES_DB=ultramcp
POSTGRES_USER=ultramcp

# Redis Configuration  
REDIS_PASSWORD=redis_secure_$(date +%s)

# CoD Protocol Service
COD_SERVICE_PORT=8001

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Security
JWT_SECRET=jwt_secret_$(date +%s)
SESSION_SECRET=session_secret_$(date +%s)

# Development/Production Mode
NODE_ENV=development
PYTHONPATH=/app

# Logging
LOG_LEVEL=info
EOF

    echo "✅ Created .env file with secure defaults"
    echo "⚠️  Please update API keys in .env file"
else
    echo "✅ .env file already exists"
fi

# Ensure data directories exist
log_info "hybrid-startup" "Creating data directories"
ensure_directory "data/debates"
ensure_directory "data/scrapes" 
ensure_directory "data/research"
ensure_directory "data/analysis"
ensure_directory "logs"

# Show startup options
echo ""
echo "🎯 UltraMCP Startup Options:"
echo "==========================="
echo "1. 🐳 Full Docker setup (Recommended)"
echo "2. 🧠 CoD Protocol service only"
echo "3. 🔧 Development mode with hot reload"
echo "4. 📊 Status check of running services"
echo "5. 🛑 Stop all services"
echo ""

read -p "Choose option [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "🐳 Starting Full Docker Hybrid System"
        echo "====================================="
        
        log_info "hybrid-startup" "Starting full Docker stack"
        
        # Pull latest images
        echo "📥 Pulling Docker images..."
        $DOCKER_COMPOSE pull
        
        # Build custom images
        echo "🔨 Building UltraMCP images..."
        $DOCKER_COMPOSE build
        
        # Start services
        echo "🚀 Starting all services..."
        $DOCKER_COMPOSE up -d
        
        # Wait for services
        echo "⏳ Waiting for services to be ready..."
        sleep 10
        
        # Check service health
        echo ""
        echo "🔍 Service Health Check:"
        echo "======================="
        
        if curl -s http://sam.chat:8001/health >/dev/null; then
            echo "✅ CoD Protocol Service: Healthy (http://sam.chat:8001)"
        else
            echo "❌ CoD Protocol Service: Not responding"
        fi
        
        if curl -s http://sam.chat:3000/health >/dev/null 2>&1; then
            echo "✅ Web Dashboard: Healthy (http://sam.chat:3000)"
        else
            echo "⚠️  Web Dashboard: Optional service not available"
        fi
        
        echo ""
        echo "🎉 UltraMCP Hybrid System is running!"
        echo "=================================="
        echo "📖 Available commands:"
        echo "  make help          - Show all available commands"
        echo "  make chat          - Quick AI chat (80% terminal)"
        echo "  make debate        - Advanced multi-LLM debate (20% orchestration)"
        echo "  make web-scrape    - Scrape web content"
        echo "  make research      - Full web research with AI analysis"
        echo "  make status        - Check system status"
        echo ""
        echo "🌐 Web interfaces:"
        echo "  CoD Protocol API: http://sam.chat:8001"
        echo "  System Dashboard: http://sam.chat:3000 (if available)"
        echo ""
        log_success "hybrid-startup" "Full Docker system started successfully"
        ;;
        
    2)
        echo ""
        echo "🧠 Starting CoD Protocol Service Only"
        echo "====================================="
        
        log_info "hybrid-startup" "Starting CoD Protocol service only"
        
        # Start only the essential services
        $DOCKER_COMPOSE up -d postgres redis cod-service
        
        echo "⏳ Waiting for CoD Protocol service..."
        sleep 5
        
        if curl -s http://sam.chat:8001/health >/dev/null; then
            echo "✅ CoD Protocol Service is running on http://sam.chat:8001"
            log_success "hybrid-startup" "CoD Protocol service started"
            
            echo ""
            echo "🎯 Terminal-first commands available:"
            echo "  make chat PROMPT='your question'"
            echo "  make debate TOPIC='your debate topic'"
            echo "  make web-scrape URL='https://example.com'"
        else
            echo "❌ CoD Protocol Service failed to start"
            log_error "hybrid-startup" "Service start failed"
        fi
        ;;
        
    3)
        echo ""
        echo "🔧 Starting Development Mode"
        echo "============================"
        
        log_info "hybrid-startup" "Starting development mode with hot reload"
        
        # Use development override
        $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up -d
        
        echo "⏳ Waiting for development services..."
        sleep 10
        
        echo "🔧 Development services started!"
        echo "  Backend: http://sam.chat:3001 (with hot reload)"
        echo "  DevTool: http://sam.chat:5174"
        echo "  Studio: http://sam.chat:8124"
        echo "  CoD Service: http://sam.chat:8001"
        
        log_success "hybrid-startup" "Development mode started"
        ;;
        
    4)
        echo ""
        echo "📊 System Status Check"
        echo "====================="
        
        log_info "hybrid-startup" "Checking system status"
        
        # Check Docker containers
        echo "🐳 Docker Containers:"
        $DOCKER_COMPOSE ps
        echo ""
        
        # Check services
        echo "🔍 Service Health:"
        services=(
            "http://sam.chat:8001/health:CoD Protocol"
            "http://sam.chat:3000:Web Dashboard"
            "http://sam.chat:5432:PostgreSQL"
            "http://sam.chat:6379:Redis"
        )
        
        for service in "${services[@]}"; do
            url="${service%:*}"
            name="${service#*:}"
            
            if curl -s "$url" >/dev/null 2>&1; then
                echo "  ✅ $name: Healthy"
            else
                echo "  ❌ $name: Not responding"
            fi
        done
        
        echo ""
        echo "📊 System Resources:"
        echo "  CPU Usage: $(top -l 1 | grep "CPU usage" | awk '{print $3}' 2>/dev/null || echo "N/A")"
        echo "  Memory: $(free -h 2>/dev/null | grep "Mem:" | awk '{print $3"/"$2}' || echo "N/A")"
        echo "  Disk: $(df -h . | tail -1 | awk '{print $5}' 2>/dev/null || echo "N/A")"
        ;;
        
    5)
        echo ""
        echo "🛑 Stopping All Services"
        echo "======================="
        
        log_info "hybrid-startup" "Stopping all services"
        
        # Stop all services
        $DOCKER_COMPOSE down
        
        # Also stop any dev services
        $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null
        
        echo "✅ All services stopped"
        log_success "hybrid-startup" "All services stopped"
        ;;
        
    *)
        echo "❌ Invalid option. Please choose 1-5."
        exit 1
        ;;
esac

echo ""
log_success "hybrid-startup" "Startup script completed"
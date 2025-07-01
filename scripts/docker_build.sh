#!/bin/bash
# Optimized Docker Build Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Build arguments
ENVIRONMENT=${1:-development}
BUILD_CACHE=${BUILD_CACHE:-true}

log_info "Building MCP System for environment: $ENVIRONMENT"

# Build options
BUILD_OPTS=""
if [[ "$BUILD_CACHE" == "false" ]]; then
    BUILD_OPTS="--no-cache"
fi

# Build backend
log_info "Building backend..."
docker build $BUILD_OPTS -f Dockerfile.backend -t mcp-backend:latest .
log_success "Backend built successfully"

# Build studio
log_info "Building studio..."
docker build $BUILD_OPTS -f Dockerfile.studio -t mcp-studio:latest .
log_success "Studio built successfully"

# Build devtool
log_info "Building devtool..."
docker build $BUILD_OPTS -f Dockerfile.devtool -t mcp-devtool:latest .
log_success "DevTool built successfully"

log_success "All services built successfully!"

# Optional: Run quick test
if [[ "$ENVIRONMENT" == "test" ]]; then
    log_info "Running quick container tests..."
    
    # Test backend
    docker run --rm -d --name mcp-backend-test mcp-backend:latest
    sleep 5
    if docker ps | grep -q mcp-backend-test; then
        log_success "Backend container test passed"
        docker stop mcp-backend-test
    fi
    
    # Test studio
    docker run --rm -d --name mcp-studio-test mcp-studio:latest
    sleep 5
    if docker ps | grep -q mcp-studio-test; then
        log_success "Studio container test passed"
        docker stop mcp-studio-test
    fi
    
    # Test devtool
    docker run --rm -d --name mcp-devtool-test mcp-devtool:latest
    sleep 5
    if docker ps | grep -q mcp-devtool-test; then
        log_success "DevTool container test passed"
        docker stop mcp-devtool-test
    fi
fi

log_success "Build process completed!"

#!/bin/bash
# Docker Build Fix Script
# Fixes common Docker build issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

fix_keys_directory() {
    log_info "Fixing keys directory issue..."
    
    # Create keys directory if it doesn't exist
    if [[ ! -d "keys" ]]; then
        mkdir -p keys
        log_success "Created keys directory"
    fi
    
    # Create a placeholder file to ensure directory exists in git
    if [[ ! -f "keys/.gitkeep" ]]; then
        touch keys/.gitkeep
        log_success "Created keys/.gitkeep placeholder"
    fi
    
    # Update .gitignore to keep .gitkeep but ignore actual keys
    if [[ -f ".gitignore" ]]; then
        if ! grep -q "keys/\*" .gitignore; then
            echo "" >> .gitignore
            echo "# Keys directory - keep structure but ignore actual keys" >> .gitignore
            echo "keys/*" >> .gitignore
            echo "!keys/.gitkeep" >> .gitignore
            log_success "Updated .gitignore for keys directory"
        fi
    fi
}

test_docker_builds() {
    log_info "Testing Docker builds..."
    
    local dockerfiles=("Dockerfile.backend" "Dockerfile.studio" "Dockerfile.devtool")
    local build_success=true
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$dockerfile" ]]; then
            log_info "Testing $dockerfile..."
            
            # Dry run build to check for syntax errors
            if docker build --dry-run -f "$dockerfile" . > /dev/null 2>&1; then
                log_success "$dockerfile: Build syntax OK"
            else
                log_error "$dockerfile: Build syntax error"
                build_success=false
            fi
        else
            log_warning "$dockerfile: File not found"
        fi
    done
    
    if [[ "$build_success" == "true" ]]; then
        log_success "All Dockerfiles passed syntax check"
    else
        log_error "Some Dockerfiles have syntax errors"
    fi
}

check_docker_context() {
    log_info "Checking Docker build context..."
    
    # Check for large files that shouldn't be in context
    local large_files=$(find . -type f -size +100M 2>/dev/null | grep -v ".git" | head -5)
    
    if [[ -n "$large_files" ]]; then
        log_warning "Large files found in build context:"
        echo "$large_files"
        log_info "Consider adding these to .dockerignore"
    else
        log_success "No large files in build context"
    fi
    
    # Check .dockerignore exists
    if [[ -f ".dockerignore" ]]; then
        log_success ".dockerignore file exists"
    else
        log_warning ".dockerignore file missing"
    fi
}

fix_common_issues() {
    log_info "Fixing common Docker issues..."
    
    # Ensure all scripts are executable
    find scripts/ -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
    log_success "Made scripts executable"
    
    # Create required directories
    local required_dirs=("logs" "uploads" "temp" "keys" "docker/nginx" "docker/postgres" "docker/redis")
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        fi
    done
    
    # Create placeholder files for empty directories
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" && -z "$(ls -A "$dir" 2>/dev/null)" ]]; then
            touch "$dir/.gitkeep"
            log_success "Created placeholder in: $dir"
        fi
    done
}

generate_build_script() {
    log_info "Generating optimized build script..."
    
    cat > "scripts/docker_build.sh" << 'EOF'
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
EOF
    
    chmod +x "scripts/docker_build.sh"
    log_success "Created optimized build script: scripts/docker_build.sh"
}

main() {
    echo "🔧 Docker Build Fix"
    echo "==================="
    echo ""
    
    fix_keys_directory
    echo ""
    
    fix_common_issues
    echo ""
    
    check_docker_context
    echo ""
    
    test_docker_builds
    echo ""
    
    generate_build_script
    echo ""
    
    log_success "Docker build fixes completed!"
    log_info "You can now run: docker-compose build"
    log_info "Or use the optimized script: ./scripts/docker_build.sh"
}

main "$@"


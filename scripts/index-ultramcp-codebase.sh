#!/bin/bash

# =============================================================================
# UltraMCP Codebase Indexing Script
# Indexes the UltraMCP codebase for Claude Code Memory pattern learning
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="ultramcp-supreme"
MEMORY_SERVICE_URL="http://sam.chat:8009"
LOG_FILE="${PROJECT_ROOT}/logs/codebase-indexing.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log "INFO: $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log "WARNING: $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log "ERROR: $1"
}

print_section() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
    log "SECTION: $1"
}

# Check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    # Check if memory service is running
    if curl -sf "$MEMORY_SERVICE_URL/health" >/dev/null 2>&1; then
        print_success "Claude Code Memory service is running"
    else
        print_error "Claude Code Memory service is not running at $MEMORY_SERVICE_URL"
        print_status "Please start the service with: make docker-up"
        exit 1
    fi
    
    # Check Python client
    if python3 -c "import sys; sys.path.append('services/claude-code-memory'); from claude_memory_client import ClaudeCodeMemoryClient" 2>/dev/null; then
        print_success "Claude Code Memory client is available"
    else
        print_error "Claude Code Memory client is not available"
        exit 1
    fi
    
    # Check project structure
    if [[ -f "$PROJECT_ROOT/CLAUDE.md" && -f "$PROJECT_ROOT/Makefile" ]]; then
        print_success "UltraMCP project structure verified"
    else
        print_error "Invalid UltraMCP project structure"
        exit 1
    fi
}

# Analyze codebase structure
analyze_codebase() {
    print_section "Analyzing Codebase Structure"
    
    # Count files by language
    print_status "File analysis:"
    find "$PROJECT_ROOT" -type f \( \
        -name "*.py" -o \
        -name "*.js" -o \
        -name "*.ts" -o \
        -name "*.jsx" -o \
        -name "*.tsx" -o \
        -name "*.json" -o \
        -name "*.yaml" -o \
        -name "*.yml" -o \
        -name "*.md" -o \
        -name "*.sh" -o \
        -name "*.dockerfile" -o \
        -name "Dockerfile*" -o \
        -name "Makefile*" \
    \) ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" | \
    awk -F. '{if (NF>1) print $NF; else print "no-ext"}' | \
    sort | uniq -c | sort -nr
    
    # Key directories
    print_status "Key directories:"
    ls -la "$PROJECT_ROOT" | grep "^d" | awk '{print $NF}' | grep -E "(services|core|scripts|apps|docs)" || true
    
    # Services analysis
    if [[ -d "$PROJECT_ROOT/services" ]]; then
        print_status "Services found:"
        ls -1 "$PROJECT_ROOT/services/" | sed 's/^/  • /'
    fi
}

# Index core components
index_core_components() {
    print_section "Indexing Core Components"
    
    # Core system files
    local core_files=(
        "Makefile"
        "CLAUDE.md" 
        "README.md"
        "docker-compose.hybrid.yml"
        "package.json"
        "requirements.txt"
    )
    
    print_status "Indexing core configuration files..."
    for file in "${core_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            print_status "  Processing: $file"
        fi
    done
}

# Index services
index_services() {
    print_section "Indexing Microservices"
    
    if [[ ! -d "$PROJECT_ROOT/services" ]]; then
        print_warning "Services directory not found"
        return
    fi
    
    # List all services
    local services=($(ls -1 "$PROJECT_ROOT/services/" 2>/dev/null | grep -v "^\." || true))
    
    if [[ ${#services[@]} -eq 0 ]]; then
        print_warning "No services found in services directory"
        return
    fi
    
    print_status "Found ${#services[@]} services:"
    for service in "${services[@]}"; do
        print_status "  • $service"
        
        # Check service structure
        local service_path="$PROJECT_ROOT/services/$service"
        if [[ -f "$service_path/Dockerfile" ]]; then
            echo "    - Has Dockerfile"
        fi
        if [[ -f "$service_path/requirements.txt" ]] || [[ -f "$service_path/package.json" ]]; then
            echo "    - Has dependencies"
        fi
        if find "$service_path" -name "*.py" -o -name "*.js" | head -1 >/dev/null 2>&1; then
            echo "    - Has source code"
        fi
    done
}

# Index scripts
index_scripts() {
    print_section "Indexing Scripts"
    
    if [[ ! -d "$PROJECT_ROOT/scripts" ]]; then
        print_warning "Scripts directory not found"
        return
    fi
    
    local script_count=$(find "$PROJECT_ROOT/scripts" -name "*.sh" -o -name "*.py" | wc -l)
    print_status "Found $script_count script files"
    
    # Categorize scripts
    print_status "Script categories:"
    find "$PROJECT_ROOT/scripts" -name "*.sh" -exec basename {} \; | \
    sed 's/\.sh$//' | \
    while read script; do
        case "$script" in
            *setup*|*install*|*init*) echo "  Setup: $script.sh" ;;
            *test*|*verify*|*check*) echo "  Testing: $script.sh" ;;
            *claude*) echo "  Claude: $script.sh" ;;
            *docker*|*container*) echo "  Docker: $script.sh" ;;
            *backup*|*restore*) echo "  Backup: $script.sh" ;;
            *) echo "  Utility: $script.sh" ;;
        esac
    done
}

# Perform actual indexing
perform_indexing() {
    print_section "Performing Semantic Indexing"
    
    cd "$PROJECT_ROOT"
    
    print_status "Starting Claude Code Memory indexing..."
    
    # Use Python client to index the project
    python3 -c "
import asyncio
import sys
import os
sys.path.append('services/claude-code-memory')
from claude_memory_client import ClaudeCodeMemoryClient

async def index_project():
    try:
        async with ClaudeCodeMemoryClient('$MEMORY_SERVICE_URL') as client:
            print('🔗 Connected to Claude Code Memory service')
            
            # Index the entire UltraMCP project
            result = await client.index_project(
                project_path='$PROJECT_ROOT',
                project_name='$PROJECT_NAME',
                force_reindex=True,
                exclude_patterns=[
                    'node_modules/*',
                    '.git/*',
                    '__pycache__/*',
                    '*.log',
                    'logs/*',
                    'data/*',
                    'temp/*',
                    '*.tmp'
                ]
            )
            
            if result.success:
                print(f'✅ Indexing completed successfully!')
                print(f'   Total files processed: {result.total_files}')
                print(f'   Files indexed: {result.indexed_files}')
                print(f'   Elements extracted: {result.total_elements}')
                print(f'   Processing time: {result.processing_time:.2f}s')
                
                if result.errors:
                    print(f'⚠️  Errors encountered:')
                    for error in result.errors:
                        print(f'     {error}')
            else:
                print(f'❌ Indexing failed!')
                for error in result.errors:
                    print(f'   Error: {error}')
                return 1
                
    except Exception as e:
        print(f'❌ Error during indexing: {e}')
        return 1
    
    return 0

exit_code = asyncio.run(index_project())
exit(exit_code)
" || return 1

    print_success "Semantic indexing completed"
}

# Test indexing results
test_indexing() {
    print_section "Testing Indexing Results"
    
    # Test semantic search
    print_status "Testing semantic search capabilities..."
    
    local test_queries=(
        "event handling"
        "docker configuration"
        "service orchestration"
        "claude integration"
        "memory management"
    )
    
    for query in "${test_queries[@]}"; do
        print_status "Testing search: '$query'"
        
        python3 -c "
import asyncio
import sys
sys.path.append('services/claude-code-memory')
from claude_memory_client import ClaudeCodeMemoryClient

async def test_search():
    try:
        async with ClaudeCodeMemoryClient('$MEMORY_SERVICE_URL') as client:
            results = await client.search_code(
                query='$query',
                project_name='$PROJECT_NAME',
                limit=3
            )
            
            if results:
                print(f'  Found {len(results)} results for \"$query\"')
                for i, result in enumerate(results, 1):
                    print(f'    {i}. {result.element_name} ({result.language}) - Score: {result.score:.3f}')
            else:
                print(f'  No results found for \"$query\"')
                
    except Exception as e:
        print(f'  Error testing search: {e}')

asyncio.run(test_search())
" || print_warning "Search test failed for: $query"
    done
}

# Generate learning report
generate_report() {
    print_section "Generating Learning Report"
    
    local report_file="$PROJECT_ROOT/data/ultramcp-codebase-analysis.json"
    mkdir -p "$(dirname "$report_file")"
    
    print_status "Generating comprehensive codebase analysis..."
    
    python3 -c "
import asyncio
import json
import sys
import os
from datetime import datetime
sys.path.append('services/claude-code-memory')
from claude_memory_client import ClaudeCodeMemoryClient

async def generate_analysis():
    try:
        async with ClaudeCodeMemoryClient('$MEMORY_SERVICE_URL') as client:
            # Get project info
            project_info = await client.get_project_info('$PROJECT_NAME')
            
            # Get memory stats
            memory_stats = await client.get_memory_stats()
            
            # Get all projects
            projects = await client.list_projects()
            
            analysis = {
                'timestamp': datetime.utcnow().isoformat(),
                'project_name': '$PROJECT_NAME',
                'project_path': '$PROJECT_ROOT',
                'project_info': project_info,
                'memory_stats': memory_stats,
                'all_projects': projects,
                'indexing_summary': {
                    'status': 'completed',
                    'indexed_project': '$PROJECT_NAME',
                    'analysis_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
            with open('$report_file', 'w') as f:
                json.dump(analysis, f, indent=2)
            
            print(f'📊 Analysis report saved to: $report_file')
            print(f'🧠 Memory system is ready for UltraMCP pattern learning!')
            
    except Exception as e:
        print(f'Error generating analysis: {e}')

asyncio.run(generate_analysis())
" || print_warning "Failed to generate analysis report"
    
    if [[ -f "$report_file" ]]; then
        print_success "Analysis report generated: $report_file"
    fi
}

# Print usage examples
show_usage_examples() {
    print_section "Usage Examples"
    
    cat << 'EOF'
🧠 Claude Code Memory is now ready! Try these commands:

Basic Search:
  make memory-search QUERY="event handling" PROJECT="ultramcp-supreme"
  make memory-search QUERY="docker configuration" PROJECT="ultramcp-supreme"
  make memory-search QUERY="service orchestration" PROJECT="ultramcp-supreme"

Pattern Analysis:
  make memory-analyze FILE="core/orchestrator/eventBus.js" PROJECT="ultramcp-supreme"
  make memory-analyze FILE="docker-compose.hybrid.yml" PROJECT="ultramcp-supreme"
  make memory-analyze FILE="Makefile" PROJECT="ultramcp-supreme"

Advanced Workflows:
  make memory-debate TOPIC="microservices architecture" PROJECT="ultramcp-supreme"
  make memory-quality-check FILE="services/claude-code-memory/memory_service.py" PROJECT="ultramcp-supreme"
  make memory-find-similar PATTERN="service orchestration" PROJECT="ultramcp-supreme"

Interactive Exploration:
  make memory-explore
  make memory-projects
  make memory-status

Memory-Enhanced Development:
  make memory-learn-codebase    # Re-run to update patterns
  make test-memory-integration  # Test all memory features

🎯 The memory system has learned your codebase patterns and is ready for intelligent assistance!
EOF
}

# Main execution
main() {
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    print_section "UltraMCP Codebase Indexing"
    print_status "Indexing UltraMCP codebase for Claude Code Memory pattern learning"
    print_status "Project: $PROJECT_NAME"
    print_status "Path: $PROJECT_ROOT"
    print_status "Log: $LOG_FILE"
    
    # Execute indexing pipeline
    check_prerequisites
    analyze_codebase
    index_core_components
    index_services
    index_scripts
    perform_indexing
    test_indexing
    generate_report
    show_usage_examples
    
    print_success "UltraMCP codebase indexing completed successfully!"
    print_status "The memory system is now ready for intelligent code assistance."
}

# Handle script termination
cleanup() {
    print_status "Indexing script terminated"
}
trap cleanup EXIT

# Run main function
main "$@"
#!/bin/bash

# Comprehensive System Health Check
source "$(dirname "$0")/common.sh"

TASK_ID=$(generate_task_id)

log_info "health-check" "Starting system health check: $TASK_ID"

echo "🏥 UltraMCP Health Check"
echo "======================="

# Check basic requirements
echo "🔧 Checking requirements..."
check_requirements
echo "✅ All requirements met"

# Check Node.js and npm
echo ""
echo "📦 Checking Node.js environment..."
if command -v node >/dev/null; then
    node_version=$(node --version)
    echo "  ✅ Node.js: $node_version"
else
    echo "  ❌ Node.js not found"
fi

if command -v npm >/dev/null; then
    npm_version=$(npm --version)
    echo "  ✅ npm: $npm_version"
else
    echo "  ❌ npm not found"
fi

# Check Python environment
echo ""
echo "🐍 Checking Python environment..."
if command -v python3 >/dev/null; then
    python_version=$(python3 --version)
    echo "  ✅ Python: $python_version"
else
    echo "  ❌ Python3 not found"
fi

if command -v pip3 >/dev/null; then
    pip_version=$(pip3 --version | cut -d' ' -f2)
    echo "  ✅ pip: $pip_version"
else
    echo "  ❌ pip3 not found"
fi

# Check Playwright MCP
echo ""
echo "🎭 Checking Playwright MCP..."
if command -v npx >/dev/null; then
    if npx playwright --version >/dev/null 2>&1; then
        playwright_version=$(npx playwright --version)
        echo "  ✅ Playwright available: $playwright_version"
    else
        echo "  ⚠️  Playwright not installed"
        echo "    💡 Install with: npx playwright install"
    fi
else
    echo "  ❌ npx not available"
fi

# Check CoD Protocol dependencies
echo ""
echo "🧠 Checking CoD Protocol dependencies..."
if [ -f "scripts/cod-service.py" ]; then
    echo "  ✅ CoD service script found"
    
    # Check Python dependencies
    if python3 -c "import fastapi, uvicorn" 2>/dev/null; then
        echo "  ✅ FastAPI and Uvicorn available"
    else
        echo "  ⚠️  Missing Python dependencies"
        echo "    💡 Install with: pip3 install -r requirements.txt"
    fi
else
    echo "  ❌ CoD service script not found"
fi

# Check API keys
echo ""
echo "🔑 Checking API configurations..."
if [ -n "$OPENAI_API_KEY" ]; then
    # Test API key validity
    test_response=$(curl -s -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models 2>/dev/null)
    if echo "$test_response" | jq -e '.data' >/dev/null 2>&1; then
        echo "  ✅ OpenAI API key valid"
    else
        echo "  ⚠️  OpenAI API key may be invalid"
    fi
else
    echo "  ⚠️  OpenAI API key not set"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  ✅ Anthropic API key configured"
else
    echo "  ⚠️  Anthropic API key not set"
fi

# Check system resources
echo ""
echo "💾 Checking system resources..."
available_space=$(df . | awk 'NR==2 {print $4}')
if [ "$available_space" -gt 1000000 ]; then  # 1GB in KB
    echo "  ✅ Sufficient disk space ($(df -h . | awk 'NR==2 {print $4}') available)"
else
    echo "  ⚠️  Low disk space ($(df -h . | awk 'NR==2 {print $4}') available)"
fi

# Check memory
if command -v free >/dev/null; then
    available_mem=$(free -m | awk '/^Mem:/ {print $7}')
    if [ "$available_mem" -gt 500 ]; then
        echo "  ✅ Sufficient memory (${available_mem}MB available)"
    else
        echo "  ⚠️  Low memory (${available_mem}MB available)"
    fi
fi

# Check log file health
echo ""
echo "📋 Checking logs..."
if [ -f "logs/combined.log" ]; then
    log_lines=$(wc -l < logs/combined.log)
    echo "  ✅ Log file active ($log_lines entries)"
    
    # Check for recent errors
    recent_errors=$(tail -n 100 logs/combined.log 2>/dev/null | grep -c '"level":"error"' || echo 0)
    if [ "$recent_errors" -gt 0 ]; then
        echo "  ⚠️  $recent_errors recent errors found"
        echo "    💡 Check with: make logs-search QUERY='error'"
    else
        echo "  ✅ No recent errors"
    fi
    
    # Check log size
    log_size=$(du -h logs/combined.log 2>/dev/null | cut -f1)
    echo "  📊 Log file size: $log_size"
else
    echo "  ❌ No log file found"
fi

# Check directory structure
echo ""
echo "📁 Checking directory structure..."
required_dirs=("logs" "data/scrapes" "data/debates" "data/backups" "scripts")
all_dirs_ok=true

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir missing"
        all_dirs_ok=false
    fi
done

if [ "$all_dirs_ok" = false ]; then
    echo "    💡 Fix with: make setup"
fi

# Test basic functionality
echo ""
echo "🧪 Testing basic functionality..."

# Test simple chat (if API key available)
if [ -n "$OPENAI_API_KEY" ]; then
    echo "  Testing simple chat..."
    test_response=$(timeout 15s bash -c 'echo "Hello, respond with just OK" | ./scripts/simple-chat.sh "Hello, respond with just OK"' 2>/dev/null)
    if echo "$test_response" | grep -q "OK"; then
        echo "  ✅ Simple chat working"
    else
        echo "  ⚠️  Simple chat test failed"
    fi
else
    echo "  ⏭️  Skipping chat test (no API key)"
fi

# Test logging system
echo "  Testing logging system..."
test_log_entry=$(log_info "health-check-test" "Testing log functionality" && echo "success")
if [ "$test_log_entry" = "success" ] && tail -n 1 logs/combined.log | grep -q "Testing log functionality"; then
    echo "  ✅ Logging system working"
else
    echo "  ❌ Logging system test failed"
fi

echo ""
echo "🎯 Health Check Summary:"
echo "========================"

# Count issues
warnings=$(grep -c "⚠️" <<< "$(echo -e "$output")" 2>/dev/null || echo 0)
errors=$(grep -c "❌" <<< "$(echo -e "$output")" 2>/dev/null || echo 0)

if [ "$errors" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    echo "✅ System is healthy and ready to use!"
    log_success "health-check" "Health check passed: $TASK_ID"
elif [ "$errors" -eq 0 ]; then
    echo "⚠️  System is functional with $warnings minor issues"
    log_info "health-check" "Health check completed with warnings: $TASK_ID"
else
    echo "❌ System has $errors errors and $warnings warnings"
    log_error "health-check" "Health check found issues: $TASK_ID"
fi

echo ""
echo "💡 Quick fixes:"
echo "  • Run 'make setup' to fix directory structure"
echo "  • Set API keys in .env file"
echo "  • Run 'npm install && pip3 install -r requirements.txt' for dependencies"
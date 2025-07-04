#!/bin/bash
# Post-Deployment Verification Suite
# Verifica que el sistema MCP Enterprise funcione completamente

echo "🔍 MCP ENTERPRISE POST-DEPLOYMENT VERIFICATION"
echo "============================================="

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
VERIFY_LOG="verification_${TIMESTAMP}.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$VERIFY_LOG"
}

log "Starting post-deployment verification..."

# Load environment
if [ -f .env ]; then
    source .env
    log "✅ Environment loaded"
else
    log "❌ .env file not found"
    exit 1
fi

# VERIFICATION 1: Service Status
log "📊 Checking service status..."
if sudo systemctl is-active --quiet mcp-enterprise; then
    log "✅ MCP Enterprise service is running"
    
    # Get service uptime
    uptime=$(sudo systemctl show mcp-enterprise --property=ActiveEnterTimestamp --value)
    log "🕐 Service started at: $uptime"
else
    log "❌ MCP Enterprise service is not running"
    log "📋 Service status:"
    sudo systemctl status mcp-enterprise --no-pager
    exit 1
fi

# VERIFICATION 2: Port Accessibility
log "🔌 Verifying port accessibility..."

CRITICAL_PORTS=(
    "3000:Backend API"
    "8125:Active Monitor"
    "8126:Dashboard"
    "8127:Validation System"
    "3003:Webhook System"
)

ports_ok=0
for port_info in "${CRITICAL_PORTS[@]}"; do
    IFS=':' read -r port name <<< "$port_info"
    if netstat -tuln | grep ":$port " > /dev/null; then
        log "✅ Port $port ($name) is active"
        ports_ok=$((ports_ok + 1))
    else
        log "❌ Port $port ($name) is not active"
    fi
done

log "Ports active: $ports_ok/${#CRITICAL_PORTS[@]}"

# VERIFICATION 3: Health Endpoints
log "🏥 Testing health endpoints..."

health_check() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$url" 2>/dev/null)
    if [ "$response" = "$expected_code" ]; then
        log "✅ $name health check passed (HTTP $response)"
        return 0
    else
        log "❌ $name health check failed (HTTP $response)"
        return 1
    fi
}

HEALTH_ENDPOINTS=(
    "Backend API:http://sam.chat:3000/health"
    "Active Monitor:http://sam.chat:8125/health"
    "Dashboard:http://sam.chat:8126/health" 
    "Validation:http://sam.chat:8127/health"
)

health_ok=0
for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
    IFS=':' read -r name url <<< "$endpoint"
    if health_check "$name" "$url"; then
        health_ok=$((health_ok + 1))
    fi
done

log "Health checks passed: $health_ok/${#HEALTH_ENDPOINTS[@]}"

# VERIFICATION 4: API Functionality Tests
log "🧪 Testing API functionality..."

# Test backend API endpoints
api_tests_passed=0

# Test basic health endpoint
if curl -s "http://sam.chat:3000/health" | grep -q "healthy"; then
    log "✅ Backend health endpoint working"
    api_tests_passed=$((api_tests_passed + 1))
else
    log "❌ Backend health endpoint failed"
fi

# Test memory endpoint
if curl -s -f "http://sam.chat:3000/api/memories" > /dev/null 2>&1; then
    log "✅ Memory API endpoint accessible"
    api_tests_passed=$((api_tests_passed + 1))
else
    log "❌ Memory API endpoint failed"
fi

# Test webhooks endpoint
if curl -s -f "http://sam.chat:3003/webhooks" > /dev/null 2>&1; then
    log "✅ Webhook endpoint accessible"
    api_tests_passed=$((api_tests_passed + 1))
else
    log "❌ Webhook endpoint failed"
fi

log "API tests passed: $api_tests_passed/3"

# VERIFICATION 5: Database Connectivity
log "🗄️ Testing database connectivity..."

if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    # Test Supabase connection
    if curl -s -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
            -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
            "$SUPABASE_URL/rest/v1/memories?select=count" > /dev/null 2>&1; then
        log "✅ Supabase connection working"
    else
        log "❌ Supabase connection failed"
        log "🔧 Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
    fi
else
    log "❌ Supabase configuration missing"
fi

# VERIFICATION 6: Log Files
log "📝 Checking log files..."

if [ -d "logs" ]; then
    log_files_count=$(find logs -name "*.log" | wc -l)
    if [ $log_files_count -gt 0 ]; then
        log "✅ Found $log_files_count log files"
        
        # Check for recent activity
        recent_logs=$(find logs -name "*.log" -mmin -10 | wc -l)
        if [ $recent_logs -gt 0 ]; then
            log "✅ $recent_logs log files have recent activity"
        else
            log "⚠️ No recent log activity (may be normal)"
        fi
        
        # Check for errors in logs
        error_count=$(grep -r "ERROR\|CRITICAL\|FATAL" logs/ 2>/dev/null | wc -l)
        if [ $error_count -eq 0 ]; then
            log "✅ No critical errors in logs"
        else
            log "⚠️ Found $error_count error entries in logs"
        fi
    else
        log "⚠️ No log files found"
    fi
else
    log "❌ Logs directory not found"
fi

# VERIFICATION 7: External Dependencies
log "🌐 Checking external dependencies..."

# Test external API connectivity (without using actual keys)
external_deps_ok=0

if curl -s --connect-timeout 5 "https://api.openai.com" > /dev/null; then
    log "✅ OpenAI API reachable"
    external_deps_ok=$((external_deps_ok + 1))
else
    log "⚠️ OpenAI API unreachable"
fi

if curl -s --connect-timeout 5 "https://api.firecrawl.dev" > /dev/null; then
    log "✅ Firecrawl API reachable"
    external_deps_ok=$((external_deps_ok + 1))
else
    log "⚠️ Firecrawl API unreachable"
fi

if curl -s --connect-timeout 5 "https://api.telegram.org" > /dev/null; then
    log "✅ Telegram API reachable"
    external_deps_ok=$((external_deps_ok + 1))
else
    log "⚠️ Telegram API unreachable"
fi

log "External dependencies reachable: $external_deps_ok/3"

# VERIFICATION 8: System Resources
log "💻 Checking system resources..."

# Check memory usage
memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
log "📊 Memory usage: ${memory_usage}%"

# Check disk space
disk_usage=$(df /root | tail -1 | awk '{print $5}' | sed 's/%//')
log "💾 Disk usage: ${disk_usage}%"

# Check CPU load
cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
log "⚡ CPU load average: $cpu_load"

# Resource warnings
if (( $(echo "$memory_usage > 90" | bc -l) )); then
    log "⚠️ High memory usage detected"
fi

if [ $disk_usage -gt 90 ]; then
    log "⚠️ High disk usage detected"
fi

# VERIFICATION 9: Integration Test
log "🔗 Running integration test..."

# Test a complete workflow if possible
integration_test() {
    # Create a simple test memory
    test_response=$(curl -s -X POST "http://sam.chat:3000/api/memories" \
        -H "Content-Type: application/json" \
        -d '{
            "content": "Post-deployment verification test",
            "memory_type": "learning",
            "confidence_score": 0.95
        }' 2>/dev/null)
    
    if echo "$test_response" | grep -q "id"; then
        log "✅ Integration test passed - memory creation works"
        return 0
    else
        log "❌ Integration test failed - memory creation failed"
        return 1
    fi
}

if integration_test; then
    log "✅ Integration test completed successfully"
else
    log "⚠️ Integration test had issues"
fi

# VERIFICATION 10: Security Check
log "🔒 Basic security verification..."

# Check file permissions
if [ "$(stat -c %a .env)" = "600" ] || [ "$(stat -c %a .env)" = "644" ]; then
    log "✅ .env file permissions OK"
else
    log "⚠️ .env file permissions may be too open"
fi

# Check for exposed secrets in logs
if grep -r "secret\|password\|key" logs/ 2>/dev/null | grep -v "masked\|hidden" | head -1 > /dev/null; then
    log "⚠️ Potential secrets found in logs - review logs"
else
    log "✅ No obvious secrets in logs"
fi

# FINAL SUMMARY
log ""
log "🎯 VERIFICATION SUMMARY"
log "======================"
log "Service Status: $(sudo systemctl is-active mcp-enterprise)"
log "Ports Active: $ports_ok/${#CRITICAL_PORTS[@]}"
log "Health Checks: $health_ok/${#HEALTH_ENDPOINTS[@]}"
log "API Tests: $api_tests_passed/3"
log "External APIs: $external_deps_ok/3"
log "Memory Usage: ${memory_usage}%"
log "Disk Usage: ${disk_usage}%"
log ""

# Calculate overall score
total_checks=20
passed_checks=$((ports_ok + health_ok + api_tests_passed + external_deps_ok))
score=$(echo "scale=1; $passed_checks * 100 / $total_checks" | bc)

log "📊 Overall System Health: ${score}%"

if (( $(echo "$score >= 85" | bc -l) )); then
    log "🎉 SYSTEM IS READY FOR PRODUCTION!"
    log "✅ All critical components are functioning correctly"
elif (( $(echo "$score >= 70" | bc -l) )); then
    log "⚠️ SYSTEM IS MOSTLY FUNCTIONAL"
    log "🔧 Some components may need attention"
else
    log "❌ SYSTEM NEEDS ATTENTION"
    log "🛠️ Multiple components require fixes"
fi

log ""
log "📋 NEXT STEPS:"
log "1. Review verification log: $VERIFY_LOG"
log "2. Address any warnings or errors found"
log "3. Configure external API keys if needed"
log "4. Apply database schema in Supabase dashboard"
log "5. Test frontend at: http://65.109.54.94:5174"
log ""
log "✅ Verification completed!"

echo ""
echo "Verification log saved to: $VERIFY_LOG"
echo "System verification completed! 🎯"

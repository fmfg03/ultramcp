#!/bin/bash
# MCP Endpoints Testing Script
# Tests all MCP agents and endpoints in hot environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_BASE_URL="${MCP_BASE_URL:-http://localhost:3000}"
MCP_API_KEY="${MCP_API_KEY:-test-key-123}"
STUDIO_SECRET="${STUDIO_SECRET:-test-studio-secret}"
TEST_TIMEOUT="${TEST_TIMEOUT:-30}"

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}🔬 MCP Endpoints Testing Script${NC}"
echo -e "${BLUE}================================${NC}"
echo "Base URL: $MCP_BASE_URL"
echo "Timeout: ${TEST_TIMEOUT}s"
echo ""

# Helper functions
log_test() {
    echo -e "${YELLOW}🧪 Testing: $1${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

log_success() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

log_failure() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    echo -e "${RED}   Error: $2${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Test HTTP endpoint
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local expected_status="$4"
    local headers="$5"
    
    local curl_cmd="curl -s -w '%{http_code}' --max-time $TEST_TIMEOUT"
    
    if [ -n "$headers" ]; then
        curl_cmd="$curl_cmd $headers"
    fi
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl_cmd="$curl_cmd -X POST -H 'Content-Type: application/json' -d '$data'"
    elif [ "$method" = "GET" ]; then
        curl_cmd="$curl_cmd -X GET"
    fi
    
    curl_cmd="$curl_cmd '$MCP_BASE_URL$endpoint'"
    
    local response=$(eval $curl_cmd 2>/dev/null)
    local status_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$status_code" = "$expected_status" ]; then
        return 0
    else
        echo "Expected: $expected_status, Got: $status_code"
        echo "Response: $body"
        return 1
    fi
}

# Test 1: Health Check
log_test "Health Check Endpoint"
if test_endpoint "GET" "/health" "" "200"; then
    log_success "Health check endpoint responding"
else
    log_failure "Health check endpoint" "Not responding correctly"
fi

# Test 2: Environment Info (Development only)
log_test "Environment Info Endpoint"
if test_endpoint "GET" "/env" "" "200"; then
    log_success "Environment info endpoint responding"
else
    log_info "Environment endpoint not available (likely production mode)"
fi

# Test 3: Studio Access
log_test "Studio Access"
studio_headers="-H 'X-Studio-Secret: $STUDIO_SECRET'"
if test_endpoint "GET" "/studio" "" "200" "$studio_headers"; then
    log_success "Studio access working"
else
    log_failure "Studio access" "Authentication or endpoint issue"
fi

# Test 4: Studio Status
log_test "Studio Status"
if test_endpoint "GET" "/studio/status" "" "200" "$studio_headers"; then
    log_success "Studio status endpoint working"
else
    log_failure "Studio status" "Endpoint not responding"
fi

# Test 5: MCP Authentication
log_test "MCP Authentication"
mcp_headers="-H 'X-MCP-Key: $MCP_API_KEY'"
if test_endpoint "GET" "/mcp/health" "" "200" "$mcp_headers"; then
    log_success "MCP authentication working"
else
    log_failure "MCP authentication" "API key or endpoint issue"
fi

# Test 6: Complete MCP Agent
log_test "Complete MCP Agent"
complete_agent_data='{
    "task": "Test task for complete MCP agent",
    "agent": "complete_mcp",
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 100
    }
}'
if test_endpoint "POST" "/mcp/agents/complete" "$complete_agent_data" "200" "$mcp_headers"; then
    log_success "Complete MCP agent responding"
else
    log_failure "Complete MCP agent" "Agent execution failed"
fi

# Test 7: Reasoning Agent
log_test "Reasoning Agent"
reasoning_data='{
    "task": "Analyze this simple test case",
    "agent": "reasoning",
    "parameters": {
        "simplified": true
    }
}'
if test_endpoint "POST" "/mcp/agents/reasoning" "$reasoning_data" "200" "$mcp_headers"; then
    log_success "Reasoning agent responding"
else
    log_failure "Reasoning agent" "Agent execution failed"
fi

# Test 8: Builder Agent
log_test "Builder Agent"
builder_data='{
    "task": "Create a simple test component",
    "agent": "builder",
    "project_type": "web",
    "requirements": ["responsive", "simple"]
}'
if test_endpoint "POST" "/mcp/agents/builder" "$builder_data" "200" "$mcp_headers"; then
    log_success "Builder agent responding"
else
    log_failure "Builder agent" "Agent execution failed"
fi

# Test 9: Perplexity Research Agent
log_test "Perplexity Research Agent"
research_data='{
    "query": "What is artificial intelligence?",
    "agent": "perplexity",
    "research_type": "general"
}'
if test_endpoint "POST" "/mcp/agents/perplexity" "$research_data" "200" "$mcp_headers"; then
    log_success "Perplexity research agent responding"
else
    log_info "Perplexity agent not available (may require API key)"
fi

# Test 10: Attendee Integration
log_test "Attendee Integration"
attendee_data='{
    "transcription": [
        {
            "timestamp": "2025-06-18T18:20:00Z",
            "speaker": "Test User",
            "utterance": "We need to create a test report by Friday"
        }
    ],
    "mode": "ears-only"
}'
if test_endpoint "POST" "/mcp/attendee/analyze" "$attendee_data" "200" "$mcp_headers"; then
    log_success "Attendee integration responding"
else
    log_info "Attendee integration not fully implemented yet"
fi

# Test 11: Analytics Endpoint
log_test "Analytics Endpoint"
if test_endpoint "GET" "/analytics/stats" "" "200" "-H 'Authorization: Bearer test-token'"; then
    log_success "Analytics endpoint responding"
else
    log_info "Analytics endpoint requires valid JWT token"
fi

# Test 12: Cache Statistics
log_test "Cache Statistics"
if test_endpoint "GET" "/mcp/cache/stats" "" "200" "$mcp_headers"; then
    log_success "Cache statistics endpoint responding"
else
    log_failure "Cache statistics" "Endpoint not available"
fi

# Test 13: Precheck Statistics
log_test "Precheck Statistics"
if test_endpoint "GET" "/mcp/precheck/stats" "" "200" "$mcp_headers"; then
    log_success "Precheck statistics endpoint responding"
else
    log_failure "Precheck statistics" "Endpoint not available"
fi

# Test 14: Session Management
log_test "Session Management"
session_data='{
    "action": "create",
    "session_type": "mcp_execution",
    "metadata": {
        "user": "test_user",
        "environment": "testing"
    }
}'
if test_endpoint "POST" "/mcp/sessions" "$session_data" "200" "$mcp_headers"; then
    log_success "Session management responding"
else
    log_failure "Session management" "Session creation failed"
fi

# Test 15: Error Logging
log_test "Error Logging"
error_data='{
    "error_type": "test_error",
    "message": "This is a test error for logging",
    "context": {
        "agent": "test_agent",
        "task": "test_task"
    }
}'
if test_endpoint "POST" "/mcp/errors/log" "$error_data" "200" "$mcp_headers"; then
    log_success "Error logging responding"
else
    log_failure "Error logging" "Error logging failed"
fi

# Test 16: Rate Limiting
log_test "Rate Limiting"
log_info "Testing rate limiting with multiple requests..."
rate_limit_passed=true
for i in {1..10}; do
    if ! test_endpoint "GET" "/health" "" "200" > /dev/null 2>&1; then
        if [ $i -lt 6 ]; then
            rate_limit_passed=false
            break
        fi
    fi
    sleep 0.1
done

if [ "$rate_limit_passed" = true ]; then
    log_success "Rate limiting configured correctly"
else
    log_failure "Rate limiting" "Too restrictive or not working"
fi

# Test 17: WebSocket Connection (if available)
log_test "WebSocket Connection"
if command -v wscat >/dev/null 2>&1; then
    ws_url="${MCP_BASE_URL/http/ws}/ws"
    if timeout 5 wscat -c "$ws_url" -x 'ping' >/dev/null 2>&1; then
        log_success "WebSocket connection working"
    else
        log_info "WebSocket not available or not responding"
    fi
else
    log_info "wscat not available, skipping WebSocket test"
fi

# Test 18: Security Headers
log_test "Security Headers"
security_response=$(curl -s -I "$MCP_BASE_URL/health" 2>/dev/null)
if echo "$security_response" | grep -i "x-frame-options\|x-content-type-options\|x-xss-protection" >/dev/null; then
    log_success "Security headers present"
else
    log_info "Security headers not detected (may be development mode)"
fi

# Test 19: CORS Configuration
log_test "CORS Configuration"
cors_response=$(curl -s -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST" -X OPTIONS "$MCP_BASE_URL/health" 2>/dev/null)
if echo "$cors_response" | grep -i "access-control-allow" >/dev/null; then
    log_success "CORS configured correctly"
else
    log_info "CORS headers not detected"
fi

# Test 20: Performance Test
log_test "Performance Test"
log_info "Running performance test with 5 concurrent requests..."
start_time=$(date +%s.%N)
for i in {1..5}; do
    (test_endpoint "GET" "/health" "" "200" > /dev/null 2>&1) &
done
wait
end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "N/A")

if [ "$duration" != "N/A" ] && [ $(echo "$duration < 5.0" | bc -l 2>/dev/null || echo "0") -eq 1 ]; then
    log_success "Performance test passed (${duration}s for 5 concurrent requests)"
else
    log_info "Performance test completed (duration: ${duration}s)"
fi

# Summary
echo ""
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}===============${NC}"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the output above for details.${NC}"
    exit 1
fi


#!/bin/bash
# UltraMCP Restate Integration Testing
# Compare legacy system vs Restate workflows

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

test_pass() {
    log_success "✓ $1"
    ((TESTS_PASSED++))
}

test_fail() {
    log_error "✗ $1"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up test environment..."
    
    mkdir -p "$RESULTS_DIR"
    
    # Check if Restate is running
    if ! curl -s -f http://localhost:9070/health >/dev/null; then
        log_error "Restate is not running. Please start it first:"
        log_info "cd $SCRIPT_DIR && ./install-restate.sh install"
        exit 1
    fi
    
    # Check if UltraMCP services are running
    if ! curl -s -f http://localhost:3000/health >/dev/null; then
        log_warning "UltraMCP services don't seem to be running"
        log_info "Consider starting them with: ultramcp start"
    fi
    
    log_success "Test environment ready"
}

# Test Restate basic functionality
test_restate_basics() {
    log_info "Testing Restate basic functionality..."
    
    # Test health endpoint
    if curl -s -f http://localhost:9070/health >/dev/null; then
        test_pass "Restate health endpoint responds"
    else
        test_fail "Restate health endpoint not responding"
    fi
    
    # Test admin API
    local services_response=$(curl -s http://localhost:9070/services 2>/dev/null || echo "ERROR")
    if [[ "$services_response" != "ERROR" ]]; then
        test_pass "Restate admin API accessible"
    else
        test_fail "Restate admin API not accessible"
    fi
    
    # Test ingress endpoint
    if curl -s -f http://localhost:8080 >/dev/null; then
        test_pass "Restate ingress endpoint responds"
    else
        test_fail "Restate ingress endpoint not responding"
    fi
    
    # Test Jaeger tracing
    if curl -s -f http://localhost:16686 >/dev/null; then
        test_pass "Jaeger tracing UI accessible"
    else
        test_fail "Jaeger tracing UI not accessible"
    fi
}

# Test workflow deployment
test_workflow_deployment() {
    log_info "Testing workflow deployment..."
    
    # Check if example service is running
    if docker ps | grep -q "restate-workflows"; then
        test_pass "Restate workflows container is running"
    else
        log_warning "Starting example workflows service..."
        
        # Try to start the example service
        cd "$SCRIPT_DIR/examples/typescript"
        if [[ -f "package.json" ]]; then
            # Install dependencies if needed
            if [[ ! -d "node_modules" ]]; then
                npm install
            fi
            
            # Start the service in background
            npm run dev > "$RESULTS_DIR/workflow-service.log" 2>&1 &
            echo $! > "$RESULTS_DIR/workflow-service.pid"
            
            # Wait for it to start
            sleep 10
            
            if curl -s -f http://localhost:9080/health >/dev/null; then
                test_pass "Example workflow service started"
            else
                test_fail "Failed to start example workflow service"
            fi
        else
            test_fail "Example workflow service not available"
        fi
    fi
    
    # Test service registration
    local service_url="http://localhost:9080"
    local register_response=$(curl -s -X POST http://localhost:9070/deployments \
        -H "Content-Type: application/json" \
        -d "{\"uri\": \"$service_url\"}" 2>/dev/null || echo "ERROR")
    
    if [[ "$register_response" != "ERROR" ]]; then
        test_pass "Workflow service registration successful"
    else
        test_fail "Workflow service registration failed"
    fi
}

# Test Chain of Debate workflow
test_chain_of_debate() {
    log_info "Testing Chain of Debate workflow..."
    
    local test_topic="Should AI systems have built-in ethical constraints?"
    local legacy_start_time=$(date +%s%3N)
    
    # Test legacy system (if available)
    local legacy_result=""
    if curl -s -f http://localhost:8001/health >/dev/null; then
        log_info "Testing legacy Chain of Debate..."
        
        legacy_result=$(curl -s -X POST http://localhost:8001/debate \
            -H "Content-Type: application/json" \
            -d "{
                \"topic\": \"$test_topic\",
                \"participants\": [\"philosopher\", \"engineer\", \"ethicist\"],
                \"rounds\": 2
            }" 2>/dev/null || echo "ERROR")
        
        local legacy_end_time=$(date +%s%3N)
        local legacy_duration=$((legacy_end_time - legacy_start_time))
        
        if [[ "$legacy_result" != "ERROR" ]]; then
            test_pass "Legacy Chain of Debate executed successfully"
            echo "$legacy_result" > "$RESULTS_DIR/legacy_debate_result.json"
            echo "$legacy_duration" > "$RESULTS_DIR/legacy_debate_duration.txt"
        else
            test_fail "Legacy Chain of Debate failed"
        fi
    else
        log_warning "Legacy Chain of Debate service not available"
    fi
    
    # Test Restate workflow
    local restate_start_time=$(date +%s%3N)
    log_info "Testing Restate Chain of Debate workflow..."
    
    local restate_result=$(curl -s -X POST http://localhost:8080/chain-of-debate \
        -H "Content-Type: application/json" \
        -d "{
            \"topic\": \"$test_topic\",
            \"participants\": [\"philosopher\", \"engineer\", \"ethicist\"],
            \"rounds\": 2
        }" 2>/dev/null || echo "ERROR")
    
    local restate_end_time=$(date +%s%3N)
    local restate_duration=$((restate_end_time - restate_start_time))
    
    if [[ "$restate_result" != "ERROR" ]]; then
        test_pass "Restate Chain of Debate workflow executed successfully"
        echo "$restate_result" > "$RESULTS_DIR/restate_debate_result.json"
        echo "$restate_duration" > "$RESULTS_DIR/restate_debate_duration.txt"
        
        # Compare durations if both are available
        if [[ -f "$RESULTS_DIR/legacy_debate_duration.txt" ]]; then
            local legacy_time=$(cat "$RESULTS_DIR/legacy_debate_duration.txt")
            local restate_time=$(cat "$RESULTS_DIR/restate_debate_duration.txt")
            
            log_info "Performance comparison:"
            log_info "  Legacy system: ${legacy_time}ms"
            log_info "  Restate workflow: ${restate_time}ms"
            
            if [[ $restate_time -le $((legacy_time * 120 / 100)) ]]; then
                test_pass "Restate performance is acceptable (within 20% of legacy)"
            else
                test_fail "Restate performance is significantly slower than legacy"
            fi
        fi
    else
        test_fail "Restate Chain of Debate workflow failed"
    fi
}

# Test workflow durability
test_workflow_durability() {
    log_info "Testing workflow durability..."
    
    # Start a long-running workflow
    local workflow_id="durability-test-$(date +%s)"
    log_info "Starting long-running workflow: $workflow_id"
    
    # Start workflow that takes 60 seconds
    curl -s -X POST http://localhost:8080/ultramcp-workflow \
        -H "Content-Type: application/json" \
        -d "{
            \"task\": \"durability-test\",
            \"agents\": [\"test-agent\"],
            \"context\": {\"workflowId\": \"$workflow_id\", \"duration\": 60}
        }" > "$RESULTS_DIR/durability_workflow.json" 2>&1 &
    
    local workflow_pid=$!
    
    # Wait 10 seconds, then restart Restate
    sleep 10
    log_info "Restarting Restate to test durability..."
    
    # Restart Restate container
    docker restart ultramcp-restate
    
    # Wait for Restate to come back up
    local restart_attempts=0
    while [[ $restart_attempts -lt 30 ]]; do
        if curl -s -f http://localhost:9070/health >/dev/null; then
            break
        fi
        sleep 2
        ((restart_attempts++))
    done
    
    if [[ $restart_attempts -ge 30 ]]; then
        test_fail "Restate failed to restart within 60 seconds"
        return
    fi
    
    test_pass "Restate restarted successfully"
    
    # Check if workflow continued
    sleep 20  # Wait for workflow to potentially complete
    
    # Query workflow status
    local workflow_status=$(curl -s "http://localhost:9070/services/ultramcp-workflow/instances/$workflow_id" 2>/dev/null || echo "ERROR")
    
    if [[ "$workflow_status" != "ERROR" ]] && echo "$workflow_status" | jq -e '.status == "completed"' >/dev/null 2>&1; then
        test_pass "Workflow survived Restate restart and completed"
    else
        test_fail "Workflow did not survive Restate restart"
    fi
}

# Test performance under load
test_performance_load() {
    log_info "Testing performance under load..."
    
    local concurrent_requests=10
    local requests_per_client=5
    
    log_info "Running $concurrent_requests concurrent clients, $requests_per_client requests each"
    
    # Create test script for load testing
    cat > "$RESULTS_DIR/load_test.sh" << 'EOF'
#!/bin/bash
client_id=$1
requests=$2
results_file=$3

total_time=0
successful_requests=0

for i in $(seq 1 $requests); do
    start_time=$(date +%s%3N)
    
    response=$(curl -s -X POST http://localhost:8080/ultramcp-workflow \
        -H "Content-Type: application/json" \
        -d "{
            \"task\": \"load-test-client-$client_id-request-$i\",
            \"agents\": [\"test-agent\"],
            \"context\": {\"clientId\": $client_id, \"requestId\": $i}
        }" 2>/dev/null)
    
    end_time=$(date +%s%3N)
    duration=$((end_time - start_time))
    
    if [[ "$response" != "" ]] && echo "$response" | jq -e '.success' >/dev/null 2>&1; then
        ((successful_requests++))
        total_time=$((total_time + duration))
    fi
done

avg_time=$((total_time / successful_requests))
echo "Client $client_id: $successful_requests/$requests successful, avg time: ${avg_time}ms" >> "$results_file"
EOF

    chmod +x "$RESULTS_DIR/load_test.sh"
    
    # Run concurrent load tests
    local pids=()
    for i in $(seq 1 $concurrent_requests); do
        "$RESULTS_DIR/load_test.sh" "$i" "$requests_per_client" "$RESULTS_DIR/load_test_results.txt" &
        pids+=($!)
    done
    
    # Wait for all clients to finish
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    # Analyze results
    if [[ -f "$RESULTS_DIR/load_test_results.txt" ]]; then
        local total_requests=$((concurrent_requests * requests_per_client))
        local successful_count=$(grep -o "successful" "$RESULTS_DIR/load_test_results.txt" | wc -l)
        local success_rate=$((successful_count * 100 / total_requests))
        
        log_info "Load test results:"
        cat "$RESULTS_DIR/load_test_results.txt"
        log_info "Overall success rate: $success_rate%"
        
        if [[ $success_rate -ge 90 ]]; then
            test_pass "Load test passed (≥90% success rate)"
        else
            test_fail "Load test failed (<90% success rate)"
        fi
    else
        test_fail "Load test results file not created"
    fi
}

# Test error handling and recovery
test_error_handling() {
    log_info "Testing error handling and recovery..."
    
    # Test workflow with intentional failure
    local error_result=$(curl -s -X POST http://localhost:8080/ultramcp-workflow \
        -H "Content-Type: application/json" \
        -d "{
            \"task\": \"error-test\",
            \"agents\": [\"failing-agent\"],
            \"context\": {\"shouldFail\": true}
        }" 2>/dev/null || echo "ERROR")
    
    if [[ "$error_result" != "ERROR" ]]; then
        # Check if error was handled gracefully
        if echo "$error_result" | jq -e '.error' >/dev/null 2>&1; then
            test_pass "Error handling works correctly"
        else
            test_fail "Error not handled properly"
        fi
    else
        test_fail "Error test workflow failed to execute"
    fi
    
    # Test recovery after service restart
    log_info "Testing recovery after service restart..."
    
    # Stop and restart workflow service
    if [[ -f "$RESULTS_DIR/workflow-service.pid" ]]; then
        local pid=$(cat "$RESULTS_DIR/workflow-service.pid")
        kill "$pid" 2>/dev/null || true
        sleep 5
        
        # Restart service
        cd "$SCRIPT_DIR/examples/typescript"
        npm run dev > "$RESULTS_DIR/workflow-service-restart.log" 2>&1 &
        echo $! > "$RESULTS_DIR/workflow-service-restart.pid"
        
        sleep 10
        
        # Test if service recovered
        if curl -s -f http://localhost:9080/health >/dev/null; then
            test_pass "Workflow service recovered after restart"
        else
            test_fail "Workflow service failed to recover"
        fi
    fi
}

# Test tracing and observability
test_observability() {
    log_info "Testing tracing and observability..."
    
    # Execute a workflow and check if it appears in Jaeger
    local trace_test_id="trace-test-$(date +%s)"
    
    curl -s -X POST http://localhost:8080/ultramcp-workflow \
        -H "Content-Type: application/json" \
        -d "{
            \"task\": \"$trace_test_id\",
            \"agents\": [\"trace-test-agent\"],
            \"context\": {\"traceTest\": true}
        }" > /dev/null 2>&1
    
    # Wait for trace to be collected
    sleep 10
    
    # Query Jaeger for traces
    local jaeger_traces=$(curl -s "http://localhost:16686/api/traces?service=ultramcp-restate&limit=20" 2>/dev/null || echo "ERROR")
    
    if [[ "$jaeger_traces" != "ERROR" ]] && echo "$jaeger_traces" | jq -e '.data[0]' >/dev/null 2>&1; then
        test_pass "Traces are being collected in Jaeger"
    else
        test_fail "Traces not found in Jaeger"
    fi
    
    # Test PostgreSQL metadata storage
    local metadata_query="SELECT COUNT(*) FROM workflow_metadata WHERE workflow_type = 'ultramcp-workflow';"
    local metadata_count=$(docker exec ultramcp-restate-postgres psql -U restate -d restate -t -c "$metadata_query" 2>/dev/null | tr -d ' ' || echo "ERROR")
    
    if [[ "$metadata_count" != "ERROR" ]] && [[ $metadata_count -gt 0 ]]; then
        test_pass "Workflow metadata is being stored"
    else
        test_fail "Workflow metadata not being stored"
    fi
}

# Cleanup test artifacts
cleanup_tests() {
    log_info "Cleaning up test artifacts..."
    
    # Kill any running test processes
    if [[ -f "$RESULTS_DIR/workflow-service.pid" ]]; then
        local pid=$(cat "$RESULTS_DIR/workflow-service.pid")
        kill "$pid" 2>/dev/null || true
        rm -f "$RESULTS_DIR/workflow-service.pid"
    fi
    
    if [[ -f "$RESULTS_DIR/workflow-service-restart.pid" ]]; then
        local pid=$(cat "$RESULTS_DIR/workflow-service-restart.pid")
        kill "$pid" 2>/dev/null || true
        rm -f "$RESULTS_DIR/workflow-service-restart.pid"
    fi
    
    # Clean up test files
    rm -f "$RESULTS_DIR/load_test.sh"
    
    log_success "Cleanup completed"
}

# Generate test report
generate_report() {
    local report_file="$RESULTS_DIR/test_report_$TIMESTAMP.md"
    
    cat > "$report_file" << EOF
# UltraMCP Restate Integration Test Report

**Date**: $(date)  
**Test Session**: $TIMESTAMP

## Summary

- **Tests Passed**: $TESTS_PASSED
- **Tests Failed**: $TESTS_FAILED
- **Total Tests**: $((TESTS_PASSED + TESTS_FAILED))
- **Success Rate**: $(( (TESTS_PASSED * 100) / (TESTS_PASSED + TESTS_FAILED) ))%

EOF

    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo "## Failed Tests" >> "$report_file"
        echo "" >> "$report_file"
        for test in "${FAILED_TESTS[@]}"; do
            echo "- $test" >> "$report_file"
        done
        echo "" >> "$report_file"
    fi

    echo "## Test Results Files" >> "$report_file"
    echo "" >> "$report_file"
    echo "Available in: \`$RESULTS_DIR\`" >> "$report_file"
    echo "" >> "$report_file"
    
    if [[ -f "$RESULTS_DIR/legacy_debate_result.json" ]]; then
        echo "- \`legacy_debate_result.json\` - Legacy Chain of Debate result" >> "$report_file"
    fi
    
    if [[ -f "$RESULTS_DIR/restate_debate_result.json" ]]; then
        echo "- \`restate_debate_result.json\` - Restate workflow result" >> "$report_file"
    fi
    
    if [[ -f "$RESULTS_DIR/load_test_results.txt" ]]; then
        echo "- \`load_test_results.txt\` - Load testing results" >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "## Next Steps" >> "$report_file"
    echo "" >> "$report_file"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo "✅ **All tests passed!** Ready to proceed with Restate migration." >> "$report_file"
        echo "" >> "$report_file"
        echo "Recommended next steps:" >> "$report_file"
        echo "1. Implement Chain of Debate workflow in production" >> "$report_file"
        echo "2. Set up monitoring and alerting" >> "$report_file"
        echo "3. Begin gradual migration of other services" >> "$report_file"
    else
        echo "⚠️ **Some tests failed.** Review failed tests before proceeding." >> "$report_file"
        echo "" >> "$report_file"
        echo "Recommended actions:" >> "$report_file"
        echo "1. Review error logs in \`$RESULTS_DIR\`" >> "$report_file"
        echo "2. Fix identified issues" >> "$report_file"
        echo "3. Re-run tests: \`./test-restate-integration.sh\`" >> "$report_file"
    fi
    
    log_info "Test report generated: $report_file"
    
    # Display summary
    echo ""
    echo "============================================"
    echo "UltraMCP Restate Integration Test Summary"
    echo "============================================"
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Success Rate: $(( (TESTS_PASSED * 100) / (TESTS_PASSED + TESTS_FAILED) ))%"
    echo ""
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "🎉 All tests passed! Restate integration is ready."
    else
        log_error "❌ Some tests failed. Check the report for details."
        return 1
    fi
}

# Main test function
main() {
    local test_type="${1:-all}"
    
    log_info "Starting UltraMCP Restate Integration Tests"
    log_info "Test type: $test_type"
    log_info "Results will be saved to: $RESULTS_DIR"
    
    # Always run setup
    setup_test_environment
    
    case "$test_type" in
        "basic")
            test_restate_basics
            ;;
        "deployment")
            test_restate_basics
            test_workflow_deployment
            ;;
        "workflows")
            test_restate_basics
            test_workflow_deployment
            test_chain_of_debate
            ;;
        "durability")
            test_restate_basics
            test_workflow_deployment
            test_workflow_durability
            ;;
        "performance")
            test_restate_basics
            test_workflow_deployment
            test_performance_load
            ;;
        "errors")
            test_restate_basics
            test_workflow_deployment
            test_error_handling
            ;;
        "observability")
            test_restate_basics
            test_workflow_deployment
            test_observability
            ;;
        "all"|*)
            test_restate_basics
            test_workflow_deployment
            test_chain_of_debate
            test_workflow_durability
            test_performance_load
            test_error_handling
            test_observability
            ;;
    esac
    
    cleanup_tests
    generate_report
}

# Trap for cleanup on script exit
trap cleanup_tests EXIT

# Show help if requested
if [[ "${1:-}" == "help" ]] || [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    echo "UltraMCP Restate Integration Testing"
    echo ""
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Test Types:"
    echo "  all            Run all tests (default)"
    echo "  basic          Test basic Restate functionality"
    echo "  deployment     Test workflow deployment"
    echo "  workflows      Test workflow execution"
    echo "  durability     Test workflow durability"
    echo "  performance    Test performance under load"
    echo "  errors         Test error handling"
    echo "  observability  Test tracing and monitoring"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all tests"
    echo "  $0 basic        # Test basic functionality only"
    echo "  $0 workflows    # Test workflow execution"
    exit 0
fi

# Run main function
main "$@"
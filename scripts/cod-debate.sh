#!/bin/bash

# CoD Protocol Debate via Terminal
source "$(dirname "$0")/common.sh"

TOPIC="$1"
TASK_ID=$(generate_task_id)

if [ -z "$TOPIC" ]; then
    echo "Usage: make debate TOPIC='debate topic here'"
    echo ""
    echo "Examples:"
    echo "  make debate TOPIC='Should we invest in AI research?'"
    echo "  make debate TOPIC='Best approach for web automation'"
    echo "  make debate TOPIC='Security vs usability trade-offs'"
    exit 1
fi

log_info "cod-debate" "Starting debate on: $TOPIC (Task: $TASK_ID)"

echo "🎭 UltraMCP Chain-of-Debate Protocol"
echo "===================================="
echo "Topic: $TOPIC"
echo "Task ID: $TASK_ID"
echo ""

# Ensure data directory exists
ensure_directory "data/debates"

# Check if CoD service is running
cod_service_url="http://localhost:8001"
if ! is_service_running "cod-service"; then
    log_info "cod-debate" "Starting CoD Protocol service"
    echo "🚀 Starting CoD Protocol service..."
    
    python3 scripts/cod-service.py &
    
    # Wait for service to be ready
    echo "⏳ Waiting for service to initialize..."
    if wait_for_service "$cod_service_url" 30 2; then
        log_success "cod-debate" "CoD Protocol service started"
    else
        handle_error "cod-debate" "SERVICE_START_FAILED" "Failed to start CoD Protocol service" '["Check Python dependencies", "Verify port 8001 is available", "Check service logs"]'
        exit 1
    fi
else
    log_info "cod-debate" "CoD Protocol service already running"
fi

# Send debate request to CoD service
echo "🧠 Initiating multi-LLM debate..."

debate_payload=$(cat << EOF
{
  "task_id": "$TASK_ID",
  "topic": "$TOPIC",
  "participants": ["gpt-4", "claude-3-sonnet"],
  "max_rounds": 3,
  "consensus_threshold": 0.75
}
EOF
)

response=$(curl -s -X POST "$cod_service_url/debate" \
  -H "Content-Type: application/json" \
  -d "$debate_payload" \
  --connect-timeout 10 \
  --max-time 120)

curl_exit_code=$?

if [ $curl_exit_code -ne 0 ]; then
    handle_error "cod-debate" "SERVICE_UNAVAILABLE" "CoD Protocol service not responding (curl exit code: $curl_exit_code)" '["Check service status with: make status", "Restart service: python3 scripts/cod-service.py", "Verify port 8001 is accessible"]'
    exit 1
fi

# Check if response is valid JSON
if ! echo "$response" | jq . >/dev/null 2>&1; then
    handle_error "cod-debate" "INVALID_RESPONSE" "Invalid JSON response from service" '["Check service logs", "Verify service is running correctly", "Try simpler topic"]'
    echo "Raw response: $response"
    exit 1
fi

# Check for error in response
if echo "$response" | jq -e '.detail' >/dev/null 2>&1; then
    error_detail=$(echo "$response" | jq -r '.detail')
    handle_error "cod-debate" "DEBATE_FAILED" "$error_detail" '["Check topic format", "Verify API keys if using real LLMs", "Try shorter topic"]'
    exit 1
fi

# Parse and display results
echo ""
echo "🎯 Debate Results"
echo "================="

if echo "$response" | jq -e '.consensus' >/dev/null 2>&1; then
    consensus=$(echo "$response" | jq -r '.consensus')
    confidence=$(echo "$response" | jq -r '.confidence_score')
    rounds=$(echo "$response" | jq -r '.rounds | length')
    
    echo "📊 Consensus: $consensus"
    echo ""
    echo "📈 Confidence Score: ${confidence}%"
    echo "🔄 Debate Rounds: $rounds"
    echo ""
    
    # Display explanations
    echo "💡 Executive Summaries:"
    echo "======================="
    
    cfo_summary=$(echo "$response" | jq -r '.explanation.forCFO // "Not available"')
    cto_summary=$(echo "$response" | jq -r '.explanation.forCTO // "Not available"')
    general_summary=$(echo "$response" | jq -r '.explanation.general // "Not available"')
    
    echo ""
    echo "💰 CFO Perspective:"
    echo "$cfo_summary"
    echo ""
    echo "🔧 CTO Perspective:" 
    echo "$cto_summary"
    echo ""
    echo "🎯 General Summary:"
    echo "$general_summary"
    echo ""
    
    # Display metadata
    participants=$(echo "$response" | jq -r '.metadata.participants | join(", ")')
    duration=$(echo "$response" | jq -r '.metadata.duration_seconds')
    
    echo "📋 Debate Metadata:"
    echo "==================="
    echo "Participants: $participants"
    echo "Duration: ${duration} seconds"
    echo "Task ID: $TASK_ID"
    echo ""
    
    # Save detailed results
    results_file="data/debates/${TASK_ID}_results.json"
    echo "$response" > "$results_file"
    
    log_success "cod-debate" "Debate completed: $TASK_ID (Confidence: ${confidence}%)"
    echo "💾 Full results saved to: $results_file"
    
else
    handle_error "cod-debate" "MALFORMED_RESPONSE" "Response missing expected fields" '["Check service implementation", "Verify API integration", "Try different topic"]'
    echo "Raw response for debugging:"
    echo "$response" | jq . 2>/dev/null || echo "$response"
    exit 1
fi
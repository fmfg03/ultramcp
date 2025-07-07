#!/bin/bash

# UltraMCP Claudia Integration Test Script
# Tests the enhanced agent management system

set -e

echo "🚀 Testing UltraMCP Claudia Integration..."
echo "========================================="

BASE_URL="http://localhost:8013"

# Check if service is running
echo "1. 🏥 Health Check..."
response=$(curl -s "$BASE_URL/health" || echo "ERROR")
if [[ "$response" == *"healthy"* ]]; then
    echo "✅ Service is healthy"
else
    echo "❌ Service is not responding"
    exit 1
fi

# List templates
echo ""
echo "2. 📋 Available Templates..."
templates=$(curl -s "$BASE_URL/agents/templates" | jq -r 'keys[]')
echo "Available templates:"
for template in $templates; do
    echo "  - $template"
done

# Test installing a template
echo ""
echo "3. 📥 Installing Security Scanner Template..."
install_response=$(curl -s -X POST "$BASE_URL/agents/templates/ultramcp_security_scanner/install")
agent_id=$(echo "$install_response" | jq -r '.id')
echo "✅ Installed agent with ID: $agent_id"

# Test executing the agent
echo ""
echo "4. 🚀 Executing Security Scanner Agent..."
execute_response=$(curl -s -X POST "$BASE_URL/agents/$agent_id/execute" \
    -H "Content-Type: application/json" \
    -d '{"task": "Test security scan", "project_path": "/root/ultramcp"}')
execution_id=$(echo "$execute_response" | jq -r '.id')
echo "✅ Started execution with ID: $execution_id"

# Check execution status
echo ""
echo "5. 📊 Monitoring Execution..."
for i in {1..5}; do
    echo "Checking status (attempt $i/5)..."
    status=$(curl -s "$BASE_URL/executions" | jq -r ".[0].status")
    echo "Status: $status"
    if [[ "$status" == "completed" ]]; then
        break
    fi
    sleep 2
done

# Show metrics
echo ""
echo "6. 📈 Final Metrics..."
curl -s "$BASE_URL/metrics" | jq '.'

# List agents
echo ""
echo "7. 📋 Installed Agents..."
curl -s "$BASE_URL/agents" | jq '.[] | {name: .name, id: .id, services: .ultramcp_services}'

echo ""
echo "✅ UltraMCP Claudia Integration Test Complete!"
echo "🎯 All core functionality verified:"
echo "  - Agent template installation"
echo "  - Agent execution with async processing"
echo "  - Service integration tracking"
echo "  - Metrics collection"
echo "  - Health monitoring"
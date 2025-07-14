#!/bin/bash

echo "🚀 Testing UltraMCP Plandex Integration"
echo "======================================="

# Check if services are running
echo "📊 Checking service health..."
health_response=$(curl -s http://localhost:7778/health)
if [[ $? -eq 0 ]]; then
    echo "✅ Agent Registry: $(echo $health_response | jq -r .status)"
else
    echo "❌ Agent Registry: Not responding"
    exit 1
fi

# List available agents
echo ""
echo "🤖 Available UltraMCP Agents:"
curl -s http://localhost:7778/api/agents | jq -r '.[] | "  - \(.name): \(.description)"'

# Test Plandex integration
echo ""
echo "🎯 Testing Plandex Integration..."
plandex_test=$(curl -s -X POST http://localhost:7778/api/test/plandex)
if [[ $(echo $plandex_test | jq -r .success) == "true" ]]; then
    echo "✅ Plandex is accessible and ready"
else
    echo "❌ Plandex integration failed"
    echo $plandex_test | jq .
    exit 1
fi

# Create a planning session
echo ""
echo "📋 Creating Planning Session..."
session_response=$(curl -s -X POST http://localhost:7778/api/planning/session \
    -H "Content-Type: application/json" \
    -d '{"topic": "Test integration workflow", "agents": ["chain-of-debate", "claude-memory"], "priority": "medium"}')

session_id=$(echo $session_response | jq -r .sessionId)
echo "✅ Session created: $session_id"

# Check session status
echo ""
echo "🔍 Session Details:"
curl -s http://localhost:7778/api/planning/session/$session_id | jq .

echo ""
echo "🎉 UltraMCP Plandex Integration Test Complete!"
echo "Ready for autonomous planning and agent orchestration."
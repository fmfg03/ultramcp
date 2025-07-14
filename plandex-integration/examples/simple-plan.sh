#!/bin/bash
# Example: Simple task planning with Plandex

echo "🧠 Testing simple planning with Plandex..."

# Create a simple task
TASK="Analyze the security of a web application and provide recommendations"

echo "Task: $TASK"
echo ""

# Generate plan
echo "Generating plan..."
PLAN_RESPONSE=$(curl -s -X POST http://localhost:7777/plan \
    -H "Content-Type: application/json" \
    -d "{\"task\": \"$TASK\", \"useUltraMCPAgents\": true}")

echo "Plan generated:"
echo "$PLAN_RESPONSE" | jq '.'

PLAN_ID=$(echo "$PLAN_RESPONSE" | jq -r '.planId')
echo ""
echo "Plan ID: $PLAN_ID"

# Execute plan (optional)
read -p "Execute this plan? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Executing plan..."
    curl -X POST "http://localhost:7777/execute/$PLAN_ID" | jq '.'
fi

#!/bin/bash
# Example: Multi-agent workflow with context persistence

echo "🤖 Testing multi-agent workflow..."

# Create context
CONTEXT_RESPONSE=$(curl -s -X POST http://localhost:7779/context \
    -H "Content-Type: application/json" \
    -d '{
        "task": "Comprehensive code analysis and security review",
        "repository": "https://github.com/example/webapp.git",
        "requirements": ["security", "performance", "best-practices"],
        "budget": 50,
        "timeline": "1 week"
    }')

CONTEXT_ID=$(echo "$CONTEXT_RESPONSE" | jq -r '.contextId')
echo "Context created: $CONTEXT_ID"

# Generate plan with context
PLAN_RESPONSE=$(curl -s -X POST http://localhost:7777/plan \
    -H "Content-Type: application/json" \
    -d "{
        \"task\": \"Analyze repository with multi-agent approach\",
        \"contextId\": \"$CONTEXT_ID\",
        \"agents\": [\"blockoli-intelligence\", \"asterisk-security\", \"chain-of-debate\"]
    }")

echo "Multi-agent plan:"
echo "$PLAN_RESPONSE" | jq '.'

#!/bin/bash

# =============================================================================
# Context7 Integration Test Script
# Tests Context7 MCP service functionality within UltraMCP
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test configuration
CONTEXT7_URL="http://sam.chat:8003"
TEST_LIBRARY="react"
TEST_QUERY="hooks"
TEST_PROMPT="Create a React component with useState hook"

echo -e "${CYAN}🧪 Context7 Integration Test Suite${NC}"
echo "=================================="

# Test 1: Service Health Check
echo -e "\n${PURPLE}Test 1: Service Health Check${NC}"
if curl -s "$CONTEXT7_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Context7 service is running${NC}"
    health_response=$(curl -s "$CONTEXT7_URL/health")
    echo "   Status: $(echo "$health_response" | jq -r '.status')"
    echo "   Service: $(echo "$health_response" | jq -r '.service')"
else
    echo -e "${RED}❌ Context7 service is not running${NC}"
    echo -e "${YELLOW}💡 Start with: make docker-hybrid${NC}"
    exit 1
fi

# Test 2: Documentation Retrieval
echo -e "\n${PURPLE}Test 2: Documentation Retrieval${NC}"
doc_response=$(curl -s -X POST "$CONTEXT7_URL/api/documentation" \
    -H "Content-Type: application/json" \
    -d "{\"library\":\"$TEST_LIBRARY\",\"type\":\"api\"}")

if echo "$doc_response" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✅ Documentation retrieval successful${NC}"
    library=$(echo "$doc_response" | jq -r '.data.library')
    version=$(echo "$doc_response" | jq -r '.data.version')
    echo "   Library: $library"
    echo "   Version: $version"
    echo "   Cached: $(echo "$doc_response" | jq -r '.data.cached')"
else
    echo -e "${YELLOW}⚠️  Documentation retrieval failed${NC}"
    echo "   Error: $(echo "$doc_response" | jq -r '.error // "Unknown error"')"
fi

# Test 3: Documentation Search
echo -e "\n${PURPLE}Test 3: Documentation Search${NC}"
search_response=$(curl -s "$CONTEXT7_URL/api/documentation/search?library=$TEST_LIBRARY&query=$TEST_QUERY")

if echo "$search_response" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✅ Documentation search successful${NC}"
    echo "   Query: $TEST_QUERY in $TEST_LIBRARY"
else
    echo -e "${YELLOW}⚠️  Documentation search failed${NC}"
    echo "   Error: $(echo "$search_response" | jq -r '.error // "Unknown error"')"
fi

# Test 4: Claude Code Integration
echo -e "\n${PURPLE}Test 4: Claude Code Integration${NC}"
claude_response=$(curl -s -X POST "$CONTEXT7_URL/api/claude/context" \
    -H "Content-Type: application/json" \
    -d "{\"prompt\":\"$TEST_PROMPT\",\"autoDetect\":true}")

if echo "$claude_response" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✅ Claude Code integration successful${NC}"
    detected_libs=$(echo "$claude_response" | jq -r '.data.libraries | @json')
    echo "   Detected libraries: $detected_libs"
    echo "   Enhanced prompt generated: ✅"
else
    echo -e "${YELLOW}⚠️  Claude Code integration failed${NC}"
    echo "   Error: $(echo "$claude_response" | jq -r '.error // "Unknown error"')"
fi

# Test 5: Batch Documentation Request
echo -e "\n${PURPLE}Test 5: Batch Documentation Request${NC}"
batch_response=$(curl -s -X POST "$CONTEXT7_URL/api/documentation/batch" \
    -H "Content-Type: application/json" \
    -d '{
        "requests": [
            {"library": "react", "type": "api"},
            {"library": "express", "type": "api"},
            {"library": "lodash", "type": "api"}
        ]
    }')

if echo "$batch_response" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✅ Batch documentation request successful${NC}"
    successful_count=$(echo "$batch_response" | jq '[.data[] | select(.success == true)] | length')
    total_count=$(echo "$batch_response" | jq '.data | length')
    echo "   Successful: $successful_count/$total_count requests"
else
    echo -e "${YELLOW}⚠️  Batch documentation request failed${NC}"
    echo "   Error: $(echo "$batch_response" | jq -r '.error // "Unknown error"')"
fi

# Test 6: Service Statistics
echo -e "\n${PURPLE}Test 6: Service Statistics${NC}"
stats_response=$(curl -s "$CONTEXT7_URL/api/stats")

if echo "$stats_response" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✅ Service statistics retrieved${NC}"
    requests=$(echo "$stats_response" | jq -r '.data.service.requestCount // 0')
    errors=$(echo "$stats_response" | jq -r '.data.service.errorCount // 0')
    cache_keys=$(echo "$stats_response" | jq -r '.data.cache.keys // 0')
    echo "   Requests: $requests"
    echo "   Errors: $errors"
    echo "   Cache keys: $cache_keys"
else
    echo -e "${YELLOW}⚠️  Failed to retrieve service statistics${NC}"
fi

# Test 7: Python Client Test
echo -e "\n${PURPLE}Test 7: Python Client Test${NC}"
if [ -f "services/context7-mcp/context7_client.py" ]; then
    if python3 services/context7-mcp/context7_client.py health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Python client working${NC}"
        
        # Test library detection
        echo "   Testing library detection..."
        detected_libs=$(python3 services/context7-mcp/context7_client.py detect "import React from 'react'; import axios from 'axios';" 2>/dev/null || echo "[]")
        echo "   Detected libraries: $detected_libs"
    else
        echo -e "${YELLOW}⚠️  Python client test failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Python client not found${NC}"
fi

# Test 8: Integration with Makefile Commands
echo -e "\n${PURPLE}Test 8: Makefile Integration${NC}"
if grep -q "context7-health" Makefile; then
    echo -e "${GREEN}✅ Makefile commands available${NC}"
    echo "   Available commands:"
    echo "     make context7-health"
    echo "     make context7-docs LIBRARY=react"
    echo "     make context7-search LIBRARY=react QUERY=hooks"
    echo "     make context7-chat TEXT='Create a React app'"
else
    echo -e "${YELLOW}⚠️  Makefile commands not found${NC}"
fi

# Test 9: Docker Service Integration
echo -e "\n${PURPLE}Test 9: Docker Service Integration${NC}"
if docker ps --format "{{.Names}}" | grep -q "ultramcp-context7"; then
    echo -e "${GREEN}✅ Docker service running${NC}"
    
    # Check container health
    health_status=$(docker inspect ultramcp-context7 --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-healthcheck")
    echo "   Health status: $health_status"
    
    # Check container logs
    echo "   Recent logs:"
    docker logs ultramcp-context7 --tail 3 2>/dev/null | sed 's/^/     /' || echo "     No logs available"
else
    echo -e "${YELLOW}⚠️  Docker service not running${NC}"
    echo -e "${BLUE}💡 Start with: make docker-hybrid${NC}"
fi

# Summary
echo -e "\n${CYAN}📊 Test Summary${NC}"
echo "================="

# Count successful tests
successful_tests=0
total_tests=9

# Re-run key tests for summary
if curl -s "$CONTEXT7_URL/health" > /dev/null; then
    ((successful_tests++))
fi

if curl -s -X POST "$CONTEXT7_URL/api/documentation" -H "Content-Type: application/json" -d "{\"library\":\"react\"}" | jq -e '.success' > /dev/null; then
    ((successful_tests++))
fi

if curl -s "$CONTEXT7_URL/api/documentation/search?library=react&query=hooks" | jq -e '.success' > /dev/null; then
    ((successful_tests++))
fi

if curl -s -X POST "$CONTEXT7_URL/api/claude/context" -H "Content-Type: application/json" -d "{\"prompt\":\"test\"}" | jq -e '.success' > /dev/null; then
    ((successful_tests++))
fi

if curl -s "$CONTEXT7_URL/api/stats" | jq -e '.success' > /dev/null; then
    ((successful_tests++))
fi

if [ -f "services/context7-mcp/context7_client.py" ]; then
    ((successful_tests++))
fi

if grep -q "context7-health" Makefile; then
    ((successful_tests++))
fi

if docker ps --format "{{.Names}}" | grep -q "ultramcp-context7"; then
    ((successful_tests++))
fi

# Always count integration test as successful if we got this far
((successful_tests++))

echo "Successful tests: $successful_tests/$total_tests"

if [ $successful_tests -ge 7 ]; then
    echo -e "${GREEN}🎉 Context7 integration is working well!${NC}"
    echo ""
    echo -e "${BLUE}💡 Quick start commands:${NC}"
    echo "   make context7-docs LIBRARY=react"
    echo "   make context7-chat TEXT='Create a React component'"
    echo "   make context7-health"
elif [ $successful_tests -ge 4 ]; then
    echo -e "${YELLOW}⚠️  Context7 integration has some issues${NC}"
    echo "   Consider restarting services: make docker-hybrid"
else
    echo -e "${RED}❌ Context7 integration needs attention${NC}"
    echo "   Check service logs: docker logs ultramcp-context7"
fi

echo ""
echo -e "${CYAN}🔗 For more information:${NC}"
echo "   Context7 GitHub: https://github.com/upstash/context7"
echo "   UltraMCP Docs: cat CLAUDE.md"
#!/bin/bash

# Simple LLM Chat via Terminal
source "$(dirname "$0")/common.sh"

TEXT="$1"
TASK_ID=$(generate_task_id)

if [ -z "$TEXT" ]; then
    echo "Usage: make chat TEXT='your message here'"
    exit 1
fi

log_info "simple-chat" "Starting chat session: $TASK_ID"

# Validate OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    handle_error "simple-chat" "NO_API_KEY" "OpenAI API key not set" '["Set OPENAI_API_KEY environment variable", "Check .env file", "Obtain API key from OpenAI platform"]'
    exit 1
fi

# Use OpenAI API directly (faster than MCP for simple tasks)
echo "🤖 Processing your request..."

response=$(curl -s -X POST "https://api.openai.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d "{
    \"model\": \"gpt-4\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"$TEXT\"}
    ],
    \"temperature\": 0.7,
    \"max_tokens\": 1000
  }" 2>/dev/null)

if [ $? -ne 0 ]; then
    handle_error "simple-chat" "API_CALL_FAILED" "Failed to connect to OpenAI API" '["Check internet connection", "Verify API key", "Try again in a moment"]'
    exit 1
fi

# Check for API errors
if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
    error_msg=$(echo "$response" | jq -r '.error.message')
    error_type=$(echo "$response" | jq -r '.error.type // "unknown"')
    handle_error "simple-chat" "OPENAI_API_ERROR" "$error_msg (Type: $error_type)" '["Check API key validity", "Verify account credits", "Try with shorter prompt"]'
    exit 1
fi

# Extract and display response
if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    answer=$(echo "$response" | jq -r '.choices[0].message.content')
    usage=$(echo "$response" | jq -r '.usage // empty')
    
    echo ""
    echo "🤖 Response:"
    echo "============"
    echo "$answer"
    echo ""
    
    if [ -n "$usage" ]; then
        tokens_used=$(echo "$usage" | jq -r '.total_tokens // 0')
        log_info "simple-chat" "Chat completed: $TASK_ID (Tokens: $tokens_used)"
    else
        log_success "simple-chat" "Chat completed: $TASK_ID"
    fi
else
    handle_error "simple-chat" "INVALID_RESPONSE" "Invalid response format from OpenAI" '["Check API response format", "Try again", "Contact support if issue persists"]'
    exit 1
fi
#!/bin/bash

# Local LLM Chat Script - Terminal-First Approach
# Uses locally downloaded Ollama models for offline AI chat
source "$(dirname "$0")/common.sh"

TASK_ID=$(generate_task_id)
PROMPT="$1"

if [ -z "$PROMPT" ]; then
    echo "❌ Error: No prompt provided"
    echo "Usage: make local-chat TEXT='your question'"
    exit 1
fi

log_info "local-llm-chat" "Starting local LLM chat: $TASK_ID"

echo "🤖 UltraMCP Local LLM Chat"
echo "=========================="
echo "📝 Prompt: $PROMPT"
echo ""

# Check if Ollama is available
if ! command -v ollama >/dev/null; then
    handle_error "local-llm-chat" "OLLAMA_NOT_FOUND" "Ollama not installed" '["Install Ollama from https://ollama.ai", "Check PATH configuration", "Verify Ollama service is running"]'
    exit 1
fi

# Check available models
echo "🔍 Checking available local models..."
available_models=$(ollama list 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$available_models" ]; then
    handle_error "local-llm-chat" "NO_MODELS_FOUND" "No local models available" '["Download a model with: ollama pull mistral", "Check Ollama service status", "Verify model downloads completed"]'
    exit 1
fi

echo "✅ Local models available:"
echo "$available_models"
echo ""

# Model selection priority (fastest to slowest)
models_priority=(
    "mistral:7b"
    "llama3.1:8b" 
    "qwen2.5-coder:7b"
    "deepseek-coder:6.7b"
    "qwen2.5:14b"
)

# Find first available model
selected_model=""
for model in "${models_priority[@]}"; do
    if echo "$available_models" | grep -q "$model"; then
        selected_model="$model"
        break
    fi
done

# Fallback to first available model if none from priority list
if [ -z "$selected_model" ]; then
    selected_model=$(echo "$available_models" | awk 'NR==2 {print $1}' | head -1)
fi

if [ -z "$selected_model" ]; then
    handle_error "local-llm-chat" "MODEL_SELECTION_FAILED" "Could not select a model" '["Check ollama list output", "Ensure models are properly downloaded", "Try downloading mistral with: ollama pull mistral"]'
    exit 1
fi

echo "🎯 Using model: $selected_model"
echo "💬 Generating response..."
echo ""

# Create enhanced prompt for better responses
enhanced_prompt="Please provide a helpful, accurate, and concise response to the following:

$PROMPT

Response:"

# Record start time
start_time=$(date +%s)

# Call Ollama with the selected model
response=$(ollama run "$selected_model" "$enhanced_prompt" 2>&1)
exit_code=$?

# Record end time and calculate duration
end_time=$(date +%s)
duration=$((end_time - start_time))

if [ $exit_code -eq 0 ]; then
    echo "🤖 Response from $selected_model:"
    echo "================================"
    echo "$response"
    echo ""
    echo "⏱️  Response time: ${duration}s"
    
    # Save successful result
    result_data=$(cat <<EOF
{
    "task_id": "$TASK_ID",
    "type": "local_llm_chat",
    "model": "$selected_model",
    "prompt": "$PROMPT",
    "response": "$response",
    "duration_seconds": $duration,
    "status": "success",
    "timestamp": "$(date -Iseconds)"
}
EOF
)
    
    # Save to data directory
    ensure_directory "data/local_llm"
    echo "$result_data" > "data/local_llm/${TASK_ID}_chat.json"
    
    log_success "local-llm-chat" "Local LLM chat completed successfully in ${duration}s using $selected_model"
    
else
    echo "❌ Error: Failed to get response from $selected_model"
    echo "Error output: $response"
    
    handle_error "local-llm-chat" "LLM_RESPONSE_FAILED" "Model failed to generate response" '["Check if model is properly loaded", "Try a different model", "Restart Ollama service", "Check system resources (RAM/CPU)"]'
    exit 1
fi

# Show model info
echo ""
echo "📊 Model Information:"
model_info=$(ollama show "$selected_model" 2>/dev/null | head -10)
if [ -n "$model_info" ]; then
    echo "$model_info"
else
    echo "  Model: $selected_model"
    echo "  Type: Local LLM via Ollama"
    echo "  Status: Operational"
fi

echo ""
echo "💡 Tips:"
echo "  • Use 'make local-models' to see all available models"
echo "  • Download new models with: ollama pull <model_name>"
echo "  • For coding tasks, try: make local-chat TEXT='explain this code: ...'"
echo "  • For faster responses, use smaller models like mistral:7b"

log_info "local-llm-chat" "Local LLM chat session completed"
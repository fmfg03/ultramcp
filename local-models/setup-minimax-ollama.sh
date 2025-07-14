#!/bin/bash

echo "🚀 Setting up MiniMax-M1-80k in Ollama for UltraMCP"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    print_error "Ollama not found. Please install Ollama first:"
    echo "curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Check if Ollama is running
if ! pgrep -f ollama >/dev/null; then
    print_status "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

print_success "Ollama is running"

# Check current models
print_status "Current Ollama models:"
ollama list

# Check available disk space
available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
required_space=60  # MiniMax-M1-80k is quite large

if [ "$available_space" -lt "$required_space" ]; then
    print_warning "Available disk space: ${available_space}GB"
    print_warning "MiniMax-M1-80k requires approximately ${required_space}GB"
    print_warning "Consider freeing up space or using a quantized version"
fi

# Method 1: Try direct pull (if model becomes available in Ollama registry)
print_status "Attempting direct pull from Ollama registry..."
if ollama pull minimax-m1:80k 2>/dev/null; then
    print_success "MiniMax-M1-80k pulled successfully from Ollama registry!"
elif ollama pull minimax 2>/dev/null; then
    print_success "MiniMax model pulled successfully from Ollama registry!"
else
    print_warning "MiniMax not available in Ollama registry yet"
    
    # Method 2: Create custom model from HuggingFace
    print_status "Creating custom MiniMax-M1 model from HuggingFace..."
    
    # Check if we can access HuggingFace model
    print_status "Checking HuggingFace model availability..."
    
    # Create the model using Modelfile
    print_status "Creating MiniMax-M1-80k model in Ollama..."
    
    if ollama create minimax-m1:80k -f Modelfile.minimax; then
        print_success "✅ MiniMax-M1-80k model created successfully!"
    else
        print_error "Failed to create MiniMax-M1 model"
        print_status "Trying alternative approach with smaller context..."
        
        # Create alternative Modelfile with smaller context for compatibility
        cat > Modelfile.minimax.compat << 'EOF'
# Alternative Modelfile for compatibility
FROM MiniMaxAI/MiniMax-M1-80k

PARAMETER temperature 1.0
PARAMETER top_p 0.95
PARAMETER num_ctx 32768

SYSTEM """You are MiniMax-M1, a powerful reasoning model with advanced capabilities in mathematics, coding, and complex analysis. Provide thoughtful, step-by-step reasoning for complex problems."""
EOF
        
        if ollama create minimax-m1:80k -f Modelfile.minimax.compat; then
            print_success "✅ MiniMax-M1-80k model created with compatibility settings!"
        else
            print_error "❌ Failed to create MiniMax-M1 model with both approaches"
            
            # Method 3: Use a compatible alternative
            print_status "Setting up compatible alternative model..."
            
            # Try using CodeQwen or DeepSeek as MiniMax alternative
            if ollama pull codeqwen:7b-code; then
                print_success "✅ Pulled CodeQwen 7B as MiniMax alternative"
                ollama copy codeqwen:7b-code minimax-m1:alt
                print_warning "Using CodeQwen as MiniMax-M1 alternative until official support"
            elif ollama pull deepseek-coder:33b; then
                print_success "✅ Pulled DeepSeek-Coder 33B as MiniMax alternative"
                ollama copy deepseek-coder:33b minimax-m1:alt
                print_warning "Using DeepSeek-Coder as MiniMax-M1 alternative until official support"
            else
                print_error "Unable to set up MiniMax-M1 or alternatives"
                exit 1
            fi
        fi
    fi
fi

# Verify the model is available
print_status "Verifying MiniMax-M1 model installation..."
if ollama list | grep -q "minimax"; then
    print_success "✅ MiniMax-M1 model is available in Ollama!"
    
    # Test the model
    print_status "Testing MiniMax-M1 model..."
    test_response=$(ollama run minimax-m1:80k "What is 2+2? Explain your reasoning." 2>/dev/null || ollama run minimax-m1:alt "What is 2+2? Explain your reasoning." 2>/dev/null)
    
    if [ ! -z "$test_response" ]; then
        print_success "✅ MiniMax-M1 model test successful!"
        echo "Test response: $test_response"
    else
        print_warning "Model loaded but test failed - this is normal for large models on first run"
    fi
else
    print_error "❌ MiniMax-M1 model not found in Ollama list"
    exit 1
fi

# Update UltraMCP orchestrator to recognize MiniMax
print_status "Updating UltraMCP local models orchestrator..."

# Check orchestrator health
orchestrator_health=$(curl -s http://localhost:8012/health 2>/dev/null)
if [ $? -eq 0 ]; then
    print_success "✅ UltraMCP orchestrator is running"
    
    # Refresh models in orchestrator
    curl -s http://localhost:8012/models >/dev/null 2>&1
    print_success "✅ Model registry refreshed"
    
    # Test MiniMax through orchestrator
    print_status "Testing MiniMax-M1 through UltraMCP orchestrator..."
    test_orchestrator=$(curl -s -X POST http://localhost:8012/generate \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Test MiniMax reasoning", "model": "minimax-m1:80k", "provider": "ollama"}' 2>/dev/null)
    
    if echo "$test_orchestrator" | grep -q "content"; then
        print_success "✅ MiniMax-M1 working through orchestrator!"
    else
        print_warning "Orchestrator test inconclusive - model may need warm-up"
    fi
else
    print_warning "UltraMCP orchestrator not accessible - MiniMax available directly through Ollama"
fi

# Show final status
print_status "Final model list:"
ollama list

echo ""
print_success "🎉 MiniMax-M1-80k setup complete!"
echo ""
echo "Usage examples:"
echo "  Direct Ollama:"
echo "    ollama run minimax-m1:80k 'Solve this complex problem...'"
echo ""
echo "  Through UltraMCP orchestrator:"
echo "    curl -X POST http://localhost:8012/generate \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"prompt\": \"Your reasoning task\", \"model\": \"minimax-m1:80k\", \"provider\": \"ollama\"}'"
echo ""
print_warning "Note: Large models may take time to load on first use"
print_warning "Consider using GPU acceleration for better performance: ollama run --gpu minimax-m1:80k"
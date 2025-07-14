#!/bin/bash

echo "🚀 Setting up MiniMax-M1-80k Integration for UltraMCP"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check requirements
print_status "Checking system requirements..."

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    gpu_info=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits)
    print_success "GPU detected: $gpu_info"
    
    # Check GPU memory (MiniMax-M1-80k needs significant VRAM)
    gpu_memory=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    if [ "$gpu_memory" -lt 40000 ]; then
        print_warning "GPU memory is ${gpu_memory}MB. MiniMax-M1-80k requires 40GB+ for optimal performance"
        print_warning "Model will use quantization and may run slower"
    else
        print_success "GPU memory sufficient: ${gpu_memory}MB"
    fi
else
    print_error "NVIDIA GPU not detected. MiniMax-M1-80k requires CUDA-capable GPU"
    exit 1
fi

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker first"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found. Please install Docker Compose first"
    exit 1
fi

print_success "System requirements check completed"

# Create directories
print_status "Creating directory structure..."
mkdir -p models logs
print_success "Directory structure created"

# Stop existing orchestrator if running
print_status "Stopping existing model orchestrator..."
docker stop ultramcp-local-models-orchestrator 2>/dev/null || true
docker rm ultramcp-local-models-orchestrator 2>/dev/null || true

# Build and start enhanced orchestrator
print_status "Building enhanced model orchestrator with MiniMax-M1-80k support..."
docker-compose -f docker-compose.minimax.yml build

print_status "Starting enhanced orchestrator..."
docker-compose -f docker-compose.minimax.yml up -d

# Wait for service to be ready
print_status "Waiting for orchestrator to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8012/health >/dev/null 2>&1; then
        print_success "Enhanced orchestrator is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Timeout waiting for orchestrator to start"
        exit 1
    fi
    sleep 2
done

# Test the integration
print_status "Testing MiniMax-M1-80k integration..."

# Check available models
models_response=$(curl -s http://localhost:8012/models)
echo "Available models and providers:"
echo $models_response | jq .

# Try to start MiniMax server
print_status "Attempting to start MiniMax-M1-80k server..."
start_response=$(curl -s -X POST http://localhost:8012/models/minimax/start)
echo "MiniMax start response:"
echo $start_response | jq .

# Test simple generation
print_status "Testing model generation..."
test_response=$(curl -s -X POST http://localhost:8012/generate \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "Explain quantum computing in simple terms",
        "task_type": "reasoning",
        "use_reasoning": true
    }')

if echo $test_response | jq -e .content >/dev/null 2>&1; then
    print_success "Model generation test successful!"
    echo "Test response preview:"
    echo $test_response | jq -r .content | head -3
else
    print_warning "Model generation test failed or model still loading"
    echo "Response: $test_response"
fi

# Show logs
print_status "Recent orchestrator logs:"
docker logs ultramcp-enhanced-models-orchestrator --tail 10

echo ""
print_success "🎉 MiniMax-M1-80k setup complete!"
echo ""
echo "Available endpoints:"
echo "  - Health check: http://localhost:8012/health"
echo "  - List models: http://localhost:8012/models"
echo "  - Generate (auto-select): http://localhost:8012/generate"
echo "  - Generate (reasoning): http://localhost:8012/generate/reasoning"
echo "  - Start MiniMax: http://localhost:8012/models/minimax/start"
echo ""
echo "Example usage:"
echo '  curl -X POST http://localhost:8012/generate/reasoning \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '\''{"prompt": "Solve this complex problem...", "task_type": "mathematics"}'\'''
echo ""
print_warning "Note: First MiniMax model download may take 30+ minutes depending on internet speed"
print_warning "Model requires 40GB+ VRAM for optimal performance"
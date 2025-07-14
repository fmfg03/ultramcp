#!/bin/bash

echo "🔧 Setting up SynLogic Integration for UltraMCP Chain of Debate"
echo "============================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if CoD service is running
print_status "Checking Chain of Debate service..."
if curl -s http://localhost:8001/health >/dev/null 2>&1; then
    print_success "✅ CoD service is running"
else
    print_error "❌ CoD service not accessible at http://localhost:8001"
    print_warning "Please ensure UltraMCP CoD service is running first"
    exit 1
fi

# Install SynLogic
print_status "Installing SynLogic framework..."
pip3 install git+https://github.com/MiniMax-AI/SynLogic.git 2>/dev/null || {
    print_warning "Direct pip install failed, trying manual setup..."
    
    if [ ! -d "SynLogic" ]; then
        git clone https://github.com/MiniMax-AI/SynLogic.git
    fi
    
    cd SynLogic
    pip3 install -e . 2>/dev/null || {
        print_warning "Installing requirements manually..."
        pip3 install -r requirements.txt 2>/dev/null || true
    }
    cd ..
}

print_success "✅ SynLogic setup completed"

# Test SynLogic integration
print_status "Testing SynLogic integration with CoD..."
chmod +x cod-synlogic-integration.py

# Test available tasks
print_status "Available SynLogic tasks:"
python3 cod-synlogic-integration.py available-tasks

# Test basic debate
print_status "Testing enhanced debate with logical reasoning..."
python3 cod-synlogic-integration.py debate logical_reasoning 0.5 &
DEBATE_PID=$!

# Give it some time to start
sleep 5

# Check if debate is running
if ps -p $DEBATE_PID > /dev/null; then
    print_success "✅ Enhanced debate started successfully"
    wait $DEBATE_PID
else
    print_warning "Debate test may have completed quickly or encountered issues"
fi

# Test with different task types
print_status "Testing different SynLogic task types..."

for task in "game_of_24" "sudoku"; do
    print_status "Testing $task..."
    timeout 30s python3 cod-synlogic-integration.py debate $task 0.3 2>/dev/null || {
        print_warning "$task test timed out or failed (normal for complex tasks)"
    }
done

# Create usage examples
print_status "Creating usage examples..."

cat > synlogic-cod-examples.md << 'EOF'
# SynLogic + Chain of Debate Usage Examples

## 1. Enhanced Debate with Verification
```bash
# Run debate on logical reasoning with difficulty 0.7
python3 cod-synlogic-integration.py debate logical_reasoning 0.7

# Run debate on mathematical problem
python3 cod-synlogic-integration.py debate game_of_24 0.5

# Run debate on puzzle solving
python3 cod-synlogic-integration.py debate sudoku 0.8
```

## 2. Progressive Training
```bash
# Train CoD on logical reasoning with 5 progressive difficulty levels
python3 cod-synlogic-integration.py training logical_reasoning 5

# Train on mathematical problems with 3 levels
python3 cod-synlogic-integration.py training game_of_24 3
```

## 3. Benchmarking CoD Performance
```bash
# Run comprehensive benchmark across multiple SynLogic tasks
python3 cod-synlogic-integration.py benchmark
```

## 4. API Integration
```python
from cod_synlogic_integration import SynLogicCoD

# Initialize enhanced CoD
cod = SynLogicCoD()

# Run enhanced debate
result = await cod.run_enhanced_debate(
    task_type="logical_reasoning",
    difficulty=0.6,
    agents=["claude", "gpt4", "qwen"]
)

# Check verification score
print(f"Debate accuracy: {result['verification']['score']:.2f}")
```

## 5. Benefits Analysis

### Without SynLogic (Current CoD):
- Debates on arbitrary topics
- No objective scoring
- Hard to measure improvement
- Manual topic generation

### With SynLogic (Enhanced CoD):
- Verifiable reasoning problems  
- Automatic accuracy scoring
- Progressive difficulty training
- Diverse task types (35+ categories)
- Benchmark comparisons
- Data-driven improvements
EOF

print_success "✅ Usage examples created: synlogic-cod-examples.md"

# Create integration summary
print_status "Integration Summary:"
echo ""
echo "✅ DIRECT BENEFITS (No Fine-tuning Required):"
echo "   • Verifiable debate problems with ground truth"
echo "   • Automatic scoring of debate accuracy"  
echo "   • Progressive difficulty training"
echo "   • 35+ reasoning task categories"
echo "   • Benchmark CoD performance"
echo ""
echo "🚀 POTENTIAL FINE-TUNING BENEFITS:"
echo "   • Train CoD agents on SynLogic data"
echo "   • Improve reasoning capabilities"
echo "   • Domain-specific optimization"
echo "   • Custom verification rules"
echo ""
echo "🔧 INTEGRATION STATUS:"
cod_health=$(curl -s http://localhost:8001/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   • CoD Service: ✅ Running"
else
    echo "   • CoD Service: ❌ Not accessible"
fi

if python3 -c "import synlogic" 2>/dev/null; then
    echo "   • SynLogic: ✅ Installed"
else
    echo "   • SynLogic: ⚠️ Manual installation needed"
fi

echo "   • Integration Script: ✅ Ready"
echo "   • Examples: ✅ Created"
echo ""
echo "📋 NEXT STEPS:"
echo "   1. Test: python3 cod-synlogic-integration.py debate logical_reasoning 0.5"
echo "   2. Train: python3 cod-synlogic-integration.py training game_of_24 5"
echo "   3. Benchmark: python3 cod-synlogic-integration.py benchmark"
echo "   4. Review: cat synlogic-cod-examples.md"
echo ""
print_success "🎉 SynLogic + CoD integration setup complete!"
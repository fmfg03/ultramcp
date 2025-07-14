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

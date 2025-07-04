# Blockoli MCP Integration

Blockoli integration for UltraMCP Supreme Stack providing semantic code intelligence, pattern analysis, and context-aware AI capabilities.

## Features

- **Semantic Code Search**: Vector-based similarity search across codebases
- **Code Pattern Analysis**: Automatic detection of architectural patterns
- **Context-Aware AI**: Enhanced AI conversations with full code context
- **Real-time Indexing**: Incremental updates as code changes
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, Rust, Go, and more

## Setup

### 1. Install Blockoli Server

```bash
# Clone Blockoli
git clone https://github.com/getAsterisk/blockoli.git
cd blockoli

# Build and run (requires Rust)
cargo build --release
./target/release/blockoli --port 8080
```

### 2. Integration with UltraMCP

The Blockoli client is automatically available in UltraMCP. Use these commands:

```bash
# Index a project
make index-project PROJECT="/path/to/code" NAME="my_project"

# Search code semantically  
make code-search QUERY="async database operations" PROJECT="my_project"

# Code-intelligent debates
make code-debate TOPIC="Refactor auth system" PROJECT="my_project"
```

## API Reference

### BlockoliCodeContext

Main client class for interacting with Blockoli server.

```python
from services.blockoli_mcp.blockoli_client import BlockoliCodeContext

async with BlockoliCodeContext("http://sam.chat:8080") as blockoli:
    # Create project
    await blockoli.create_project("my_app")
    
    # Index codebase
    result = await blockoli.index_codebase("my_app", "/path/to/code")
    
    # Search for similar code
    matches = await blockoli.search_similar_code("authentication", "my_app")
    
    # Get comprehensive context
    context = await blockoli.get_code_context("user login", "my_app")
```

### Key Methods

- `create_project(name)` - Create new project
- `index_codebase(project, path)` - Index entire codebase  
- `search_similar_code(query, project)` - Semantic code search
- `get_code_context(query, project)` - Full context with patterns and insights
- `analyze_code_patterns(blocks)` - Pattern analysis
- `extract_architecture_insights(blocks)` - Architectural analysis

## Integration Points

### 1. Enhanced CoD Protocol

Code-intelligent debates with full codebase context:

```python
from services.cod_protocol.code_intelligent_orchestrator import CodeIntelligentCoDOrchestrator

orchestrator = CodeIntelligentCoDOrchestrator()
result = await orchestrator.run_code_intelligent_debate(
    topic="Should we refactor the payment processing system?",
    project_name="ecommerce_app",
    code_query="payment processing"
)
```

### 2. Security Analysis Enhancement

```python
from services.asterisk_mcp.code_intelligent_security import CodeIntelligentSecurityAnalyzer

analyzer = CodeIntelligentSecurityAnalyzer(blockoli_client, asterisk_client)
security_report = await analyzer.intelligent_security_scan("my_project", "authentication")
```

### 3. Claudia Dashboard Integration

Visual code intelligence interface with:
- Semantic search panel
- Code pattern visualization  
- Architecture insights dashboard
- Real-time code context viewer

## Configuration

Set these environment variables:

```bash
# Blockoli server endpoint (default: http://sam.chat:8080)
BLOCKOLI_ENDPOINT=http://sam.chat:8080

# Optional API key for authentication
BLOCKOLI_API_KEY=your-api-key

# Enable debug logging
BLOCKOLI_DEBUG=true
```

## File Structure

```
services/blockoli-mcp/
├── README.md
├── blockoli_client.py          # Main client implementation
├── code_intelligent_cod.py     # Enhanced CoD Protocol
├── pattern_analyzer.py         # Code pattern analysis
├── real_time_monitor.py        # Real-time code monitoring
└── integrations/
    ├── security_integration.py # Asterisk MCP integration
    ├── deepclaude_integration.py # DeepClaude integration
    └── claudia_integration.py  # Claudia dashboard integration
```

## Usage Examples

### Basic Code Search

```bash
make code-search QUERY="database connection pooling" PROJECT="backend_api"
```

### Architecture Analysis

```bash
make architecture-analysis PROJECT="microservices" FOCUS="service boundaries"
```

### Intelligent Code Review

```bash
make intelligent-code-review FILE="src/auth/login.py" PROJECT="web_app"
```

### Pattern-Based Security Scan

```bash
make pattern-security-scan PROJECT="payment_app" PATTERN="sql query"
```

## Performance

- **Indexing**: ~1000 files/minute on modern hardware
- **Search**: Sub-second semantic search across large codebases  
- **Memory**: ~100MB per 10k indexed files
- **Real-time**: <1s latency for incremental updates

## Troubleshooting

### Common Issues

1. **Blockoli server not running**
   ```bash
   # Check if server is running
   curl http://sam.chat:8080/health
   
   # Start server if needed
   blockoli --port 8080
   ```

2. **Index not found**
   ```bash
   # Re-index project
   make index-project PROJECT="/path/to/code" NAME="project_name"
   ```

3. **Search returns no results**
   ```bash
   # Check project stats
   python3 services/blockoli-mcp/blockoli_client.py health
   ```

## Contributing

1. Follow existing code patterns
2. Add tests for new features
3. Update documentation
4. Ensure compatibility with UltraMCP architecture

## License

Part of UltraMCP Supreme Stack - MIT License
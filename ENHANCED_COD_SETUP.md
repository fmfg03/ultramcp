# Enhanced CoD Protocol Setup Guide

## Local LLM + Chain-of-Debate Integration

### Quick Start

1. **Ensure Ollama is running with models:**
   ```bash
   ollama list
   # Should show: qwen2.5:14b, llama3.1:8b, qwen2.5-coder:7b, mistral:7b, deepseek-coder:6.7b
   ```

2. **Test the enhanced system:**
   ```bash
   make cod-local TOPIC="Should we use microservices or monolith architecture?"
   ```

3. **Try different modes:**
   ```bash
   make cod-hybrid TOPIC="AI ethics in autonomous vehicles"
   make cod-privacy TOPIC="Internal security policy changes"
   make cod-cost-optimized TOPIC="Cloud migration strategy"
   ```

### Available Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| `make cod-local` | Local-only debate | Privacy-sensitive topics |
| `make cod-hybrid` | Mixed local+API | Best quality results |
| `make cod-privacy` | Privacy-first | Confidential discussions |
| `make cod-cost-optimized` | Cost-efficient | Budget-conscious analysis |
| `make dev-decision` | Quick local decision | Development choices |
| `make claude-debate` | Claude Code optimized | Development workflows |

### Integration Benefits

- **100% Privacy**: Sensitive topics stay local
- **Zero API Costs**: Local models are free after download
- **Unlimited Usage**: No rate limits on local models
- **Offline Capability**: Works without internet
- **Role-based Analysis**: CFO, CTO, Analyst perspectives
- **Claude Code Ready**: Optimized for development workflows

### Troubleshooting

**Models not responding:**
```bash
make local-status
ollama ps
```

**Performance issues:**
```bash
make test-cod-performance
```

**Missing dependencies:**
```bash
pip3 install aiohttp asyncio
```

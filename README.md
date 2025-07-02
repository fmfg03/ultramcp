# 🚀 UltraMCP - World's First Hybrid Local+API Multi-LLM Platform

[![GitHub Stars](https://img.shields.io/github/stars/fmfg03/ultramcp?style=for-the-badge)](https://github.com/fmfg03/ultramcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg?style=for-the-badge)](https://nodejs.org/)
[![Local LLMs](https://img.shields.io/badge/Local_LLMs-5_Models-orange.svg?style=for-the-badge)](https://ollama.ai/)
[![Terminal First](https://img.shields.io/badge/Terminal_First-80%25-brightgreen.svg?style=for-the-badge)](https://claude.ai/code)

> **UltraMCP** is the world's first hybrid local+API multi-LLM orchestration platform featuring revolutionary terminal-first architecture (80%) with advanced Chain-of-Debate Protocol, local model integration, and enterprise-grade automation capabilities.

## 🌟 What is UltraMCP?

UltraMCP revolutionizes AI system orchestration with the world's first hybrid architecture:

- **🎭 Enhanced Chain-of-Debate Protocol**: Revolutionary local+API multi-LLM debates with 5 local models
- **🤖 Local LLM Integration**: Qwen 2.5 14B, Llama 3.1 8B, Qwen Coder 7B, Mistral 7B, DeepSeek Coder 6.7B
- **⚡ Terminal-First Architecture**: 80% terminal commands + 20% advanced orchestration for maximum productivity
- **🔒 Privacy-First Debates**: 100% local processing option for sensitive enterprise decisions
- **💰 Zero-Cost Local Operations**: Unlimited local model usage with API flexibility when needed
- **🚀 Claude Code Optimized**: Purpose-built for Claude Code integration and developer productivity
- **🗣️ Voice System Integration**: Full-duplex voice AI with real-time processing
- **📊 Enterprise Monitoring**: Real-time system observability and analytics

## 🏛️ Architecture Overview

```mermaid
graph TB
    subgraph "🎯 Frontend Layer"
        A[Observatory UI] --> B[DevTools Dashboard]
        B --> C[Voice Interface]
    end
    
    subgraph "⚡ Application Layer"
        D[Backend API] --> E[Frontend React]
        D --> F[MCP Orchestration]
    end
    
    subgraph "🧠 Services Layer"
        G[CoD Protocol] --> H[Voice System]
        H --> I[LangGraph Studio]
        I --> J[Observatory]
    end
    
    subgraph "🔧 Infrastructure"
        K[Docker Containers] --> L[Redis Cache]
        L --> M[PostgreSQL]
        M --> N[Monitoring Stack]
    end
    
    A --> D
    D --> G
    G --> K
```

## 📁 Project Structure

```
supermcp/
├── 🎯 apps/                          # Main Applications
│   ├── 📱 backend/                    # Core API & MCP Server
│   │   ├── src/adapters/              # 20+ MCP Adapters
│   │   ├── src/controllers/           # Request Controllers
│   │   ├── src/services/              # Business Logic
│   │   └── src/middleware/            # Auth, Monitoring, Security
│   └── 🌐 frontend/                   # React Dashboard
│       ├── src/components/            # UI Components
│       └── src/services/              # API Integration
├── 🧠 services/                       # Specialized Microservices
│   ├── 🎭 cod-protocol/               # Chain-of-Debate (7000+ lines)
│   │   ├── orchestrator.py            # Multi-LLM Orchestration
│   │   ├── shadow_llm.py              # Adversarial Analysis
│   │   ├── counterfactual_auditor.py  # External Validation
│   │   ├── circuit_breaker.py         # Performance Optimization
│   │   ├── cod_rest_adapter.py        # REST API
│   │   ├── cod_telegram_adapter.py    # Telegram Bot
│   │   └── dashboard.html             # Real-time WebUI
│   ├── 🗣️ voice-system/               # Voice AI Processing
│   │   ├── core/voice_api.py          # Voice Processing Engine
│   │   ├── voice_api_langwatch.py     # Langwatch Integration
│   │   └── tests/                     # Voice System Tests
│   ├── 🔬 langgraph-studio/           # LangGraph Integration
│   │   ├── agents/                    # AI Agents
│   │   ├── nodes/                     # Processing Nodes
│   │   └── studio/                    # Studio Interface
│   └── 📊 observatory/                # System Monitoring
├── 🏗️ infrastructure/                # Infrastructure as Code
│   ├── docker/                        # Container Configs
│   ├── k8s/                          # Kubernetes Manifests
│   └── scripts/                       # Deployment Scripts
├── 📚 docs/                          # Comprehensive Documentation
├── 🧪 tests/                         # Test Suites
└── 🛠️ tools/                         # Development Tools
```

## ✨ Key Features

### 🎭 Chain-of-Debate Protocol
- **Multi-LLM Orchestration**: Coordinate multiple AI models in structured debates
- **Dynamic Role Assignment**: Context-aware role allocation (CFO, CTO, Analyst, etc.)
- **Shadow LLM Analysis**: Adversarial criticism and bias detection
- **Counterfactual Auditing**: External validation with scenario analysis
- **Meta-Fusion Engine**: Advanced consensus algorithms with 6 fusion strategies
- **Circuit Breakers**: Performance optimization and resilience patterns

### 🗣️ Voice System
- **Real-time Processing**: Low-latency voice recognition and synthesis
- **Langwatch Integration**: Advanced voice analytics and monitoring
- **CPU Optimized**: Efficient processing for production environments
- **WebSocket Support**: Real-time voice streaming capabilities

### 🔗 MCP Enterprise
- **20+ Adapters**: GitHub, Notion, Telegram, Email, Jupyter, and more
- **Security Hardening**: Enterprise-grade authentication and authorization
- **Rate Limiting**: Advanced throttling and protection mechanisms
- **Monitoring & Observability**: Comprehensive system insights

### 📊 Observatory & DevTools
- **Real-time Dashboards**: Live system monitoring and metrics
- **Performance Analytics**: Detailed performance insights and optimization
- **Debug Interfaces**: Advanced debugging and troubleshooting tools
- **WebSocket Monitoring**: Real-time connection and data flow tracking

## 🚀 Quick Start

### Prerequisites

```bash
# Required
Node.js 18+
Python 3.8+
Docker & Docker Compose
Ollama (for local models)
Redis
PostgreSQL

# Optional for Enhanced Features
Kubernetes (for production)
Nginx (for reverse proxy)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/fmfg03/ultramcp.git
cd ultramcp

# 2. Quick setup (recommended)
make setup

# 3. Set up environment (if not using make)
cp .env.example .env
# Edit .env with your API keys

# 4. Start hybrid system
make start

# 5. Quick test
make chat TEXT="Hello from UltraMCP!"
make cod-local TOPIC="Should we use local AI models?"
```

### Docker Deployment

```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Enterprise (with monitoring)
docker-compose -f docker-compose.enterprise.yml up -d
```

## 📋 Terminal-First Commands (Claude Code Optimized)

### Core System (80% Usage)
```bash
make start               # Interactive startup menu
make status              # Check all services
make health-check        # Comprehensive health check
make logs               # View system logs
make backup             # Create system backup
```

### AI Operations (Local + API)
```bash
# Quick AI interactions
make chat TEXT="Your question"                    # OpenAI API chat
make local-chat TEXT="Your question"              # Local model chat
make analyze FILE="data.csv"                      # AI data analysis
make research URL="https://example.com"           # Web research + AI

# Enhanced Chain-of-Debate Protocol
make cod-local TOPIC="Your debate topic"          # 100% local debate
make cod-hybrid TOPIC="Your debate topic"         # Mix local + API
make cod-privacy TOPIC="Sensitive topic"          # Privacy-first mode
make cod-cost-optimized TOPIC="Budget decision"   # Minimize API costs
```

### Local LLM Management
```bash
make local-models                                 # List 5 available models
make local-status                                 # Check Ollama status
make local-pull MODEL="llama3.2"                  # Download new model
make local-remove MODEL="old-model"               # Remove model
```

### Web Automation (Playwright MCP)
```bash
make web-scrape URL="https://news.site.com"       # Scrape website
make test-site URL="https://myapp.com"            # Test website
make web-monitor URL="https://api.service.com"    # Monitor endpoint
```

### Production
```bash
npm run prod             # Start production environment
npm run build            # Build all packages
npm run build:frontend   # Build frontend only
npm run build:backend    # Build backend only
```

### Testing
```bash
npm run test             # Run all tests
npm run test:unit        # Run unit tests
npm run test:integration # Run integration tests
npm run test:e2e         # Run end-to-end tests
```

### Utilities
```bash
npm run lint             # Lint all packages
npm run format           # Format code
npm run security:audit   # Security audit
npm run migrate:validate # Validate migration
```

## 🎯 Core Components

### 🎭 Enhanced Chain-of-Debate Protocol Usage

#### Terminal Interface (Recommended)
```bash
# Local-only debate (zero cost, maximum privacy)
make cod-local TOPIC="Should we prioritize local AI models for enterprise?"

# Hybrid debate (best of both worlds)
make cod-hybrid TOPIC="Cloud migration strategy evaluation"

# Privacy-first debate (sensitive topics)
make cod-privacy TOPIC="Employee performance evaluation criteria"
```

#### Python API
```python
# Enhanced local+API debate
from enhanced_orchestrator import EnhancedCoDOrchestrator, DebateMode

orchestrator = EnhancedCoDOrchestrator({
    "enable_local_models": True,
    "max_rounds": 3
})

result = await orchestrator.run_cod_session(
    task={"content": "Should we migrate to microservices?"},
    mode=DebateMode.HYBRID,
    auto_select=True
)

print(f"Consensus: {result.consensus}")
print(f"Local models used: {result.metadata['local_models_used']}")
print(f"Total cost: ${result.metadata['total_cost']:.4f}")
print(f"Privacy score: {result.metadata['privacy_score']*100:.1f}%")
```

```python
# Full orchestration
from cod_protocol import CoDOrchestrator

orchestrator = CoDOrchestrator({
    "max_rounds": 3,
    "enable_shadow_llm": True,
    "enable_auditor": True
})

result = await orchestrator.run_cod_session({
    "task_id": "decision_001",
    "content": "Evaluate cloud migration strategy",
    "participants": ["gpt-4", "claude-3-opus", "gemini-pro"]
})
```

### 🤖 Local LLM Usage

#### Terminal Interface (80% Usage)
```bash
# Direct local model chat
make local-chat TEXT="Explain quantum computing in simple terms"

# Quick development decisions
make dev-decision DECISION="Should we use React or Vue for this component?"

# Performance testing
make test-cod-performance
```

#### Python API (20% Usage)
```python
# Local model management
from local_models import local_model_manager

# Get available models
models = await local_model_manager.get_available_models()
print(f"Available: {models}")

# Select best model for task
best_model = await local_model_manager.select_best_model_for_task(
    task_type="coding",
    requirements={"fast_response": True}
)

# Generate response
model = await local_model_manager.get_model(best_model)
response = await model.generate_response(
    "Write a Python function to calculate fibonacci numbers",
    context={"role": "CTO", "round": 1}
)
```

### 🔗 MCP Adapter Usage

```javascript
// GitHub Adapter
const github = new GitHubAdapter({
    token: process.env.GITHUB_TOKEN,
    organization: "my-org"
});

const issues = await github.listIssues({
    repository: "my-repo",
    state: "open"
});
```

## 🔧 Configuration

### Environment Variables

```bash
# Core API Keys (Optional - local models work without these)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/supermcp
REDIS_URL=redis://localhost:6379

# Voice System
ELEVENLABS_API_KEY=your-elevenlabs-key
DEEPGRAM_API_KEY=your-deepgram-key

# External Integrations
GITHUB_TOKEN=your-github-token
NOTION_TOKEN=your-notion-token
TELEGRAM_BOT_TOKEN=your-telegram-token

# Monitoring
LANGWATCH_API_KEY=your-langwatch-key
SENTRY_DSN=your-sentry-dsn
```

### Configuration Files

```yaml
# config/config.yml
debate_config:
  max_rounds: 3
  timeout_per_round: 120
  consensus_threshold: 0.75
  enable_shadow_llm: true
  enable_auditor: true

models:
  default_models: ["gpt-4", "claude-3-sonnet"]
  temperament_profiles:
    analytical: {temperature: 0.3, top_p: 0.8}
    creative: {temperature: 0.9, top_p: 0.95}

performance:
  cache_ttl: 300
  max_cache_size: 1000
  circuit_breaker_timeout: 30
```

## 📊 Monitoring & Observability

### System Health (Terminal-First)
```bash
# Check all services
make status

# Comprehensive health check
make health-check

# View live logs
make logs-tail

# Search logs
make logs-search QUERY="error"

# Check fallback systems
make fallback-status

# Service discovery status
make service-discovery
```

### Local Model Performance
```bash
# Check Ollama status
make local-status

# List available models with specs
make local-models

# Test local model performance
make test-cod-performance
```

### Performance Monitoring
- **Real-time Metrics**: Request rates, response times, error rates
- **Circuit Breaker Status**: System resilience monitoring
- **Cache Performance**: Hit rates and optimization insights
- **Database Metrics**: Query performance and connection pooling
- **Voice System Analytics**: Processing latency and quality metrics

## 🚀 Deployment

### Development (Terminal-First)
```bash
# Start development environment
make docker-dev

# Check system status
make status

# Test everything works
make claude-test
```

### Hybrid System
```bash
# Optimized hybrid stack
make docker-hybrid

# Interactive startup menu
make start
```

### Staging
```bash
# Staging environment
docker-compose -f docker-compose.staging.yml up -d
```

### Production
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With SSL and monitoring
docker-compose -f docker-compose.enterprise.yml up -d
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f infrastructure/k8s/

# Monitor deployment
kubectl get pods -n supermcp
```

## 📚 Documentation

- [🤖 Claude Code Integration](CLAUDE.md) - Optimized workflows for maximum productivity
- [🌟 Enhanced CoD Setup](ENHANCED_COD_SETUP.md) - Complete local+API setup guide
- [🤖 Local LLM Guide](LOCAL_LLM_GUIDE.md) - Comprehensive local model documentation
- [🏗️ Architecture Guide](docs/architecture/) - Hybrid system architecture
- [🎭 CoD Protocol Guide](services/cod-protocol/README.md) - Enhanced Chain-of-Debate documentation
- [📖 API Documentation](docs/api/) - Complete API reference
- [🔧 Development Guide](docs/development/) - Development setup and guidelines

## 🧪 Testing

```bash
# Run all tests
npm run test

# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Performance tests
npm run test:performance

# Security tests
npm run test:security
```

## 🔒 Security

- **Enterprise Authentication**: Multi-factor authentication and SSO support
- **API Security**: Rate limiting, request validation, and CORS protection
- **Data Encryption**: End-to-end encryption for sensitive data
- **Secure Communications**: TLS/SSL for all network communications
- **Audit Logging**: Comprehensive security event logging
- **Vulnerability Scanning**: Automated security vulnerability detection

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development/CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/ultramcp.git
cd ultramcp

# Install dependencies
npm install
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes and commit
git commit -m 'feat: add amazing feature'

# Push and create a pull request
git push origin feature/amazing-feature
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **OpenAI, Anthropic, and Google** for their excellent LLM APIs
- **The MCP Community** for inspiration and collaboration
- **All Contributors** who helped make this project possible

---

<div align="center">

**🚀 UltraMCP - World's First Hybrid Local+API Multi-LLM Platform**

*80% Terminal-First • 20% Advanced Orchestration • 100% Privacy When Needed*

[Documentation](CLAUDE.md) • [Local LLM Guide](LOCAL_LLM_GUIDE.md) • [Issues](https://github.com/fmfg03/ultramcp/issues) • [Discussions](https://github.com/fmfg03/ultramcp/discussions)

</div>

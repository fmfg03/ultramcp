# 🚀 SuperMCP - Next-Generation AI Orchestration Platform

[![GitHub Stars](https://img.shields.io/github/stars/fmfg03/ultramcp?style=for-the-badge)](https://github.com/fmfg03/ultramcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg?style=for-the-badge)](https://nodejs.org/)

> **SuperMCP** is a comprehensive, enterprise-grade AI orchestration platform that combines Model Context Protocol (MCP) with advanced multi-LLM coordination, voice processing, and intelligent automation capabilities.

## 🌟 What is SuperMCP?

SuperMCP revolutionizes AI system orchestration by providing:

- **🎭 Chain-of-Debate Protocol**: Multi-LLM consensus systems with adversarial validation
- **🗣️ Voice System Integration**: Full-duplex voice AI with real-time processing
- **🔗 MCP Enterprise Support**: Advanced Model Context Protocol implementation
- **📊 Observatory & Monitoring**: Real-time system observability and analytics
- **🏗️ Modular Architecture**: Clean, scalable microservices design
- **🚀 Production Ready**: Enterprise-grade security, monitoring, and deployment

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
Redis
PostgreSQL

# Optional
Kubernetes (for production)
Nginx (for reverse proxy)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/fmfg03/ultramcp.git
cd ultramcp

# 2. Install dependencies
npm install
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env with your API keys and configuration

# 4. Start development environment
npm run dev

# 5. Access the applications
# Frontend: http://localhost:3000
# Backend API: http://localhost:3001
# Observatory: http://localhost:3002
# CoD Protocol Dashboard: http://localhost:8080
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

## 📋 Available Scripts

### Development
```bash
npm run dev              # Start development environment
npm run dev:backend      # Start backend only
npm run dev:frontend     # Start frontend only
npm run dev:services     # Start microservices
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

### 🎭 Chain-of-Debate Protocol Usage

```python
# Simple debate
from cod_protocol import quick_debate

result = await quick_debate(
    task_content="Should we migrate to microservices?",
    participants=["gpt-4", "claude-3-sonnet"]
)

print(f"Consensus: {result.consensus}")
print(f"Confidence: {result.confidence_score}%")
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

### 🗣️ Voice System Usage

```python
# Voice API
from voice_system import VoiceAPI

voice_api = VoiceAPI()
await voice_api.start_conversation(
    config={
        "language": "en-US",
        "voice_model": "neural-enhanced",
        "real_time": True
    }
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
# Core API Keys
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

### System Health
```bash
# Check system status
curl http://localhost:3001/api/health

# View metrics
curl http://localhost:3001/api/metrics

# Observatory dashboard
open http://localhost:3002
```

### Performance Monitoring
- **Real-time Metrics**: Request rates, response times, error rates
- **Circuit Breaker Status**: System resilience monitoring
- **Cache Performance**: Hit rates and optimization insights
- **Database Metrics**: Query performance and connection pooling
- **Voice System Analytics**: Processing latency and quality metrics

## 🚀 Deployment

### Development
```bash
# Local development
npm run dev

# With hot reload
npm run dev:watch
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

- [🏗️ Architecture Guide](docs/architecture/) - System architecture and design patterns
- [🚀 Deployment Guide](docs/deployment/) - Deployment strategies and configurations
- [📖 API Documentation](docs/api/) - Complete API reference
- [🔧 Development Guide](docs/development/) - Development setup and guidelines
- [🎭 CoD Protocol Guide](services/cod-protocol/README.md) - Chain-of-Debate detailed documentation
- [🗣️ Voice System Guide](services/voice-system/) - Voice processing documentation
- [📊 Observatory Guide](services/observatory/) - Monitoring and observability

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

**🚀 SuperMCP - Elevating AI Orchestration to Enterprise Level**

[Documentation](https://github.com/fmfg03/ultramcp/wiki) • [Issues](https://github.com/fmfg03/ultramcp/issues) • [Discussions](https://github.com/fmfg03/ultramcp/discussions)

</div>

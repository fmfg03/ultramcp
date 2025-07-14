# UltraMCP Enhanced Integrations

🚀 **Advanced AI Agent Orchestration Platform with Scientific Reasoning**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg?style=for-the-badge)](https://nodejs.org/)
[![SynLogic](https://img.shields.io/badge/SynLogic-Verified_Reasoning-success.svg?style=for-the-badge)](https://github.com/MiniMax-AI/SynLogic)
[![MiniMax](https://img.shields.io/badge/MiniMax_M1-Integrated-orange.svg?style=for-the-badge)](https://github.com/MiniMax-AI/MiniMax-M1)
[![Plandex](https://img.shields.io/badge/Plandex-Planning_Agent-brightgreen.svg?style=for-the-badge)](https://github.com/plandex-ai/plandex)

This repository contains enhanced integrations for UltraMCP that transform AI agents from subjective to scientific, featuring objective reasoning measurement, autonomous planning, advanced local models, and cloud-scale deployment capabilities.

## 🌟 What is UltraMCP Supreme Stack?

UltraMCP revolutionizes AI system orchestration with comprehensive service integration and hybrid architecture:

- **🔗 Complete Integration**: All 8 microservices fully integrated with zero loose components
- **🎭 Enhanced Chain-of-Debate Protocol**: Revolutionary local+API multi-LLM debates with 5 local models
- **🧠 Blockoli Code Intelligence**: Advanced semantic code search and analysis with Rust-powered indexing
- **🧠 Claude Code Memory**: Tree-sitter AST parsing + Qdrant semantic search + pattern analysis
- **🔒 Asterisk Security Suite**: Enterprise-grade security scanning and compliance validation
- **🗣️ Voice System Integration**: Full-duplex voice AI with real-time WebSocket processing
- **🤖 DeepClaude Metacognitive Engine**: Advanced reasoning and decision-making capabilities
- **🎯 Sam MCP Tool**: Autonomous agent with complete LangGraph integration and local LLM priority
- **🎛️ Control Tower Orchestration**: Central coordination hub for all microservices
- **⚡ Terminal-First Architecture**: 80% terminal commands + 20% advanced orchestration
- **🔒 Privacy-First Debates**: 100% local processing option for sensitive enterprise decisions
- **💰 Zero-Cost Local Operations**: Unlimited local model usage with API flexibility
- **🚀 Claude Code Optimized**: Purpose-built for Claude Code integration and developer productivity

## 🏛️ Complete Architecture Overview

```mermaid
graph TB
    subgraph "🌐 API Gateway Layer"
        API[Backend API Gateway]
        API --> |Proxy| SEC[Security Service]
        API --> |Proxy| BLK[Blockoli Service]
        API --> |Proxy| VCE[Voice Service]
        API --> |Proxy| DCP[DeepClaude Service]
        API --> |Proxy| MEM[Claude Memory Service]
        API --> |Proxy| COD[CoD Service]
        API --> |Proxy| CTL[Control Tower]
    end
    
    subgraph "🧠 Core Services Layer"
        SEC[🔒 Asterisk Security] --> |Scan Results| CTL
        BLK[🧠 Blockoli Intelligence] --> |Code Context| CTL
        MEM[🧠 Claude Code Memory] --> |Semantic Search| CTL
        VCE[🗣️ Voice System] --> |Audio Processing| CTL
        DCP[🤖 DeepClaude Engine] --> |Reasoning| CTL
        COD[🎭 CoD Protocol] --> |Debates| CTL
        SAM[🎯 Sam MCP Tool] --> |Autonomous Tasks| CTL
        CTL[🎛️ Control Tower] --> |Orchestration| ALL[All Services]
    end
    
    subgraph "💾 Data Layer"
        DB[(PostgreSQL)]
        REDIS[(Redis Cache)]
        SEC --> DB
        BLK --> DB
        VCE --> DB
        DCP --> DB
        COD --> DB
        CTL --> DB
        ALL --> REDIS
    end
    
    subgraph "🤖 Local AI Layer"
        OLL[Ollama Models]
        OLL --> |5 Models| COD
        OLL --> |Local Processing| BLK
        OLL --> |Voice AI| VCE
    end
    
    subgraph "🎯 Frontend & Monitoring"
        DASH[Observatory Dashboard]
        CLAUD[Claudia Visual Interface]
        WS[WebSocket Monitoring]
        API --> DASH
        CTL --> WS
        WS --> CLAUD
    end
```

## 📁 Complete Project Structure

```
ultramcp/
├── 🎯 apps/                           # Main Applications
│   ├── 📱 backend/                     # Core API Gateway & MCP Server
│   │   ├── src/
│   │   │   ├── adapters/               # 20+ MCP Adapters
│   │   │   ├── controllers/            # Request Controllers
│   │   │   ├── services/               # Business Logic
│   │   │   ├── middleware/             # Auth, Monitoring, Security
│   │   │   └── index.js                # 🌐 Complete API Gateway with Proxy Routing
│   │   └── package.json                # ✅ Updated with http-proxy-middleware
│   └── 🌐 frontend/                    # React Dashboard
├── 🧠 services/                        # 🔗 Fully Integrated Microservices
│   ├── 🎭 chain-of-debate/             # Enhanced CoD Protocol (7000+ lines)
│   │   ├── orchestrator.py             # Multi-LLM Orchestration
│   │   ├── enhanced_orchestrator.py    # Local+API Hybrid Engine
│   │   ├── shadow_llm.py               # Adversarial Analysis
│   │   ├── counterfactual_auditor.py   # External Validation
│   │   └── entrypoint.py               # FastAPI Service Entry
│   ├── 🔒 asterisk-mcp/                # ✅ Security & Compliance Suite
│   │   ├── asterisk_security_service.py # FastAPI Security Service
│   │   ├── asterisk_security_client.py # Security Scanner Client
│   │   ├── Dockerfile                  # Container Configuration
│   │   └── requirements.txt            # Python Dependencies
│   ├── 🧠 blockoli-mcp/                # ✅ Code Intelligence Service
│   │   ├── blockoli_service.py         # FastAPI Code Intelligence Service
│   │   ├── blockoli_client.py          # Blockoli Integration Client
│   │   ├── code_intelligent_cod.py     # Code-Intelligent CoD Protocol
│   │   ├── Dockerfile                  # Container Configuration
│   │   └── requirements.txt            # Python Dependencies
│   ├── 🗣️ voice-system/                # ✅ Voice Processing Service
│   │   ├── voice_service.py            # FastAPI Voice Service with WebSocket
│   │   ├── core/voice_api.py           # Voice Processing Engine
│   │   ├── voice_api_langwatch.py      # Langwatch Integration
│   │   ├── Dockerfile                  # Container Configuration
│   │   └── requirements.txt            # Python Dependencies
│   ├── 🤖 deepclaude/                  # ✅ Metacognitive Reasoning Service
│   │   ├── deepclaude_service.py       # FastAPI Reasoning Service
│   │   ├── deepclaude_client.py        # Reasoning Engine Client
│   │   ├── Dockerfile                  # Container Configuration
│   │   └── requirements.txt            # Python Dependencies
│   ├── 🎛️ control-tower/               # ✅ Central Orchestration Service
│   │   ├── control_tower_service.js    # Node.js Orchestration Service
│   │   ├── Dockerfile                  # Container Configuration
│   │   └── package.json                # Node.js Dependencies
│   ├── 🔬 langgraph-studio/            # LangGraph Integration
│   └── 📊 observatory/                 # System Monitoring
├── 💾 database/                        # ✅ Complete Database Integration
│   └── schemas/
│       └── init.sql                    # 🗄️ Unified Schema for All Services
├── 🛠️ scripts/                        # Enhanced Automation Scripts
│   ├── verify-integration.sh           # ✅ Complete Integration Verification
│   ├── enhanced-cod-terminal.py        # Enhanced CoD with Local Models
│   ├── local-llm-chat.sh              # Local Model Chat
│   └── health-check.sh                # System Health Monitoring
├── 🏗️ infrastructure/                 # Infrastructure as Code
├── 📚 docs/                           # Comprehensive Documentation
├── 🧪 tests/                          # Test Suites
├── 🛠️ tools/                          # Development Tools
├── 🎨 integrations/                   # External Integrations
│   └── claudia/                       # Claudia Visual Interface
├── stagewise-integration/             # 🖱️ Browser-First AI Integration
│   ├── install-stagewise.sh          # Automated setup script
│   ├── service/src/index.js           # DOM context capture microservice
│   ├── framework-toolbars/react/      # React/Next.js integration
│   └── examples/                      # Usage examples and demos
├── 🔧 Makefile                        # ✅ Terminal-First Command Interface
├── 🐳 docker-compose.hybrid.yml       # ✅ Complete Service Orchestration
├── ⚙️ .env.example                    # ✅ Complete Environment Configuration
└── 📖 CLAUDE.md                       # Claude Code Integration Guide
```

## ✨ Complete Feature Set

### 🔗 Zero Loose Components Integration
- **✅ Complete Service Integration**: All 7 microservices fully integrated and orchestrated
- **✅ API Gateway Routing**: Unified proxy routing to all services with error handling
- **✅ Database Schema Integration**: Comprehensive schema supporting all services
- **✅ Environment Configuration**: Complete service URLs and configuration management
- **✅ Health Monitoring**: System-wide health checks and status aggregation
- **✅ Docker Orchestration**: All services properly containerized with dependencies
- **✅ Cross-Service Communication**: WebSocket and REST API integration
- **✅ Integration Verification**: `make verify-integration` ensures no loose components

### 🎭 Enhanced Chain-of-Debate Protocol
- **Multi-LLM Orchestration**: Coordinate multiple AI models in structured debates
- **Local+API Hybrid Mode**: Seamlessly blend 5 local models with cloud APIs
- **Dynamic Role Assignment**: Context-aware role allocation (CFO, CTO, Analyst, etc.)
- **Shadow LLM Analysis**: Adversarial criticism and bias detection
- **Counterfactual Auditing**: External validation with scenario analysis
- **Meta-Fusion Engine**: Advanced consensus algorithms with 6 fusion strategies
- **Privacy Modes**: 100% local processing for sensitive topics
- **Cost Optimization**: Intelligent model selection for budget control

### 🧠 Blockoli Code Intelligence
- **Semantic Code Search**: Advanced code indexing and pattern recognition
- **Project Analysis**: Comprehensive codebase analysis and insights
- **Code-Intelligent Debates**: AI debates with deep code context understanding
- **Architecture Analysis**: System architecture evaluation and recommendations
- **Pattern Recognition**: Identify code patterns and anti-patterns
- **Integration with CoD**: Code-aware multi-LLM debates for technical decisions

### 🧠 Claude Code Memory (NEW!)
- **Tree-sitter AST Parsing**: Advanced syntax analysis for 20+ programming languages
- **Qdrant Semantic Search**: Vector-based semantic code search with sentence transformers
- **Pattern Analysis**: Comprehensive code pattern detection (design patterns, anti-patterns, smells)
- **Memory-Enhanced Debates**: CoD Protocol with intelligent code context injection
- **Quality Assessment**: Automated code quality scoring and recommendations
- **Project Learning**: Intelligent codebase indexing and pattern recognition
- **Cache Management**: Multi-tier caching for optimal performance

### 🔒 Asterisk Security Suite
- **Vulnerability Scanning**: Comprehensive security vulnerability detection
- **Compliance Checking**: SOC2, HIPAA, GDPR compliance validation
- **Threat Modeling**: Advanced threat analysis and risk assessment
- **Security Scoring**: Automated security posture evaluation
- **Integration Scanning**: Scan entire UltraMCP stack for vulnerabilities
- **Real-time Monitoring**: Continuous security monitoring and alerting

### 🗣️ Voice System Integration
- **Real-time Processing**: Low-latency voice recognition and synthesis
- **WebSocket Support**: Real-time voice streaming capabilities
- **AI Voice Conversations**: Full-duplex voice AI interactions
- **Session Management**: Voice session tracking and analytics
- **Multi-format Support**: WAV, MP3, and streaming audio formats
- **Langwatch Integration**: Advanced voice analytics and monitoring

### 🤖 DeepClaude Metacognitive Engine
- **Advanced Reasoning**: Multi-layered reasoning and decision-making
- **Metacognitive Analysis**: Self-reflective reasoning processes
- **Context-Aware Processing**: Deep context understanding and analysis
- **Reasoning Modes**: Analytical, creative, and strategic reasoning modes
- **Insight Generation**: Automated insight extraction and reporting
- **Integration with CoD**: Enhanced reasoning for debate participants

### 🎯 Sam MCP Tool (NEW!)
- **LangGraph Integration**: Complete MCP tool definition with typed schemas
- **Autonomous Execution**: Fully autonomous task execution with local LLM priority
- **Multi-Task Support**: Research, coding, analysis, creative, reasoning, and batch processing
- **Local Model Priority**: Preferential use of Mistral, Llama, DeepSeek, and Qwen models
- **Intelligent Fallback**: Automatic fallback between models for optimal results
- **Memory Injection**: Complete project context injection for informed decisions
- **Batch Processing**: Execute multiple tasks with dependency management
- **Escalation Handling**: Smart escalation to human-in-the-loop when needed

### 🎛️ Control Tower Orchestration
- **Central Coordination**: Unified coordination hub for all microservices
- **Multi-Service Workflows**: Complex workflows spanning multiple services
- **Real-time Monitoring**: Live monitoring of all system components
- **WebSocket Integration**: Real-time communication and updates
- **Health Aggregation**: System-wide health monitoring and reporting
- **Automated Orchestration**: Intelligent service coordination and load balancing

### 🤖 Local LLM Integration
- **5 Local Models**: Qwen 2.5 14B, Llama 3.1 8B, Codellama 7B, Mistral 7B, Phi3 3.8B
- **Zero-Cost Operations**: Unlimited local processing without API costs
- **Intelligent Model Selection**: Automatic model selection based on task requirements
- **Performance Optimization**: Optimized inference for production environments
- **Privacy Guarantee**: 100% local processing for sensitive data
- **Hybrid Fallback**: Seamless fallback to API models when needed

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

# 3. Set up environment
cp .env.example .env
# Edit .env with your API keys (optional for local-only usage)

# 4. Start complete integrated system
make start

# 5. Verify integration (ensures no loose components)
make verify-integration

# 6. Quick test all services
make health-check
make local-chat TEXT="Test all integrated services"
make cod-local TOPIC="Test the complete integration"
```

### 5. Stagewise Browser Integration (NEW!)

Add browser-first AI agent orchestration to your web applications:

```bash
# Install Stagewise integration
cd stagewise-integration
./install-stagewise.sh

# Add to your React project
npm install @ultramcp/stagewise-react

# Add toolbar to your app (see examples/)
# Ctrl+Alt+Click any DOM element for instant AI analysis
```

**Results**: Click any UI element → get contextual Chain of Debate, Plandex planning, or component analysis!

### Docker Deployment

```bash
# Development with full integration
make docker-dev

# Optimized hybrid system (recommended)
make docker-hybrid

# Production with all services
docker-compose -f docker-compose.hybrid.yml up -d

# Enterprise with monitoring
docker-compose -f docker-compose.enterprise.yml up -d
```

## 📋 Terminal-First Commands (Claude Code Optimized)

### Core System Operations (80% Usage)
```bash
make start                    # Interactive startup menu
make status                   # Check all 7 services
make verify-integration       # Ensure no loose components (NEW!)
make health-check            # Comprehensive health check
make logs                    # View system logs
make backup                  # Create system backup
```

### AI Operations (Local + API Hybrid)
```bash
# Quick AI interactions
make chat TEXT="Your question"                    # OpenAI API chat
make local-chat TEXT="Your question"              # Local model chat (zero cost)
make analyze FILE="data.csv"                      # AI data analysis
make research URL="https://example.com"           # Web research + AI

# Enhanced Chain-of-Debate Protocol
make cod-local TOPIC="Your debate topic"          # 100% local debate
make cod-hybrid TOPIC="Your debate topic"         # Mix local + API
make cod-privacy TOPIC="Sensitive topic"          # Privacy-first mode
make cod-cost-optimized TOPIC="Budget decision"   # Minimize API costs
```

### Code Intelligence Operations (NEW!)
```bash
# Blockoli code intelligence
make index-project PROJECT="/path/to/code" NAME="my-project"  # Index codebase
make code-search QUERY="authentication logic" PROJECT="my-project"  # Semantic search
make code-debate TOPIC="Refactor user auth" PROJECT="my-project"   # Code-intelligent debate
make architecture-analysis FOCUS="security" PROJECT="my-project"   # Architecture analysis
make pattern-analysis PATTERN="singleton" PROJECT="my-project"     # Pattern analysis
make intelligent-code-review FILE="src/auth.py" PROJECT="my-project"  # AI code review
```

### Claude Code Memory Operations (NEW!)
```bash
# Advanced semantic code analysis
make memory-index PROJECT="/path/to/code" NAME="my-project"   # Index for semantic memory
make memory-search QUERY="authentication patterns" PROJECT="my-project"  # Smart search
make memory-analyze FILE="src/auth.py" PROJECT="my-project"  # Pattern analysis
make memory-learn-codebase                                   # Learn UltraMCP codebase
make memory-debate TOPIC="architecture decision" PROJECT="my-project"  # Memory-enhanced debates
make memory-quality-check FILE="src/main.py" PROJECT="my-project"      # Quality assessment
make memory-explore                                          # Interactive exploration
```

### Security Operations (NEW!)
```bash
# Asterisk security suite
make security-scan PATH="/app" TYPE="vulnerability"  # Vulnerability scan
make compliance-check FRAMEWORK="SOC2" TARGET="/app"  # Compliance validation
make threat-model SYSTEM="web-app" SCOPE="authentication"  # Threat modeling
make security-report TYPE="summary" FORMAT="json"   # Generate security report
```

### Voice System Operations (NEW!)
```bash
# Voice system integration
make voice-session TYPE="conversation" AI="enabled"  # Start voice session
make voice-transcribe FILE="audio.wav"              # Transcribe audio
make voice-analyze SESSION="session-123"            # Analyze voice session
```

### Local LLM Management
```bash
make local-models                                 # List 5 available models
make local-status                                 # Check Ollama status
make local-pull MODEL="llama3.2"                  # Download new model
make local-remove MODEL="old-model"               # Remove model
make test-cod-performance                         # Test local model performance
```

### System Monitoring & Integration
```bash
# Integration verification
make verify-integration                           # Comprehensive integration check
make service-discovery                           # Check service discovery
make api-gateway-status                          # API Gateway routing status
make cross-service-test                          # Test cross-service communication

# Health monitoring
make health-aggregation                          # Aggregate health from all services
make performance-metrics                         # System performance metrics
make websocket-status                           # WebSocket connection status
```

### Development & Debugging
```bash
# Development environment
make docker-dev                                  # Development with hot reload
make logs-tail                                  # Follow live logs
make logs-search QUERY="error"                  # Search logs

# Service-specific debugging
make debug-service SERVICE="blockoli"           # Debug specific service
make restart-service SERVICE="voice-system"     # Restart specific service
make scale-service SERVICE="cod-service" REPLICAS=3  # Scale service
```

## 🎯 Complete Service Integration Guide

### 🔗 API Gateway Routing

All services are accessible through the unified API Gateway:

```bash
# Security service (Asterisk)
curl http://sam.chat:3001/api/security/scan
curl http://sam.chat:3001/api/security/compliance

# Code intelligence (Blockoli)
curl http://sam.chat:3001/api/blockoli/search
curl http://sam.chat:3001/api/blockoli/analyze

# Voice system
curl http://sam.chat:3001/api/voice/sessions
curl http://sam.chat:3001/api/voice/transcribe

# DeepClaude reasoning
curl http://sam.chat:3001/api/deepclaude/reason
curl http://sam.chat:3001/api/deepclaude/insights

# Chain-of-Debate
curl http://sam.chat:3001/api/cod/debate
curl http://sam.chat:3001/api/cod/status

# Control Tower orchestration
curl http://sam.chat:3001/api/orchestrate/workflow
curl http://sam.chat:3001/api/orchestrate/status

# System health aggregation
curl http://sam.chat:3001/api/health
curl http://sam.chat:3001/api/status
```

### 🎭 Enhanced Chain-of-Debate Usage

#### Terminal Interface (Recommended - 80% Usage)
```bash
# Local-only debate (zero cost, maximum privacy)
make cod-local TOPIC="Should we prioritize local AI models for enterprise?"

# Hybrid debate with code intelligence
make code-debate TOPIC="Microservices vs monolith architecture" PROJECT="my-app"

# Privacy-first debate with security analysis
make cod-privacy TOPIC="Employee data handling policies"

# Cost-optimized debate
make cod-cost-optimized TOPIC="Cloud migration strategy"
```

#### Python API (20% Usage)
```python
# Enhanced local+API debate with full integration
from enhanced_orchestrator import EnhancedCoDOrchestrator, DebateMode

orchestrator = EnhancedCoDOrchestrator({
    "enable_local_models": True,
    "enable_code_intelligence": True,
    "enable_security_analysis": True,
    "enable_voice_input": True,
    "max_rounds": 3
})

result = await orchestrator.run_integrated_cod_session(
    task={"content": "Should we migrate to microservices?"},
    mode=DebateMode.HYBRID,
    project_context="my-enterprise-app",
    security_requirements=["SOC2", "HIPAA"],
    auto_select=True
)

print(f"Consensus: {result.consensus}")
print(f"Code insights: {result.metadata['code_insights']}")
print(f"Security score: {result.metadata['security_score']}")
print(f"Privacy score: {result.metadata['privacy_score']*100:.1f}%")
print(f"Total cost: ${result.metadata['total_cost']:.4f}")
```

### 🧠 Code Intelligence Integration

```python
# Blockoli code intelligence with CoD integration
from blockoli_client import BlockoliCodeContext
from code_intelligent_cod import CodeIntelligentCoDOrchestrator

# Index project for semantic search
context = BlockoliCodeContext()
await context.index_codebase("/path/to/project", "my-project")

# Run code-intelligent debate
orchestrator = CodeIntelligentCoDOrchestrator()
result = await orchestrator.run_code_intelligent_debate(
    topic="Refactor authentication system",
    project_name="my-project",
    intelligence_mode="deep_analysis",
    include_patterns=["*.py", "*.js"],
    focus_areas=["security", "performance"]
)
```

### 🔒 Security Integration

```python
# Asterisk security integration
from asterisk_security_client import SecurityScanner

scanner = SecurityScanner()

# Comprehensive security scan
scan_result = await scanner.vulnerability_scan(
    target_path="/app",
    scan_type="comprehensive",
    include_compliance=["SOC2", "HIPAA"]
)

# Generate security report
report = await scanner.generate_report(
    scan_id=scan_result.scan_id,
    format="detailed",
    include_recommendations=True
)
```

## 🔧 Complete Environment Configuration

### Core Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@ultramcp-postgres:5432/ultramcp
POSTGRES_PASSWORD=your-secure-password
REDIS_URL=redis://:redis_secure@ultramcp-redis:6379/0
REDIS_PASSWORD=your-redis-password

# Service URLs (Auto-configured in Docker)
COD_SERVICE_URL=http://ultramcp-cod-service:8001
ASTERISK_SERVICE_URL=http://ultramcp-asterisk-mcp:8002
BLOCKOLI_SERVICE_URL=http://ultramcp-blockoli:8003
VOICE_SERVICE_URL=http://ultramcp-voice:8004
DEEPCLAUDE_SERVICE_URL=http://ultramcp-deepclaude:8006
CONTROL_TOWER_URL=http://ultramcp-control-tower:8007

# API Keys (Optional - local models work without these)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Service-Specific Configuration
ASTERISK_SECURITY_LEVEL=strict
ASTERISK_COMPLIANCE_FRAMEWORKS=SOC2,HIPAA,GDPR
BLOCKOLI_SEMANTIC_SEARCH_ENABLED=true
VOICE_AI_ENABLED=true
DEEPCLAUDE_REASONING_DEPTH=deep
CONTROL_TOWER_WEBSOCKET_ENABLED=true

# Local LLM Configuration
OLLAMA_BASE_URL=http://ultramcp-ollama:11434
OLLAMA_MODELS=qwen2.5:14b,llama3.1:8b,codellama:7b,mistral:7b,phi3:3.8b

# Monitoring and Observability
ENABLE_METRICS=true
ENABLE_HEALTH_CHECKS=true
LANGWATCH_API_KEY=your-langwatch-key
```

## 📊 Complete Monitoring & Integration Verification

### System Health Monitoring
```bash
# Comprehensive integration verification
make verify-integration                    # Zero loose components check

# Service health monitoring
make health-check                         # All services health check
make service-discovery                    # Service discovery status
make api-gateway-status                   # API Gateway routing status

# Performance monitoring
make performance-metrics                  # System performance metrics
make cross-service-test                   # Test inter-service communication
make websocket-status                     # Real-time connection status
```

### Integration Verification Features
- **✅ Docker Orchestration Check**: Verifies all 7 services in docker-compose.hybrid.yml
- **✅ API Gateway Verification**: Confirms proxy routing for all services
- **✅ Database Schema Validation**: Ensures complete schema for all services
- **✅ Environment Configuration Check**: Validates service URLs and configuration
- **✅ Cross-Service Integration Test**: Tests inter-service communication
- **✅ Health Endpoint Verification**: Confirms health endpoints for all services
- **✅ WebSocket Connection Test**: Validates real-time communication channels

### Real-time Monitoring Dashboard
Access the integrated monitoring at:
- **System Health**: `http://sam.chat:3001/api/health`
- **Service Status**: `http://sam.chat:3001/api/status`
- **Observatory Dashboard**: `http://sam.chat:3000`
- **Control Tower**: `http://sam.chat:8007` (WebSocket: `ws://sam.chat:8008`)

## 🚀 Production Deployment

### Complete Docker Deployment
```bash
# Development with all services
make docker-dev

# Optimized hybrid production
make docker-hybrid

# Enterprise deployment with monitoring
docker-compose -f docker-compose.enterprise.yml up -d
```

### Kubernetes Deployment
```bash
# Deploy complete integrated stack
kubectl apply -f infrastructure/k8s/

# Monitor all services
kubectl get pods -n ultramcp
kubectl get services -n ultramcp
```

### Health Check Endpoints
All services provide standardized health endpoints:
- **API Gateway**: `http://sam.chat:3001/health`
- **CoD Service**: `http://sam.chat:8001/health`
- **Security Service**: `http://sam.chat:8002/health`
- **Blockoli Service**: `http://sam.chat:8003/health`
- **Voice Service**: `http://sam.chat:8004/health`
- **DeepClaude Service**: `http://sam.chat:8006/health`
- **Control Tower**: `http://sam.chat:8007/health`

## 📚 Complete Documentation

- [🤖 Claude Code Integration](CLAUDE.md) - Complete terminal-first workflows
- [🔗 Integration Verification Guide](docs/integration-verification.md) - Zero loose components guide
- [🧠 Blockoli Code Intelligence](docs/blockoli-integration.md) - Code intelligence documentation
- [🔒 Asterisk Security Suite](docs/security-integration.md) - Security and compliance guide
- [🗣️ Voice System Integration](docs/voice-integration.md) - Voice processing documentation
- [🤖 DeepClaude Reasoning](docs/deepclaude-integration.md) - Metacognitive reasoning guide
- [🎛️ Control Tower Orchestration](docs/control-tower.md) - Service orchestration guide
- [🎭 Enhanced CoD Protocol](docs/enhanced-cod.md) - Complete CoD documentation
- [📖 API Documentation](docs/api/) - Complete API reference
- [🏗️ Architecture Guide](docs/architecture/) - Complete system architecture
- [🔧 Development Guide](docs/development/) - Development and contribution guide

## 🧪 Complete Testing Suite

```bash
# Integration tests (recommended)
make verify-integration                    # Complete integration verification
make test-cross-services                   # Cross-service communication tests
make test-api-gateway                      # API Gateway routing tests

# Service-specific tests
npm run test:security                      # Security service tests
npm run test:blockoli                      # Code intelligence tests
npm run test:voice                         # Voice system tests
npm run test:deepclaude                    # Reasoning engine tests
npm run test:control-tower                 # Orchestration tests

# System tests
npm run test:performance                   # Performance tests
npm run test:integration                   # Full integration tests
npm run test:e2e                          # End-to-end tests
npm run test:security                      # Security vulnerability tests
```

## 🔒 Enterprise Security

- **Complete Integration Security**: All 7 services secured with unified authentication
- **API Gateway Protection**: Rate limiting, CORS, and request validation
- **Service-to-Service Authentication**: Secure inter-service communication
- **Asterisk Security Integration**: Comprehensive vulnerability scanning
- **Compliance Validation**: SOC2, HIPAA, GDPR compliance checking
- **Zero-Trust Architecture**: No loose components or unprotected endpoints
- **Audit Logging**: Complete audit trail across all services
- **End-to-End Encryption**: Encrypted communication between all services

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development/CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone
git clone https://github.com/yourusername/ultramcp.git
cd ultramcp

# Complete setup
make setup

# Verify integration before development
make verify-integration

# Start development environment
make docker-dev

# Create feature branch
git checkout -b feature/amazing-integration

# Test integration after changes
make verify-integration
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **OpenAI, Anthropic, and Google** for their excellent LLM APIs
- **Blockoli Team** for the revolutionary code intelligence platform
- **The MCP Community** for inspiration and collaboration
- **All Contributors** who helped achieve complete integration

---

<div align="center">

**🚀 UltraMCP Supreme Stack - Complete Integrated AI Platform**

*Zero Loose Components • 100% Service Integration • 80% Terminal-First • 20% Advanced Orchestration*

**✅ All 8 Services Fully Integrated ✅**

[Complete Documentation](CLAUDE.md) • [Integration Guide](docs/integration-verification.md) • [Issues](https://github.com/fmfg03/ultramcp/issues) • [Discussions](https://github.com/fmfg03/ultramcp/discussions)

</div>
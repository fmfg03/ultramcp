# 🌐 UltraMCP Supreme Stack - Complete API Documentation

## Overview

The UltraMCP Supreme Stack provides a unified API Gateway that routes to all 7 integrated microservices. All services are accessible through `http://sam.chat:3001/api/` with automatic proxy routing, error handling, and health monitoring.

## 🚀 Quick Start

### Base URL
```
http://sam.chat:3001/api/
```

### Authentication
Most endpoints require API keys set in environment variables:
```bash
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Health Check
```bash
curl http://sam.chat:3001/api/health
```

## 🔗 API Gateway Endpoints

### System Health & Status

#### GET /api/health
System-wide health aggregation across all 7 services.

**Response:**
```json
{
  "overall_health": "healthy",
  "healthy_services": 7,
  "total_services": 7,
  "services": {
    "cod": {"status": "healthy", "url": "http://ultramcp-cod-service:8001"},
    "asterisk": {"status": "healthy", "url": "http://ultramcp-asterisk-mcp:8002"},
    "blockoli": {"status": "healthy", "url": "http://ultramcp-blockoli:8003"},
    "voice": {"status": "healthy", "url": "http://ultramcp-voice:8004"},
    "deepclaude": {"status": "healthy", "url": "http://ultramcp-deepclaude:8006"},
    "controlTower": {"status": "healthy", "url": "http://ultramcp-control-tower:8007"}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/status
System status aggregation with service availability.

**Response:**
```json
{
  "system": "UltraMCP Supreme Stack",
  "api_gateway": "operational",
  "services": {
    "cod": {"status": "available", "data": {...}},
    "asterisk": {"status": "available", "data": {...}},
    "blockoli": {"status": "available", "data": {...}},
    "voice": {"status": "available", "data": {...}},
    "deepclaude": {"status": "available", "data": {...}},
    "controlTower": {"status": "available", "data": {...}}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔒 Security Service API (Asterisk MCP)

Base path: `/api/security`

### Vulnerability Scanning

#### POST /api/security/scan
Start a comprehensive vulnerability scan.

**Request:**
```json
{
  "target_path": "/app",
  "scan_type": "comprehensive",
  "options": {
    "max_depth": 10,
    "security_level": "strict",
    "include_compliance": ["SOC2", "HIPAA"]
  }
}
```

**Response:**
```json
{
  "scan_id": "scan_123456",
  "status": "started",
  "target_path": "/app",
  "estimated_duration": "5-10 minutes",
  "scan_type": "comprehensive"
}
```

#### GET /api/security/scan/{scan_id}
Get scan results and status.

**Response:**
```json
{
  "scan_id": "scan_123456",
  "status": "completed",
  "vulnerability_count": 3,
  "risk_score": 7.2,
  "results": {
    "high_severity": 1,
    "medium_severity": 2,
    "low_severity": 0,
    "vulnerabilities": [
      {
        "type": "SQL_INJECTION",
        "severity": "HIGH",
        "file_path": "/app/src/auth.py",
        "line_number": 42,
        "description": "Potential SQL injection vulnerability",
        "recommendation": "Use parameterized queries"
      }
    ]
  }
}
```

### Compliance Checking

#### POST /api/security/compliance
Run compliance validation.

**Request:**
```json
{
  "framework": "SOC2",
  "target_system": "/app",
  "scope": ["authentication", "data_protection"]
}
```

**Response:**
```json
{
  "check_id": "compliance_789",
  "framework": "SOC2",
  "compliance_score": 85.5,
  "status": "completed",
  "results": {
    "passed_controls": 17,
    "failed_controls": 3,
    "total_controls": 20,
    "recommendations": [
      "Implement multi-factor authentication",
      "Add audit logging for sensitive operations"
    ]
  }
}
```

### Threat Modeling

#### POST /api/security/threat-model
Generate threat model analysis.

**Request:**
```json
{
  "system_type": "web_application",
  "scope": "authentication_system",
  "assets": ["user_data", "session_tokens"],
  "trust_boundaries": ["client", "api", "database"]
}
```

**Response:**
```json
{
  "model_id": "threat_456",
  "threats_identified": 12,
  "high_priority_threats": 3,
  "mitigation_strategies": [
    {
      "threat": "Session hijacking",
      "likelihood": "medium",
      "impact": "high",
      "mitigation": "Implement secure session management"
    }
  ]
}
```

## 🧠 Code Intelligence API (Blockoli)

Base path: `/api/blockoli`

### Project Indexing

#### POST /api/blockoli/index
Index a codebase for semantic search.

**Request:**
```json
{
  "project_name": "my-app",
  "project_path": "/path/to/project",
  "include_patterns": ["*.py", "*.js", "*.ts"],
  "exclude_patterns": ["node_modules", "__pycache__"]
}
```

**Response:**
```json
{
  "index_id": "index_123",
  "project_name": "my-app",
  "status": "indexing",
  "total_files": 245,
  "estimated_time": "2-3 minutes"
}
```

#### GET /api/blockoli/index/{index_id}
Get indexing status and results.

**Response:**
```json
{
  "index_id": "index_123",
  "project_name": "my-app",
  "status": "completed",
  "total_files": 245,
  "indexed_files": 243,
  "skipped_files": 2,
  "index_size": "15.2 MB",
  "completion_time": "2m 45s"
}
```

### Semantic Code Search

#### POST /api/blockoli/search
Perform semantic code search.

**Request:**
```json
{
  "project_name": "my-app",
  "query": "authentication logic",
  "search_type": "semantic",
  "max_results": 10,
  "include_context": true
}
```

**Response:**
```json
{
  "search_id": "search_789",
  "query": "authentication logic",
  "results_count": 7,
  "results": [
    {
      "file_path": "/src/auth/login.py",
      "line_number": 25,
      "relevance_score": 0.92,
      "code_snippet": "def authenticate_user(username, password):",
      "context": {
        "function_name": "authenticate_user",
        "class_name": "AuthManager",
        "description": "Main user authentication function"
      }
    }
  ]
}
```

### Code Analysis

#### POST /api/blockoli/analyze
Analyze code patterns and architecture.

**Request:**
```json
{
  "project_name": "my-app",
  "analysis_type": "architecture",
  "focus_areas": ["security", "performance", "maintainability"]
}
```

**Response:**
```json
{
  "analysis_id": "analysis_456",
  "project_name": "my-app",
  "analysis_type": "architecture",
  "insights": {
    "security_score": 7.8,
    "performance_score": 8.5,
    "maintainability_score": 6.9,
    "patterns_detected": ["MVC", "Repository", "Factory"],
    "anti_patterns": ["God Object in UserManager"],
    "recommendations": [
      "Split UserManager into smaller, focused classes",
      "Implement input validation in API layer"
    ]
  }
}
```

### Code-Intelligent Debates

#### POST /api/blockoli/code-debate
Run AI debate with code context.

**Request:**
```json
{
  "project_name": "my-app",
  "topic": "Should we refactor the authentication system?",
  "intelligence_mode": "deep_analysis",
  "participants": ["architect", "security_expert", "developer"],
  "max_rounds": 3
}
```

**Response:**
```json
{
  "debate_id": "debate_789",
  "topic": "Should we refactor the authentication system?",
  "status": "completed",
  "consensus": "Yes, refactor with focus on security and modularity",
  "confidence_score": 0.85,
  "code_context": {
    "relevant_files": 12,
    "security_issues": 3,
    "complexity_score": 7.2
  },
  "debate_summary": {
    "rounds": 3,
    "participants": ["architect", "security_expert", "developer"],
    "key_arguments": [
      "Current auth system has security vulnerabilities",
      "Monolithic structure makes testing difficult",
      "Refactoring will improve maintainability"
    ]
  }
}
```

## 🗣️ Voice System API

Base path: `/api/voice`

### Voice Sessions

#### POST /api/voice/sessions
Start a new voice session.

**Request:**
```json
{
  "session_type": "conversation",
  "ai_enabled": true,
  "real_time": true,
  "audio_format": "wav",
  "sample_rate": 16000
}
```

**Response:**
```json
{
  "session_id": "voice_session_123",
  "session_type": "conversation",
  "status": "active",
  "websocket_url": "ws://sam.chat:8005/voice/voice_session_123",
  "ai_enabled": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/voice/sessions/{session_id}
Get voice session details.

**Response:**
```json
{
  "session_id": "voice_session_123",
  "status": "active",
  "duration": "5m 23s",
  "participant_count": 2,
  "ai_interactions": 8,
  "transcription_status": "real_time",
  "audio_quality": "high"
}
```

### Audio Transcription

#### POST /api/voice/transcribe
Transcribe audio file or stream.

**Request (Multipart form data):**
```
Content-Type: multipart/form-data

audio_file: [binary audio data]
format: wav
language: en-US
speaker_identification: true
```

**Response:**
```json
{
  "transcription_id": "trans_456",
  "status": "completed",
  "text": "Hello, this is a test of the voice transcription system.",
  "confidence_score": 0.94,
  "duration": "3.2s",
  "speakers": [
    {
      "speaker_id": "speaker_1",
      "text": "Hello, this is a test of the voice transcription system.",
      "timestamp": "0.0s-3.2s"
    }
  ]
}
```

### Voice Analysis

#### POST /api/voice/analyze
Analyze voice session or audio.

**Request:**
```json
{
  "session_id": "voice_session_123",
  "analysis_type": "sentiment_and_topics",
  "include_ai_insights": true
}
```

**Response:**
```json
{
  "analysis_id": "analysis_789",
  "session_id": "voice_session_123",
  "sentiment_analysis": {
    "overall_sentiment": "positive",
    "sentiment_score": 0.72,
    "emotional_tone": ["confident", "engaging"]
  },
  "topic_analysis": {
    "main_topics": ["project planning", "technical architecture"],
    "topic_confidence": 0.88
  },
  "ai_insights": [
    "Discussion focused on technical implementation",
    "High confidence in proposed solutions",
    "Clear decision-making pattern observed"
  ]
}
```

## 🤖 DeepClaude Metacognitive API

Base path: `/api/deepclaude`

### Reasoning Sessions

#### POST /api/deepclaude/reason
Start advanced reasoning session.

**Request:**
```json
{
  "topic": "Evaluate microservices architecture for e-commerce platform",
  "reasoning_mode": "analytical",
  "depth": "deep",
  "context_data": {
    "current_system": "monolithic",
    "scale_requirements": "10M users",
    "team_size": 25
  }
}
```

**Response:**
```json
{
  "reasoning_id": "reasoning_123",
  "topic": "Evaluate microservices architecture for e-commerce platform",
  "status": "processing",
  "reasoning_mode": "analytical",
  "estimated_completion": "3-5 minutes",
  "processing_stages": [
    "Context analysis",
    "Multi-perspective evaluation",
    "Risk assessment",
    "Recommendation synthesis"
  ]
}
```

#### GET /api/deepclaude/reason/{reasoning_id}
Get reasoning results.

**Response:**
```json
{
  "reasoning_id": "reasoning_123",
  "status": "completed",
  "confidence_score": 0.87,
  "reasoning_steps": [
    {
      "step": 1,
      "type": "context_analysis",
      "insight": "Current monolithic system shows scaling bottlenecks",
      "evidence": ["Database connection pooling issues", "Deployment complexity"]
    },
    {
      "step": 2,
      "type": "option_evaluation",
      "insight": "Microservices offer better scalability but increase complexity",
      "trade_offs": {
        "benefits": ["Independent scaling", "Technology diversity"],
        "costs": ["Network latency", "Distributed debugging"]
      }
    }
  ],
  "final_conclusion": "Recommend gradual migration to microservices starting with user management service",
  "risk_assessment": {
    "implementation_risk": "medium",
    "business_risk": "low",
    "mitigation_strategies": ["Start with non-critical services", "Invest in monitoring"]
  }
}
```

### Insight Generation

#### POST /api/deepclaude/insights
Generate insights from data or context.

**Request:**
```json
{
  "data_source": "project_metrics",
  "data": {
    "code_quality_score": 7.2,
    "security_score": 8.1,
    "performance_metrics": {"response_time": "245ms", "throughput": "1000 rps"},
    "team_velocity": 32
  },
  "insight_types": ["optimization", "risk_assessment", "strategic"]
}
```

**Response:**
```json
{
  "insight_id": "insight_456",
  "insights": [
    {
      "type": "optimization",
      "priority": "high",
      "insight": "Code quality score of 7.2 indicates technical debt accumulation",
      "recommendation": "Allocate 20% of sprint capacity to refactoring",
      "impact": "Will improve maintainability and reduce bug rate"
    },
    {
      "type": "strategic",
      "priority": "medium",
      "insight": "Strong security posture provides competitive advantage",
      "recommendation": "Leverage security as a market differentiator",
      "opportunity": "Consider SOC2 certification to attract enterprise customers"
    }
  ]
}
```

## 🎭 Chain-of-Debate API

Base path: `/api/cod`

### Start Debate

#### POST /api/cod/debate
Start multi-LLM debate session.

**Request:**
```json
{
  "topic": "Should we adopt GraphQL over REST for our API?",
  "debate_type": "technical_decision",
  "participants": ["backend_architect", "frontend_developer", "devops_engineer"],
  "max_rounds": 3,
  "use_local_models": true,
  "enable_code_context": true,
  "project_context": "my-app"
}
```

**Response:**
```json
{
  "debate_id": "debate_789",
  "topic": "Should we adopt GraphQL over REST for our API?",
  "status": "in_progress",
  "participants": ["backend_architect", "frontend_developer", "devops_engineer"],
  "current_round": 1,
  "max_rounds": 3,
  "local_models_used": ["qwen2.5:14b", "llama3.1:8b"],
  "code_context_included": true
}
```

#### GET /api/cod/debate/{debate_id}
Get debate status and results.

**Response:**
```json
{
  "debate_id": "debate_789",
  "status": "completed",
  "consensus": "Adopt GraphQL for new features, maintain REST for existing APIs",
  "confidence_score": 0.82,
  "rounds_completed": 3,
  "metadata": {
    "local_models_used": true,
    "total_cost": 0.00,
    "privacy_score": 1.0,
    "processing_time": "4m 32s"
  },
  "debate_summary": {
    "key_arguments": [
      "GraphQL reduces over-fetching and improves mobile performance",
      "REST APIs are well-established and team has expertise",
      "Migration cost and complexity need consideration"
    ],
    "decision_factors": [
      "Team learning curve",
      "Performance benefits",
      "Existing API investments"
    ]
  }
}
```

### Debate History

#### GET /api/cod/debates
List recent debates.

**Response:**
```json
{
  "debates": [
    {
      "debate_id": "debate_789",
      "topic": "Should we adopt GraphQL over REST for our API?",
      "status": "completed",
      "consensus": "Adopt GraphQL for new features",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:34:32Z"
    }
  ],
  "total_debates": 15,
  "page": 1,
  "per_page": 10
}
```

## 🎛️ Control Tower Orchestration API

Base path: `/api/orchestrate`

### Complex Workflows

#### POST /api/orchestrate/workflow
Start complex multi-service workflow.

**Request:**
```json
{
  "workflow_type": "code_security_analysis",
  "project_name": "my-app",
  "workflow_config": {
    "include_services": ["blockoli", "asterisk", "cod", "deepclaude"],
    "analysis_depth": "comprehensive",
    "generate_report": true
  },
  "context": {
    "project_path": "/app",
    "compliance_requirements": ["SOC2", "HIPAA"]
  }
}
```

**Response:**
```json
{
  "workflow_id": "workflow_123",
  "workflow_type": "code_security_analysis",
  "status": "orchestrating",
  "services_involved": ["blockoli", "asterisk", "cod", "deepclaude"],
  "estimated_duration": "8-12 minutes",
  "websocket_url": "ws://sam.chat:8008/workflows/workflow_123",
  "progress": {
    "current_stage": "code_indexing",
    "completion_percentage": 15
  }
}
```

#### GET /api/orchestrate/workflow/{workflow_id}
Get workflow status and results.

**Response:**
```json
{
  "workflow_id": "workflow_123",
  "status": "completed",
  "duration": "9m 45s",
  "services_coordination": {
    "blockoli": {
      "status": "completed",
      "results": "Code indexed, 245 files analyzed"
    },
    "asterisk": {
      "status": "completed", 
      "results": "3 vulnerabilities found, SOC2 compliance: 85%"
    },
    "cod": {
      "status": "completed",
      "results": "Consensus: Prioritize security improvements"
    },
    "deepclaude": {
      "status": "completed",
      "results": "Strategic recommendation: 6-month security roadmap"
    }
  },
  "final_report": {
    "overall_score": 7.2,
    "recommendations": [
      "Address SQL injection vulnerability in auth module",
      "Implement automated security testing",
      "Plan SOC2 certification timeline"
    ],
    "next_actions": [
      "Schedule security team review",
      "Allocate budget for compliance tools",
      "Update development security guidelines"
    ]
  }
}
```

### Service Coordination

#### GET /api/orchestrate/status
Get Control Tower coordination status.

**Response:**
```json
{
  "control_tower_status": "operational",
  "active_orchestrations": 3,
  "services_monitored": 7,
  "websocket_connections": 15,
  "last_health_check": "2024-01-15T10:35:00Z",
  "service_health": {
    "cod": "healthy",
    "asterisk": "healthy", 
    "blockoli": "healthy",
    "voice": "healthy",
    "deepclaude": "healthy"
  }
}
```

## 📡 WebSocket Connections

### Real-time Updates

#### Control Tower WebSocket
```
ws://sam.chat:8008/
```

**Message Types:**
- `workflow_progress` - Workflow execution updates
- `service_health` - Service health changes
- `system_alerts` - System-wide alerts

#### Voice System WebSocket
```
ws://sam.chat:8005/voice/{session_id}
```

**Message Types:**
- `audio_stream` - Real-time audio data
- `transcription` - Live transcription updates
- `ai_response` - AI-generated responses

## 🔧 Error Handling

All APIs use consistent error response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "project_name",
      "issue": "Required field missing"
    },
    "request_id": "req_123456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR` - Invalid request parameters
- `SERVICE_UNAVAILABLE` - Target service is down
- `AUTHENTICATION_REQUIRED` - Missing or invalid API key
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Unexpected server error

## 📊 Rate Limiting

Default rate limits:
- **Health endpoints**: 60 requests/minute
- **Search/Analysis**: 30 requests/minute  
- **Debates/Workflows**: 10 requests/minute
- **File uploads**: 5 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1642248000
```

## 🔐 Security

### API Key Configuration
```bash
# Required for API-based services
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=claude-your-key

# Optional for enhanced features
BLOCKOLI_API_KEY=your-blockoli-key
LANGWATCH_API_KEY=your-langwatch-key
```

### HTTPS/TLS
Production deployments should use HTTPS:
```
https://your-domain.com/api/
```

### CORS Configuration
CORS is enabled for web applications. Configure allowed origins in environment:
```bash
CORS_ORIGINS=http://sam.chat:3000,https://your-app.com
```

## 🏃‍♂️ Getting Started

1. **Start the integrated system:**
   ```bash
   make docker-hybrid
   ```

2. **Verify all services are running:**
   ```bash
   make verify-integration
   ```

3. **Test the API Gateway:**
   ```bash
   curl http://sam.chat:3001/api/health
   ```

4. **Run your first code intelligence analysis:**
   ```bash
   curl -X POST http://sam.chat:3001/api/blockoli/index \
     -H "Content-Type: application/json" \
     -d '{"project_name": "test", "project_path": "/app"}'
   ```

For more examples and workflows, see [CLAUDE.md](../../CLAUDE.md).
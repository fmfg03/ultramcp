# 📚 SuperMCP API Reference

[![API Version](https://img.shields.io/badge/API-v2.0-blue.svg)](https://github.com/fmfg03/ultramcp)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-green.svg)](https://swagger.io/specification/)

**Complete API documentation for the SuperMCP ecosystem**

## 🎯 Overview

SuperMCP provides multiple API interfaces for different services and use cases:

- **🏢 Backend API** - Core MCP orchestration and management
- **🎭 CoD Protocol API** - Chain-of-Debate multi-LLM orchestration  
- **🗣️ Voice System API** - Voice processing and real-time communication
- **📊 Observatory API** - Monitoring and analytics
- **🔧 DevTools API** - Development and debugging tools

## 🏢 Backend API

**Base URL:** `http://localhost:3001/api`  
**Authentication:** Bearer Token

### Authentication

```bash
# Get authentication token
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Response
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "username": "admin",
    "role": "admin"
  }
}
```

### MCP Orchestration

#### Execute MCP Command

```http
POST /api/mcp/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "adapter": "github",
  "method": "listRepositories",
  "params": {
    "organization": "my-org",
    "visibility": "public"
  },
  "timeout": 30000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "repositories": [
      {
        "name": "awesome-project",
        "description": "An awesome project",
        "url": "https://github.com/my-org/awesome-project",
        "stars": 1250,
        "language": "TypeScript"
      }
    ]
  },
  "execution_time": 1.2,
  "adapter_version": "1.0.0"
}
```

#### List Available Adapters

```http
GET /api/mcp/adapters
Authorization: Bearer <token>
```

**Response:**
```json
{
  "adapters": [
    {
      "name": "github",
      "version": "1.2.0",
      "status": "active",
      "methods": ["listRepositories", "createIssue", "updatePullRequest"],
      "description": "GitHub API integration"
    },
    {
      "name": "notion",
      "version": "1.1.0", 
      "status": "active",
      "methods": ["createPage", "updateDatabase", "queryDatabase"],
      "description": "Notion workspace integration"
    }
  ]
}
```

#### Get Adapter Status

```http
GET /api/mcp/adapters/{adapter_name}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "adapter": "github",
  "status": "healthy",
  "last_health_check": "2024-01-15T10:30:00Z",
  "metrics": {
    "total_requests": 1543,
    "success_rate": 0.987,
    "avg_response_time": 1.2,
    "errors_last_hour": 2
  },
  "configuration": {
    "rate_limit": "5000/hour",
    "timeout": 30000,
    "retry_attempts": 3
  }
}
```

### A2A Agent Management

#### Create A2A Agent

```http
POST /api/a2a/agents
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "DataAnalysisAgent",
  "type": "enhanced_sam",
  "configuration": {
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 2000,
    "tools": ["python", "pandas", "matplotlib"]
  },
  "capabilities": ["data_analysis", "visualization", "reporting"],
  "security_level": "high"
}
```

**Response:**
```json
{
  "agent_id": "agent_12345",
  "name": "DataAnalysisAgent",
  "status": "initializing",
  "created_at": "2024-01-15T10:30:00Z",
  "endpoints": {
    "execute": "/api/a2a/agents/agent_12345/execute",
    "status": "/api/a2a/agents/agent_12345/status",
    "logs": "/api/a2a/agents/agent_12345/logs"
  }
}
```

#### Execute Agent Task

```http
POST /api/a2a/agents/{agent_id}/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "task": {
    "type": "data_analysis",
    "input": {
      "dataset_url": "https://example.com/sales_data.csv",
      "analysis_type": "trend_analysis",
      "output_format": "dashboard"
    }
  },
  "context": {
    "user_id": "user_123",
    "session_id": "session_456"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_789",
  "status": "running",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "progress": {
    "stage": "data_loading",
    "completion_percentage": 15
  },
  "intermediate_results": {
    "rows_processed": 1500,
    "total_rows": 10000
  }
}
```

### Analytics & Monitoring

#### Get System Metrics

```http
GET /api/analytics/metrics
Authorization: Bearer <token>
Query Parameters:
  - timeframe: 1h|6h|24h|7d|30d
  - metrics: requests,errors,performance,agents
```

**Response:**
```json
{
  "timeframe": "1h",
  "timestamp": "2024-01-15T10:30:00Z",
  "metrics": {
    "requests": {
      "total": 1543,
      "successful": 1521,
      "failed": 22,
      "success_rate": 0.987
    },
    "performance": {
      "avg_response_time": 1.2,
      "p95_response_time": 2.8,
      "p99_response_time": 5.1
    },
    "agents": {
      "active": 12,
      "idle": 3,
      "executing": 5,
      "failed": 1
    },
    "resources": {
      "cpu_usage": 0.45,
      "memory_usage": 0.62,
      "disk_usage": 0.23
    }
  }
}
```

## 🎭 CoD Protocol API

**Base URL:** `http://localhost:8000/api`  
**Authentication:** Bearer Token or API Key

### Quick Debate

```http
POST /api/quick-debate
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_content": "Should we adopt microservices architecture?",
  "participants": ["gpt-4", "claude-3-sonnet"],
  "config": {
    "max_rounds": 2,
    "timeout_per_round": 60
  }
}
```

**Response:**
```json
{
  "debate_id": "debate_123",
  "status": "completed",
  "consensus": "Adopt microservices with gradual migration approach...",
  "confidence_score": 85.2,
  "consensus_level": "strong",
  "explanation": {
    "summary": "Both models agree on benefits but recommend phased approach",
    "forCFO": "ROI positive after 18 months with 40% operational cost reduction",
    "forCTO": "Technical complexity manageable with proper tooling and team training"
  },
  "processing_time": 45.6,
  "participants_count": 2,
  "rounds_completed": 2
}
```

### Full Debate Session

```http
POST /api/debate
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_content": "Evaluate AI adoption strategy for customer service",
  "participants": ["gpt-4", "claude-3-opus", "gemini-pro"],
  "config": {
    "max_rounds": 3,
    "consensus_threshold": 0.75,
    "enable_shadow_llm": true,
    "enable_auditor": true,
    "enable_memory_context": true
  },
  "context": {
    "domain": "customer_service",
    "company_size": "enterprise",
    "current_tools": ["zendesk", "intercom"]
  }
}
```

**Response:**
```json
{
  "session_id": "session_456",
  "status": "processing",
  "estimated_completion": "2024-01-15T10:45:00Z",
  "progress": {
    "current_round": 1,
    "total_rounds": 3,
    "stage": "model_responses",
    "completion_percentage": 20
  },
  "websocket_url": "ws://localhost:8080/debate/session_456"
}
```

### Debate Status & Results

```http
GET /api/debate/{session_id}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "session_id": "session_456",
  "status": "completed",
  "results": {
    "consensus": "Implement AI chatbot for tier-1 support with human escalation...",
    "confidence_score": 92.1,
    "consensus_level": "very_strong",
    "shadow_analysis": {
      "robustness_score": 87.5,
      "risk_assessment": 34.2,
      "critical_issues": 2,
      "bias_detection": "minimal_confirmation_bias"
    },
    "audit_report": {
      "audit_result": "approved",
      "overall_score": 89.3,
      "business_feasibility": 91.0,
      "technical_feasibility": 87.5,
      "recommendations": [
        "Start with pilot program in one department",
        "Establish clear escalation protocols",
        "Implement comprehensive training program"
      ]
    },
    "quality_indicators": {
      "overall_quality": 0.89,
      "innovation_factor": 0.76,
      "business_alignment": 0.94
    },
    "performance_metrics": {
      "processing_time": 67.8,
      "cache_hit_rate": 0.73,
      "circuit_breaker_status": "healthy"
    }
  }
}
```

### Validation & Testing

```http
POST /api/validate
Authorization: Bearer <token>
Content-Type: application/json

{
  "consensus": "Implement AI-powered recommendation engine...",
  "confidence_score": 78.5,
  "context": {
    "domain": "e-commerce",
    "business_model": "B2C",
    "data_volume": "high"
  },
  "validation_type": "business_feasibility"
}
```

**Response:**
```json
{
  "validation_id": "val_789",
  "status": "completed",
  "results": {
    "feasibility_score": 82.1,
    "implementation_complexity": "medium",
    "estimated_timeline": "6-9 months",
    "resource_requirements": {
      "team_size": "8-12 developers",
      "infrastructure": "cloud_native",
      "budget_range": "$500k-$750k"
    },
    "risk_factors": [
      "Data quality and completeness",
      "Cold start problem for new users",
      "Privacy and compliance requirements"
    ],
    "success_indicators": [
      "Increase in conversion rate by 15-25%",
      "Improved customer engagement metrics",
      "Reduced customer acquisition cost"
    ]
  }
}
```

## 🗣️ Voice System API

**Base URL:** `http://localhost:3003/api`  
**WebSocket:** `ws://localhost:3003/ws`

### Start Voice Conversation

```http
POST /api/voice/conversation/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "config": {
    "language": "en-US",
    "voice_model": "neural-enhanced",
    "voice_settings": {
      "speed": 1.0,
      "pitch": 0.0,
      "volume": 0.8
    },
    "recognition_settings": {
      "auto_punctuation": true,
      "filter_profanity": false,
      "model": "enhanced"
    }
  },
  "context": {
    "user_id": "user_123",
    "session_type": "customer_support"
  }
}
```

**Response:**
```json
{
  "conversation_id": "conv_456",
  "status": "active",
  "websocket_url": "ws://localhost:3003/ws/voice/conv_456",
  "configuration": {
    "sample_rate": 16000,
    "channels": 1,
    "format": "PCM",
    "chunk_size": 1024
  },
  "capabilities": [
    "real_time_transcription",
    "voice_synthesis",
    "emotion_detection",
    "language_detection"
  ]
}
```

### Voice Analytics

```http
GET /api/voice/analytics/{conversation_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "conversation_id": "conv_456",
  "duration": 180.5,
  "metrics": {
    "speech_to_text_accuracy": 0.967,
    "average_response_time": 1.2,
    "emotion_analysis": {
      "dominant_emotion": "neutral",
      "emotion_timeline": [
        {"timestamp": 0, "emotion": "neutral", "confidence": 0.8},
        {"timestamp": 30, "emotion": "satisfied", "confidence": 0.7}
      ]
    },
    "conversation_quality": {
      "clarity_score": 0.91,
      "coherence_score": 0.88,
      "engagement_score": 0.79
    }
  },
  "transcript": {
    "turns": [
      {
        "speaker": "user",
        "text": "I need help with my account",
        "timestamp": 5.2,
        "confidence": 0.95
      },
      {
        "speaker": "assistant", 
        "text": "I'd be happy to help you with your account. What specific issue are you experiencing?",
        "timestamp": 8.1
      }
    ]
  }
}
```

## 📊 Observatory API

**Base URL:** `http://localhost:3002/api`

### System Overview

```http
GET /api/observatory/overview
Authorization: Bearer <token>
```

**Response:**
```json
{
  "system_status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "backend": {
      "status": "healthy",
      "uptime": 172800,
      "version": "2.1.0",
      "health_score": 0.98
    },
    "cod_protocol": {
      "status": "healthy",
      "active_debates": 5,
      "completed_today": 127,
      "avg_processing_time": 45.2
    },
    "voice_system": {
      "status": "healthy",
      "active_conversations": 12,
      "total_minutes_today": 8940,
      "accuracy_rate": 0.967
    },
    "database": {
      "status": "healthy",
      "connections_active": 23,
      "connections_max": 100,
      "query_performance": 0.89
    }
  },
  "alerts": [
    {
      "level": "warning",
      "component": "voice_system",
      "message": "High CPU usage detected",
      "timestamp": "2024-01-15T10:25:00Z"
    }
  ]
}
```

### Real-time Metrics Stream

```javascript
// WebSocket connection for real-time metrics
const ws = new WebSocket('ws://localhost:3002/ws/metrics');

ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  console.log('Real-time metrics:', metrics);
};

// Example message format
{
  "timestamp": "2024-01-15T10:30:15Z",
  "type": "system_metrics",
  "data": {
    "cpu_usage": 0.45,
    "memory_usage": 0.62,
    "active_requests": 23,
    "response_time_p95": 1.8,
    "error_rate": 0.012
  }
}
```

### Performance Analytics

```http
GET /api/observatory/analytics/performance
Authorization: Bearer <token>
Query Parameters:
  - timeframe: 1h|6h|24h|7d|30d
  - components: backend,cod,voice,all
  - metrics: latency,throughput,errors,resources
```

**Response:**
```json
{
  "timeframe": "24h",
  "performance_summary": {
    "overall_health_score": 0.94,
    "sla_compliance": 0.997,
    "total_requests": 45230,
    "avg_response_time": 1.24,
    "error_rate": 0.008
  },
  "component_breakdown": {
    "backend": {
      "health_score": 0.96,
      "requests": 32145,
      "avg_latency": 0.89,
      "error_rate": 0.005
    },
    "cod_protocol": {
      "health_score": 0.91,
      "debates_completed": 287,
      "avg_processing_time": 47.3,
      "success_rate": 0.994
    },
    "voice_system": {
      "health_score": 0.93,
      "conversations": 156,
      "avg_accuracy": 0.967,
      "uptime": 0.998
    }
  },
  "trends": {
    "performance_trend": "stable",
    "growth_rate": 0.15,
    "bottlenecks": ["voice_processing_cpu", "database_connections"]
  }
}
```

## 🔧 DevTools API

**Base URL:** `http://localhost:3004/api`

### Execute Debug Command

```http
POST /api/devtools/debug/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "command": "inspect_agent",
  "target": {
    "agent_id": "agent_123",
    "component": "memory_state"
  },
  "options": {
    "include_history": true,
    "depth": 2
  }
}
```

**Response:**
```json
{
  "execution_id": "debug_789",
  "status": "completed",
  "results": {
    "agent_state": {
      "id": "agent_123",
      "status": "active",
      "memory_usage": 156.7,
      "active_tasks": 3,
      "performance_metrics": {
        "tasks_completed": 47,
        "avg_execution_time": 2.3,
        "success_rate": 0.96
      }
    },
    "memory_analysis": {
      "total_entries": 234,
      "active_patterns": 12,
      "cache_efficiency": 0.84,
      "cleanup_needed": false
    }
  },
  "execution_time": 0.89
}
```

### System Diagnostics

```http
GET /api/devtools/diagnostics/system
Authorization: Bearer <token>
```

**Response:**
```json
{
  "system_health": {
    "overall_status": "healthy",
    "components_checked": 15,
    "issues_found": 1,
    "last_check": "2024-01-15T10:30:00Z"
  },
  "diagnostics": {
    "network": {
      "status": "healthy",
      "latency": 12.3,
      "bandwidth_utilization": 0.34
    },
    "database": {
      "status": "healthy",
      "connection_pool": "optimal",
      "query_performance": "good"
    },
    "cache": {
      "status": "warning",
      "hit_rate": 0.67,
      "memory_usage": 0.89,
      "recommendation": "Consider cache cleanup"
    },
    "agents": {
      "status": "healthy",
      "active_count": 12,
      "average_load": 0.45
    }
  },
  "recommendations": [
    "Schedule cache cleanup during low-traffic hours",
    "Monitor memory usage trends",
    "Consider scaling cache cluster"
  ]
}
```

## 🔐 Authentication & Security

### API Key Authentication

```bash
# Using API Key in header
curl -X GET http://localhost:3001/api/mcp/adapters \
  -H "X-API-Key: your-api-key-here"

# Using API Key in query parameter
curl -X GET "http://localhost:3001/api/mcp/adapters?api_key=your-api-key-here"
```

### OAuth 2.0 Flow

```http
# Step 1: Get authorization URL
GET /api/auth/oauth/authorize
  ?client_id=your-client-id
  &response_type=code
  &redirect_uri=http://localhost:3000/callback
  &scope=read write admin

# Step 2: Exchange code for token
POST /api/auth/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&client_id=your-client-id
&client_secret=your-client-secret
&code=authorization-code-from-step-1
&redirect_uri=http://localhost:3000/callback
```

### Rate Limiting

All APIs implement rate limiting with the following headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
X-RateLimit-Retry-After: 3600
```

**Rate Limits by Endpoint:**
- Authentication: 100 requests/hour
- MCP Operations: 1000 requests/hour  
- CoD Protocol: 50 debates/hour
- Voice System: 500 requests/hour
- Analytics: 2000 requests/hour

## 📊 Error Codes & Handling

### Standard HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "The request parameters are invalid",
    "details": {
      "field": "participants",
      "reason": "At least 2 participants required",
      "provided": 1
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456",
    "documentation_url": "https://docs.supermcp.com/errors/INVALID_PARAMETERS"
  }
}
```

### Common Error Codes

| Code | Component | Description |
|------|-----------|-------------|
| `ADAPTER_NOT_FOUND` | MCP | Requested adapter is not available |
| `AUTHENTICATION_FAILED` | Auth | Invalid credentials provided |
| `DEBATE_TIMEOUT` | CoD | Debate session exceeded timeout |
| `INSUFFICIENT_MODELS` | CoD | Not enough models available for debate |
| `VOICE_SERVICE_UNAVAILABLE` | Voice | Voice processing service is down |
| `QUOTA_EXCEEDED` | General | API quota exceeded |
| `VALIDATION_ERROR` | General | Request validation failed |

## 🔄 WebSocket APIs

### Real-time Debate Updates

```javascript
// Connect to debate session
const ws = new WebSocket('ws://localhost:8080/debate/session_456');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  switch(update.type) {
    case 'round_started':
      console.log(`Round ${update.round} started`);
      break;
    case 'model_response':
      console.log(`Model ${update.model} responded`);
      break;
    case 'consensus_reached':
      console.log('Consensus achieved:', update.consensus);
      break;
  }
};
```

### Voice Stream Processing

```javascript
// Real-time voice processing
const voiceWs = new WebSocket('ws://localhost:3003/ws/voice/conv_456');

// Send audio chunks
const sendAudioChunk = (audioData) => {
  voiceWs.send(JSON.stringify({
    type: 'audio_chunk',
    data: audioData,
    timestamp: Date.now()
  }));
};

// Receive transcription
voiceWs.onmessage = (event) => {
  const response = JSON.parse(event.data);
  
  if (response.type === 'transcription') {
    console.log('Transcribed text:', response.text);
  } else if (response.type === 'audio_response') {
    // Play synthesized audio
    playAudio(response.audio_data);
  }
};
```

## 📋 SDK Examples

### Python SDK

```python
from supermcp import SuperMCPClient

# Initialize client
client = SuperMCPClient(
    base_url="http://localhost:3001",
    api_key="your-api-key"
)

# Execute MCP command
result = await client.mcp.execute(
    adapter="github",
    method="listRepositories",
    params={"organization": "my-org"}
)

# Start CoD debate
debate = await client.cod.quick_debate(
    task_content="Should we adopt microservices?",
    participants=["gpt-4", "claude-3-sonnet"]
)

print(f"Consensus: {debate.consensus}")
print(f"Confidence: {debate.confidence_score}%")
```

### JavaScript SDK

```javascript
import { SuperMCPClient } from '@supermcp/client';

const client = new SuperMCPClient({
  baseUrl: 'http://localhost:3001',
  apiKey: 'your-api-key'
});

// Execute MCP command
const result = await client.mcp.execute({
  adapter: 'notion',
  method: 'createPage',
  params: {
    database_id: 'db_123',
    properties: {
      title: 'New Project Ideas'
    }
  }
});

// Start voice conversation
const conversation = await client.voice.startConversation({
  language: 'en-US',
  voice_model: 'neural-enhanced'
});

console.log('Conversation started:', conversation.id);
```

---

## 📚 Additional Resources

- **[OpenAPI Specification](./openapi.yaml)** - Complete API schema
- **[Postman Collection](./supermcp.postman_collection.json)** - Ready-to-use API collection
- **[SDK Documentation](./sdks/)** - Language-specific SDKs
- **[Examples Repository](./examples/)** - Code examples and tutorials
- **[Rate Limiting Guide](./rate-limiting.md)** - Detailed rate limiting information
- **[Authentication Guide](./authentication.md)** - Complete authentication documentation

---

<div align="center">

**📚 SuperMCP API Reference - Complete integration guide for all services**

[Main Documentation](../README.md) • [Getting Started](../getting-started.md) • [Examples](./examples/)

</div>
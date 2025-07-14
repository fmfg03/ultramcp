#!/bin/bash
# UltraMCP Plandex Integration - Installation Script
# Install Plandex as planning microservice for autonomous agent orchestration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANDEX_VERSION="latest"
PLANDEX_PORT="7777"
REGISTRY_PORT="7778"
BRIDGE_PORT="7779"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check system requirements
check_requirements() {
    log_info "Checking system requirements for Plandex integration..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is required but not installed"
        exit 1
    fi
    
    # Check available ports
    local ports=("$PLANDEX_PORT" "$REGISTRY_PORT" "$BRIDGE_PORT")
    for port in "${ports[@]}"; do
        if netstat -ln | grep ":$port " &> /dev/null; then
            log_warning "Port $port is already in use"
        fi
    done
    
    log_success "System requirements check completed"
}

# Create directory structure
setup_directories() {
    log_info "Setting up Plandex directory structure..."
    
    mkdir -p "$SCRIPT_DIR"/{config,data,logs,services,workspace,examples}
    mkdir -p "$SCRIPT_DIR"/services/{agent-registry,context-bridge,plandex-adapter}
    mkdir -p "$SCRIPT_DIR"/data/{workspace,plans,contexts}
    
    log_success "Directory structure created"
}

# Create Plandex Docker Compose configuration
create_docker_compose() {
    log_info "Creating Plandex Docker Compose configuration..."
    
    cat > "$SCRIPT_DIR/docker-compose.yml" << EOF
version: '3.8'

services:
  # Plandex Core Service
  plandex:
    image: plandex/plandex:${PLANDEX_VERSION}
    container_name: ultramcp-plandex
    restart: unless-stopped
    ports:
      - "${PLANDEX_PORT}:7777"
    environment:
      - PLANDEX_ENV=production
      - PLANDEX_HOST=0.0.0.0
      - PLANDEX_PORT=7777
      - OPENROUTER_API_KEY=\${OPENROUTER_API_KEY}
      - ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - PLANDEX_WORKSPACE=/workspace
      - PLANDEX_DATA_DIR=/data
      - ULTRAMCP_REGISTRY_URL=http://agent-registry:${REGISTRY_PORT}
    volumes:
      - ./workspace:/workspace
      - ./data:/data
      - ./config:/config:ro
      - ./logs:/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7777/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    networks:
      - plandex-network
      - ultramcp

  # UltraMCP Agent Registry
  agent-registry:
    build: ./services/agent-registry
    container_name: ultramcp-agent-registry
    restart: unless-stopped
    ports:
      - "${REGISTRY_PORT}:${REGISTRY_PORT}"
    environment:
      - PORT=${REGISTRY_PORT}
      - PLANDEX_URL=http://plandex:7777
      - POSTGRES_URL=\${POSTGRES_URL:-postgresql://postgres:ultramcp_password@postgres:5432/ultramcp}
      - REDIS_URL=\${REDIS_URL:-redis://redis:6379}
      - NODE_ENV=production
    volumes:
      - ./data/registry:/data
      - ./logs:/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${REGISTRY_PORT}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - plandex-network
      - ultramcp
    depends_on:
      - plandex

  # Context Bridge Service  
  context-bridge:
    build: ./services/context-bridge
    container_name: ultramcp-context-bridge
    restart: unless-stopped
    ports:
      - "${BRIDGE_PORT}:${BRIDGE_PORT}"
    environment:
      - PORT=${BRIDGE_PORT}
      - PLANDEX_URL=http://plandex:7777
      - ULTRAMCP_MEMORY_URL=\${ULTRAMCP_MEMORY_URL:-http://ultramcp-memory:8007}
      - ULTRAMCP_API_URL=\${ULTRAMCP_API_URL:-http://ultramcp-api:3000}
      - REDIS_URL=\${REDIS_URL:-redis://redis:6379}
      - NODE_ENV=production
    volumes:
      - ./data/contexts:/data
      - ./logs:/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${BRIDGE_PORT}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - plandex-network
      - ultramcp
    depends_on:
      - plandex
      - agent-registry

  # Plandex Web UI (optional)
  plandex-ui:
    image: plandex/plandex-ui:latest
    container_name: ultramcp-plandex-ui
    restart: unless-stopped
    ports:
      - "7780:3000"
    environment:
      - PLANDEX_API_URL=http://plandex:7777
      - NEXT_PUBLIC_API_URL=http://localhost:${PLANDEX_PORT}
    networks:
      - plandex-network
    depends_on:
      - plandex

networks:
  plandex-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.31.0.0/16
  
  # Connect to existing UltraMCP network
  ultramcp:
    external: true

volumes:
  plandex-workspace:
    driver: local
  plandex-data:
    driver: local
EOF

    log_success "Docker Compose configuration created"
}

# Create Agent Registry Service
create_agent_registry() {
    log_info "Creating UltraMCP Agent Registry service..."
    
    mkdir -p "$SCRIPT_DIR/services/agent-registry"
    
    # Package.json
    cat > "$SCRIPT_DIR/services/agent-registry/package.json" << 'EOF'
{
  "name": "ultramcp-agent-registry",
  "version": "1.0.0",
  "description": "UltraMCP Agent Registry for Plandex Integration",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "axios": "^1.6.0",
    "pg": "^8.11.0",
    "redis": "^4.6.0",
    "uuid": "^9.0.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.0"
  }
}
EOF

    # Main service file
    cat > "$SCRIPT_DIR/services/agent-registry/index.js" << 'EOF'
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { Pool } = require('pg');
const redis = require('redis');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 7778;

// Middleware
app.use(cors());
app.use(express.json());

// Database connections
const pgPool = new Pool({
  connectionString: process.env.POSTGRES_URL
});

const redisClient = redis.createClient({
  url: process.env.REDIS_URL
});

// Initialize connections
async function initializeConnections() {
  try {
    await redisClient.connect();
    console.log('Connected to Redis');
    
    // Test PostgreSQL connection
    await pgPool.query('SELECT NOW()');
    console.log('Connected to PostgreSQL');
    
    // Create tables if they don't exist
    await createTables();
  } catch (error) {
    console.error('Database connection error:', error);
  }
}

// Create necessary tables
async function createTables() {
  const createAgentsTable = `
    CREATE TABLE IF NOT EXISTS registered_agents (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(100) UNIQUE NOT NULL,
      type VARCHAR(50) NOT NULL,
      endpoint VARCHAR(500) NOT NULL,
      capabilities JSONB DEFAULT '{}',
      cost_per_execution DECIMAL(10,4) DEFAULT 0,
      avg_execution_time INTEGER DEFAULT 0,
      success_rate DECIMAL(5,2) DEFAULT 100,
      is_active BOOLEAN DEFAULT true,
      last_health_check TIMESTAMP,
      registered_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
    );
  `;
  
  const createPlansTable = `
    CREATE TABLE IF NOT EXISTS execution_plans (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      plan_id VARCHAR(255) UNIQUE NOT NULL,
      task_description TEXT NOT NULL,
      generated_plan JSONB NOT NULL,
      execution_status VARCHAR(50) DEFAULT 'pending',
      total_cost DECIMAL(10,4) DEFAULT 0,
      total_execution_time INTEGER DEFAULT 0,
      success_rate DECIMAL(5,2) DEFAULT 0,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
    );
  `;
  
  await pgPool.query(createAgentsTable);
  await pgPool.query(createPlansTable);
  console.log('Database tables initialized');
}

// UltraMCP Agent definitions
const defaultAgents = [
  {
    name: 'chain-of-debate',
    type: 'orchestrator',
    endpoint: 'http://ultramcp-cod:8001',
    capabilities: {
      'multi-llm-debate': true,
      'consensus-building': true,
      'decision-making': true,
      'expert-simulation': true
    },
    costPerExecution: 0.05,
    avgExecutionTime: 30000
  },
  {
    name: 'asterisk-security',
    type: 'scanner',
    endpoint: 'http://ultramcp-security:8002',
    capabilities: {
      'vulnerability-scan': true,
      'compliance-check': true,
      'threat-modeling': true,
      'security-analysis': true
    },
    costPerExecution: 0.02,
    avgExecutionTime: 60000
  },
  {
    name: 'blockoli-intelligence',
    type: 'analyzer',
    endpoint: 'http://ultramcp-blockoli:8003',
    capabilities: {
      'code-analysis': true,
      'pattern-recognition': true,
      'ast-parsing': true,
      'quality-assessment': true
    },
    costPerExecution: 0.03,
    avgExecutionTime: 45000
  },
  {
    name: 'voice-system',
    type: 'interface',
    endpoint: 'http://ultramcp-voice:8004',
    capabilities: {
      'voice-processing': true,
      'transcription': true,
      'speech-synthesis': true,
      'user-interaction': true
    },
    costPerExecution: 0.01,
    avgExecutionTime: 15000
  },
  {
    name: 'deepclaude-engine',
    type: 'reasoning',
    endpoint: 'http://ultramcp-deepclaude:8005',
    capabilities: {
      'metacognitive-analysis': true,
      'deep-reasoning': true,
      'pattern-synthesis': true,
      'strategic-thinking': true
    },
    costPerExecution: 0.08,
    avgExecutionTime: 40000
  },
  {
    name: 'control-tower',
    type: 'orchestrator',
    endpoint: 'http://ultramcp-control:8006',
    capabilities: {
      'service-coordination': true,
      'health-monitoring': true,
      'load-balancing': true,
      'system-orchestration': true
    },
    costPerExecution: 0.001,
    avgExecutionTime: 5000
  },
  {
    name: 'claude-memory',
    type: 'memory',
    endpoint: 'http://ultramcp-memory:8007',
    capabilities: {
      'semantic-search': true,
      'code-intelligence': true,
      'context-persistence': true,
      'knowledge-retrieval': true
    },
    costPerExecution: 0.02,
    avgExecutionTime: 20000
  },
  {
    name: 'sam-mcp',
    type: 'agent',
    endpoint: 'http://ultramcp-sam:8008',
    capabilities: {
      'autonomous-execution': true,
      'langgraph-integration': true,
      'local-llm-priority': true,
      'tool-usage': true
    },
    costPerExecution: 0.04,
    avgExecutionTime: 25000
  }
];

// Register default agents on startup
async function registerDefaultAgents() {
  for (const agent of defaultAgents) {
    try {
      await registerAgent(agent);
      console.log(`Registered agent: ${agent.name}`);
    } catch (error) {
      console.error(`Failed to register agent ${agent.name}:`, error.message);
    }
  }
}

// Register an agent
async function registerAgent(agentData) {
  const query = `
    INSERT INTO registered_agents (name, type, endpoint, capabilities, cost_per_execution, avg_execution_time)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (name) 
    DO UPDATE SET 
      type = $2,
      endpoint = $3,
      capabilities = $4,
      cost_per_execution = $5,
      avg_execution_time = $6,
      updated_at = NOW()
    RETURNING *;
  `;
  
  const values = [
    agentData.name,
    agentData.type,
    agentData.endpoint,
    JSON.stringify(agentData.capabilities),
    agentData.costPerExecution,
    agentData.avgExecutionTime
  ];
  
  const result = await pgPool.query(query, values);
  return result.rows[0];
}

// API Routes

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'ultramcp-agent-registry' });
});

// Get all registered agents
app.get('/agents', async (req, res) => {
  try {
    const result = await pgPool.query('SELECT * FROM registered_agents WHERE is_active = true ORDER BY name');
    res.json({ agents: result.rows });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get agent by name
app.get('/agents/:name', async (req, res) => {
  try {
    const result = await pgPool.query('SELECT * FROM registered_agents WHERE name = $1', [req.params.name]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    res.json({ agent: result.rows[0] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Register new agent
app.post('/agents', async (req, res) => {
  try {
    const agent = await registerAgent(req.body);
    res.status(201).json({ agent });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Execute agent task
app.post('/agents/:name/execute', async (req, res) => {
  try {
    const agentName = req.params.name;
    const { task, context } = req.body;
    
    // Get agent info
    const agentResult = await pgPool.query('SELECT * FROM registered_agents WHERE name = $1', [agentName]);
    if (agentResult.rows.length === 0) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentResult.rows[0];
    const startTime = Date.now();
    
    // Execute task on agent
    const response = await axios.post(`${agent.endpoint}/execute`, {
      task,
      context,
      agentName,
      executionId: uuidv4()
    }, {
      timeout: 120000 // 2 minute timeout
    });
    
    const executionTime = Date.now() - startTime;
    
    // Update agent statistics
    await pgPool.query(`
      UPDATE registered_agents 
      SET 
        avg_execution_time = (avg_execution_time + $1) / 2,
        last_health_check = NOW(),
        updated_at = NOW()
      WHERE name = $2
    `, [executionTime, agentName]);
    
    res.json({
      agentName,
      executionTime,
      result: response.data
    });
    
  } catch (error) {
    console.error(`Agent execution error for ${req.params.name}:`, error.message);
    
    // Update agent health status
    await pgPool.query(`
      UPDATE registered_agents 
      SET last_health_check = NOW()
      WHERE name = $1
    `, [req.params.name]);
    
    res.status(500).json({ 
      error: error.message,
      agentName: req.params.name 
    });
  }
});

// Get agent capabilities for planning
app.get('/capabilities', async (req, res) => {
  try {
    const result = await pgPool.query(`
      SELECT name, type, capabilities, cost_per_execution, avg_execution_time
      FROM registered_agents 
      WHERE is_active = true
    `);
    
    const capabilities = result.rows.reduce((acc, agent) => {
      acc[agent.name] = {
        type: agent.type,
        capabilities: agent.capabilities,
        cost: agent.cost_per_execution,
        avgTime: agent.avg_execution_time
      };
      return acc;
    }, {});
    
    res.json({ capabilities });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Store execution plan
app.post('/plans', async (req, res) => {
  try {
    const { planId, taskDescription, generatedPlan } = req.body;
    
    const query = `
      INSERT INTO execution_plans (plan_id, task_description, generated_plan)
      VALUES ($1, $2, $3)
      RETURNING *;
    `;
    
    const result = await pgPool.query(query, [planId, taskDescription, JSON.stringify(generatedPlan)]);
    res.status(201).json({ plan: result.rows[0] });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Get execution plan
app.get('/plans/:planId', async (req, res) => {
  try {
    const result = await pgPool.query('SELECT * FROM execution_plans WHERE plan_id = $1', [req.params.planId]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Plan not found' });
    }
    res.json({ plan: result.rows[0] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health check for all agents
app.get('/agents/health/check', async (req, res) => {
  try {
    const agents = await pgPool.query('SELECT name, endpoint FROM registered_agents WHERE is_active = true');
    const healthChecks = [];
    
    for (const agent of agents.rows) {
      try {
        const response = await axios.get(`${agent.endpoint}/health`, { timeout: 5000 });
        healthChecks.push({
          name: agent.name,
          status: 'healthy',
          responseTime: response.headers['x-response-time'] || 'unknown'
        });
      } catch (error) {
        healthChecks.push({
          name: agent.name,
          status: 'unhealthy',
          error: error.message
        });
      }
    }
    
    res.json({ healthChecks });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
async function startServer() {
  await initializeConnections();
  await registerDefaultAgents();
  
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`UltraMCP Agent Registry running on port ${PORT}`);
  });
}

startServer().catch(console.error);
EOF

    # Dockerfile
    cat > "$SCRIPT_DIR/services/agent-registry/Dockerfile" << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Expose port
EXPOSE 7778

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:7778/health || exit 1

# Start the service
CMD ["npm", "start"]
EOF

    log_success "Agent Registry service created"
}

# Create Context Bridge Service
create_context_bridge() {
    log_info "Creating Context Bridge service..."
    
    mkdir -p "$SCRIPT_DIR/services/context-bridge"
    
    # Package.json
    cat > "$SCRIPT_DIR/services/context-bridge/package.json" << 'EOF'
{
  "name": "ultramcp-context-bridge",
  "version": "1.0.0",
  "description": "Context Bridge between Plandex and UltraMCP",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "axios": "^1.6.0",
    "redis": "^4.6.0",
    "uuid": "^9.0.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.0"
  }
}
EOF

    # Main service file
    cat > "$SCRIPT_DIR/services/context-bridge/index.js" << 'EOF'
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const redis = require('redis');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 7779;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Redis client for context storage
const redisClient = redis.createClient({
  url: process.env.REDIS_URL
});

// Initialize Redis connection
async function initializeRedis() {
  try {
    await redisClient.connect();
    console.log('Context Bridge connected to Redis');
  } catch (error) {
    console.error('Redis connection error:', error);
  }
}

// Context management functions
class ContextManager {
  static async storeContext(contextId, context) {
    const key = `context:${contextId}`;
    await redisClient.setEx(key, 3600, JSON.stringify(context)); // 1 hour TTL
    return contextId;
  }
  
  static async getContext(contextId) {
    const key = `context:${contextId}`;
    const context = await redisClient.get(key);
    return context ? JSON.parse(context) : null;
  }
  
  static async updateContext(contextId, updates) {
    const existing = await this.getContext(contextId);
    if (!existing) {
      throw new Error('Context not found');
    }
    
    const updated = { ...existing, ...updates, updatedAt: new Date().toISOString() };
    await this.storeContext(contextId, updated);
    return updated;
  }
  
  static async appendToContext(contextId, key, value) {
    const existing = await this.getContext(contextId);
    if (!existing) {
      throw new Error('Context not found');
    }
    
    if (!existing[key]) {
      existing[key] = [];
    }
    
    if (Array.isArray(existing[key])) {
      existing[key].push(value);
    } else {
      existing[key] = [existing[key], value];
    }
    
    existing.updatedAt = new Date().toISOString();
    await this.storeContext(contextId, existing);
    return existing;
  }
}

// Convert UltraMCP context to Plandex format
function toPlandexContext(ultramcpContext) {
  return {
    taskId: ultramcpContext.taskId || uuidv4(),
    userInput: ultramcpContext.userInput || ultramcpContext.task,
    projectContext: {
      repository: ultramcpContext.repository,
      codebase: ultramcpContext.codebase,
      analysis: ultramcpContext.analysis
    },
    agentResults: ultramcpContext.agentResults || {},
    constraints: {
      budget: ultramcpContext.budget,
      timeline: ultramcpContext.timeline,
      requirements: ultramcpContext.requirements
    },
    preferences: ultramcpContext.preferences || {},
    metadata: {
      sessionId: ultramcpContext.sessionId,
      userId: ultramcpContext.userId,
      timestamp: new Date().toISOString()
    }
  };
}

// Convert Plandex result to UltraMCP format
function toUltraMCPResult(plandexResult) {
  return {
    success: plandexResult.success || true,
    planId: plandexResult.planId,
    executionId: plandexResult.executionId,
    result: plandexResult.result,
    steps: plandexResult.steps,
    totalCost: plandexResult.totalCost,
    totalTime: plandexResult.totalTime,
    agentExecutions: plandexResult.agentExecutions || [],
    metadata: {
      plandexVersion: plandexResult.version,
      generatedAt: plandexResult.generatedAt,
      completedAt: new Date().toISOString()
    }
  };
}

// API Routes

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'ultramcp-context-bridge' });
});

// Create new context
app.post('/context', async (req, res) => {
  try {
    const contextId = uuidv4();
    const context = {
      id: contextId,
      ...req.body,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    await ContextManager.storeContext(contextId, context);
    res.status(201).json({ contextId, context });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get context
app.get('/context/:contextId', async (req, res) => {
  try {
    const context = await ContextManager.getContext(req.params.contextId);
    if (!context) {
      return res.status(404).json({ error: 'Context not found' });
    }
    res.json({ context });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update context
app.put('/context/:contextId', async (req, res) => {
  try {
    const updated = await ContextManager.updateContext(req.params.contextId, req.body);
    res.json({ context: updated });
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
});

// Append to context
app.post('/context/:contextId/append', async (req, res) => {
  try {
    const { key, value } = req.body;
    const updated = await ContextManager.appendToContext(req.params.contextId, key, value);
    res.json({ context: updated });
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
});

// Convert UltraMCP context to Plandex format
app.post('/convert/to-plandex', async (req, res) => {
  try {
    const plandexContext = toPlandexContext(req.body);
    res.json({ plandexContext });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Convert Plandex result to UltraMCP format
app.post('/convert/to-ultramcp', async (req, res) => {
  try {
    const ultramcpResult = toUltraMCPResult(req.body);
    res.json({ ultramcpResult });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Create context from UltraMCP memory
app.post('/context/from-memory', async (req, res) => {
  try {
    const { query, projectId } = req.body;
    
    // Query UltraMCP Memory service
    const memoryResponse = await axios.post(`${process.env.ULTRAMCP_MEMORY_URL}/search`, {
      query,
      projectId,
      limit: 20
    });
    
    const contextId = uuidv4();
    const context = {
      id: contextId,
      query,
      projectId,
      memoryResults: memoryResponse.data,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    await ContextManager.storeContext(contextId, context);
    res.status(201).json({ contextId, context });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Persist execution result to memory
app.post('/context/:contextId/to-memory', async (req, res) => {
  try {
    const contextId = req.params.contextId;
    const context = await ContextManager.getContext(contextId);
    
    if (!context) {
      return res.status(404).json({ error: 'Context not found' });
    }
    
    // Store in UltraMCP Memory
    const memoryResponse = await axios.post(`${process.env.ULTRAMCP_MEMORY_URL}/store`, {
      contextId,
      content: context,
      metadata: {
        type: 'plandex-execution',
        timestamp: new Date().toISOString()
      }
    });
    
    res.json({ 
      stored: true, 
      memoryId: memoryResponse.data.id,
      contextId 
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// List contexts
app.get('/contexts', async (req, res) => {
  try {
    const keys = await redisClient.keys('context:*');
    const contexts = [];
    
    for (const key of keys) {
      const context = await redisClient.get(key);
      if (context) {
        const parsed = JSON.parse(context);
        contexts.push({
          id: parsed.id,
          createdAt: parsed.createdAt,
          updatedAt: parsed.updatedAt,
          summary: parsed.userInput || parsed.task || 'Unknown task'
        });
      }
    }
    
    res.json({ contexts });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
async function startServer() {
  await initializeRedis();
  
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`UltraMCP Context Bridge running on port ${PORT}`);
  });
}

startServer().catch(console.error);
EOF

    # Dockerfile
    cat > "$SCRIPT_DIR/services/context-bridge/Dockerfile" << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Expose port
EXPOSE 7779

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:7779/health || exit 1

# Start the service
CMD ["npm", "start"]
EOF

    log_success "Context Bridge service created"
}

# Create configuration files
create_config_files() {
    log_info "Creating configuration files..."
    
    # Environment configuration
    cat > "$SCRIPT_DIR/.env.example" << 'EOF'
# Plandex Integration Configuration

# API Keys
OPENROUTER_API_KEY=your-openrouter-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
OPENAI_API_KEY=your-openai-key-here

# Database connections (use existing UltraMCP connections)
POSTGRES_URL=postgresql://postgres:ultramcp_password@postgres:5432/ultramcp
REDIS_URL=redis://redis:6379

# UltraMCP service URLs
ULTRAMCP_MEMORY_URL=http://ultramcp-memory:8007
ULTRAMCP_API_URL=http://ultramcp-api:3000

# Service ports
PLANDEX_PORT=7777
REGISTRY_PORT=7778
BRIDGE_PORT=7779

# Plandex configuration
PLANDEX_ENV=production
PLANDEX_WORKSPACE=/workspace
PLANDEX_DATA_DIR=/data
EOF

    # Plandex configuration
    cat > "$SCRIPT_DIR/config/plandex.json" << 'EOF'
{
  "models": {
    "default": "anthropic/claude-3-sonnet",
    "planning": "anthropic/claude-3-opus",
    "execution": "openai/gpt-4-turbo",
    "fallback": "openai/gpt-3.5-turbo"
  },
  "limits": {
    "maxTokens": 4000,
    "maxContext": 2000000,
    "maxSteps": 50,
    "timeoutMs": 300000
  },
  "features": {
    "autonomousMode": true,
    "contextCaching": true,
    "errorRecovery": true,
    "multiModelSupport": true
  },
  "ultramcp": {
    "agentRegistry": "http://agent-registry:7778",
    "contextBridge": "http://context-bridge:7779",
    "defaultAgents": [
      "chain-of-debate",
      "asterisk-security", 
      "blockoli-intelligence",
      "claude-memory"
    ]
  }
}
EOF

    log_success "Configuration files created"
}

# Create management scripts
create_management_scripts() {
    log_info "Creating management scripts..."
    
    cat > "$SCRIPT_DIR/manage-plandex.sh" << 'EOF'
#!/bin/bash
# UltraMCP Plandex Management Script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

case "${1:-help}" in
    "start")
        log_info "Starting Plandex services..."
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Plandex services started"
        ;;
    "stop")
        log_info "Stopping Plandex services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Plandex services stopped"
        ;;
    "restart")
        log_info "Restarting Plandex services..."
        docker-compose -f "$COMPOSE_FILE" down
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Plandex services restarted"
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        service="${2:-}"
        if [[ -n "$service" ]]; then
            docker-compose -f "$COMPOSE_FILE" logs -f "$service"
        else
            docker-compose -f "$COMPOSE_FILE" logs -f
        fi
        ;;
    "health")
        log_info "Checking Plandex health..."
        
        # Check Plandex core
        if curl -s -f http://localhost:7777/health >/dev/null; then
            log_success "✓ Plandex core is healthy"
        else
            log_error "✗ Plandex core is unhealthy"
        fi
        
        # Check Agent Registry
        if curl -s -f http://localhost:7778/health >/dev/null; then
            log_success "✓ Agent Registry is healthy"
        else
            log_error "✗ Agent Registry is unhealthy"
        fi
        
        # Check Context Bridge
        if curl -s -f http://localhost:7779/health >/dev/null; then
            log_success "✓ Context Bridge is healthy"
        else
            log_error "✗ Context Bridge is unhealthy"
        fi
        ;;
    "agents")
        log_info "Listing registered agents..."
        curl -s http://localhost:7778/agents | jq '.agents[] | {name: .name, type: .type, status: .is_active}'
        ;;
    "plan")
        task="${2:-}"
        if [[ -z "$task" ]]; then
            log_error "Task required. Usage: $0 plan \"<task description>\""
            exit 1
        fi
        
        log_info "Generating plan for: $task"
        curl -X POST http://localhost:7777/plan \
            -H "Content-Type: application/json" \
            -d "{\"task\": \"$task\"}" | jq '.'
        ;;
    "execute")
        plan_id="${2:-}"
        if [[ -z "$plan_id" ]]; then
            log_error "Plan ID required. Usage: $0 execute <plan_id>"
            exit 1
        fi
        
        log_info "Executing plan: $plan_id"
        curl -X POST "http://localhost:7777/execute/$plan_id" | jq '.'
        ;;
    "contexts")
        log_info "Listing active contexts..."
        curl -s http://localhost:7779/contexts | jq '.contexts[] | {id: .id, summary: .summary, created: .createdAt}'
        ;;
    "dashboard")
        log_info "Plandex Integration URLs:"
        echo ""
        echo "🧠 Plandex Core:        http://localhost:7777"
        echo "🤖 Agent Registry:      http://localhost:7778"
        echo "🔗 Context Bridge:      http://localhost:7779"
        echo "🌐 Plandex UI:          http://localhost:7780"
        echo ""
        echo "📝 API Examples:"
        echo "  List agents:    curl http://localhost:7778/agents"
        echo "  Health check:   curl http://localhost:7778/agents/health/check"
        echo "  Create context: curl -X POST http://localhost:7779/context -d '{\"task\":\"test\"}'"
        ;;
    "build")
        log_info "Building Plandex services..."
        docker-compose -f "$COMPOSE_FILE" build
        log_success "Build completed"
        ;;
    "help"|*)
        echo "UltraMCP Plandex Management"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  start                    Start Plandex services"
        echo "  stop                     Stop Plandex services"
        echo "  restart                  Restart Plandex services"
        echo "  status                   Show service status"
        echo "  logs [service]           Show logs"
        echo "  health                   Check service health"
        echo "  agents                   List registered agents"
        echo "  plan \"<task>\"            Generate execution plan"
        echo "  execute <plan_id>        Execute a plan"
        echo "  contexts                 List active contexts"
        echo "  dashboard                Show dashboard URLs"
        echo "  build                    Build services"
        echo "  help                     Show this help"
        ;;
esac
EOF

    chmod +x "$SCRIPT_DIR/manage-plandex.sh"
    
    # Create symlink for global access
    sudo ln -sf "$SCRIPT_DIR/manage-plandex.sh" /usr/local/bin/ultramcp-plandex
    
    log_success "Management scripts created"
}

# Create example usage scripts
create_examples() {
    log_info "Creating example usage scripts..."
    
    mkdir -p "$SCRIPT_DIR/examples"
    
    # Example 1: Simple planning
    cat > "$SCRIPT_DIR/examples/simple-plan.sh" << 'EOF'
#!/bin/bash
# Example: Simple task planning with Plandex

echo "🧠 Testing simple planning with Plandex..."

# Create a simple task
TASK="Analyze the security of a web application and provide recommendations"

echo "Task: $TASK"
echo ""

# Generate plan
echo "Generating plan..."
PLAN_RESPONSE=$(curl -s -X POST http://localhost:7777/plan \
    -H "Content-Type: application/json" \
    -d "{\"task\": \"$TASK\", \"useUltraMCPAgents\": true}")

echo "Plan generated:"
echo "$PLAN_RESPONSE" | jq '.'

PLAN_ID=$(echo "$PLAN_RESPONSE" | jq -r '.planId')
echo ""
echo "Plan ID: $PLAN_ID"

# Execute plan (optional)
read -p "Execute this plan? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Executing plan..."
    curl -X POST "http://localhost:7777/execute/$PLAN_ID" | jq '.'
fi
EOF

    # Example 2: Multi-agent workflow
    cat > "$SCRIPT_DIR/examples/multi-agent-workflow.sh" << 'EOF'
#!/bin/bash
# Example: Multi-agent workflow with context persistence

echo "🤖 Testing multi-agent workflow..."

# Create context
CONTEXT_RESPONSE=$(curl -s -X POST http://localhost:7779/context \
    -H "Content-Type: application/json" \
    -d '{
        "task": "Comprehensive code analysis and security review",
        "repository": "https://github.com/example/webapp.git",
        "requirements": ["security", "performance", "best-practices"],
        "budget": 50,
        "timeline": "1 week"
    }')

CONTEXT_ID=$(echo "$CONTEXT_RESPONSE" | jq -r '.contextId')
echo "Context created: $CONTEXT_ID"

# Generate plan with context
PLAN_RESPONSE=$(curl -s -X POST http://localhost:7777/plan \
    -H "Content-Type: application/json" \
    -d "{
        \"task\": \"Analyze repository with multi-agent approach\",
        \"contextId\": \"$CONTEXT_ID\",
        \"agents\": [\"blockoli-intelligence\", \"asterisk-security\", \"chain-of-debate\"]
    }")

echo "Multi-agent plan:"
echo "$PLAN_RESPONSE" | jq '.'
EOF

    chmod +x "$SCRIPT_DIR/examples"/*.sh
    
    log_success "Example scripts created"
}

# Start services
start_services() {
    log_info "Starting Plandex services..."
    
    # Check if .env file exists
    if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
        log_warning "No .env file found, copying from example..."
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        log_warning "Please edit $SCRIPT_DIR/.env with your API keys before starting"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    
    # Build services first
    log_info "Building services..."
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    log_info "Waiting for services to start..."
    sleep 30
    
    # Health check
    if curl -s -f http://localhost:7778/health >/dev/null; then
        log_success "Plandex integration is running!"
        
        echo ""
        echo "🎉 Plandex Integration Installed Successfully!"
        echo ""
        echo "📊 Dashboard URLs:"
        echo "  Agent Registry:     http://localhost:7778"
        echo "  Context Bridge:     http://localhost:7779"
        echo "  Plandex UI:         http://localhost:7780"
        echo ""
        echo "🛠️ Management Commands:"
        echo "  ultramcp-plandex status    # Check service status"
        echo "  ultramcp-plandex health    # Health check"
        echo "  ultramcp-plandex agents    # List agents"
        echo "  ultramcp-plandex dashboard # Show all URLs"
        echo ""
        echo "📝 Next Steps:"
        echo "1. Configure API keys in .env file"
        echo "2. Test agent registration: ultramcp-plandex agents"
        echo "3. Try planning: ultramcp-plandex plan \"Create a website\""
        echo "4. Run examples: ./examples/simple-plan.sh"
        
    else
        log_error "Plandex services failed to start properly"
        echo ""
        echo "Debugging steps:"
        echo "1. Check logs: ultramcp-plandex logs"
        echo "2. Check .env configuration"
        echo "3. Verify UltraMCP services are running"
    fi
}

# Main installation function
main() {
    local action="${1:-install}"
    
    case "$action" in
        "install")
            log_info "Starting UltraMCP Plandex integration installation..."
            check_requirements
            setup_directories
            create_docker_compose
            create_agent_registry
            create_context_bridge
            create_config_files
            create_management_scripts
            create_examples
            start_services
            ;;
        "uninstall")
            log_warning "Uninstalling Plandex integration..."
            cd "$SCRIPT_DIR"
            docker-compose down -v
            sudo rm -f /usr/local/bin/ultramcp-plandex
            log_success "Plandex integration uninstalled"
            ;;
        "help"|*)
            echo "UltraMCP Plandex Integration Installation"
            echo ""
            echo "Usage: $0 <action>"
            echo ""
            echo "Actions:"
            echo "  install     Install and start Plandex integration"
            echo "  uninstall   Remove Plandex integration completely"
            echo "  help        Show this help"
            ;;
    esac
}

# Run main function
main "$@"
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

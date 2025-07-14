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

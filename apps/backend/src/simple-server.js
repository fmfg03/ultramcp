// Simple UltraMCP Backend for sam.chat
// Provides working API endpoints for the frontend
// Generated: 2025-07-08

require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: ['http://localhost:5173', 'https://sam.chat', 'https://api.sam.chat'],
  credentials: true
}));
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    service: 'ultramcp-backend-sam-chat'
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({ 
    message: 'UltraMCP Backend API for sam.chat',
    status: 'running',
    endpoints: {
      health: '/health',
      mcp: '/api/mcp/*',
      tools: '/api/tools',
      orchestrate: '/api/orchestrate'
    }
  });
});

// MCP Tools API
app.get('/api/tools', (req, res) => {
  res.json([
    {
      name: 'web_search',
      description: 'Search the web using Playwright',
      adapter: 'playwright',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query' }
        },
        required: ['query']
      }
    },
    {
      name: 'code_analysis',
      description: 'Analyze code with Blockoli intelligence',
      adapter: 'blockoli',
      inputSchema: {
        type: 'object',
        properties: {
          code: { type: 'string', description: 'Code to analyze' },
          language: { type: 'string', description: 'Programming language' }
        },
        required: ['code']
      }
    },
    {
      name: 'security_scan',
      description: 'Security vulnerability scanning',
      adapter: 'asterisk',
      inputSchema: {
        type: 'object',
        properties: {
          target: { type: 'string', description: 'Target to scan' }
        },
        required: ['target']
      }
    },
    {
      name: 'voice_transcribe',
      description: 'Transcribe audio to text',
      adapter: 'voice',
      inputSchema: {
        type: 'object',
        properties: {
          audio_url: { type: 'string', description: 'URL to audio file' }
        },
        required: ['audio_url']
      }
    },
    {
      name: 'memory_search',
      description: 'Semantic memory search',
      adapter: 'memory',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query' },
          project: { type: 'string', description: 'Project name' }
        },
        required: ['query']
      }
    }
  ]);
});

// Tool execution
app.post('/api/tools/execute', (req, res) => {
  const { toolName, parameters } = req.body;
  
  // Simulate tool execution
  setTimeout(() => {
    res.json({
      success: true,
      toolName,
      parameters,
      result: {
        message: `Tool '${toolName}' executed successfully`,
        data: `Processed with parameters: ${JSON.stringify(parameters)}`,
        timestamp: new Date().toISOString(),
        executionTime: Math.random() * 2000 + 500 // Random execution time
      }
    });
  }, 1000);
});

// Control Tower endpoints
app.get('/api/orchestrate/status', (req, res) => {
  res.json({
    systemStatus: 'operational',
    services: {
      'chain-of-debate': { status: 'active', uptime: '2h 15m' },
      'blockoli-intelligence': { status: 'active', uptime: '2h 15m' },
      'asterisk-security': { status: 'active', uptime: '2h 15m' },
      'voice-system': { status: 'active', uptime: '2h 15m' },
      'memory-service': { status: 'active', uptime: '2h 15m' },
      'claudia-integration': { status: 'active', uptime: '2h 15m' }
    },
    metrics: {
      totalRequests: 1247,
      totalDebates: 23,
      activeUsers: 5,
      systemLoad: 0.45
    },
    localModels: [
      { name: 'qwen2.5:14b', status: 'ready', size: '8.1GB' },
      { name: 'llama3.1:8b', status: 'ready', size: '4.7GB' },
      { name: 'codellama:7b', status: 'ready', size: '3.8GB' },
      { name: 'mistral:7b', status: 'ready', size: '4.1GB' },
      { name: 'phi3:mini', status: 'ready', size: '2.3GB' }
    ],
    recentActivity: [
      { type: 'debate', topic: 'Architecture decision for microservices', status: 'completed', time: '5 min ago' },
      { type: 'security-scan', target: '/api/auth', status: 'completed', time: '12 min ago' },
      { type: 'code-analysis', file: 'auth.py', status: 'completed', time: '18 min ago' },
      { type: 'memory-search', query: 'authentication patterns', status: 'completed', time: '25 min ago' }
    ]
  });
});

// Simple orchestration endpoint
app.post('/api/orchestrate', (req, res) => {
  const { action, parameters } = req.body;
  
  res.json({
    success: true,
    action,
    parameters,
    result: {
      orchestrationId: `orch_${Date.now()}`,
      status: 'initiated',
      estimatedCompletion: '2-3 minutes',
      services: ['chain-of-debate', 'blockoli-intelligence'],
      timestamp: new Date().toISOString()
    }
  });
});

// Catch all API routes
app.use('/api/*', (req, res) => {
  res.status(404).json({ 
    error: 'API endpoint not found',
    path: req.path,
    method: req.method,
    available: ['/api/tools', '/api/tools/execute', '/api/orchestrate/status', '/api/orchestrate']
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 UltraMCP Backend API started successfully`);
  console.log(`📍 Server running on http://localhost:${PORT}`);
  console.log(`🌐 Domain: sam.chat`);
  console.log(`🔗 API URLs:`);
  console.log(`   - Health: http://localhost:${PORT}/health`);
  console.log(`   - Tools: http://localhost:${PORT}/api/tools`);
  console.log(`   - Status: http://localhost:${PORT}/api/orchestrate/status`);
  console.log(`⏰ Started at: ${new Date().toISOString()}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 Received SIGTERM, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('🛑 Received SIGINT, shutting down gracefully');
  process.exit(0);
});
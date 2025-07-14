const express = require('express');
const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = process.env.PORT || 7778;

app.use(express.json());

// In-memory storage for simplicity
const agents = {
    'chain-of-debate': {
        id: 'chain-of-debate',
        name: 'Chain of Debate Service',
        description: 'Multi-LLM orchestration for complex decision making',
        capabilities: ['debate', 'orchestration', 'consensus'],
        status: 'available',
        url: 'http://localhost:8001'
    },
    'claude-memory': {
        id: 'claude-memory',
        name: 'Claude Code Memory',
        description: 'Semantic code analysis and memory system',
        capabilities: ['code-analysis', 'semantic-search', 'pattern-recognition'],
        status: 'available',
        url: 'http://localhost:8007'
    },
    'sam-mcp': {
        id: 'sam-mcp',
        name: 'Sam MCP Tool',
        description: 'Autonomous agent with tool calling capabilities',
        capabilities: ['automation', 'tool-calling', 'task-execution'],
        status: 'available',
        url: 'http://localhost:8010'
    }
};

const contexts = new Map();

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'ultramcp-agent-registry' });
});

// List all registered agents
app.get('/api/agents', (req, res) => {
    res.json(Object.values(agents));
});

// Get specific agent
app.get('/api/agents/:id', (req, res) => {
    const agent = agents[req.params.id];
    if (!agent) {
        return res.status(404).json({ error: 'Agent not found' });
    }
    res.json(agent);
});

// Execute Plandex command with agent context
app.post('/api/plandex/execute', async (req, res) => {
    const { command, agentId, context } = req.body;
    
    try {
        // Store context if provided
        if (context) {
            contexts.set(`${agentId}-${Date.now()}`, context);
        }
        
        // Execute Plandex command
        const plandexCommand = `${process.env.PLANDEX_BINARY || 'plandex'} ${command}`;
        
        exec(plandexCommand, { cwd: '/workspace' }, (error, stdout, stderr) => {
            if (error) {
                return res.status(500).json({ 
                    error: 'Plandex execution failed', 
                    details: error.message,
                    stderr: stderr
                });
            }
            
            res.json({ 
                success: true, 
                output: stdout,
                agentId: agentId,
                timestamp: new Date().toISOString()
            });
        });
        
    } catch (error) {
        res.status(500).json({ error: 'Failed to execute Plandex command', details: error.message });
    }
});

// Create planning session with UltraMCP agents
app.post('/api/planning/session', async (req, res) => {
    const { topic, agents: requestedAgents, priority = 'medium' } = req.body;
    
    const sessionId = `session-${Date.now()}`;
    const session = {
        id: sessionId,
        topic: topic,
        agents: requestedAgents || ['chain-of-debate', 'claude-memory'],
        status: 'created',
        priority: priority,
        created: new Date().toISOString(),
        steps: []
    };
    
    // Store session context
    contexts.set(sessionId, session);
    
    res.json({ 
        sessionId: sessionId,
        message: 'Planning session created',
        session: session
    });
});

// Get planning session status
app.get('/api/planning/session/:id', (req, res) => {
    const session = contexts.get(req.params.id);
    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }
    res.json(session);
});

// Simple Plandex integration test
app.post('/api/test/plandex', (req, res) => {
    const testCommand = `${process.env.PLANDEX_BINARY || 'plandex'} --help`;
    
    exec(testCommand, (error, stdout, stderr) => {
        if (error) {
            return res.status(500).json({ 
                success: false, 
                error: 'Plandex not accessible',
                details: error.message
            });
        }
        
        res.json({ 
            success: true, 
            message: 'Plandex is accessible',
            version: stdout.includes('Plandex') ? 'detected' : 'unknown'
        });
    });
});

app.listen(PORT, () => {
    console.log(`UltraMCP Simple Agent Registry running on port ${PORT}`);
    console.log('Available endpoints:');
    console.log('  GET  /health - Health check');
    console.log('  GET  /api/agents - List all agents');
    console.log('  POST /api/plandex/execute - Execute Plandex commands');
    console.log('  POST /api/planning/session - Create planning session');
    console.log('  POST /api/test/plandex - Test Plandex integration');
});
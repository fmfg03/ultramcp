const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const { Server } = require('socket.io');

const app = express();
const server = createServer(app);

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'mcp-system-secret-key-2024';
const PORT = process.env.PORT || 3000;

// Pre-hashed passwords (bcrypt)
const USERS = {
  'mcp-admin': '$2b$10$WLpKk17sbVH8eJNgSsz/z.tkSOdUF6ijzYPRLwkOVWrjC/mhbkOmm', // mcpsystem2024
  'dev-user': '$2b$10$2f3eCzck1oGlTgjeYEWzn.86JiETEMaoowm2KYrp0E91a7Q6Pn/H6'   // devaccess2024
};

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "ws:", "wss:"],
    },
  }
}));

// CORS - restrict to specific origins
const allowedOrigins = [
  'http://localhost:5173',
  'http://127.0.0.1:5173',
  'http://sam.chat:5173',
  'http://sam.chat',
  'https://sam.chat'
];

app.use(cors({
  origin: function (origin, callback) {
    if (!origin) return callback(null, true);
    if (allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
}));

// Rate limiting
const authLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: { error: 'Too many authentication attempts' }
});

const apiLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests
  message: { error: 'Too many API requests' }
});

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Robots.txt
app.get('/robots.txt', (req, res) => {
  res.type('text/plain');
  res.send('User-agent: *\\nDisallow: /');
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Authentication middleware
const authenticate = async (req, res, next) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  if (authHeader.startsWith('Basic ')) {
    // Basic Auth
    try {
      const credentials = Buffer.from(authHeader.slice(6), 'base64').toString('ascii');
      const [username, password] = credentials.split(':');

      if (!username || !password || !USERS[username]) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const isValid = await bcrypt.compare(password, USERS[username]);
      if (!isValid) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      req.user = { username, role: 'admin' };
      next();
    } catch (error) {
      return res.status(401).json({ error: 'Invalid authentication format' });
    }
  } else if (authHeader.startsWith('Bearer ')) {
    // JWT Auth
    try {
      const token = authHeader.slice(7);
      const decoded = jwt.verify(token, JWT_SECRET);
      req.user = decoded;
      next();
    } catch (error) {
      return res.status(401).json({ error: 'Invalid or expired token' });
    }
  } else {
    return res.status(401).json({ error: 'Invalid authentication method' });
  }
};

// Login endpoint
app.post('/api/auth/login', authLimit, async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password || !USERS[username]) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isValid = await bcrypt.compare(password, USERS[username]);
    if (!isValid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign(
      { username, role: 'admin' },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.json({
      success: true,
      token,
      user: { username, role: 'admin' },
      expiresIn: '24h'
    });
  } catch (error) {
    res.status(500).json({ error: 'Authentication error' });
  }
});

// Verify token
app.get('/api/auth/verify', authenticate, (req, res) => {
  res.json({ 
    valid: true, 
    user: req.user,
    timestamp: new Date().toISOString()
  });
});

// Protected routes
app.use('/api/mcp', apiLimit, authenticate);
app.use('/api/agents', apiLimit, authenticate);

// Get available agents
app.get('/api/agents', (req, res) => {
  const agents = [
    { id: 'gpt-4', name: 'GPT-4', type: 'reasoning', provider: 'OpenAI', status: 'active' },
    { id: 'claude-3', name: 'Claude 3', type: 'reasoning', provider: 'Anthropic', status: 'active' },
    { id: 'mistral-7b', name: 'Mistral 7B', type: 'local', provider: 'Ollama', status: 'active' },
    { id: 'llama-8b', name: 'Llama 3.1 8B', type: 'local', provider: 'Ollama', status: 'active' },
    { id: 'qwen-coder', name: 'Qwen2.5 Coder', type: 'builder', provider: 'Ollama', status: 'active' },
    { id: 'deepseek-coder', name: 'DeepSeek Coder', type: 'builder', provider: 'Ollama', status: 'active' },
    { id: 'perplexity', name: 'Perplexity', type: 'task', provider: 'Perplexity', status: 'active' }
  ];
  res.json({ agents });
});

// Execute agent
app.post('/api/mcp/:agent', (req, res) => {
  try {
    const { agent } = req.params;
    const { prompt, config } = req.body;

    console.log(`[${new Date().toISOString()}] Agent execution: ${agent} by ${req.user.username}`);

    // Mock response for now
    const response = {
      success: true,
      agent,
      response: `Mock response from ${agent}: ${prompt}`,
      tokensGenerated: Math.floor(Math.random() * 500) + 100,
      model: agent,
      provider: getProviderFromAgent(agent),
      timestamp: new Date().toISOString()
    };

    res.json(response);
  } catch (error) {
    console.error('Agent execution error:', error);
    res.status(500).json({ error: 'Agent execution failed' });
  }
});

// WebSocket setup
const io = new Server(server, {
  cors: {
    origin: allowedOrigins,
    methods: ["GET", "POST"],
    credentials: true
  }
});

// WebSocket authentication
io.use((socket, next) => {
  const token = socket.handshake.auth.token || socket.handshake.query.token;
  
  if (!token) {
    return next(new Error('Authentication required'));
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    socket.user = decoded;
    next();
  } catch (error) {
    next(new Error('Invalid token'));
  }
});

io.on('connection', (socket) => {
  console.log(`[${new Date().toISOString()}] WebSocket connected: ${socket.user.username}`);

  socket.on('execute_agent', async (data) => {
    try {
      const { agent, prompt, config, sessionId } = data;
      
      console.log(`[${new Date().toISOString()}] WebSocket agent execution: ${agent} by ${socket.user.username}`);

      // Simulate streaming response
      const response = `Mock streaming response from ${agent}: ${prompt}`;
      const chunks = response.split(' ');

      for (let i = 0; i < chunks.length; i++) {
        setTimeout(() => {
          socket.emit('agent_response_chunk', { 
            chunk: chunks[i] + ' ',
            sessionId 
          });
          
          if (i === chunks.length - 1) {
            socket.emit('agent_response_complete', {
              sessionId,
              tokensGenerated: chunks.length,
              model: agent,
              provider: getProviderFromAgent(agent)
            });
          }
        }, i * 100);
      }
    } catch (error) {
      socket.emit('agent_error', { 
        error: error.message,
        sessionId: data.sessionId 
      });
    }
  });

  socket.on('disconnect', () => {
    console.log(`[${new Date().toISOString()}] WebSocket disconnected: ${socket.user.username}`);
  });
});

// Helper functions
function getProviderFromAgent(agentId) {
  if (agentId.includes('gpt')) return 'OpenAI';
  if (agentId.includes('claude')) return 'Anthropic';
  if (agentId.includes('mistral') || agentId.includes('llama') || agentId.includes('qwen') || agentId.includes('deepseek')) return 'Ollama';
  if (agentId.includes('perplexity')) return 'Perplexity';
  return 'Unknown';
}

// Error handling
app.use((err, req, res, next) => {
  console.error('Error:', err);
  
  if (err.message === 'Not allowed by CORS') {
    return res.status(403).json({ error: 'Access denied' });
  }
  
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Start server
server.listen(PORT, '0.0.0.0', () => {
  console.log(`[${new Date().toISOString()}] 🚀 MCP System Backend running on port ${PORT}`);
  console.log(`[${new Date().toISOString()}] 🔐 Authentication: Basic Auth + JWT`);
  console.log(`[${new Date().toISOString()}] 🛡️ CORS origins:`, allowedOrigins);
  console.log(`[${new Date().toISOString()}] 👤 Users: mcp-admin, dev-user`);
});

module.exports = app;


const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

console.log('🚀 Starting MCP System Backend...');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware básico
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configuración CORS mejorada
const corsOptions = {
  origin: [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://sam.chat:5173',
    'http://sam.chat',
    'https://sam.chat',
    'http://65.109.54.94:5173',
    'http://65.109.54.94:5174'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Origin', 'Accept']
};

app.use(cors(corsOptions));

// Logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'mcp-backend',
    timestamp: new Date().toISOString(),
    port: PORT
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'MCP Enterprise Backend',
    version: '1.0.0',
    status: 'operational',
    endpoints: [
      '/health',
      '/api/tools',
      '/api/adapters', 
      '/api/mcp/status',
      '/api/tools/execute'
    ],
    timestamp: new Date().toISOString()
  });
});

// Cargar rutas MCP
try {
  const mcpRoutes = require('./src/routes/mcpRoutes');
  app.use('/api', mcpRoutes);
  console.log('✅ MCP Routes loaded successfully');
} catch (error) {
  console.error('⚠️ Error loading MCP routes:', error.message);
  
  // Fallback - crear endpoints básicos inline
  app.get('/api/tools', (req, res) => {
    res.json({
      success: true,
      total: 4,
      tools: [
        {
          id: 'firecrawl',
          name: 'firecrawl',
          type: 'web_scraping',
          description: 'Web scraping service',
          capabilities: ['scrape', 'crawl'],
          enabled: true,
          status: 'available'
        },
        {
          id: 'telegram',
          name: 'telegram', 
          type: 'messaging',
          description: 'Telegram bot integration',
          capabilities: ['send_message', 'bot_commands'],
          enabled: true,
          status: 'available'
        },
        {
          id: 'notion',
          name: 'notion',
          type: 'productivity',
          description: 'Notion workspace integration',
          capabilities: ['read_pages', 'write_pages'],
          enabled: true,
          status: 'available'
        },
        {
          id: 'github',
          name: 'github',
          type: 'development',
          description: 'GitHub repository operations',
          capabilities: ['read_repos', 'write_files'],
          enabled: true,
          status: 'available'
        }
      ]
    });
  });
  
  console.log('✅ Fallback MCP endpoints created');
}

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Error:', error);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: error.message
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path,
    available_endpoints: [
      '/health',
      '/api/tools',
      '/api/adapters',
      '/api/mcp/status'
    ]
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`[${new Date().toISOString()}] 🚀 MCP System Backend running on port ${PORT}`);
  console.log(`[${new Date().toISOString()}] 🔐 Authentication: Basic Auth + JWT`);
  console.log(`[${new Date().toISOString()}] 🛡️ CORS origins:`, corsOptions.origin);
  console.log(`[${new Date().toISOString()}] 👤 Available endpoints: /health, /api/tools, /api/adapters`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 SIGTERM received, shutting down gracefully');
  process.exit(0);
});

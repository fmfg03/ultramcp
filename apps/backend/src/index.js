require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");
const serveStatic = require("serve-static");
const { createProxyMiddleware } = require('http-proxy-middleware');
const mcpRoutes = require("./routes/mcpRoutes");
const mcpBrokerService = require("./services/mcpBrokerService");
const orchestrationService = require("./services/orchestrationService"); // Import orchestrationService

// Import all adapters
const GetzepAdapter = require("./adapters/getzepAdapter");
const FirecrawlAdapter = require("./adapters/firecrawlAdapter");
const StagehandAdapter = require("./adapters/stagehandAdapter");
const ChromaAdapter = require("./adapters/chromaAdapter");
const CliAdapter = require("./adapters/cliAdapter");
const GithubAdapter = require("./adapters/githubAdapter");
const JupyterAdapter = require("./adapters/jupyterAdapter");
const PythonAdapter = require("./adapters/pythonAdapter");
const SchedulerAdapter = require("./adapters/schedulerAdapter");
const EmailAdapter = require("./adapters/emailAdapter");
const NotionAdapter = require("./adapters/notionAdapter"); // Import NotionAdapter
const TelegramAdapter = require("./adapters/TelegramAdapter"); // Import TelegramAdapter
const SupabaseAdapter = require("../../../src/adapters/supabaseAdapter"); // Import SupabaseAdapter

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Initialize and Register adapters on startup
const adaptersToRegister = [
  new GetzepAdapter(),
  new FirecrawlAdapter(),
  new StagehandAdapter(),
  new ChromaAdapter(),
  new CliAdapter(),
  new GithubAdapter(),
  new JupyterAdapter(),
  new PythonAdapter(),
  new SchedulerAdapter(orchestrationService),
  new EmailAdapter(),
  new NotionAdapter(), // Add NotionAdapter instance
  new TelegramAdapter(), // Add TelegramAdapter instance
  new SupabaseAdapter() // Add SupabaseAdapter instance
];

async function initializeAndRegisterAdapters() {
  for (const adapter of adaptersToRegister) {
    try {
      if (typeof adapter.initialize === "function") {
        await adapter.initialize(); // Call initialize if it exists
      }
      mcpBrokerService.registerAdapter(adapter);
    } catch (error) {
      console.error(`Error initializing or registering adapter ${adapter.name || adapter.id}:`, error);
    }
  }
}

initializeAndRegisterAdapters();

// Service URLs configuration
const serviceUrls = {
  cod: process.env.COD_SERVICE_URL || 'http://ultramcp-cod-service:8001',
  asterisk: process.env.ASTERISK_SERVICE_URL || 'http://ultramcp-asterisk-mcp:8002',
  blockoli: process.env.BLOCKOLI_SERVICE_URL || 'http://ultramcp-blockoli:8003',
  voice: process.env.VOICE_SERVICE_URL || 'http://ultramcp-voice:8004',
  deepclaude: process.env.DEEPCLAUDE_SERVICE_URL || 'http://ultramcp-deepclaude:8006',
  controlTower: process.env.CONTROL_TOWER_URL || 'http://ultramcp-control-tower:8007'
};

// API Gateway - Proxy routes to microservices
console.log('🔄 Setting up API Gateway routing...');

// Security service routes (Asterisk MCP)
app.use('/api/security', createProxyMiddleware({
  target: serviceUrls.asterisk,
  changeOrigin: true,
  pathRewrite: {
    '^/api/security': '/api/v1'
  },
  onError: (err, req, res) => {
    console.error('Security service proxy error:', err.message);
    res.status(503).json({ error: 'Security service unavailable' });
  }
}));

// Code intelligence routes (Blockoli)
app.use('/api/blockoli', createProxyMiddleware({
  target: serviceUrls.blockoli,
  changeOrigin: true,
  pathRewrite: {
    '^/api/blockoli': '/api/v1'
  },
  onError: (err, req, res) => {
    console.error('Blockoli service proxy error:', err.message);
    res.status(503).json({ error: 'Code intelligence service unavailable' });
  }
}));

// Voice system routes
app.use('/api/voice', createProxyMiddleware({
  target: serviceUrls.voice,
  changeOrigin: true,
  pathRewrite: {
    '^/api/voice': '/api/v1'
  },
  onError: (err, req, res) => {
    console.error('Voice service proxy error:', err.message);
    res.status(503).json({ error: 'Voice service unavailable' });
  }
}));

// DeepClaude metacognitive routes
app.use('/api/deepclaude', createProxyMiddleware({
  target: serviceUrls.deepclaude,
  changeOrigin: true,
  pathRewrite: {
    '^/api/deepclaude': '/api/v1'
  },
  onError: (err, req, res) => {
    console.error('DeepClaude service proxy error:', err.message);
    res.status(503).json({ error: 'DeepClaude service unavailable' });
  }
}));

// Chain-of-Debate routes
app.use('/api/cod', createProxyMiddleware({
  target: serviceUrls.cod,
  changeOrigin: true,
  pathRewrite: {
    '^/api/cod': '/api/v1'
  },
  onError: (err, req, res) => {
    console.error('CoD service proxy error:', err.message);
    res.status(503).json({ error: 'Chain-of-Debate service unavailable' });
  }
}));

// Control Tower orchestration routes
app.use('/api/orchestrate', createProxyMiddleware({
  target: serviceUrls.controlTower,
  changeOrigin: true,
  pathRewrite: {
    '^/api/orchestrate': '/api/v1/orchestrate'
  },
  onError: (err, req, res) => {
    console.error('Control Tower proxy error:', err.message);
    res.status(503).json({ error: 'Control Tower service unavailable' });
  }
}));

// WebSocket proxy for Control Tower
app.use('/ws', createProxyMiddleware({
  target: 'http://ultramcp-control-tower:8008',
  ws: true,
  changeOrigin: true,
  onError: (err, req, res) => {
    console.error('WebSocket proxy error:', err.message);
    if (res) res.status(503).json({ error: 'WebSocket service unavailable' });
  }
}));

// System health aggregation endpoint
app.get('/api/health', async (req, res) => {
  console.log('🏥 Checking system health...');
  
  const healthChecks = {};
  const axios = require('axios');
  
  // Check all services
  for (const [serviceName, serviceUrl] of Object.entries(serviceUrls)) {
    try {
      const response = await axios.get(`${serviceUrl}/health`, { timeout: 5000 });
      healthChecks[serviceName] = {
        status: 'healthy',
        url: serviceUrl,
        data: response.data
      };
    } catch (error) {
      healthChecks[serviceName] = {
        status: 'unhealthy',
        url: serviceUrl,
        error: error.message
      };
    }
  }
  
  // Determine overall health
  const healthyServices = Object.values(healthChecks).filter(h => h.status === 'healthy').length;
  const totalServices = Object.keys(healthChecks).length;
  const overallHealth = healthyServices === totalServices ? 'healthy' : 
                       healthyServices > totalServices / 2 ? 'degraded' : 'unhealthy';
  
  res.json({
    overall_health: overallHealth,
    healthy_services: healthyServices,
    total_services: totalServices,
    services: healthChecks,
    timestamp: new Date().toISOString()
  });
});

// System status aggregation endpoint
app.get('/api/status', async (req, res) => {
  console.log('📊 Getting system status...');
  
  const statusChecks = {};
  const axios = require('axios');
  
  // Get status from all services
  for (const [serviceName, serviceUrl] of Object.entries(serviceUrls)) {
    try {
      const response = await axios.get(`${serviceUrl}/api/v1/status`, { timeout: 5000 });
      statusChecks[serviceName] = {
        status: 'available',
        url: serviceUrl,
        data: response.data
      };
    } catch (error) {
      statusChecks[serviceName] = {
        status: 'unavailable',
        url: serviceUrl,
        error: error.message
      };
    }
  }
  
  res.json({
    system: 'UltraMCP Supreme Stack',
    api_gateway: 'operational',
    services: statusChecks,
    timestamp: new Date().toISOString()
  });
});

// Mount MCP API routes
app.use("/api/mcp", mcpRoutes);

// --- Serve Frontend Static Files using serve-static ---
const frontendBuildPath = path.resolve(__dirname, "../../frontend/dist");

app.use(serveStatic(frontendBuildPath, { index: ["index.html"] }));

// --- End Serve Frontend ---

const server = app.listen(port, () => {
  console.log(`MCP Broker backend listening on port ${port}`);
});

// Graceful shutdown for adapters that need it (like Scheduler)
const gracefulShutdown = async () => {
  console.log("\nGracefully shutting down...");
  for (const adapter of adaptersToRegister) {
    if (typeof adapter.shutdown === "function") {
      try {
        await adapter.shutdown();
      } catch (e) {
        console.error(`Error during shutdown for adapter ${adapter.name || adapter.id}:`, e);
      }
    }
  }
  server.close(() => {
    console.log("Server closed.");
    process.exit(0);
  });

  // Force close server after 5 seconds if it hasn't closed yet
  setTimeout(() => {
    console.error("Could not close connections in time, forcefully shutting down");
    process.exit(1);
  }, 5000);
};

process.on("SIGTERM", gracefulShutdown);
process.on("SIGINT", gracefulShutdown);


/**
 * Updated Server Configuration
 * 
 * Servidor principal actualizado para incluir las nuevas rutas de orquestación
 * y el sistema refactorizado de reasoning/reward shells
 */

require("dotenv").config({ path: require("path").resolve(__dirname, "../../.env") });
const express = require("express");
const cors = require("cors");
const morgan = require("morgan");
const { v4: uuidv4 } = require("uuid");

// Import utilities and middleware
const logger = require("./utils/logger.js");
const globalErrorHandler = require("./middleware/errorHandler.js");
const AppError = require("./utils/AppError.js");

// Import existing routes
const apiRoutes = require("./routes/api.cjs");
const a2aRoutes = require("./routes/a2aRoutes.js");
const googleAIRoutes = require("./routes/googleAIRoutes.js");
const swarmRoutes = require("./routes/swarmRoutes.js");
const enhancedMemoryRoutes = require("./routes/enhancedMemoryRoutes.js");
const enhancedAgentsRoutes = require("./routes/enhancedAgentsRoutes.js");
const enhancedAgentsMonitoringRoutes = require("./routes/enhancedAgentsMonitoringRoutes.js");

// Import new task routes (ES modules)
let taskRoutes;
(async () => {
  try {
    const taskRoutesModule = await import("./routes/taskRoutes.js");
    taskRoutes = taskRoutesModule.default;
  } catch (error) {
    logger.error("Error importing task routes:", error);
  }
})();

// MCP Services and Adapters
const mcpBrokerService = require("./services/mcpBrokerService.js");
const { setupTables } = require("../../src/adapters/supabaseAdapter.js"); 
const { setupAdapterRegistrationsTable, loadPersistedAdapters } = require("./utils/adapterLoader.js");

// Explicit adapter imports for potential initial registration
const FirecrawlAdapter = require("./adapters/firecrawlAdapter.js");
const TelegramAdapter = require("./adapters/TelegramAdapter.js");
const EmbeddingSearchAdapter = require("./adapters/EmbeddingSearchAdapter.js");
const ClaudeWebSearchAdapter = require("./adapters/ClaudeWebSearchAdapter.js");

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: true, // Allow all origins for development
  credentials: true
}));

app.use(morgan("combined", { 
  stream: { 
    write: (message) => logger.info(message.trim()) 
  } 
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request ID middleware
app.use((req, res, next) => {
  req.id = uuidv4();
  res.setHeader('X-Request-ID', req.id);
  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  });
});

// API Routes
app.use('/api', apiRoutes);

// A2A Routes (Agent-to-Agent communication)
app.use('/api/a2a', a2aRoutes);

// Google AI Routes (Google AI/Gemini integration)
app.use('/api/google-ai', googleAIRoutes);

// Swarm Intelligence Routes (Advanced P2P agent networks)
app.use('/api/swarm', swarmRoutes);

// Enhanced Memory Routes (Graphiti Knowledge Graph integration)
app.use('/api/memory/enhanced', enhancedMemoryRoutes);

// Enhanced Agents Routes (LangGraph + Graphiti + MCP integration)
app.use('/api/agents/enhanced', enhancedAgentsRoutes);

// Enhanced Agents Monitoring Routes (Observability and analytics)
app.use('/api/monitoring', enhancedAgentsMonitoringRoutes);

// Task Routes (new orchestration system)
app.use('/api', (req, res, next) => {
  if (taskRoutes) {
    taskRoutes(req, res, next);
  } else {
    next(new AppError('Task routes not available', 503));
  }
});

// 404 handler
app.use('*', (req, res, next) => {
  next(new AppError(`Route ${req.originalUrl} not found`, 404));
});

// Global error handler
app.use(globalErrorHandler);

/**
 * Initialize the server and all services
 */
async function initializeServer() {
  try {
    logger.info("🚀 Starting MCP Broker Server...");

    // Initialize database tables
    logger.info("📊 Setting up database tables...");
    await setupTables();
    await setupAdapterRegistrationsTable();

    // Initialize memory service tables
    try {
      const { initializeTables } = await import("./services/memoryService.js");
      const memoryResult = await initializeTables();
      if (memoryResult.success) {
        logger.info("✅ Memory service tables initialized");
      } else {
        logger.warn("⚠️ Memory service tables need manual setup in Supabase");
      }
    } catch (memoryError) {
      logger.warn("⚠️ Memory service initialization skipped:", memoryError.message);
    }

    // Load persisted adapters
    logger.info("🔌 Loading persisted adapters...");
    await loadPersistedAdapters();

    // Register default adapters if none exist
    const registeredAdapters = mcpBrokerService.getRegisteredAdapters();
    if (registeredAdapters.length === 0) {
      logger.info("📝 Registering default adapters...");
      
      try {
        await mcpBrokerService.registerAdapter(new FirecrawlAdapter());
        logger.info("✅ FirecrawlAdapter registered");
      } catch (error) {
        logger.warn("⚠️ Failed to register FirecrawlAdapter:", error.message);
      }

      try {
        await mcpBrokerService.registerAdapter(new TelegramAdapter());
        logger.info("✅ TelegramAdapter registered");
      } catch (error) {
        logger.warn("⚠️ Failed to register TelegramAdapter:", error.message);
      }

      try {
        await mcpBrokerService.registerAdapter(new EmbeddingSearchAdapter());
        logger.info("✅ EmbeddingSearchAdapter registered");
      } catch (error) {
        logger.warn("⚠️ Failed to register EmbeddingSearchAdapter:", error.message);
      }

      try {
        await mcpBrokerService.registerAdapter(new ClaudeWebSearchAdapter());
        logger.info("✅ ClaudeWebSearchAdapter registered");
      } catch (error) {
        logger.warn("⚠️ Failed to register ClaudeWebSearchAdapter:", error.message);
      }
    }

    // Initialize LLM instances for orchestration
    try {
      const { initializeAllLlms } = await import("./services/orchestrationService.js");
      initializeAllLlms();
      logger.info("🤖 LLM instances initialized for orchestration");
    } catch (llmError) {
      logger.warn("⚠️ LLM initialization skipped:", llmError.message);
    }

    // Initialize LangWatch for Enhanced Agents
    try {
      const { initializeLangwatch } = await import("./middleware/langwatchMiddleware.js");
      if (initializeLangwatch()) {
        logger.info("🔍 LangWatch initialized for Enhanced Agents monitoring");
      } else {
        logger.warn("⚠️ LangWatch not configured - set LANGWATCH_API_KEY for monitoring");
      }
    } catch (langwatchError) {
      logger.warn("⚠️ LangWatch initialization skipped:", langwatchError.message);
    }

    logger.info(`✅ MCP Broker Server initialized successfully`);
    logger.info(`📊 Registered adapters: ${mcpBrokerService.getRegisteredAdapters().length}`);
    
    return true;
  } catch (error) {
    logger.error("❌ Failed to initialize server:", error);
    throw error;
  }
}

/**
 * Start the server
 */
async function startServer() {
  try {
    await initializeServer();
    
    const server = app.listen(PORT, '0.0.0.0', () => {
      logger.info(`🌐 MCP Broker Server running on http://0.0.0.0:${PORT}`);
      logger.info(`📋 Available endpoints:`);
      logger.info(`   - GET  /health - Health check`);
      logger.info(`   - GET  /api/mcp/tools - List MCP tools`);
      logger.info(`   - POST /api/mcp/execute - Execute MCP tool`);
      logger.info(`   - POST /api/run-task - Execute orchestrated task (NEW)`);
      logger.info(`   - GET  /api/task/:id - Get task status (NEW)`);
      logger.info(`   - GET  /api/tasks/history - Get task history (NEW)`);
      logger.info(`   - POST /api/task/:id/retry - Retry task (NEW)`);
      logger.info(`   - POST /api/swarm/agents/register - Register swarm agent (NEW)`);
      logger.info(`   - POST /api/swarm/decisions/collective - Collective decisions (NEW)`);
      logger.info(`   - POST /api/swarm/intelligence/emergent - Emergent solving (NEW)`);
      logger.info(`   - POST /api/swarm/optimization - Swarm optimization (NEW)`);
      logger.info(`   - GET  /api/swarm/topology - Network topology (NEW)`);
      logger.info(`   - GET  /api/swarm/metrics - Swarm metrics (NEW)`);
      logger.info(`   - POST /api/memory/enhanced/store - Enhanced memory storage (NEW)`);
      logger.info(`   - POST /api/memory/enhanced/search - Hybrid vector+graph search (NEW)`);
      logger.info(`   - POST /api/memory/enhanced/temporal - Temporal reasoning (NEW)`);
      logger.info(`   - POST /api/memory/enhanced/collaboration - Agent collaboration (NEW)`);
      logger.info(`   - POST /api/memory/enhanced/predict - Predictive assistance (NEW)`);
      logger.info(`   - GET  /api/memory/enhanced/health - Enhanced memory health (NEW)`);
      logger.info(`   - POST /api/task/:id/cancel - Cancel task (NEW)`);
      logger.info(`   - GET  /api/tasks/stats - System statistics (NEW)`);
      logger.info(`   - POST /api/agents/enhanced/chat - Enhanced SAM agent chat (NEW)`);
      logger.info(`   - POST /api/agents/enhanced/execute - Enhanced Manus task execution (NEW)`);
      logger.info(`   - POST /api/agents/enhanced/collaborate - Multi-agent collaboration (NEW)`);
      logger.info(`   - POST /api/agents/enhanced/knowledge-share - Agent knowledge sharing (NEW)`);
      logger.info(`   - GET  /api/agents/enhanced/metrics - Enhanced agents metrics (NEW)`);
      logger.info(`   - GET  /api/agents/enhanced/status - Enhanced agents status (NEW)`);
      logger.info(`   - GET  /api/agents/enhanced/capabilities - Enhanced agents capabilities (NEW)`);
      logger.info(`   - GET  /api/agents/enhanced/langwatch - LangWatch integration status (NEW)`);
      logger.info(`   - GET  /api/monitoring/dashboard - Comprehensive monitoring dashboard (NEW)`);
      logger.info(`   - GET  /api/monitoring/health - System health monitoring (NEW)`);
      logger.info(`   - GET  /api/monitoring/performance - Performance analytics (NEW)`);
      logger.info(`   - GET  /api/monitoring/workflows - Workflow metrics and patterns (NEW)`);
      logger.info(`   - GET  /api/monitoring/agents - Agent performance metrics (NEW)`);
      logger.info(`   - GET  /api/monitoring/alerts - System alerts management (NEW)`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => {
      logger.info('🛑 SIGTERM received, shutting down gracefully...');
      server.close(() => {
        logger.info('✅ Server closed');
        process.exit(0);
      });
    });

    process.on('SIGINT', () => {
      logger.info('🛑 SIGINT received, shutting down gracefully...');
      server.close(() => {
        logger.info('✅ Server closed');
        process.exit(0);
      });
    });

    return server;
  } catch (error) {
    logger.error("❌ Failed to start server:", error);
    process.exit(1);
  }
}

// Start the server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = { app, startServer, initializeServer };


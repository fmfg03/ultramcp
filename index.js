#!/usr/bin/env node

/**
 * UltraMCP - Main Application Entry Point
 * 
 * Orchestrates all SuperMCP components into a unified system with
 * intelligent task routing, service discovery, and workflow execution.
 */

const path = require('path');
const { createServer } = require('http');

// Core orchestration components
const Orchestrator = require('./core/orchestrator');
const APIGateway = require('./api/gateway');

// Configuration
const config = {
    // Server configuration
    port: process.env.PORT || 3000,
    host: process.env.HOST || '0.0.0.0',
    
    // Environment
    environment: process.env.NODE_ENV || 'development',
    
    // Core orchestrator configuration
    orchestrator: {
        enableMetrics: true,
        enableHealthChecks: true,
        taskTimeout: 5 * 60 * 1000, // 5 minutes
        maxConcurrentTasks: process.env.MAX_CONCURRENT_TASKS || 100,
        enableCircuitBreaker: true,
        enableServiceDiscovery: true
    },
    
    // API Gateway configuration
    gateway: {
        enableCors: true,
        enableRateLimit: true,
        enableAuth: process.env.ENABLE_AUTH !== 'false',
        enableLogging: true,
        enableMetrics: true
    },
    
    // State management
    state: {
        enablePersistence: process.env.ENABLE_PERSISTENCE === 'true',
        persistencePath: process.env.STATE_PATH || './data/state'
    },
    
    // Plugin system
    plugins: {
        enableHotReload: process.env.NODE_ENV === 'development',
        directories: [
            './plugins',
            './services',
            './adapters',
            './workflows/plugins'
        ]
    }
};

class UltraMCP {
    constructor(config) {
        this.config = config;
        this.orchestrator = null;
        this.gateway = null;
        this.server = null;
        this.isShuttingDown = false;
    }

    /**
     * Initialize and start UltraMCP
     */
    async start() {
        try {
            console.log('🚀 Starting UltraMCP...');
            console.log(`📋 Environment: ${this.config.environment}`);
            console.log(`🌐 Server: http://${this.config.host}:${this.config.port}`);
            
            // Initialize core orchestrator
            await this.initializeOrchestrator();
            
            // Initialize API Gateway
            await this.initializeGateway();
            
            // Start HTTP server
            await this.startServer();
            
            // Setup graceful shutdown
            this.setupGracefulShutdown();
            
            console.log('✅ UltraMCP started successfully');
            console.log(`🎯 Ready to orchestrate tasks at http://${this.config.host}:${this.config.port}`);
            
            // Emit startup event
            this.orchestrator.eventBus.emitSystemEvent('system.started', {
                timestamp: new Date().toISOString(),
                version: this.getVersion(),
                config: this.sanitizeConfig()
            });
            
        } catch (error) {
            console.error('❌ Failed to start UltraMCP:', error);
            process.exit(1);
        }
    }

    /**
     * Initialize core orchestrator
     */
    async initializeOrchestrator() {
        console.log('🔧 Initializing orchestrator...');
        
        this.orchestrator = new Orchestrator({
            ...this.config.orchestrator,
            stateConfig: this.config.state,
            pluginConfig: this.config.plugins
        });
        
        await this.orchestrator.initialize();
        
        // Setup orchestrator event handlers
        this.setupOrchestratorEvents();
        
        console.log('✅ Orchestrator initialized');
    }

    /**
     * Initialize API Gateway
     */
    async initializeGateway() {
        console.log('🌐 Initializing API Gateway...');
        
        this.gateway = new APIGateway({
            ...this.config.gateway,
            orchestrator: this.orchestrator
        });
        
        await this.gateway.initialize();
        
        console.log('✅ API Gateway initialized');
    }

    /**
     * Start HTTP server
     */
    async startServer() {
        return new Promise((resolve, reject) => {
            // Create HTTP server with gateway app
            this.server = createServer(this.gateway.app);
            
            // Setup WebSocket server if gateway supports it
            if (this.gateway.setupWebSocket) {
                this.gateway.setupWebSocket(this.server);
            }
            
            this.server.listen(this.config.port, this.config.host, (error) => {
                if (error) {
                    reject(error);
                } else {
                    resolve();
                }
            });
            
            this.server.on('error', (error) => {
                if (error.code === 'EADDRINUSE') {
                    console.error(`❌ Port ${this.config.port} is already in use`);
                } else {
                    console.error('❌ Server error:', error);
                }
                reject(error);
            });
        });
    }

    /**
     * Setup orchestrator event handlers
     */
    setupOrchestratorEvents() {
        const eventBus = this.orchestrator.eventBus;
        
        // Log critical system events
        eventBus.on('system.*', (event, data) => {
            console.log(`📡 System Event: ${event}`, data);
        });
        
        // Monitor task execution
        eventBus.on('task.started', (data) => {
            console.log(`🎯 Task started: ${data.taskId}`);
        });
        
        eventBus.on('task.completed', (data) => {
            console.log(`✅ Task completed: ${data.taskId} (${data.duration}ms)`);
        });
        
        eventBus.on('task.failed', (data) => {
            console.error(`❌ Task failed: ${data.taskId} - ${data.error}`);
        });
        
        // Monitor service health
        eventBus.on('service.health.critical', (data) => {
            console.warn(`⚠️ Service health critical: ${data.serviceId}`);
        });
        
        // Monitor system performance
        eventBus.on('system.performance.warning', (data) => {
            console.warn(`⚠️ Performance warning:`, data);
        });
    }

    /**
     * Setup graceful shutdown handlers
     */
    setupGracefulShutdown() {
        const gracefulShutdown = async (signal) => {
            if (this.isShuttingDown) {
                console.log('🔄 Shutdown already in progress...');
                return;
            }
            
            this.isShuttingDown = true;
            console.log(`🛑 Received ${signal}, starting graceful shutdown...`);
            
            try {
                // Stop accepting new connections
                if (this.server) {
                    this.server.close();
                }
                
                // Shutdown API Gateway
                if (this.gateway) {
                    await this.gateway.shutdown();
                }
                
                // Shutdown orchestrator (this handles all subsystems)
                if (this.orchestrator) {
                    await this.orchestrator.shutdown();
                }
                
                console.log('✅ UltraMCP shutdown complete');
                process.exit(0);
                
            } catch (error) {
                console.error('❌ Error during shutdown:', error);
                process.exit(1);
            }
        };
        
        // Handle different shutdown signals
        process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
        process.on('SIGINT', () => gracefulShutdown('SIGINT'));
        process.on('SIGUSR2', () => gracefulShutdown('SIGUSR2')); // nodemon restart
        
        // Handle uncaught exceptions
        process.on('uncaughtException', (error) => {
            console.error('❌ Uncaught Exception:', error);
            gracefulShutdown('uncaughtException');
        });
        
        process.on('unhandledRejection', (reason, promise) => {
            console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
            gracefulShutdown('unhandledRejection');
        });
    }

    /**
     * Get application version
     */
    getVersion() {
        try {
            const packageJson = require('./package.json');
            return packageJson.version;
        } catch {
            return 'unknown';
        }
    }

    /**
     * Sanitize config for logging (remove sensitive data)
     */
    sanitizeConfig() {
        const sanitized = { ...this.config };
        
        // Remove any potential sensitive information
        if (sanitized.database?.password) delete sanitized.database.password;
        if (sanitized.redis?.password) delete sanitized.redis.password;
        if (sanitized.auth?.secret) delete sanitized.auth.secret;
        
        return sanitized;
    }

    /**
     * Get system status
     */
    async getStatus() {
        const status = {
            application: {
                name: 'UltraMCP',
                version: this.getVersion(),
                environment: this.config.environment,
                uptime: process.uptime(),
                pid: process.pid
            },
            server: {
                host: this.config.host,
                port: this.config.port,
                isListening: this.server?.listening || false
            },
            memory: process.memoryUsage(),
            orchestrator: null,
            gateway: null
        };
        
        // Get orchestrator status
        if (this.orchestrator) {
            status.orchestrator = await this.orchestrator.getStatus();
        }
        
        // Get gateway status
        if (this.gateway) {
            status.gateway = this.gateway.getStatus();
        }
        
        return status;
    }
}

// CLI entry point
async function main() {
    // Handle command line arguments
    const args = process.argv.slice(2);
    
    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
UltraMCP - Universal Task Orchestration Platform

Usage: node index.js [options]

Options:
  --help, -h          Show this help message
  --version, -v       Show version information
  --config <file>     Load configuration from file
  --port <port>       Override server port
  --env <env>         Set environment (development, production)

Environment Variables:
  PORT                Server port (default: 3000)
  HOST                Server host (default: 0.0.0.0)
  NODE_ENV            Environment (development, production)
  ENABLE_AUTH         Enable authentication (default: true)
  ENABLE_PERSISTENCE  Enable state persistence (default: false)
  STATE_PATH          State persistence directory
  MAX_CONCURRENT_TASKS Maximum concurrent tasks

Examples:
  node index.js                          # Start with default configuration
  node index.js --port 8080              # Start on port 8080
  node index.js --env production          # Start in production mode
  PORT=3001 node index.js                # Start with environment variable
        `);
        process.exit(0);
    }
    
    if (args.includes('--version') || args.includes('-v')) {
        const app = new UltraMCP(config);
        console.log(`UltraMCP v${app.getVersion()}`);
        process.exit(0);
    }
    
    // Override config with command line arguments
    const portIndex = args.indexOf('--port');
    if (portIndex !== -1 && args[portIndex + 1]) {
        config.port = parseInt(args[portIndex + 1]);
    }
    
    const envIndex = args.indexOf('--env');
    if (envIndex !== -1 && args[envIndex + 1]) {
        config.environment = args[envIndex + 1];
        process.env.NODE_ENV = config.environment;
    }
    
    // Create and start application
    const app = new UltraMCP(config);
    await app.start();
    
    // Keep process alive
    process.stdin.resume();
}

// Export for testing
module.exports = UltraMCP;

// Run if called directly
if (require.main === module) {
    main().catch(error => {
        console.error('❌ Application startup failed:', error);
        process.exit(1);
    });
}
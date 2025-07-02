/**
 * API Gateway for UltraMCP
 * 
 * Central entry point for all API requests with routing, authentication,
 * rate limiting, and integration with the orchestrator.
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { Server: WebSocketServer } = require('ws');
const { v4: uuidv4 } = require('uuid');

class APIGateway {
    constructor(config = {}) {
        this.config = {
            enableCors: config.enableCors || true,
            enableRateLimit: config.enableRateLimit || true,
            enableAuth: config.enableAuth || true,
            enableLogging: config.enableLogging || true,
            enableMetrics: config.enableMetrics || true,
            enableWebSocket: config.enableWebSocket !== false,
            rateLimitWindow: config.rateLimitWindow || 15 * 60 * 1000, // 15 minutes
            rateLimitMax: config.rateLimitMax || 100,
            ...config
        };

        this.orchestrator = config.orchestrator;
        this.app = express();
        this.wsServer = null;
        this.wsClients = new Map();
        
        // Statistics
        this.stats = {
            requests: 0,
            errors: 0,
            activeConnections: 0,
            wsConnections: 0,
            lastActivity: null
        };
    }

    /**
     * Initialize API Gateway
     */
    async initialize() {
        console.log('🌐 Setting up API Gateway...');
        
        // Setup middleware
        this.setupMiddleware();
        
        // Setup routes
        this.setupRoutes();
        
        // Setup error handling
        this.setupErrorHandling();
        
        console.log('✅ API Gateway setup complete');
    }

    /**
     * Setup Express middleware
     */
    setupMiddleware() {
        // Security middleware
        this.app.use(helmet({
            contentSecurityPolicy: false, // Allow WebSocket connections
            crossOriginEmbedderPolicy: false
        }));
        
        // Compression
        this.app.use(compression());
        
        // CORS
        if (this.config.enableCors) {
            this.app.use(cors({
                origin: process.env.CORS_ORIGIN || true,
                credentials: true,
                methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
            }));
        }
        
        // Rate limiting
        if (this.config.enableRateLimit) {
            const limiter = rateLimit({
                windowMs: this.config.rateLimitWindow,
                max: this.config.rateLimitMax,
                message: {
                    error: 'Rate limit exceeded',
                    retryAfter: this.config.rateLimitWindow / 1000
                },
                standardHeaders: true,
                legacyHeaders: false
            });
            this.app.use('/api/', limiter);
        }
        
        // Body parsing
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));
        
        // Request logging and metrics
        if (this.config.enableLogging) {
            this.app.use((req, res, next) => {
                const start = Date.now();
                
                res.on('finish', () => {
                    const duration = Date.now() - start;
                    this.stats.requests++;
                    this.stats.lastActivity = new Date().toISOString();
                    
                    if (res.statusCode >= 400) {
                        this.stats.errors++;
                    }
                    
                    console.log(`${req.method} ${req.path} ${res.statusCode} ${duration}ms`);
                });
                
                next();
            });
        }
    }

    /**
     * Setup API routes
     */
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                version: this.getVersion(),
                uptime: process.uptime()
            });
        });

        // System status
        this.app.get('/api/status', async (req, res) => {
            try {
                const status = await this.getSystemStatus();
                res.json(status);
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get system status',
                    message: error.message
                });
            }
        });

        // Task execution endpoint
        this.app.post('/api/tasks', async (req, res) => {
            try {
                const taskData = req.body;
                const userContext = this.extractUserContext(req);
                
                // Validate task data
                if (!taskData || typeof taskData !== 'object') {
                    return res.status(400).json({
                        error: 'Invalid task data',
                        message: 'Request body must contain valid task data'
                    });
                }
                
                // Process task through orchestrator
                const result = await this.orchestrator.processTask(taskData, userContext);
                
                res.json({
                    success: true,
                    data: result,
                    metadata: {
                        timestamp: new Date().toISOString(),
                        taskId: result.taskId
                    }
                });
                
            } catch (error) {
                console.error('Task execution error:', error);
                res.status(500).json({
                    error: 'Task execution failed',
                    message: error.message,
                    code: error.code || 'TASK_ERROR'
                });
            }
        });

        // Get task status
        this.app.get('/api/tasks/:taskId', async (req, res) => {
            try {
                const { taskId } = req.params;
                const context = this.orchestrator.contextManager.getContext(taskId);
                
                if (!context) {
                    return res.status(404).json({
                        error: 'Task not found',
                        taskId
                    });
                }
                
                const metrics = this.orchestrator.contextManager.getExecutionMetrics(taskId);
                
                res.json({
                    taskId,
                    status: context.execution.errors.length > 0 ? 'failed' : 'running',
                    metrics,
                    createdAt: context.createdAt,
                    steps: context.execution.steps.length,
                    services: context.execution.services.length
                });
                
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get task status',
                    message: error.message
                });
            }
        });

        // Service discovery
        this.app.get('/api/services', async (req, res) => {
            try {
                const services = this.orchestrator.serviceRegistry.getAllServices();
                res.json({
                    services: services.map(service => ({
                        id: service.id,
                        name: service.name,
                        capabilities: service.capabilities,
                        health: service.health,
                        lastHealthCheck: service.lastHealthCheck
                    }))
                });
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get services',
                    message: error.message
                });
            }
        });

        // Workflow management
        this.app.get('/api/workflows', (req, res) => {
            try {
                const workflows = this.orchestrator.workflowEngine.getAllWorkflows();
                res.json({ workflows });
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get workflows',
                    message: error.message
                });
            }
        });

        // Plugin management
        this.app.get('/api/plugins', (req, res) => {
            try {
                const plugins = this.orchestrator.pluginLoader.getAllPlugins();
                res.json({ plugins });
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get plugins',
                    message: error.message
                });
            }
        });

        // State management endpoints
        this.app.get('/api/state/global/:key', (req, res) => {
            try {
                const { key } = req.params;
                const value = this.orchestrator.stateManager.getGlobal(key);
                
                if (value === undefined) {
                    return res.status(404).json({
                        error: 'Key not found',
                        key
                    });
                }
                
                res.json({ key, value });
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get state',
                    message: error.message
                });
            }
        });

        this.app.post('/api/state/global/:key', (req, res) => {
            try {
                const { key } = req.params;
                const { value } = req.body;
                
                this.orchestrator.stateManager.setGlobal(key, value);
                
                res.json({
                    success: true,
                    key,
                    value
                });
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to set state',
                    message: error.message
                });
            }
        });

        // Analytics and metrics
        this.app.get('/api/metrics', (req, res) => {
            try {
                const orchestratorStats = this.orchestrator.getStats();
                const gatewayStats = this.getStats();
                
                res.json({
                    gateway: gatewayStats,
                    orchestrator: orchestratorStats,
                    timestamp: new Date().toISOString()
                });
            } catch (error) {
                res.status(500).json({
                    error: 'Failed to get metrics',
                    message: error.message
                });
            }
        });

        // Static file serving for dashboard
        this.app.use('/dashboard', express.static('public/dashboard'));
        
        // Default route
        this.app.get('/', (req, res) => {
            res.json({
                name: 'UltraMCP API Gateway',
                version: this.getVersion(),
                status: 'operational',
                endpoints: {
                    health: '/health',
                    status: '/api/status',
                    tasks: '/api/tasks',
                    services: '/api/services',
                    workflows: '/api/workflows',
                    plugins: '/api/plugins',
                    metrics: '/api/metrics',
                    dashboard: '/dashboard'
                }
            });
        });
    }

    /**
     * Setup WebSocket server
     */
    setupWebSocket(server) {
        if (!this.config.enableWebSocket) return;
        
        console.log('🔌 Setting up WebSocket server...');
        
        this.wsServer = new WebSocketServer({ server, path: '/ws' });
        
        this.wsServer.on('connection', (ws, req) => {
            const clientId = uuidv4();
            const clientInfo = {
                id: clientId,
                ip: req.socket.remoteAddress,
                userAgent: req.headers['user-agent'],
                connectedAt: new Date().toISOString()
            };
            
            this.wsClients.set(clientId, { ws, info: clientInfo });
            this.stats.wsConnections++;
            
            console.log(`🔌 WebSocket client connected: ${clientId}`);
            
            // Send welcome message
            ws.send(JSON.stringify({
                type: 'connected',
                clientId,
                timestamp: new Date().toISOString()
            }));
            
            // Handle messages
            ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleWebSocketMessage(clientId, message);
                } catch (error) {
                    ws.send(JSON.stringify({
                        type: 'error',
                        error: 'Invalid message format'
                    }));
                }
            });
            
            // Handle disconnect
            ws.on('close', () => {
                this.wsClients.delete(clientId);
                console.log(`🔌 WebSocket client disconnected: ${clientId}`);
            });
            
            ws.on('error', (error) => {
                console.error(`WebSocket error for client ${clientId}:`, error);
                this.wsClients.delete(clientId);
            });
        });
        
        // Setup orchestrator event forwarding
        this.setupWebSocketEventForwarding();
        
        console.log('✅ WebSocket server setup complete');
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(clientId, message) {
        const client = this.wsClients.get(clientId);
        if (!client) return;
        
        const { ws } = client;
        
        switch (message.type) {
            case 'subscribe':
                // Subscribe to specific events
                client.subscriptions = message.events || [];
                ws.send(JSON.stringify({
                    type: 'subscribed',
                    events: client.subscriptions
                }));
                break;
                
            case 'ping':
                ws.send(JSON.stringify({
                    type: 'pong',
                    timestamp: new Date().toISOString()
                }));
                break;
                
            default:
                ws.send(JSON.stringify({
                    type: 'error',
                    error: 'Unknown message type'
                }));
        }
    }

    /**
     * Setup WebSocket event forwarding from orchestrator
     */
    setupWebSocketEventForwarding() {
        if (!this.orchestrator?.eventBus) return;
        
        // Forward all events to subscribed WebSocket clients
        this.orchestrator.eventBus.on('*', (eventName, data) => {
            const message = {
                type: 'event',
                event: eventName,
                data,
                timestamp: new Date().toISOString()
            };
            
            for (const [clientId, client] of this.wsClients) {
                try {
                    const { ws, subscriptions = [] } = client;
                    
                    // Send if client subscribed to this event or subscribed to all
                    if (subscriptions.length === 0 || 
                        subscriptions.includes(eventName) || 
                        subscriptions.includes('*')) {
                        
                        if (ws.readyState === ws.OPEN) {
                            ws.send(JSON.stringify(message));
                        }
                    }
                } catch (error) {
                    console.error(`Failed to send event to WebSocket client ${clientId}:`, error);
                }
            }
        });
    }

    /**
     * Setup error handling
     */
    setupErrorHandling() {
        // 404 handler
        this.app.use((req, res) => {
            res.status(404).json({
                error: 'Not Found',
                message: `Route ${req.method} ${req.path} not found`,
                timestamp: new Date().toISOString()
            });
        });
        
        // Global error handler
        this.app.use((error, req, res, next) => {
            console.error('API Gateway error:', error);
            
            const status = error.status || error.statusCode || 500;
            const message = error.message || 'Internal Server Error';
            
            res.status(status).json({
                error: status === 500 ? 'Internal Server Error' : message,
                message: status === 500 ? 'An unexpected error occurred' : message,
                timestamp: new Date().toISOString(),
                ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
            });
        });
    }

    /**
     * Extract user context from request
     */
    extractUserContext(req) {
        return {
            ip: req.ip || req.connection.remoteAddress,
            userAgent: req.get('User-Agent'),
            headers: req.headers,
            userId: req.user?.id,
            sessionId: req.sessionID,
            origin: req.get('Origin'),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Get system status
     */
    async getSystemStatus() {
        const status = {
            gateway: this.getStatus(),
            orchestrator: null,
            timestamp: new Date().toISOString()
        };
        
        if (this.orchestrator) {
            status.orchestrator = await this.orchestrator.getStatus();
        }
        
        return status;
    }

    /**
     * Get gateway status
     */
    getStatus() {
        return {
            status: 'operational',
            stats: this.stats,
            config: {
                cors: this.config.enableCors,
                rateLimit: this.config.enableRateLimit,
                auth: this.config.enableAuth,
                webSocket: this.config.enableWebSocket
            },
            websocket: {
                enabled: this.config.enableWebSocket,
                connections: this.wsClients.size,
                server: !!this.wsServer
            }
        };
    }

    /**
     * Get gateway statistics
     */
    getStats() {
        return {
            ...this.stats,
            websocketConnections: this.wsClients.size,
            uptime: process.uptime(),
            memory: process.memoryUsage()
        };
    }

    /**
     * Get application version
     */
    getVersion() {
        try {
            const packageJson = require('../package.json');
            return packageJson.version;
        } catch {
            return 'unknown';
        }
    }

    /**
     * Broadcast message to all WebSocket clients
     */
    broadcast(message) {
        const payload = JSON.stringify({
            type: 'broadcast',
            data: message,
            timestamp: new Date().toISOString()
        });
        
        let sentCount = 0;
        for (const [clientId, client] of this.wsClients) {
            try {
                if (client.ws.readyState === client.ws.OPEN) {
                    client.ws.send(payload);
                    sentCount++;
                }
            } catch (error) {
                console.error(`Failed to broadcast to client ${clientId}:`, error);
            }
        }
        
        return sentCount;
    }

    /**
     * Shutdown gateway
     */
    async shutdown() {
        console.log('🛑 Shutting down API Gateway...');
        
        // Close WebSocket server
        if (this.wsServer) {
            this.wsServer.close();
            
            // Close all WebSocket connections
            for (const [clientId, client] of this.wsClients) {
                try {
                    client.ws.close();
                } catch (error) {
                    console.error(`Error closing WebSocket connection ${clientId}:`, error);
                }
            }
            
            this.wsClients.clear();
        }
        
        console.log('✅ API Gateway shutdown complete');
    }
}

module.exports = APIGateway;
// MCP Observatory Backend Server - Fixed ES6 Module Version
// This server provides a complete MCP backend with proper module loading

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { mcpRoutes, mcpRegistry, mcpExecutionEngine } from './mcpRoutes.mjs';

// ES6 module compatibility
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", "ws:", "wss:"]
        }
    }
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000, // limit each IP to 1000 requests per windowMs
    message: {
        error: 'Too many requests from this IP',
        retryAfter: '15 minutes'
    }
});
app.use('/api/', limiter);

// CORS configuration
app.use(cors({
    origin: ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://65.109.54.94:5173', 'http://65.109.54.94:5174', 'https://sam.chat'],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'X-API-Key'],
    credentials: true
}));

// Logging
app.use(morgan('combined'));

// Compression
app.use(compression());

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Static files
app.use(express.static(join(__dirname, 'public')));

// Request tracking middleware
app.use((req, res, next) => {
    req.requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    req.startTime = Date.now();
    
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - ${req.requestId}`);
    
    res.on('finish', () => {
        const duration = Date.now() - req.startTime;
        console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - ${res.statusCode} (${duration}ms) - ${req.requestId}`);
    });
    
    next();
});

// Health check endpoint (before API routes)
app.get('/health', (req, res) => {
    const uptime = process.uptime();
    const memoryUsage = process.memoryUsage();
    
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: {
            seconds: Math.floor(uptime),
            formatted: `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m ${Math.floor(uptime % 60)}s`
        },
        memory: {
            used: Math.round(memoryUsage.heapUsed / 1024 / 1024),
            total: Math.round(memoryUsage.heapTotal / 1024 / 1024),
            external: Math.round(memoryUsage.external / 1024 / 1024)
        },
        version: '2.0.0',
        node_version: process.version,
        environment: process.env.NODE_ENV || 'development'
    });
});

// API routes
app.use('/api', mcpRoutes);

// Legacy compatibility routes
app.get('/api/tools', (req, res, next) => {
    // This will be handled by mcpRoutes, but we add logging
    console.log('[Legacy] Tools endpoint accessed');
    next();
});

app.post('/api/tools/execute', (req, res, next) => {
    // This will be handled by mcpRoutes, but we add logging
    console.log('[Legacy] Execute endpoint accessed:', req.body);
    next();
});

// Fallback API endpoints for backward compatibility
app.get('/api/adapters', (req, res) => {
    try {
        const adapters = mcpRegistry.getAllAdapters();
        res.json(adapters);
    } catch (error) {
        res.status(500).json({ error: 'Failed to retrieve adapters', message: error.message });
    }
});

app.get('/api/metrics', (req, res) => {
    try {
        const metrics = mcpRegistry.getMetrics();
        const activeExecutions = mcpExecutionEngine.getActiveExecutions();
        
        res.json({
            ...metrics,
            activeExecutions: activeExecutions.length,
            server: {
                uptime: process.uptime(),
                memory: process.memoryUsage(),
                version: '2.0.0'
            }
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to retrieve metrics', message: error.message });
    }
});

// WebSocket support for real-time updates
import { createServer } from 'http';
import { WebSocketServer } from 'ws';

const server = createServer(app);
const wss = new WebSocketServer({ server });

wss.on('connection', (ws, req) => {
    console.log(`[WebSocket] Client connected from ${req.socket.remoteAddress}`);
    
    // Send initial status
    ws.send(JSON.stringify({
        type: 'connection',
        status: 'connected',
        timestamp: new Date().toISOString()
    }));
    
    // Handle messages
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            console.log('[WebSocket] Received:', data);
            
            // Echo back for now
            ws.send(JSON.stringify({
                type: 'echo',
                data,
                timestamp: new Date().toISOString()
            }));
        } catch (error) {
            ws.send(JSON.stringify({
                type: 'error',
                error: 'Invalid JSON',
                timestamp: new Date().toISOString()
            }));
        }
    });
    
    ws.on('close', () => {
        console.log('[WebSocket] Client disconnected');
    });
    
    ws.on('error', (error) => {
        console.error('[WebSocket] Error:', error);
    });
});

// Periodic status broadcast to WebSocket clients
setInterval(() => {
    const status = {
        type: 'status_update',
        tools: mcpRegistry.getAllTools().length,
        adapters: mcpRegistry.getAllAdapters().length,
        activeExecutions: mcpExecutionEngine.getActiveExecutions().length,
        metrics: mcpRegistry.getMetrics(),
        timestamp: new Date().toISOString()
    };
    
    wss.clients.forEach((client) => {
        if (client.readyState === client.OPEN) {
            client.send(JSON.stringify(status));
        }
    });
}, 30000); // Every 30 seconds

// Error handling middleware
app.use((error, req, res, next) => {
    console.error(`[Error] ${req.method} ${req.path} - ${error.message}`, error);
    
    res.status(error.status || 500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
        requestId: req.requestId,
        timestamp: new Date().toISOString()
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: 'Not found',
        path: req.path,
        method: req.method,
        message: 'The requested resource was not found',
        requestId: req.requestId,
        timestamp: new Date().toISOString()
    });
});

// Graceful shutdown handling
process.on('SIGTERM', () => {
    console.log('[Server] SIGTERM received, shutting down gracefully');
    server.close(() => {
        console.log('[Server] Process terminated');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('[Server] SIGINT received, shutting down gracefully');
    server.close(() => {
        console.log('[Server] Process terminated');
        process.exit(0);
    });
});

// Start server
server.listen(PORT, '0.0.0.0', () => {
    console.log('');
    console.log('🚀 MCP Observatory Backend Server v2.0.0');
    console.log('==========================================');
    console.log(`📡 Server running on: http://0.0.0.0:${PORT}`);
    console.log(`🌐 External access: http://65.109.54.94:${PORT}`);
    console.log(`🔍 Health check: http://localhost:${PORT}/health`);
    console.log(`🛠️  Tools API: http://localhost:${PORT}/api/tools`);
    console.log(`⚡ Execute API: http://localhost:${PORT}/api/tools/execute`);
    console.log(`📊 Metrics API: http://localhost:${PORT}/api/metrics`);
    console.log(`🔌 WebSocket: ws://localhost:${PORT}`);
    console.log('');
    console.log('🔧 Available MCP Tools:');
    mcpRegistry.getAllTools().forEach(tool => {
        console.log(`   • ${tool.name}: ${tool.description}`);
    });
    console.log('');
    console.log('🔗 Available MCP Adapters:');
    mcpRegistry.getAllAdapters().forEach(adapter => {
        console.log(`   • ${adapter.name}: ${adapter.description}`);
    });
    console.log('');
    console.log('✅ Server ready for connections');
    console.log('==========================================');
});

export default app;


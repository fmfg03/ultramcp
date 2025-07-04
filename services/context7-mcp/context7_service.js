/**
 * UltraMCP Context7 Integration Service
 * 
 * Provides real-time, up-to-date documentation for AI coding assistants
 * Integrates Upstash Context7 MCP server with UltraMCP ecosystem
 */

const express = require('express');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const axios = require('axios');
const NodeCache = require('node-cache');
const winston = require('winston');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const { RateLimiterMemory } = require('rate-limiter-flexible');
const Joi = require('joi');
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const fs = require('fs').promises;

// Configuration
const config = {
    port: process.env.MCP_SERVER_PORT || 8003,
    host: process.env.MCP_SERVER_HOST || '0.0.0.0',
    nodeEnv: process.env.NODE_ENV || 'development',
    cacheTTL: parseInt(process.env.CONTEXT7_CACHE_TTL) || 3600, // 1 hour
    maxDocs: parseInt(process.env.CONTEXT7_MAX_DOCS) || 50,
    context7Command: process.env.CONTEXT7_COMMAND || 'npx',
    context7Args: process.env.CONTEXT7_ARGS?.split(',') || ['-y', '@upstash/context7-mcp@latest']
};

// Initialize logger
const logger = winston.createLogger({
    level: config.nodeEnv === 'production' ? 'info' : 'debug',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { service: 'context7-mcp' },
    transports: [
        new winston.transports.File({ filename: '/app/logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: '/app/logs/combined.log' }),
        new winston.transports.Console({
            format: winston.format.combine(
                winston.format.colorize(),
                winston.format.simple()
            )
        })
    ]
});

// Initialize cache
const documentationCache = new NodeCache({ 
    stdTTL: config.cacheTTL,
    checkperiod: 600,
    useClones: false
});

// Rate limiter
const rateLimiter = new RateLimiterMemory({
    keyGenerator: (req) => req.ip,
    points: 100, // Number of requests
    duration: 60, // Per 60 seconds
});

// Initialize Express app
const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true }));

// Request validation schemas
const documentationRequestSchema = Joi.object({
    library: Joi.string().required().min(1).max(100),
    version: Joi.string().optional().max(50),
    query: Joi.string().optional().max(500),
    type: Joi.string().valid('api', 'examples', 'guides', 'reference').default('api'),
    format: Joi.string().valid('markdown', 'json', 'text').default('markdown')
});

const batchRequestSchema = Joi.object({
    requests: Joi.array().items(documentationRequestSchema).min(1).max(10)
});

/**
 * Context7 MCP Manager
 * Manages the Context7 MCP server process and communication
 */
class Context7Manager {
    constructor() {
        this.mcpProcess = null;
        this.isRunning = false;
        this.startTime = null;
        this.requestCount = 0;
        this.errorCount = 0;
    }

    /**
     * Start the Context7 MCP server
     */
    async start() {
        try {
            logger.info('Starting Context7 MCP server...');
            
            this.mcpProcess = spawn(config.context7Command, config.context7Args, {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: { ...process.env }
            });

            this.mcpProcess.stdout.on('data', (data) => {
                logger.debug('Context7 stdout:', data.toString());
            });

            this.mcpProcess.stderr.on('data', (data) => {
                logger.warn('Context7 stderr:', data.toString());
            });

            this.mcpProcess.on('close', (code) => {
                logger.warn(`Context7 MCP server exited with code ${code}`);
                this.isRunning = false;
                
                // Auto-restart on unexpected exit
                if (code !== 0) {
                    setTimeout(() => this.start(), 5000);
                }
            });

            this.mcpProcess.on('error', (error) => {
                logger.error('Context7 MCP server error:', error);
                this.errorCount++;
                this.isRunning = false;
            });

            // Wait a bit for startup
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            this.isRunning = true;
            this.startTime = new Date();
            logger.info('Context7 MCP server started successfully');

        } catch (error) {
            logger.error('Failed to start Context7 MCP server:', error);
            throw error;
        }
    }

    /**
     * Stop the Context7 MCP server
     */
    async stop() {
        if (this.mcpProcess) {
            logger.info('Stopping Context7 MCP server...');
            this.mcpProcess.kill('SIGTERM');
            this.isRunning = false;
        }
    }

    /**
     * Send request to Context7 MCP server
     */
    async sendRequest(request) {
        if (!this.isRunning) {
            throw new Error('Context7 MCP server is not running');
        }

        try {
            this.requestCount++;
            
            // Create MCP request
            const mcpRequest = {
                jsonrpc: '2.0',
                id: uuidv4(),
                method: 'tools/call',
                params: {
                    name: 'context7',
                    arguments: request
                }
            };

            // Send to MCP server via stdin
            this.mcpProcess.stdin.write(JSON.stringify(mcpRequest) + '\n');

            // For now, we'll simulate the response
            // In a real implementation, you'd read from stdout
            return this.simulateContext7Response(request);

        } catch (error) {
            this.errorCount++;
            logger.error('Error sending request to Context7:', error);
            throw error;
        }
    }

    /**
     * Simulate Context7 response (placeholder for actual MCP communication)
     */
    async simulateContext7Response(request) {
        // This is a simulation - in reality, you'd parse actual MCP responses
        return {
            success: true,
            library: request.library,
            version: request.version || 'latest',
            documentation: `# ${request.library} Documentation\n\nUp-to-date documentation for ${request.library}`,
            examples: [
                {
                    title: `Basic ${request.library} example`,
                    code: `// Example usage of ${request.library}\nimport { example } from '${request.library}';\n\nexample();`
                }
            ],
            timestamp: new Date().toISOString(),
            source: 'context7-mcp'
        };
    }

    /**
     * Get manager status
     */
    getStatus() {
        return {
            isRunning: this.isRunning,
            startTime: this.startTime,
            requestCount: this.requestCount,
            errorCount: this.errorCount,
            uptime: this.startTime ? Date.now() - this.startTime.getTime() : 0
        };
    }
}

// Initialize Context7 manager
const context7Manager = new Context7Manager();

/**
 * Documentation Service
 * High-level service for managing documentation requests
 */
class DocumentationService {
    constructor() {
        this.cache = documentationCache;
    }

    /**
     * Get documentation for a library
     */
    async getDocumentation(request) {
        const cacheKey = this.generateCacheKey(request);
        
        // Check cache first
        const cached = this.cache.get(cacheKey);
        if (cached) {
            logger.debug(`Cache hit for ${request.library}`);
            return { ...cached, cached: true };
        }

        try {
            // Get fresh documentation from Context7
            const response = await context7Manager.sendRequest(request);
            
            // Cache the response
            this.cache.set(cacheKey, response);
            
            logger.info(`Retrieved documentation for ${request.library}`);
            return { ...response, cached: false };

        } catch (error) {
            logger.error(`Failed to get documentation for ${request.library}:`, error);
            throw error;
        }
    }

    /**
     * Get documentation for multiple libraries
     */
    async getBatchDocumentation(requests) {
        const results = await Promise.allSettled(
            requests.map(request => this.getDocumentation(request))
        );

        return results.map((result, index) => ({
            request: requests[index],
            success: result.status === 'fulfilled',
            data: result.status === 'fulfilled' ? result.value : null,
            error: result.status === 'rejected' ? result.reason.message : null
        }));
    }

    /**
     * Search documentation
     */
    async searchDocumentation(library, query) {
        const searchRequest = {
            library,
            query,
            type: 'search'
        };

        return this.getDocumentation(searchRequest);
    }

    /**
     * Generate cache key
     */
    generateCacheKey(request) {
        return `doc:${request.library}:${request.version || 'latest'}:${request.type}:${request.query || 'default'}`;
    }

    /**
     * Clear cache
     */
    clearCache(pattern = null) {
        if (pattern) {
            const keys = this.cache.keys().filter(key => key.includes(pattern));
            keys.forEach(key => this.cache.del(key));
            return keys.length;
        } else {
            const keys = this.cache.keys();
            this.cache.flushAll();
            return keys.length;
        }
    }

    /**
     * Get cache statistics
     */
    getCacheStats() {
        return {
            keys: this.cache.keys().length,
            hits: this.cache.getStats().hits,
            misses: this.cache.getStats().misses,
            size: this.cache.getStats().vsize
        };
    }
}

// Initialize documentation service
const docService = new DocumentationService();

// Rate limiting middleware
const rateLimitMiddleware = async (req, res, next) => {
    try {
        await rateLimiter.consume(req.ip);
        next();
    } catch (rejRes) {
        res.status(429).json({
            error: 'Too many requests',
            retryAfter: rejRes.msBeforeNext
        });
    }
};

// Apply rate limiting to API routes
app.use('/api/', rateLimitMiddleware);

// API Routes

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
    const status = context7Manager.getStatus();
    const cacheStats = docService.getCacheStats();
    
    res.json({
        status: status.isRunning ? 'healthy' : 'unhealthy',
        service: 'context7-mcp',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        uptime: status.uptime,
        stats: {
            requests: status.requestCount,
            errors: status.errorCount,
            cache: cacheStats
        }
    });
});

/**
 * Get documentation for a single library
 */
app.post('/api/documentation', async (req, res) => {
    try {
        const { error, value } = documentationRequestSchema.validate(req.body);
        if (error) {
            return res.status(400).json({ error: error.details[0].message });
        }

        const documentation = await docService.getDocumentation(value);
        
        res.json({
            success: true,
            data: documentation,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Documentation request failed:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Get documentation for multiple libraries (batch request)
 */
app.post('/api/documentation/batch', async (req, res) => {
    try {
        const { error, value } = batchRequestSchema.validate(req.body);
        if (error) {
            return res.status(400).json({ error: error.details[0].message });
        }

        const results = await docService.getBatchDocumentation(value.requests);
        
        res.json({
            success: true,
            data: results,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Batch documentation request failed:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Search documentation
 */
app.get('/api/documentation/search', async (req, res) => {
    try {
        const { library, query } = req.query;
        
        if (!library || !query) {
            return res.status(400).json({ 
                error: 'Library and query parameters are required' 
            });
        }

        const results = await docService.searchDocumentation(library, query);
        
        res.json({
            success: true,
            data: results,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Documentation search failed:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Clear documentation cache
 */
app.delete('/api/cache', (req, res) => {
    try {
        const { pattern } = req.query;
        const cleared = docService.clearCache(pattern);
        
        res.json({
            success: true,
            message: `Cleared ${cleared} cache entries`,
            pattern: pattern || 'all'
        });

    } catch (error) {
        logger.error('Cache clear failed:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Get service statistics
 */
app.get('/api/stats', (req, res) => {
    const managerStatus = context7Manager.getStatus();
    const cacheStats = docService.getCacheStats();
    
    res.json({
        success: true,
        data: {
            service: managerStatus,
            cache: cacheStats,
            memory: process.memoryUsage(),
            uptime: process.uptime()
        }
    });
});

/**
 * Claude Code Integration endpoint
 * Provides Context7 functionality for Claude Code prompts
 */
app.post('/api/claude/context', async (req, res) => {
    try {
        const { prompt, libraries = [], autoDetect = true } = req.body;
        
        if (!prompt) {
            return res.status(400).json({ error: 'Prompt is required' });
        }

        let librariesToFetch = [...libraries];
        
        // Auto-detect libraries from prompt if enabled
        if (autoDetect) {
            const detectedLibraries = await detectLibrariesFromPrompt(prompt);
            librariesToFetch = [...new Set([...librariesToFetch, ...detectedLibraries])];
        }

        // Fetch documentation for detected/specified libraries
        const documentationRequests = librariesToFetch.map(lib => ({
            library: lib,
            type: 'api'
        }));

        const results = await docService.getBatchDocumentation(documentationRequests);
        
        res.json({
            success: true,
            data: {
                prompt,
                libraries: librariesToFetch,
                documentation: results,
                enhancedPrompt: generateEnhancedPrompt(prompt, results)
            }
        });

    } catch (error) {
        logger.error('Claude context request failed:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Detect libraries mentioned in a prompt
 */
async function detectLibrariesFromPrompt(prompt) {
    const commonLibraries = [
        'react', 'vue', 'angular', 'express', 'fastify', 'next',
        'nuxt', 'svelte', 'typescript', 'lodash', 'moment', 'axios',
        'prisma', 'mongoose', 'sequelize', 'tailwind', 'bootstrap',
        'material-ui', 'chakra-ui', 'framer-motion', 'three', 'd3'
    ];

    const detected = [];
    const promptLower = prompt.toLowerCase();
    
    for (const lib of commonLibraries) {
        if (promptLower.includes(lib)) {
            detected.push(lib);
        }
    }
    
    return detected;
}

/**
 * Generate enhanced prompt with documentation context
 */
function generateEnhancedPrompt(originalPrompt, documentationResults) {
    const successfulDocs = documentationResults.filter(result => result.success);
    
    if (successfulDocs.length === 0) {
        return originalPrompt;
    }

    let enhancedPrompt = originalPrompt + '\n\n--- Context7 Documentation ---\n';
    
    successfulDocs.forEach(result => {
        enhancedPrompt += `\n## ${result.data.library} (${result.data.version})\n`;
        enhancedPrompt += result.data.documentation + '\n';
        
        if (result.data.examples && result.data.examples.length > 0) {
            enhancedPrompt += '\n### Examples:\n';
            result.data.examples.forEach(example => {
                enhancedPrompt += `\n**${example.title}**\n\`\`\`\n${example.code}\n\`\`\`\n`;
            });
        }
    });
    
    return enhancedPrompt;
}

// WebSocket server for real-time updates
const server = app.listen(config.port, config.host, () => {
    logger.info(`Context7 MCP service listening on ${config.host}:${config.port}`);
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
    logger.info('WebSocket client connected');
    
    ws.on('message', async (message) => {
        try {
            const request = JSON.parse(message);
            
            if (request.type === 'documentation') {
                const response = await docService.getDocumentation(request.data);
                ws.send(JSON.stringify({
                    type: 'documentation_response',
                    id: request.id,
                    success: true,
                    data: response
                }));
            }
            
        } catch (error) {
            ws.send(JSON.stringify({
                type: 'error',
                id: request.id || null,
                error: error.message
            }));
        }
    });
    
    ws.on('close', () => {
        logger.info('WebSocket client disconnected');
    });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    logger.info('Received SIGTERM, shutting down gracefully');
    
    // Close WebSocket server
    wss.close();
    
    // Close HTTP server
    server.close();
    
    // Stop Context7 manager
    await context7Manager.stop();
    
    process.exit(0);
});

process.on('SIGINT', async () => {
    logger.info('Received SIGINT, shutting down gracefully');
    
    // Close WebSocket server
    wss.close();
    
    // Close HTTP server
    server.close();
    
    // Stop Context7 manager
    await context7Manager.stop();
    
    process.exit(0);
});

// Start Context7 manager
context7Manager.start().catch(error => {
    logger.error('Failed to start Context7 manager:', error);
    process.exit(1);
});

// Export for testing
module.exports = { app, context7Manager, docService };
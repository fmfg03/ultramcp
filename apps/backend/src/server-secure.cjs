/**
 * Secure Server Configuration with Environment-based Security
 * Integrates SecurityManager and EnvironmentManager for production-ready setup
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const { securityManager } = require('./middleware/securityMiddleware');
const { environmentManager } = require('./utils/environmentManager');
const { logger } = require('./utils/logger');

// Import route handlers
const taskRoutes = require('./routes/taskRoutes');
const analyticsRoutes = require('./routes/analyticsRoutes');

class SecureServer {
  constructor() {
    this.app = express();
    this.environment = environmentManager.environment;
    this.config = environmentManager.getServerConfig();
    this.securityConfig = environmentManager.getSecurityConfig();
    
    this._validateEnvironment();
    this._setupMiddleware();
    this._setupRoutes();
    this._setupErrorHandling();
    
    logger.info(`🔐 Secure server initialized for ${this.environment} environment`);
  }

  /**
   * Validate environment setup
   */
  _validateEnvironment() {
    const validation = environmentManager.validateEnvironment();
    
    if (!validation.valid) {
      logger.error('❌ Environment validation failed:', validation.issues);
      if (this.environment === 'production') {
        process.exit(1);
      }
    }

    if (validation.warnings.length > 0) {
      logger.warn('⚠️ Environment warnings:', validation.warnings);
    }

    logger.info('✅ Environment validation passed');
  }

  /**
   * Setup middleware stack
   */
  _setupMiddleware() {
    // Trust proxy in production
    if (this.environment === 'production') {
      this.app.set('trust proxy', 1);
    }

    // Security headers (production only)
    if (environmentManager.isFeatureEnabled('enableHelmet')) {
      this.app.use(helmet({
        contentSecurityPolicy: {
          directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", "ws:", "wss:"]
          }
        },
        hsts: {
          maxAge: 31536000,
          includeSubDomains: true,
          preload: true
        }
      }));
    }

    // Compression (production only)
    if (environmentManager.isFeatureEnabled('enableCompression')) {
      this.app.use(compression());
    }

    // CORS configuration
    if (environmentManager.isFeatureEnabled('enableCORS')) {
      this.app.use(cors(this.config.cors));
    }

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Environment detection middleware
    this.app.use(securityManager.environmentMiddleware());

    // Security audit logging
    this.app.use(securityManager.auditMiddleware());

    // Input sanitization
    this.app.use(securityManager.sanitizationMiddleware());

    // General rate limiting
    this.app.use(securityManager.rateLimitMiddleware('general'));

    logger.info('🛡️ Security middleware configured');
  }

  /**
   * Setup application routes with security
   */
  _setupRoutes() {
    // Health check (no auth required)
    this.app.get('/health', (req, res) => {
      const status = {
        status: 'healthy',
        environment: this.environment,
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        security: securityManager.getSecurityStatus()
      };

      res.json(status);
    });

    // Environment info (development only)
    if (this.environment === 'development') {
      this.app.get('/env', (req, res) => {
        res.json(environmentManager.getStatus());
      });
    }

    // Public API routes (with rate limiting)
    this.app.use('/api', 
      securityManager.rateLimitMiddleware('general'),
      taskRoutes
    );

    // MCP routes (with enhanced security)
    this.app.use('/mcp',
      securityManager.rateLimitMiddleware('mcp'),
      securityManager.mcpAuthMiddleware(),
      securityManager.ipAuthMiddleware(),
      taskRoutes
    );

    // Studio routes (with studio-specific auth)
    this.app.use('/studio',
      securityManager.rateLimitMiddleware('studio'),
      securityManager.studioAuthMiddleware(),
      this._setupStudioRoutes()
    );

    // Analytics routes (with token auth)
    this.app.use('/analytics',
      securityManager.rateLimitMiddleware('general'),
      securityManager.tokenAuthMiddleware(),
      analyticsRoutes
    );

    // Authentication routes (with strict rate limiting)
    this.app.use('/auth',
      securityManager.rateLimitMiddleware('auth'),
      this._setupAuthRoutes()
    );

    // Serve static files (development only)
    if (this.environment === 'development') {
      this.app.use('/static', express.static('public'));
    }

    logger.info('🛣️ Secure routes configured');
  }

  /**
   * Setup Studio-specific routes
   * @returns {express.Router} Studio router
   */
  _setupStudioRoutes() {
    const router = express.Router();

    // Studio dashboard
    router.get('/', (req, res) => {
      res.json({
        message: 'LangGraph Studio API',
        environment: this.environment,
        features: {
          debugging: environmentManager.isFeatureEnabled('enableStudioDebug'),
          auth: environmentManager.isFeatureEnabled('enableStudioAuth'),
          metrics: environmentManager.isFeatureEnabled('enableMetrics')
        }
      });
    });

    // Studio status
    router.get('/status', (req, res) => {
      res.json({
        status: 'active',
        environment: this.environment,
        sessions: 0, // TODO: Implement session tracking
        agents: ['complete_mcp', 'reasoning', 'builder', 'perplexity', 'attendee']
      });
    });

    // Studio metrics (if enabled)
    if (environmentManager.isFeatureEnabled('enableMetrics')) {
      router.get('/metrics', (req, res) => {
        res.json({
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          environment: this.environment
        });
      });
    }

    return router;
  }

  /**
   * Setup authentication routes
   * @returns {express.Router} Auth router
   */
  _setupAuthRoutes() {
    const router = express.Router();

    // Generate temporary token
    router.post('/token', (req, res) => {
      try {
        const { purpose = 'general', duration = '24h' } = req.body;
        
        const token = securityManager.generateToken({
          purpose,
          ip: req.ip,
          userAgent: req.headers['user-agent']
        }, duration);

        logger.info(`Token generated for ${req.ip}, purpose: ${purpose}`);

        res.json({
          token,
          expiresIn: duration,
          purpose,
          environment: this.environment
        });
      } catch (error) {
        logger.error('Token generation failed:', error);
        res.status(500).json({
          error: 'Token generation failed',
          message: error.message
        });
      }
    });

    // Validate token
    router.post('/validate', securityManager.tokenAuthMiddleware(), (req, res) => {
      res.json({
        valid: true,
        user: req.user,
        environment: this.environment
      });
    });

    return router;
  }

  /**
   * Setup error handling
   */
  _setupErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      logger.warn(`404 - Route not found: ${req.method} ${req.originalUrl}`);
      res.status(404).json({
        error: 'Not Found',
        message: 'The requested resource was not found',
        path: req.originalUrl
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      logger.error('Unhandled error:', error);

      // Don't leak error details in production
      const isDevelopment = this.environment === 'development';
      
      res.status(error.status || 500).json({
        error: error.name || 'Internal Server Error',
        message: isDevelopment ? error.message : 'An internal error occurred',
        ...(isDevelopment && { stack: error.stack }),
        timestamp: new Date().toISOString(),
        requestId: req.id || 'unknown'
      });
    });

    logger.info('🚨 Error handling configured');
  }

  /**
   * Start the server
   * @param {number} port - Port to listen on
   * @returns {Promise} Server instance
   */
  async start(port = this.config.port) {
    return new Promise((resolve, reject) => {
      try {
        const server = this.app.listen(port, this.config.host, () => {
          logger.info(`🚀 Secure MCP Server running on ${this.config.host}:${port}`);
          logger.info(`🌍 Environment: ${this.environment}`);
          logger.info(`🔐 Security: ${this.securityConfig.authRequired ? 'Enabled' : 'Development Mode'}`);
          
          if (this.environment === 'development') {
            logger.info('📊 Available endpoints:');
            logger.info('  - Health: http://localhost:' + port + '/health');
            logger.info('  - Environment: http://localhost:' + port + '/env');
            logger.info('  - Studio: http://localhost:' + port + '/studio');
            logger.info('  - API: http://localhost:' + port + '/api');
            logger.info('  - MCP: http://localhost:' + port + '/mcp');
          }
          
          resolve(server);
        });

        // Graceful shutdown
        process.on('SIGTERM', () => {
          logger.info('🛑 SIGTERM received, shutting down gracefully');
          server.close(() => {
            logger.info('✅ Server closed');
            process.exit(0);
          });
        });

        process.on('SIGINT', () => {
          logger.info('🛑 SIGINT received, shutting down gracefully');
          server.close(() => {
            logger.info('✅ Server closed');
            process.exit(0);
          });
        });

      } catch (error) {
        logger.error('❌ Failed to start server:', error);
        reject(error);
      }
    });
  }

  /**
   * Get Express app instance
   * @returns {express.Application} Express app
   */
  getApp() {
    return this.app;
  }
}

// Export for use in other modules
module.exports = { SecureServer };

// Start server if this file is run directly
if (require.main === module) {
  const server = new SecureServer();
  server.start().catch(error => {
    logger.error('❌ Server startup failed:', error);
    process.exit(1);
  });
}


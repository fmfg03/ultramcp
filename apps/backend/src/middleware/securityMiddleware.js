/**
 * Security Middleware for MCP System
 * Implements rate limiting, authentication, and environment-based controls
 */

const rateLimit = require('express-rate-limit');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { logger } = require('../utils/logger');

class SecurityManager {
  constructor() {
    this.environment = this._detectEnvironment();
    this.rateLimiters = this._setupRateLimiters();
    this.authTokens = new Map(); // In-memory token store (use Redis in production)
    this.ipWhitelist = this._loadIPWhitelist();
    this.secretKey = process.env.STUDIO_SECRET || this._generateSecret();
    
    logger.info(`Security Manager initialized for ${this.environment} environment`);
  }

  /**
   * Detect current environment
   * @returns {string} Environment name
   */
  _detectEnvironment() {
    // Check explicit environment variable
    if (process.env.NODE_ENV) {
      return process.env.NODE_ENV.toLowerCase();
    }

    // Check for development indicators
    if (process.env.DEBUG || 
        process.env.DEVELOPMENT || 
        process.argv.includes('--dev') ||
        process.cwd().includes('dev') ||
        process.env.PORT === '3000') {
      return 'development';
    }

    // Check for test indicators
    if (process.env.TEST || 
        process.argv.includes('--test') ||
        process.env.CI ||
        process.env.JEST_WORKER_ID) {
      return 'test';
    }

    // Check for production indicators
    if (process.env.PRODUCTION ||
        process.env.PM2_HOME ||
        process.env.KUBERNETES_SERVICE_HOST ||
        process.env.HEROKU_APP_NAME ||
        process.env.VERCEL ||
        process.env.NETLIFY) {
      return 'production';
    }

    // Default to development for safety
    return 'development';
  }

  /**
   * Setup rate limiters for different endpoints
   * @returns {Object} Rate limiter configurations
   */
  _setupRateLimiters() {
    const baseConfig = {
      windowMs: 15 * 60 * 1000, // 15 minutes
      standardHeaders: true,
      legacyHeaders: false,
      handler: (req, res) => {
        logger.warn(`Rate limit exceeded for IP: ${req.ip}, endpoint: ${req.path}`);
        res.status(429).json({
          error: 'Too many requests',
          message: 'Rate limit exceeded. Please try again later.',
          retryAfter: Math.ceil(req.rateLimit.resetTime / 1000)
        });
      }
    };

    return {
      // General API rate limiting
      general: rateLimit({
        ...baseConfig,
        max: this.environment === 'production' ? 100 : 1000, // requests per window
        message: 'Too many API requests'
      }),

      // MCP endpoints - more restrictive
      mcp: rateLimit({
        ...baseConfig,
        max: this.environment === 'production' ? 50 : 500,
        windowMs: 10 * 60 * 1000, // 10 minutes
        message: 'Too many MCP requests'
      }),

      // Studio endpoints - moderate restrictions
      studio: rateLimit({
        ...baseConfig,
        max: this.environment === 'production' ? 200 : 2000,
        message: 'Too many Studio requests'
      }),

      // Authentication endpoints - very restrictive
      auth: rateLimit({
        ...baseConfig,
        max: this.environment === 'production' ? 5 : 50,
        windowMs: 5 * 60 * 1000, // 5 minutes
        message: 'Too many authentication attempts'
      })
    };
  }

  /**
   * Load IP whitelist from environment
   * @returns {Set} Set of whitelisted IPs
   */
  _loadIPWhitelist() {
    const whitelist = new Set();
    
    // Always allow localhost in development
    if (this.environment === 'development') {
      whitelist.add('127.0.0.1');
      whitelist.add('::1');
      whitelist.add('localhost');
    }

    // Load from environment variable
    if (process.env.IP_WHITELIST) {
      const ips = process.env.IP_WHITELIST.split(',');
      ips.forEach(ip => whitelist.add(ip.trim()));
    }

    return whitelist;
  }

  /**
   * Generate a secure secret key
   * @returns {string} Generated secret
   */
  _generateSecret() {
    const secret = crypto.randomBytes(32).toString('hex');
    logger.warn('Generated temporary secret key. Set STUDIO_SECRET in production!');
    return secret;
  }

  /**
   * General rate limiting middleware
   * @param {string} type - Rate limiter type
   * @returns {Function} Express middleware
   */
  rateLimitMiddleware(type = 'general') {
    return this.rateLimiters[type] || this.rateLimiters.general;
  }

  /**
   * IP-based authentication middleware
   * @returns {Function} Express middleware
   */
  ipAuthMiddleware() {
    return (req, res, next) => {
      // Skip IP check in development
      if (this.environment === 'development') {
        return next();
      }

      const clientIP = req.ip || req.connection.remoteAddress;
      
      if (this.ipWhitelist.has(clientIP)) {
        logger.info(`Allowed IP access: ${clientIP}`);
        return next();
      }

      logger.warn(`Blocked IP access attempt: ${clientIP}`);
      return res.status(403).json({
        error: 'Access denied',
        message: 'Your IP address is not authorized to access this resource'
      });
    };
  }

  /**
   * Token-based authentication middleware
   * @returns {Function} Express middleware
   */
  tokenAuthMiddleware() {
    return (req, res, next) => {
      // Extract token from header or query
      const token = req.headers.authorization?.replace('Bearer ', '') || 
                   req.query.token || 
                   req.headers['x-api-key'];

      if (!token) {
        return res.status(401).json({
          error: 'Authentication required',
          message: 'No authentication token provided'
        });
      }

      try {
        // Verify JWT token
        const decoded = jwt.verify(token, this.secretKey);
        req.user = decoded;
        
        logger.info(`Authenticated user: ${decoded.id || 'unknown'}`);
        next();
      } catch (error) {
        logger.warn(`Invalid token attempt: ${error.message}`);
        return res.status(401).json({
          error: 'Invalid token',
          message: 'The provided authentication token is invalid or expired'
        });
      }
    };
  }

  /**
   * Environment-based middleware
   * @returns {Function} Express middleware
   */
  environmentMiddleware() {
    return (req, res, next) => {
      // Add environment info to request
      req.environment = this.environment;
      req.isProduction = this.environment === 'production';
      req.isDevelopment = this.environment === 'development';
      req.isTest = this.environment === 'test';

      // Set security headers based on environment
      if (this.environment === 'production') {
        res.setHeader('X-Content-Type-Options', 'nosniff');
        res.setHeader('X-Frame-Options', 'DENY');
        res.setHeader('X-XSS-Protection', '1; mode=block');
        res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
      }

      // Add environment header for debugging
      if (this.environment !== 'production') {
        res.setHeader('X-Environment', this.environment);
      }

      next();
    };
  }

  /**
   * Studio-specific authentication
   * @returns {Function} Express middleware
   */
  studioAuthMiddleware() {
    return (req, res, next) => {
      // In development, allow access without auth
      if (this.environment === 'development') {
        return next();
      }

      // Check for studio secret
      const studioSecret = req.headers['x-studio-secret'] || req.query.secret;
      
      if (!studioSecret || studioSecret !== process.env.STUDIO_SECRET) {
        logger.warn(`Unauthorized Studio access attempt from ${req.ip}`);
        return res.status(401).json({
          error: 'Studio access denied',
          message: 'Valid studio secret required'
        });
      }

      next();
    };
  }

  /**
   * MCP-specific authentication
   * @returns {Function} Express middleware
   */
  mcpAuthMiddleware() {
    return (req, res, next) => {
      // In development, allow access without auth
      if (this.environment === 'development') {
        return next();
      }

      // Check for MCP API key
      const apiKey = req.headers['x-mcp-key'] || req.query.key;
      
      if (!apiKey || !this._validateMCPKey(apiKey)) {
        logger.warn(`Unauthorized MCP access attempt from ${req.ip}`);
        return res.status(401).json({
          error: 'MCP access denied',
          message: 'Valid MCP API key required'
        });
      }

      next();
    };
  }

  /**
   * Validate MCP API key
   * @param {string} key - API key to validate
   * @returns {boolean} Validation result
   */
  _validateMCPKey(key) {
    // Check against environment variable
    const validKeys = (process.env.MCP_API_KEYS || '').split(',').map(k => k.trim());
    return validKeys.includes(key);
  }

  /**
   * Generate temporary access token
   * @param {Object} payload - Token payload
   * @param {string} expiresIn - Expiration time
   * @returns {string} JWT token
   */
  generateToken(payload = {}, expiresIn = '24h') {
    const tokenPayload = {
      ...payload,
      iat: Math.floor(Date.now() / 1000),
      env: this.environment
    };

    return jwt.sign(tokenPayload, this.secretKey, { expiresIn });
  }

  /**
   * Security audit middleware
   * @returns {Function} Express middleware
   */
  auditMiddleware() {
    return (req, res, next) => {
      const startTime = Date.now();
      
      // Log security-relevant requests
      if (req.path.startsWith('/mcp') || req.path.startsWith('/studio')) {
        logger.info(`Security audit: ${req.method} ${req.path} from ${req.ip}`, {
          userAgent: req.headers['user-agent'],
          referer: req.headers.referer,
          environment: this.environment
        });
      }

      // Monitor response
      res.on('finish', () => {
        const duration = Date.now() - startTime;
        
        // Log suspicious activity
        if (res.statusCode >= 400) {
          logger.warn(`Security event: ${res.statusCode} response for ${req.path}`, {
            ip: req.ip,
            duration,
            statusCode: res.statusCode
          });
        }
      });

      next();
    };
  }

  /**
   * Input sanitization middleware
   * @returns {Function} Express middleware
   */
  sanitizationMiddleware() {
    return (req, res, next) => {
      // Sanitize query parameters
      if (req.query) {
        for (const [key, value] of Object.entries(req.query)) {
          if (typeof value === 'string') {
            req.query[key] = this._sanitizeInput(value);
          }
        }
      }

      // Sanitize body parameters
      if (req.body && typeof req.body === 'object') {
        req.body = this._sanitizeObject(req.body);
      }

      next();
    };
  }

  /**
   * Sanitize input string
   * @param {string} input - Input to sanitize
   * @returns {string} Sanitized input
   */
  _sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    
    // Remove potentially dangerous characters
    return input
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '')
      .trim();
  }

  /**
   * Sanitize object recursively
   * @param {Object} obj - Object to sanitize
   * @returns {Object} Sanitized object
   */
  _sanitizeObject(obj) {
    if (typeof obj !== 'object' || obj === null) return obj;
    
    const sanitized = {};
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'string') {
        sanitized[key] = this._sanitizeInput(value);
      } else if (typeof value === 'object') {
        sanitized[key] = this._sanitizeObject(value);
      } else {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }

  /**
   * Get security status
   * @returns {Object} Security status information
   */
  getSecurityStatus() {
    return {
      environment: this.environment,
      rateLimitersActive: Object.keys(this.rateLimiters).length,
      ipWhitelistSize: this.ipWhitelist.size,
      authTokensActive: this.authTokens.size,
      securityLevel: this.environment === 'production' ? 'high' : 'medium'
    };
  }
}

// Export singleton instance
const securityManager = new SecurityManager();

module.exports = {
  securityManager,
  SecurityManager
};


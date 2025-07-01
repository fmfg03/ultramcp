/**
 * Environment Detection and Configuration
 * Automatically detects environment and configures system accordingly
 */

const path = require('path');
const fs = require('fs');

class EnvironmentManager {
  constructor() {
    this.environment = this._detectEnvironment();
    this.config = this._loadEnvironmentConfig();
    this.features = this._configureFeatures();
    
    // Set global environment
    process.env.NODE_ENV = this.environment;
    
    console.log(`🌍 Environment detected: ${this.environment.toUpperCase()}`);
    this._logEnvironmentInfo();
  }

  /**
   * Comprehensive environment detection
   * @returns {string} Detected environment
   */
  _detectEnvironment() {
    // 1. Explicit NODE_ENV
    if (process.env.NODE_ENV) {
      return process.env.NODE_ENV.toLowerCase();
    }

    // 2. Command line arguments
    const args = process.argv.join(' ');
    if (args.includes('--prod') || args.includes('--production')) return 'production';
    if (args.includes('--test') || args.includes('--testing')) return 'test';
    if (args.includes('--dev') || args.includes('--development')) return 'development';

    // 3. Environment variables indicators
    const envIndicators = {
      production: [
        'PRODUCTION',
        'PROD',
        'PM2_HOME',
        'KUBERNETES_SERVICE_HOST',
        'HEROKU_APP_NAME',
        'VERCEL',
        'NETLIFY',
        'AWS_LAMBDA_FUNCTION_NAME',
        'GOOGLE_CLOUD_PROJECT'
      ],
      test: [
        'TEST',
        'TESTING',
        'CI',
        'CONTINUOUS_INTEGRATION',
        'JEST_WORKER_ID',
        'MOCHA',
        'VITEST'
      ],
      development: [
        'DEBUG',
        'DEVELOPMENT',
        'DEV',
        'LOCAL'
      ]
    };

    for (const [env, indicators] of Object.entries(envIndicators)) {
      if (indicators.some(indicator => process.env[indicator])) {
        return env;
      }
    }

    // 4. Port-based detection
    const port = process.env.PORT || '3000';
    if (['80', '443', '8080'].includes(port)) return 'production';
    if (port === '3000' || port.startsWith('300')) return 'development';

    // 5. Directory structure analysis
    const cwd = process.cwd();
    if (cwd.includes('/prod') || cwd.includes('/production')) return 'production';
    if (cwd.includes('/test') || cwd.includes('/testing')) return 'test';
    if (cwd.includes('/dev') || cwd.includes('/development')) return 'development';

    // 6. Package.json script detection
    try {
      const packagePath = path.join(cwd, 'package.json');
      if (fs.existsSync(packagePath)) {
        const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
        const script = process.env.npm_lifecycle_event;
        
        if (script) {
          if (script.includes('prod')) return 'production';
          if (script.includes('test')) return 'test';
          if (script.includes('dev')) return 'development';
        }
      }
    } catch (error) {
      // Ignore package.json parsing errors
    }

    // 7. File system indicators
    const indicators = {
      production: ['.prod', 'production.env', 'prod.config.js'],
      test: ['.test', 'test.env', 'jest.config.js', 'vitest.config.js'],
      development: ['.dev', 'development.env', 'dev.config.js']
    };

    for (const [env, files] of Object.entries(indicators)) {
      if (files.some(file => fs.existsSync(path.join(cwd, file)))) {
        return env;
      }
    }

    // Default to development for safety
    return 'development';
  }

  /**
   * Load environment-specific configuration
   * @returns {Object} Environment configuration
   */
  _loadEnvironmentConfig() {
    const baseConfig = {
      development: {
        logLevel: 'debug',
        enableDebug: true,
        enableMetrics: true,
        enableStudio: true,
        rateLimitMultiplier: 10,
        authRequired: false,
        corsOrigins: ['http://localhost:3000', 'http://localhost:5173'],
        allowedIPs: ['127.0.0.1', '::1'],
        database: {
          pool: { min: 1, max: 5 },
          timeout: 30000
        }
      },
      test: {
        logLevel: 'warn',
        enableDebug: false,
        enableMetrics: false,
        enableStudio: false,
        rateLimitMultiplier: 100,
        authRequired: false,
        corsOrigins: ['http://localhost:3000'],
        allowedIPs: ['127.0.0.1'],
        database: {
          pool: { min: 1, max: 3 },
          timeout: 10000
        }
      },
      production: {
        logLevel: 'info',
        enableDebug: false,
        enableMetrics: true,
        enableStudio: true,
        rateLimitMultiplier: 1,
        authRequired: true,
        corsOrigins: process.env.CORS_ORIGINS?.split(',') || [],
        allowedIPs: process.env.ALLOWED_IPS?.split(',') || [],
        database: {
          pool: { min: 5, max: 20 },
          timeout: 60000
        }
      }
    };

    return baseConfig[this.environment] || baseConfig.development;
  }

  /**
   * Configure features based on environment
   * @returns {Object} Feature configuration
   */
  _configureFeatures() {
    return {
      // Logging features
      enableConsoleLogging: this.environment !== 'production',
      enableFileLogging: this.environment === 'production',
      enableRemoteLogging: this.environment === 'production',
      logSensitiveData: this.environment === 'development',

      // Security features
      enableRateLimit: true,
      enableAuth: this.config.authRequired,
      enableIPWhitelist: this.environment === 'production',
      enableCORS: true,
      enableHelmet: this.environment === 'production',

      // Development features
      enableHotReload: this.environment === 'development',
      enableSourceMaps: this.environment !== 'production',
      enableProfiling: this.environment === 'development',
      enableMockData: this.environment === 'test',

      // Monitoring features
      enableHealthCheck: true,
      enableMetrics: this.config.enableMetrics,
      enableTracing: this.environment === 'production',
      enableAlerting: this.environment === 'production',

      // Studio features
      enableStudio: this.config.enableStudio,
      enableStudioAuth: this.environment === 'production',
      enableStudioDebug: this.environment !== 'production',

      // Performance features
      enableCaching: this.environment === 'production',
      enableCompression: this.environment === 'production',
      enableMinification: this.environment === 'production',
      enableCDN: this.environment === 'production'
    };
  }

  /**
   * Log environment information
   */
  _logEnvironmentInfo() {
    const info = {
      environment: this.environment,
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch,
      pid: process.pid,
      cwd: process.cwd(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      features: Object.entries(this.features)
        .filter(([, enabled]) => enabled)
        .map(([feature]) => feature)
    };

    if (this.environment === 'development') {
      console.log('🔧 Environment Configuration:', JSON.stringify(info, null, 2));
    } else {
      console.log(`📊 Environment: ${this.environment}, Features: ${info.features.length} enabled`);
    }
  }

  /**
   * Get environment-specific logger configuration
   * @returns {Object} Logger configuration
   */
  getLoggerConfig() {
    return {
      level: this.config.logLevel,
      format: this.environment === 'production' ? 'json' : 'simple',
      enableConsole: this.features.enableConsoleLogging,
      enableFile: this.features.enableFileLogging,
      enableRemote: this.features.enableRemoteLogging,
      redactSensitive: !this.features.logSensitiveData,
      transports: this._getLogTransports()
    };
  }

  /**
   * Get log transports based on environment
   * @returns {Array} Log transport configurations
   */
  _getLogTransports() {
    const transports = [];

    // Console transport
    if (this.features.enableConsoleLogging) {
      transports.push({
        type: 'console',
        level: this.config.logLevel,
        colorize: this.environment === 'development'
      });
    }

    // File transport
    if (this.features.enableFileLogging) {
      transports.push({
        type: 'file',
        filename: `logs/mcp-${this.environment}.log`,
        maxsize: 10485760, // 10MB
        maxFiles: 5,
        level: 'info'
      });
    }

    // Error file transport
    if (this.environment === 'production') {
      transports.push({
        type: 'file',
        filename: 'logs/error.log',
        level: 'error',
        maxsize: 5242880, // 5MB
        maxFiles: 3
      });
    }

    return transports;
  }

  /**
   * Get database configuration
   * @returns {Object} Database configuration
   */
  getDatabaseConfig() {
    return {
      ...this.config.database,
      ssl: this.environment === 'production',
      logging: this.environment === 'development',
      synchronize: this.environment !== 'production',
      dropSchema: this.environment === 'test'
    };
  }

  /**
   * Get server configuration
   * @returns {Object} Server configuration
   */
  getServerConfig() {
    return {
      port: process.env.PORT || (this.environment === 'production' ? 8080 : 3000),
      host: this.environment === 'production' ? '0.0.0.0' : 'localhost',
      cors: {
        origin: this.config.corsOrigins,
        credentials: true,
        optionsSuccessStatus: 200
      },
      compression: this.features.enableCompression,
      helmet: this.features.enableHelmet,
      rateLimit: {
        enabled: this.features.enableRateLimit,
        multiplier: this.config.rateLimitMultiplier
      }
    };
  }

  /**
   * Get security configuration
   * @returns {Object} Security configuration
   */
  getSecurityConfig() {
    return {
      authRequired: this.config.authRequired,
      ipWhitelist: this.config.allowedIPs,
      enableIPWhitelist: this.features.enableIPWhitelist,
      jwtSecret: process.env.JWT_SECRET || 'dev-secret-key',
      sessionSecret: process.env.SESSION_SECRET || 'dev-session-secret',
      bcryptRounds: this.environment === 'production' ? 12 : 8,
      tokenExpiry: this.environment === 'production' ? '1h' : '24h'
    };
  }

  /**
   * Check if feature is enabled
   * @param {string} feature - Feature name
   * @returns {boolean} Feature status
   */
  isFeatureEnabled(feature) {
    return this.features[feature] || false;
  }

  /**
   * Get environment status
   * @returns {Object} Environment status
   */
  getStatus() {
    return {
      environment: this.environment,
      config: this.config,
      features: this.features,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      versions: process.versions
    };
  }

  /**
   * Validate environment setup
   * @returns {Object} Validation results
   */
  validateEnvironment() {
    const issues = [];
    const warnings = [];

    // Check required environment variables
    const requiredVars = {
      production: ['JWT_SECRET', 'SESSION_SECRET', 'DATABASE_URL'],
      test: ['TEST_DATABASE_URL'],
      development: []
    };

    const required = requiredVars[this.environment] || [];
    for (const varName of required) {
      if (!process.env[varName]) {
        issues.push(`Missing required environment variable: ${varName}`);
      }
    }

    // Check optional but recommended variables
    const recommendedVars = {
      production: ['STUDIO_SECRET', 'MCP_API_KEYS', 'LANGWATCH_API_KEY'],
      development: ['DEBUG'],
      test: []
    };

    const recommended = recommendedVars[this.environment] || [];
    for (const varName of recommended) {
      if (!process.env[varName]) {
        warnings.push(`Recommended environment variable not set: ${varName}`);
      }
    }

    // Check file permissions
    if (this.features.enableFileLogging) {
      try {
        const logDir = path.join(process.cwd(), 'logs');
        if (!fs.existsSync(logDir)) {
          fs.mkdirSync(logDir, { recursive: true });
        }
      } catch (error) {
        issues.push(`Cannot create logs directory: ${error.message}`);
      }
    }

    return {
      valid: issues.length === 0,
      issues,
      warnings,
      environment: this.environment
    };
  }
}

// Export singleton instance
const environmentManager = new EnvironmentManager();

module.exports = {
  environmentManager,
  EnvironmentManager
};


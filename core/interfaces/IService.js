/**
 * Service Interface for UltraMCP
 * 
 * Standard interface that all services must implement to integrate
 * with the orchestration system.
 */

class IService {
    constructor(config = {}) {
        this.id = config.id || this.constructor.name.toLowerCase();
        this.name = config.name || this.id;
        this.capabilities = config.capabilities || [];
        this.config = config;
        this.initialized = false;
        this.metadata = {
            version: config.version || '1.0.0',
            description: config.description || '',
            author: config.author || '',
            tags: config.tags || []
        };
    }

    // ===== REQUIRED METHODS =====

    /**
     * Initialize the service
     * Must be implemented by each service
     */
    async initialize() {
        throw new Error(`initialize() must be implemented by service ${this.id}`);
    }

    /**
     * Execute service operation
     * Must be implemented by each service
     */
    async execute(input, context) {
        throw new Error(`execute() must be implemented by service ${this.id}`);
    }

    /**
     * Health check for service
     * Must be implemented by each service
     */
    async healthCheck() {
        throw new Error(`healthCheck() must be implemented by service ${this.id}`);
    }

    // ===== OPTIONAL METHODS WITH DEFAULT IMPLEMENTATIONS =====

    /**
     * Shutdown the service gracefully
     */
    async shutdown() {
        this.initialized = false;
        console.log(`🛑 Service ${this.id} shutdown`);
    }

    /**
     * Get service capabilities
     */
    getCapabilities() {
        return [...this.capabilities];
    }

    /**
     * Get service metadata
     */
    getMetadata() {
        return {
            id: this.id,
            name: this.name,
            capabilities: this.getCapabilities(),
            initialized: this.initialized,
            ...this.metadata
        };
    }

    /**
     * Validate input before execution
     */
    validateInput(input, context) {
        if (input === null || input === undefined) {
            throw this.createError('Input cannot be null or undefined', 'INVALID_INPUT');
        }
        return true;
    }

    /**
     * Preprocess input before execution
     */
    async preprocessInput(input, context) {
        // Default implementation - can be overridden
        return input;
    }

    /**
     * Postprocess result after execution
     */
    async postprocessResult(result, context) {
        // Default implementation - can be overridden
        return result;
    }

    /**
     * Handle errors that occur during execution
     */
    handleError(error, context) {
        // Default error handling - can be overridden
        if (error instanceof ServiceError) {
            throw error;
        }
        
        throw this.createError(
            error.message || 'Unknown service error',
            error.code || 'SERVICE_ERROR',
            { originalError: error }
        );
    }

    // ===== HELPER METHODS =====

    /**
     * Create standardized service error
     */
    createError(message, code = 'SERVICE_ERROR', details = {}) {
        const error = new ServiceError(message);
        error.code = code;
        error.serviceId = this.id;
        error.serviceName = this.name;
        error.details = details;
        error.timestamp = new Date().toISOString();
        return error;
    }

    /**
     * Create standardized success result
     */
    createResult(data, metadata = {}) {
        return {
            success: true,
            data,
            metadata: {
                serviceId: this.id,
                serviceName: this.name,
                timestamp: new Date().toISOString(),
                executionTime: metadata.executionTime,
                ...metadata
            }
        };
    }

    /**
     * Create standardized error result
     */
    createErrorResult(error, metadata = {}) {
        return {
            success: false,
            error: {
                message: error.message,
                code: error.code || 'SERVICE_ERROR',
                serviceId: this.id,
                serviceName: this.name,
                details: error.details || {}
            },
            metadata: {
                serviceId: this.id,
                serviceName: this.name,
                timestamp: new Date().toISOString(),
                ...metadata
            }
        };
    }

    /**
     * Log service activity
     */
    log(level, message, details = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            level,
            serviceId: this.id,
            serviceName: this.name,
            message,
            details
        };

        switch (level) {
            case 'error':
                console.error(`❌ [${this.name}]`, message, details);
                break;
            case 'warn':
                console.warn(`⚠️ [${this.name}]`, message, details);
                break;
            case 'info':
                console.log(`ℹ️ [${this.name}]`, message, details);
                break;
            case 'debug':
                if (process.env.NODE_ENV === 'development') {
                    console.log(`🐛 [${this.name}]`, message, details);
                }
                break;
        }
    }

    /**
     * Measure execution time
     */
    async measureExecution(fn, operationName = 'operation') {
        const startTime = Date.now();
        
        try {
            const result = await fn();
            const executionTime = Date.now() - startTime;
            
            this.log('debug', `${operationName} completed`, { 
                executionTime: `${executionTime}ms` 
            });
            
            return { result, executionTime };
        } catch (error) {
            const executionTime = Date.now() - startTime;
            
            this.log('error', `${operationName} failed`, { 
                executionTime: `${executionTime}ms`,
                error: error.message 
            });
            
            throw error;
        }
    }

    /**
     * Validate service configuration
     */
    validateConfig() {
        const required = this.getRequiredConfig();
        const missing = [];

        for (const field of required) {
            if (!this.config[field]) {
                missing.push(field);
            }
        }

        if (missing.length > 0) {
            throw this.createError(
                `Missing required configuration: ${missing.join(', ')}`,
                'CONFIG_ERROR',
                { missingFields: missing }
            );
        }
    }

    /**
     * Get required configuration fields
     * Override in subclasses to specify required config
     */
    getRequiredConfig() {
        return [];
    }

    /**
     * Get service status information
     */
    getStatus() {
        return {
            id: this.id,
            name: this.name,
            initialized: this.initialized,
            capabilities: this.getCapabilities(),
            health: 'unknown', // Will be updated by health check
            metadata: this.getMetadata()
        };
    }

    /**
     * Check if service supports a specific capability
     */
    hasCapability(capability) {
        return this.capabilities.includes(capability);
    }

    /**
     * Add capability to service
     */
    addCapability(capability) {
        if (!this.hasCapability(capability)) {
            this.capabilities.push(capability);
        }
    }

    /**
     * Remove capability from service
     */
    removeCapability(capability) {
        const index = this.capabilities.indexOf(capability);
        if (index > -1) {
            this.capabilities.splice(index, 1);
        }
    }

    /**
     * Execute with automatic error handling and result formatting
     */
    async safeExecute(input, context) {
        const startTime = Date.now();
        
        try {
            // Validate service state
            if (!this.initialized) {
                throw this.createError('Service not initialized', 'NOT_INITIALIZED');
            }

            // Validate input
            this.validateInput(input, context);

            // Preprocess input
            const processedInput = await this.preprocessInput(input, context);

            // Execute main operation
            const result = await this.execute(processedInput, context);

            // Postprocess result
            const finalResult = await this.postprocessResult(result, context);

            // Calculate execution time
            const executionTime = Date.now() - startTime;

            // Return standardized result
            return this.createResult(finalResult, { executionTime });

        } catch (error) {
            const executionTime = Date.now() - startTime;
            
            // Handle and format error
            const handledError = this.handleError(error, context);
            
            // Log error
            this.log('error', 'Service execution failed', {
                error: handledError.message,
                executionTime: `${executionTime}ms`,
                input: typeof input === 'string' ? input.substring(0, 100) : 'object'
            });

            throw handledError;
        }
    }

    /**
     * Execute with retry logic
     */
    async executeWithRetry(input, context, retryOptions = {}) {
        const {
            maxAttempts = 3,
            baseDelay = 1000,
            exponentialBackoff = true,
            retryCondition = (error) => !error.code?.includes('INVALID')
        } = retryOptions;

        let lastError;
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await this.safeExecute(input, context);
            } catch (error) {
                lastError = error;
                
                // Don't retry if condition fails or on last attempt
                if (!retryCondition(error) || attempt === maxAttempts) {
                    break;
                }

                // Calculate delay
                const delay = exponentialBackoff 
                    ? baseDelay * Math.pow(2, attempt - 1)
                    : baseDelay;

                this.log('warn', `Execution attempt ${attempt} failed, retrying in ${delay}ms`, {
                    error: error.message,
                    attempt,
                    maxAttempts
                });

                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }

        throw lastError;
    }
}

/**
 * Service Error class
 */
class ServiceError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ServiceError';
    }
}

module.exports = { IService, ServiceError };
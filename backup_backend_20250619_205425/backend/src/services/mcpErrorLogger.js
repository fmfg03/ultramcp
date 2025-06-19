/**
 * Error Logging Service for MCP Transactions
 * Logs failed MCP transactions to Supabase with detailed context
 */

const { createClient } = require('@supabase/supabase-js');
const { logger } = require('../utils/logger');

class MCPErrorLogger {
    constructor() {
        this.supabase = null;
        this.initializeSupabase();
        this.errorQueue = [];
        this.isProcessing = false;
    }

    /**
     * Initialize Supabase client
     */
    initializeSupabase() {
        const supabaseUrl = process.env.SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_ANON_KEY;

        if (supabaseUrl && supabaseKey) {
            this.supabase = createClient(supabaseUrl, supabaseKey);
            logger.info('✅ MCP Error Logger initialized with Supabase');
        } else {
            logger.warn('⚠️ Supabase credentials not found, error logging will be local only');
        }
    }

    /**
     * Log MCP transaction error
     * @param {Object} errorData - Error information
     */
    async logMCPError(errorData) {
        const errorRecord = {
            ...errorData,
            timestamp: new Date().toISOString(),
            error_id: this.generateErrorId(),
            environment: process.env.NODE_ENV || 'development'
        };

        // Add to queue for processing
        this.errorQueue.push(errorRecord);
        
        // Process queue if not already processing
        if (!this.isProcessing) {
            this.processErrorQueue();
        }

        // Log locally immediately
        logger.error('MCP Transaction Failed:', errorRecord);

        return errorRecord.error_id;
    }

    /**
     * Log task builder specific errors
     * @param {Object} taskData - Task information
     * @param {Error} error - Error object
     * @param {Object} context - Additional context
     */
    async logTaskBuilderError(taskData, error, context = {}) {
        const errorData = {
            error_type: 'task_builder_failure',
            agent_name: 'taskBuilder',
            task_id: taskData.task_id || this.generateTaskId(),
            session_id: context.session_id,
            user_id: context.user_id,
            task_description: taskData.task || taskData.description,
            task_parameters: taskData.parameters || {},
            error_message: error.message,
            error_stack: error.stack,
            error_code: error.code || 'UNKNOWN',
            execution_context: {
                agent_path: context.agent_path || [],
                execution_time: context.execution_time,
                memory_usage: process.memoryUsage(),
                node_version: process.version,
                platform: process.platform
            },
            input_data: {
                original_task: taskData,
                processed_input: context.processed_input,
                validation_errors: context.validation_errors
            },
            failure_point: context.failure_point || 'unknown',
            retry_count: context.retry_count || 0,
            severity: this.determineSeverity(error, context),
            tags: this.generateTags(taskData, error, context)
        };

        return await this.logMCPError(errorData);
    }

    /**
     * Log agent execution errors
     * @param {string} agentName - Name of the agent
     * @param {Object} state - Agent state
     * @param {Error} error - Error object
     * @param {Object} context - Additional context
     */
    async logAgentError(agentName, state, error, context = {}) {
        const errorData = {
            error_type: 'agent_execution_failure',
            agent_name: agentName,
            session_id: state.session_id || context.session_id,
            task_id: state.task_id || context.task_id,
            user_id: context.user_id,
            error_message: error.message,
            error_stack: error.stack,
            error_code: error.code || 'AGENT_ERROR',
            agent_state: {
                current_node: context.current_node,
                previous_nodes: context.previous_nodes || [],
                state_data: this.sanitizeState(state),
                execution_path: context.execution_path || []
            },
            execution_context: {
                execution_time: context.execution_time,
                memory_usage: process.memoryUsage(),
                cache_stats: context.cache_stats,
                precheck_result: context.precheck_result
            },
            failure_point: context.failure_point || 'unknown',
            retry_count: context.retry_count || 0,
            severity: this.determineSeverity(error, context),
            tags: this.generateTags({ agent: agentName }, error, context)
        };

        return await this.logMCPError(errorData);
    }

    /**
     * Log LLM service errors
     * @param {string} service - LLM service name
     * @param {Object} request - Request data
     * @param {Error} error - Error object
     * @param {Object} context - Additional context
     */
    async logLLMError(service, request, error, context = {}) {
        const errorData = {
            error_type: 'llm_service_failure',
            service_name: service,
            session_id: context.session_id,
            task_id: context.task_id,
            error_message: error.message,
            error_stack: error.stack,
            error_code: error.code || 'LLM_ERROR',
            request_data: {
                model: request.model,
                prompt_length: request.prompt?.length || 0,
                max_tokens: request.max_tokens,
                temperature: request.temperature,
                parameters: request.parameters
            },
            response_data: {
                status_code: error.status || error.statusCode,
                response_headers: error.headers,
                partial_response: context.partial_response
            },
            service_context: {
                endpoint: request.endpoint || context.endpoint,
                api_version: context.api_version,
                rate_limit_remaining: context.rate_limit_remaining,
                quota_remaining: context.quota_remaining
            },
            failure_point: context.failure_point || 'llm_call',
            retry_count: context.retry_count || 0,
            severity: this.determineSeverity(error, context),
            tags: this.generateTags({ service }, error, context)
        };

        return await this.logMCPError(errorData);
    }

    /**
     * Log integration errors (GitHub, Notion, etc.)
     * @param {string} integration - Integration name
     * @param {Object} operation - Operation details
     * @param {Error} error - Error object
     * @param {Object} context - Additional context
     */
    async logIntegrationError(integration, operation, error, context = {}) {
        const errorData = {
            error_type: 'integration_failure',
            integration_name: integration,
            operation_type: operation.type || 'unknown',
            session_id: context.session_id,
            task_id: context.task_id,
            error_message: error.message,
            error_stack: error.stack,
            error_code: error.code || 'INTEGRATION_ERROR',
            operation_data: {
                operation_id: operation.id,
                parameters: operation.parameters,
                endpoint: operation.endpoint,
                method: operation.method
            },
            integration_context: {
                api_version: context.api_version,
                authentication_type: context.auth_type,
                rate_limit_status: context.rate_limit_status,
                service_status: context.service_status
            },
            failure_point: context.failure_point || 'integration_call',
            retry_count: context.retry_count || 0,
            severity: this.determineSeverity(error, context),
            tags: this.generateTags({ integration }, error, context)
        };

        return await this.logMCPError(errorData);
    }

    /**
     * Process error queue
     */
    async processErrorQueue() {
        if (this.isProcessing || this.errorQueue.length === 0) {
            return;
        }

        this.isProcessing = true;

        try {
            while (this.errorQueue.length > 0) {
                const errorRecord = this.errorQueue.shift();
                await this.saveToSupabase(errorRecord);
            }
        } catch (error) {
            logger.error('Failed to process error queue:', error);
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Save error to Supabase
     * @param {Object} errorRecord - Error record to save
     */
    async saveToSupabase(errorRecord) {
        if (!this.supabase) {
            // Save to local file if Supabase not available
            await this.saveToLocalFile(errorRecord);
            return;
        }

        try {
            const { data, error } = await this.supabase
                .from('mcp_error_logs')
                .insert([errorRecord]);

            if (error) {
                throw error;
            }

            logger.debug(`Error logged to Supabase: ${errorRecord.error_id}`);
        } catch (error) {
            logger.error('Failed to save error to Supabase:', error);
            // Fallback to local file
            await this.saveToLocalFile(errorRecord);
        }
    }

    /**
     * Save error to local file as fallback
     * @param {Object} errorRecord - Error record to save
     */
    async saveToLocalFile(errorRecord) {
        const fs = require('fs').promises;
        const path = require('path');

        try {
            const logDir = path.join(process.cwd(), 'logs', 'errors');
            await fs.mkdir(logDir, { recursive: true });

            const filename = `mcp_errors_${new Date().toISOString().split('T')[0]}.jsonl`;
            const filepath = path.join(logDir, filename);

            await fs.appendFile(filepath, JSON.stringify(errorRecord) + '\n');
            logger.debug(`Error logged to file: ${filepath}`);
        } catch (error) {
            logger.error('Failed to save error to local file:', error);
        }
    }

    /**
     * Generate unique error ID
     * @returns {string} Error ID
     */
    generateErrorId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 8);
        return `mcp_error_${timestamp}_${random}`;
    }

    /**
     * Generate unique task ID
     * @returns {string} Task ID
     */
    generateTaskId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 8);
        return `task_${timestamp}_${random}`;
    }

    /**
     * Determine error severity
     * @param {Error} error - Error object
     * @param {Object} context - Context information
     * @returns {string} Severity level
     */
    determineSeverity(error, context) {
        // Critical errors
        if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
            return 'critical';
        }

        // High severity
        if (error.status >= 500 || context.retry_count > 2) {
            return 'high';
        }

        // Medium severity
        if (error.status >= 400 || context.retry_count > 0) {
            return 'medium';
        }

        // Low severity
        return 'low';
    }

    /**
     * Generate tags for error categorization
     * @param {Object} data - Data object
     * @param {Error} error - Error object
     * @param {Object} context - Context information
     * @returns {Array} Tags array
     */
    generateTags(data, error, context) {
        const tags = [];

        // Add agent/service tags
        if (data.agent) tags.push(`agent:${data.agent}`);
        if (data.service) tags.push(`service:${data.service}`);
        if (data.integration) tags.push(`integration:${data.integration}`);

        // Add error type tags
        if (error.code) tags.push(`error_code:${error.code}`);
        if (error.status) tags.push(`http_status:${error.status}`);

        // Add context tags
        if (context.retry_count > 0) tags.push('retried');
        if (context.cache_hit) tags.push('cache_hit');
        if (context.simplified) tags.push('simplified');

        // Add environment tags
        tags.push(`env:${process.env.NODE_ENV || 'development'}`);

        return tags;
    }

    /**
     * Sanitize state data for logging
     * @param {Object} state - State object
     * @returns {Object} Sanitized state
     */
    sanitizeState(state) {
        const sanitized = { ...state };

        // Remove sensitive data
        delete sanitized.api_keys;
        delete sanitized.tokens;
        delete sanitized.passwords;
        delete sanitized.secrets;

        // Truncate large data
        Object.keys(sanitized).forEach(key => {
            if (typeof sanitized[key] === 'string' && sanitized[key].length > 1000) {
                sanitized[key] = sanitized[key].substring(0, 1000) + '... [truncated]';
            }
        });

        return sanitized;
    }

    /**
     * Get error statistics
     * @param {Object} filters - Filter options
     * @returns {Object} Error statistics
     */
    async getErrorStats(filters = {}) {
        if (!this.supabase) {
            return { error: 'Supabase not available' };
        }

        try {
            let query = this.supabase
                .from('mcp_error_logs')
                .select('error_type, severity, agent_name, timestamp');

            // Apply filters
            if (filters.start_date) {
                query = query.gte('timestamp', filters.start_date);
            }
            if (filters.end_date) {
                query = query.lte('timestamp', filters.end_date);
            }
            if (filters.agent_name) {
                query = query.eq('agent_name', filters.agent_name);
            }
            if (filters.severity) {
                query = query.eq('severity', filters.severity);
            }

            const { data, error } = await query;

            if (error) throw error;

            // Calculate statistics
            const stats = {
                total_errors: data.length,
                by_type: {},
                by_severity: {},
                by_agent: {},
                by_hour: {}
            };

            data.forEach(record => {
                // By type
                stats.by_type[record.error_type] = (stats.by_type[record.error_type] || 0) + 1;

                // By severity
                stats.by_severity[record.severity] = (stats.by_severity[record.severity] || 0) + 1;

                // By agent
                if (record.agent_name) {
                    stats.by_agent[record.agent_name] = (stats.by_agent[record.agent_name] || 0) + 1;
                }

                // By hour
                const hour = new Date(record.timestamp).getHours();
                stats.by_hour[hour] = (stats.by_hour[hour] || 0) + 1;
            });

            return stats;
        } catch (error) {
            logger.error('Failed to get error stats:', error);
            return { error: error.message };
        }
    }
}

// Global error logger instance
const mcpErrorLogger = new MCPErrorLogger();

// Export functions for easy use
module.exports = {
    MCPErrorLogger,
    mcpErrorLogger,
    
    // Convenience functions
    logTaskBuilderError: (taskData, error, context) => 
        mcpErrorLogger.logTaskBuilderError(taskData, error, context),
    
    logAgentError: (agentName, state, error, context) => 
        mcpErrorLogger.logAgentError(agentName, state, error, context),
    
    logLLMError: (service, request, error, context) => 
        mcpErrorLogger.logLLMError(service, request, error, context),
    
    logIntegrationError: (integration, operation, error, context) => 
        mcpErrorLogger.logIntegrationError(integration, operation, error, context),
    
    getErrorStats: (filters) => 
        mcpErrorLogger.getErrorStats(filters)
};


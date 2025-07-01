/**
 * Context Manager for UltraMCP
 * 
 * Manages request context throughout task execution lifecycle,
 * providing security, analytics, and debugging capabilities.
 */

class ContextManager {
    constructor() {
        this.contexts = new Map();
        this.defaultTimeout = 30 * 60 * 1000; // 30 minutes
        this.cleanupInterval = 5 * 60 * 1000; // 5 minutes
        
        // Start periodic cleanup
        this.startPeriodicCleanup();
    }

    /**
     * Create a new execution context
     */
    createContext(taskId, userContext = {}) {
        const context = {
            taskId,
            createdAt: new Date().toISOString(),
            userId: userContext.userId,
            sessionId: userContext.sessionId,
            
            // Request metadata
            request: {
                ip: userContext.ip,
                userAgent: userContext.userAgent,
                headers: userContext.headers || {},
                origin: userContext.origin,
                timestamp: new Date().toISOString()
            },
            
            // Execution tracking
            execution: {
                startTime: Date.now(),
                steps: [],
                services: [],
                workflows: [],
                errors: [],
                warnings: [],
                performance: {
                    totalDuration: 0,
                    serviceCallDuration: 0,
                    waitTime: 0,
                    cacheHits: 0,
                    cacheMisses: 0
                }
            },
            
            // User-provided context
            user: {
                preferences: userContext.preferences || {},
                settings: userContext.settings || {},
                metadata: userContext.metadata || {},
                ...userContext.user
            },
            
            // Dynamic context (updated during execution)
            dynamic: {},
            
            // Security and permissions
            security: {
                authenticated: !!userContext.userId,
                roles: userContext.roles || [],
                permissions: userContext.permissions || [],
                riskLevel: userContext.riskLevel || 'low',
                rateLimitKey: userContext.rateLimitKey || userContext.ip
            },
            
            // Resource tracking
            resources: {
                memoryUsage: 0,
                cpuTime: 0,
                networkCalls: 0,
                diskOperations: 0
            },
            
            // Analytics and debugging
            analytics: {
                tags: userContext.tags || [],
                experiment: userContext.experiment,
                cohort: userContext.cohort,
                debugMode: userContext.debug || false,
                traceId: userContext.traceId || this.generateTraceId()
            }
        };

        this.contexts.set(taskId, context);
        
        // Set cleanup timer for this context
        setTimeout(() => {
            this.cleanup(taskId);
        }, this.defaultTimeout);

        return context;
    }

    /**
     * Get context by task ID
     */
    getContext(taskId) {
        return this.contexts.get(taskId);
    }

    /**
     * Update dynamic context properties
     */
    updateContext(taskId, updates) {
        const context = this.contexts.get(taskId);
        if (context) {
            Object.assign(context.dynamic, updates);
            return context;
        }
        return null;
    }

    /**
     * Add execution step tracking
     */
    addExecutionStep(taskId, step) {
        const context = this.contexts.get(taskId);
        if (context) {
            const stepData = {
                ...step,
                timestamp: new Date().toISOString(),
                duration: step.duration || 0,
                memoryDelta: step.memoryDelta || 0
            };
            
            context.execution.steps.push(stepData);
            
            // Update performance metrics
            if (stepData.duration) {
                context.execution.performance.totalDuration += stepData.duration;
            }
        }
    }

    /**
     * Track service usage
     */
    addServiceUsage(taskId, serviceId, operation, duration, success, metadata = {}) {
        const context = this.contexts.get(taskId);
        if (context) {
            const serviceUsage = {
                serviceId,
                operation,
                duration,
                success,
                metadata,
                timestamp: new Date().toISOString(),
                memoryUsage: process.memoryUsage().heapUsed
            };
            
            context.execution.services.push(serviceUsage);
            context.resources.networkCalls++;
            
            // Update performance metrics
            context.execution.performance.serviceCallDuration += duration;
            
            if (metadata.cached) {
                context.execution.performance.cacheHits++;
            } else if (metadata.cacheMiss) {
                context.execution.performance.cacheMisses++;
            }
        }
    }

    /**
     * Track workflow execution
     */
    addWorkflowExecution(taskId, workflowId, executionId, status, duration, metadata = {}) {
        const context = this.contexts.get(taskId);
        if (context) {
            const workflowExecution = {
                workflowId,
                executionId,
                status,
                duration,
                metadata,
                timestamp: new Date().toISOString()
            };
            
            context.execution.workflows.push(workflowExecution);
        }
    }

    /**
     * Add error to context
     */
    addError(taskId, error, category = 'general', severity = 'error') {
        const context = this.contexts.get(taskId);
        if (context) {
            const errorData = {
                message: error.message,
                code: error.code,
                category,
                severity,
                stack: error.stack,
                timestamp: new Date().toISOString(),
                context: error.context || {}
            };
            
            if (severity === 'error') {
                context.execution.errors.push(errorData);
            } else {
                context.execution.warnings.push(errorData);
            }
        }
    }

    /**
     * Add warning to context
     */
    addWarning(taskId, message, category = 'general', metadata = {}) {
        this.addError(taskId, { message, metadata }, category, 'warning');
    }

    /**
     * Update resource usage
     */
    updateResourceUsage(taskId, resourceType, value, operation = 'add') {
        const context = this.contexts.get(taskId);
        if (context) {
            switch (operation) {
                case 'add':
                    context.resources[resourceType] = (context.resources[resourceType] || 0) + value;
                    break;
                case 'set':
                    context.resources[resourceType] = value;
                    break;
                case 'max':
                    context.resources[resourceType] = Math.max(context.resources[resourceType] || 0, value);
                    break;
            }
        }
    }

    /**
     * Add analytics tag
     */
    addTag(taskId, tag) {
        const context = this.contexts.get(taskId);
        if (context && !context.analytics.tags.includes(tag)) {
            context.analytics.tags.push(tag);
        }
    }

    /**
     * Set experiment information
     */
    setExperiment(taskId, experimentId, variant) {
        const context = this.contexts.get(taskId);
        if (context) {
            context.analytics.experiment = {
                id: experimentId,
                variant,
                timestamp: new Date().toISOString()
            };
        }
    }

    // ===== SECURITY HELPERS =====

    /**
     * Check if user has permission
     */
    hasPermission(taskId, permission) {
        const context = this.contexts.get(taskId);
        return context?.security.permissions.includes(permission) || false;
    }

    /**
     * Check if user has role
     */
    hasRole(taskId, role) {
        const context = this.contexts.get(taskId);
        return context?.security.roles.includes(role) || false;
    }

    /**
     * Check if context is authenticated
     */
    isAuthenticated(taskId) {
        const context = this.contexts.get(taskId);
        return context?.security.authenticated || false;
    }

    /**
     * Get security risk level
     */
    getRiskLevel(taskId) {
        const context = this.contexts.get(taskId);
        return context?.security.riskLevel || 'unknown';
    }

    /**
     * Update risk level based on execution
     */
    updateRiskLevel(taskId, level, reason) {
        const context = this.contexts.get(taskId);
        if (context) {
            context.security.riskLevel = level;
            this.addWarning(taskId, `Risk level updated to ${level}`, 'security', { reason });
        }
    }

    // ===== ANALYTICS HELPERS =====

    /**
     * Get execution metrics
     */
    getExecutionMetrics(taskId) {
        const context = this.contexts.get(taskId);
        if (!context) return null;

        const totalDuration = Date.now() - context.execution.startTime;
        const serviceUsage = context.execution.services;
        const errorCount = context.execution.errors.length;
        const warningCount = context.execution.warnings.length;

        return {
            totalDuration,
            stepCount: context.execution.steps.length,
            serviceCount: serviceUsage.length,
            workflowCount: context.execution.workflows.length,
            errorCount,
            warningCount,
            successRate: serviceUsage.length > 0 ? 
                serviceUsage.filter(s => s.success).length / serviceUsage.length : 1,
            performance: context.execution.performance,
            resources: context.resources
        };
    }

    /**
     * Get performance summary
     */
    getPerformanceSummary(taskId) {
        const context = this.contexts.get(taskId);
        if (!context) return null;

        const metrics = this.getExecutionMetrics(taskId);
        const perf = context.execution.performance;
        
        return {
            efficiency: metrics.totalDuration > 0 ? 
                (perf.serviceCallDuration / metrics.totalDuration) : 0,
            cacheEfficiency: (perf.cacheHits + perf.cacheMisses) > 0 ? 
                (perf.cacheHits / (perf.cacheHits + perf.cacheMisses)) : 0,
            serviceUtilization: metrics.serviceCount,
            errorRate: metrics.errorCount / Math.max(metrics.stepCount, 1),
            warningRate: metrics.warningCount / Math.max(metrics.stepCount, 1)
        };
    }

    /**
     * Generate analytics report
     */
    generateAnalyticsReport(taskId) {
        const context = this.contexts.get(taskId);
        if (!context) return null;

        const metrics = this.getExecutionMetrics(taskId);
        const performance = this.getPerformanceSummary(taskId);

        return {
            taskId,
            traceId: context.analytics.traceId,
            userId: context.userId,
            sessionId: context.sessionId,
            
            execution: {
                startTime: context.execution.startTime,
                endTime: Date.now(),
                duration: metrics.totalDuration,
                status: metrics.errorCount > 0 ? 'failed' : 'succeeded'
            },
            
            metrics,
            performance,
            
            services: context.execution.services.map(s => ({
                serviceId: s.serviceId,
                operation: s.operation,
                duration: s.duration,
                success: s.success
            })),
            
            workflows: context.execution.workflows,
            
            errors: context.execution.errors.map(e => ({
                message: e.message,
                code: e.code,
                category: e.category,
                timestamp: e.timestamp
            })),
            
            security: {
                authenticated: context.security.authenticated,
                riskLevel: context.security.riskLevel,
                roles: context.security.roles.length
            },
            
            resources: context.resources,
            
            tags: context.analytics.tags,
            experiment: context.analytics.experiment,
            
            request: {
                userAgent: context.request.userAgent,
                origin: context.request.origin,
                timestamp: context.request.timestamp
            }
        };
    }

    // ===== DEBUGGING HELPERS =====

    /**
     * Enable debug mode for context
     */
    enableDebugMode(taskId) {
        const context = this.contexts.get(taskId);
        if (context) {
            context.analytics.debugMode = true;
            this.addTag(taskId, 'debug');
        }
    }

    /**
     * Get debug information
     */
    getDebugInfo(taskId) {
        const context = this.contexts.get(taskId);
        if (!context || !context.analytics.debugMode) {
            return null;
        }

        return {
            context: this.sanitizeContext(context),
            metrics: this.getExecutionMetrics(taskId),
            performance: this.getPerformanceSummary(taskId),
            timeline: this.getExecutionTimeline(taskId)
        };
    }

    /**
     * Get execution timeline
     */
    getExecutionTimeline(taskId) {
        const context = this.contexts.get(taskId);
        if (!context) return [];

        const timeline = [];
        const baseTime = context.execution.startTime;

        // Add steps
        for (const step of context.execution.steps) {
            timeline.push({
                type: 'step',
                timestamp: step.timestamp,
                relativeTime: new Date(step.timestamp).getTime() - baseTime,
                event: step.step || 'unknown',
                details: step
            });
        }

        // Add service calls
        for (const service of context.execution.services) {
            timeline.push({
                type: 'service',
                timestamp: service.timestamp,
                relativeTime: new Date(service.timestamp).getTime() - baseTime,
                event: `${service.serviceId}.${service.operation}`,
                details: service
            });
        }

        // Add errors
        for (const error of context.execution.errors) {
            timeline.push({
                type: 'error',
                timestamp: error.timestamp,
                relativeTime: new Date(error.timestamp).getTime() - baseTime,
                event: error.message,
                details: error
            });
        }

        // Sort by timestamp
        timeline.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        return timeline;
    }

    /**
     * Sanitize context for external exposure
     */
    sanitizeContext(context) {
        const sanitized = { ...context };
        
        // Remove sensitive information
        if (sanitized.request?.headers) {
            delete sanitized.request.headers.authorization;
            delete sanitized.request.headers.cookie;
        }
        
        // Truncate large arrays
        if (sanitized.execution?.steps?.length > 100) {
            sanitized.execution.steps = sanitized.execution.steps.slice(0, 100);
        }
        
        if (sanitized.execution?.services?.length > 100) {
            sanitized.execution.services = sanitized.execution.services.slice(0, 100);
        }
        
        return sanitized;
    }

    // ===== CLEANUP =====

    /**
     * Clean up context
     */
    cleanup(taskId) {
        const context = this.contexts.get(taskId);
        if (context) {
            // Generate final analytics report if needed
            if (context.analytics.debugMode || context.user.preferences?.analytics) {
                const report = this.generateAnalyticsReport(taskId);
                // Could emit event or store report here
            }
            
            this.contexts.delete(taskId);
            return true;
        }
        return false;
    }

    /**
     * Start periodic cleanup of expired contexts
     */
    startPeriodicCleanup() {
        setInterval(() => {
            const now = Date.now();
            const expiredContexts = [];
            
            for (const [taskId, context] of this.contexts) {
                const age = now - context.execution.startTime;
                if (age > this.defaultTimeout) {
                    expiredContexts.push(taskId);
                }
            }
            
            for (const taskId of expiredContexts) {
                this.cleanup(taskId);
            }
            
            if (expiredContexts.length > 0) {
                console.log(`🧹 Cleaned up ${expiredContexts.length} expired contexts`);
            }
        }, this.cleanupInterval);
    }

    /**
     * Get context statistics
     */
    getStats() {
        const contexts = Array.from(this.contexts.values());
        const now = Date.now();
        
        return {
            totalContexts: contexts.length,
            authenticatedContexts: contexts.filter(c => c.security.authenticated).length,
            debugContexts: contexts.filter(c => c.analytics.debugMode).length,
            avgAge: contexts.length > 0 ? 
                contexts.reduce((sum, c) => sum + (now - c.execution.startTime), 0) / contexts.length : 0,
            riskLevels: contexts.reduce((acc, c) => {
                acc[c.security.riskLevel] = (acc[c.security.riskLevel] || 0) + 1;
                return acc;
            }, {}),
            topUsers: this.getTopUsers(contexts),
            topTags: this.getTopTags(contexts)
        };
    }

    /**
     * Get top users by context count
     */
    getTopUsers(contexts) {
        const userCounts = contexts.reduce((acc, c) => {
            if (c.userId) {
                acc[c.userId] = (acc[c.userId] || 0) + 1;
            }
            return acc;
        }, {});
        
        return Object.entries(userCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10)
            .map(([userId, count]) => ({ userId, count }));
    }

    /**
     * Get top analytics tags
     */
    getTopTags(contexts) {
        const tagCounts = contexts.reduce((acc, c) => {
            for (const tag of c.analytics.tags) {
                acc[tag] = (acc[tag] || 0) + 1;
            }
            return acc;
        }, {});
        
        return Object.entries(tagCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 20)
            .map(([tag, count]) => ({ tag, count }));
    }

    /**
     * Generate trace ID
     */
    generateTraceId() {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);
        return `trace_${timestamp}_${random}`;
    }

    /**
     * Get all active contexts (for debugging)
     */
    getAllContexts() {
        return Array.from(this.contexts.entries()).map(([taskId, context]) => ({
            taskId,
            userId: context.userId,
            sessionId: context.sessionId,
            age: Date.now() - context.execution.startTime,
            stepCount: context.execution.steps.length,
            errorCount: context.execution.errors.length,
            authenticated: context.security.authenticated,
            debugMode: context.analytics.debugMode
        }));
    }

    /**
     * Force cleanup all contexts (for shutdown)
     */
    cleanupAll() {
        const count = this.contexts.size;
        this.contexts.clear();
        return count;
    }
}

module.exports = ContextManager;
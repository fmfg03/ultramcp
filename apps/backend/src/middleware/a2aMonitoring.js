/**
 * A2A Monitoring Middleware - Observability for Agent-to-Agent communication
 * Integrates with Langwatch and provides comprehensive monitoring
 */

const logger = require('../utils/logger');
const { v4: uuidv4 } = require('uuid');

// Langwatch integration (optional)
let langwatch;
try {
    langwatch = require('langwatch');
} catch (error) {
    logger.debug('Langwatch not available for A2A monitoring');
}

class A2AMonitoring {
    constructor() {
        this.activeTraces = new Map();
        this.metrics = {
            total_requests: 0,
            successful_requests: 0,
            failed_requests: 0,
            average_response_time: 0,
            agent_interactions: new Map(),
            task_types: new Map(),
            performance_metrics: []
        };
        
        this.startMetricsCollection();
    }
    
    /**
     * Middleware for monitoring A2A requests
     */
    monitorA2ARequest(req, res, next) {
        const traceId = req.headers['x-trace-id'] || uuidv4();
        const startTime = Date.now();
        
        // Attach trace information to request
        req.a2aTrace = {
            traceId,
            startTime,
            endpoint: req.originalUrl,
            method: req.method,
            requestBody: req.body,
            userAgent: req.headers['user-agent'],
            sourceAgent: req.headers['x-source-agent'] || 'unknown'
        };
        
        // Start Langwatch trace if available
        if (langwatch && process.env.LANGWATCH_API_KEY) {
            try {
                const trace = langwatch.trace({
                    id: traceId,
                    metadata: {
                        endpoint: req.originalUrl,
                        method: req.method,
                        source_agent: req.a2aTrace.sourceAgent,
                        a2a_protocol: true
                    }
                });
                req.langwatchTrace = trace;
            } catch (error) {
                logger.debug('Failed to start Langwatch trace', { error: error.message });
            }
        }
        
        // Store active trace
        this.activeTraces.set(traceId, req.a2aTrace);
        
        // Override res.json to capture response
        const originalJson = res.json;
        res.json = (data) => {
            this._recordResponse(req, res, data);
            return originalJson.call(res, data);
        };
        
        // Record request metrics
        this.metrics.total_requests++;
        
        logger.info('A2A request started', {
            traceId,
            endpoint: req.originalUrl,
            method: req.method,
            sourceAgent: req.a2aTrace.sourceAgent
        });
        
        next();
    }
    
    /**
     * Record response and complete trace
     */
    _recordResponse(req, res, responseData) {
        const { traceId, startTime, sourceAgent } = req.a2aTrace;
        const duration = Date.now() - startTime;
        const success = res.statusCode >= 200 && res.statusCode < 400;
        
        // Update metrics
        if (success) {
            this.metrics.successful_requests++;
        } else {
            this.metrics.failed_requests++;
        }
        
        // Update average response time
        this._updateAverageResponseTime(duration);
        
        // Record agent interaction
        this._recordAgentInteraction(sourceAgent, req.originalUrl, duration, success);
        
        // Record task type metrics
        if (req.body?.task_type) {
            this._recordTaskTypeMetrics(req.body.task_type, duration, success);
        }
        
        // Complete Langwatch trace
        if (req.langwatchTrace) {
            try {
                req.langwatchTrace.end({
                    output: responseData,
                    metadata: {
                        duration,
                        success,
                        status_code: res.statusCode,
                        response_size: JSON.stringify(responseData).length
                    }
                });
            } catch (error) {
                logger.debug('Failed to end Langwatch trace', { error: error.message });
            }
        }
        
        // Log completion
        logger.info('A2A request completed', {
            traceId,
            duration,
            success,
            statusCode: res.statusCode,
            sourceAgent,
            responseSize: JSON.stringify(responseData).length
        });
        
        // Store performance metrics
        this.metrics.performance_metrics.push({
            timestamp: new Date().toISOString(),
            traceId,
            endpoint: req.originalUrl,
            duration,
            success,
            sourceAgent,
            taskType: req.body?.task_type
        });
        
        // Keep only last 1000 performance metrics
        if (this.metrics.performance_metrics.length > 1000) {
            this.metrics.performance_metrics = this.metrics.performance_metrics.slice(-1000);
        }
        
        // Remove from active traces
        this.activeTraces.delete(traceId);
    }
    
    /**
     * Update average response time
     */
    _updateAverageResponseTime(duration) {
        const totalRequests = this.metrics.total_requests;
        const currentAverage = this.metrics.average_response_time;
        
        // Calculate new rolling average
        this.metrics.average_response_time = 
            ((currentAverage * (totalRequests - 1)) + duration) / totalRequests;
    }
    
    /**
     * Record agent interaction metrics
     */
    _recordAgentInteraction(sourceAgent, endpoint, duration, success) {
        if (!this.metrics.agent_interactions.has(sourceAgent)) {
            this.metrics.agent_interactions.set(sourceAgent, {
                total_requests: 0,
                successful_requests: 0,
                failed_requests: 0,
                total_duration: 0,
                average_duration: 0,
                endpoints: new Map()
            });
        }
        
        const agentMetrics = this.metrics.agent_interactions.get(sourceAgent);
        agentMetrics.total_requests++;
        agentMetrics.total_duration += duration;
        agentMetrics.average_duration = agentMetrics.total_duration / agentMetrics.total_requests;
        
        if (success) {
            agentMetrics.successful_requests++;
        } else {
            agentMetrics.failed_requests++;
        }
        
        // Track endpoint usage
        if (!agentMetrics.endpoints.has(endpoint)) {
            agentMetrics.endpoints.set(endpoint, { count: 0, avg_duration: 0 });
        }
        
        const endpointMetrics = agentMetrics.endpoints.get(endpoint);
        const prevCount = endpointMetrics.count;
        endpointMetrics.count++;
        endpointMetrics.avg_duration = 
            ((endpointMetrics.avg_duration * prevCount) + duration) / endpointMetrics.count;
    }
    
    /**
     * Record task type metrics
     */
    _recordTaskTypeMetrics(taskType, duration, success) {
        if (!this.metrics.task_types.has(taskType)) {
            this.metrics.task_types.set(taskType, {
                total_executions: 0,
                successful_executions: 0,
                failed_executions: 0,
                total_duration: 0,
                average_duration: 0,
                min_duration: Infinity,
                max_duration: 0
            });
        }
        
        const taskMetrics = this.metrics.task_types.get(taskType);
        taskMetrics.total_executions++;
        taskMetrics.total_duration += duration;
        taskMetrics.average_duration = taskMetrics.total_duration / taskMetrics.total_executions;
        taskMetrics.min_duration = Math.min(taskMetrics.min_duration, duration);
        taskMetrics.max_duration = Math.max(taskMetrics.max_duration, duration);
        
        if (success) {
            taskMetrics.successful_executions++;
        } else {
            taskMetrics.failed_executions++;
        }
    }
    
    /**
     * Start periodic metrics collection
     */
    startMetricsCollection() {
        setInterval(() => {
            this._collectSystemMetrics();
        }, 30000); // Every 30 seconds
        
        setInterval(() => {
            this._logMetricsSummary();
        }, 300000); // Every 5 minutes
    }
    
    /**
     * Collect system-level metrics
     */
    _collectSystemMetrics() {
        const memoryUsage = process.memoryUsage();
        const cpuUsage = process.cpuUsage();
        
        logger.debug('A2A system metrics', {
            activeTraces: this.activeTraces.size,
            totalRequests: this.metrics.total_requests,
            successRate: (this.metrics.successful_requests / this.metrics.total_requests * 100).toFixed(2) + '%',
            averageResponseTime: Math.round(this.metrics.average_response_time) + 'ms',
            memoryUsage: {
                heapUsed: Math.round(memoryUsage.heapUsed / 1024 / 1024) + 'MB',
                heapTotal: Math.round(memoryUsage.heapTotal / 1024 / 1024) + 'MB'
            }
        });
    }
    
    /**
     * Log comprehensive metrics summary
     */
    _logMetricsSummary() {
        const topAgents = Array.from(this.metrics.agent_interactions.entries())
            .sort(([,a], [,b]) => b.total_requests - a.total_requests)
            .slice(0, 5);
            
        const topTaskTypes = Array.from(this.metrics.task_types.entries())
            .sort(([,a], [,b]) => b.total_executions - a.total_executions)
            .slice(0, 5);
        
        logger.info('A2A metrics summary', {
            overview: {
                totalRequests: this.metrics.total_requests,
                successfulRequests: this.metrics.successful_requests,
                failedRequests: this.metrics.failed_requests,
                successRate: (this.metrics.successful_requests / this.metrics.total_requests * 100).toFixed(2) + '%',
                averageResponseTime: Math.round(this.metrics.average_response_time) + 'ms'
            },
            topAgents: topAgents.map(([agent, metrics]) => ({
                agent,
                requests: metrics.total_requests,
                avgDuration: Math.round(metrics.average_duration) + 'ms',
                successRate: (metrics.successful_requests / metrics.total_requests * 100).toFixed(2) + '%'
            })),
            topTaskTypes: topTaskTypes.map(([taskType, metrics]) => ({
                taskType,
                executions: metrics.total_executions,
                avgDuration: Math.round(metrics.average_duration) + 'ms',
                successRate: (metrics.successful_executions / metrics.total_executions * 100).toFixed(2) + '%'
            }))
        });
    }
    
    /**
     * Get current metrics for API endpoints
     */
    getMetrics() {
        return {
            overview: {
                total_requests: this.metrics.total_requests,
                successful_requests: this.metrics.successful_requests,
                failed_requests: this.metrics.failed_requests,
                success_rate: this.metrics.total_requests > 0 
                    ? (this.metrics.successful_requests / this.metrics.total_requests * 100)
                    : 0,
                average_response_time: Math.round(this.metrics.average_response_time),
                active_traces: this.activeTraces.size
            },
            agents: Object.fromEntries(
                Array.from(this.metrics.agent_interactions.entries()).map(([agent, metrics]) => [
                    agent,
                    {
                        ...metrics,
                        success_rate: metrics.total_requests > 0 
                            ? (metrics.successful_requests / metrics.total_requests * 100)
                            : 0,
                        average_duration: Math.round(metrics.average_duration),
                        endpoints: Object.fromEntries(metrics.endpoints)
                    }
                ])
            ),
            task_types: Object.fromEntries(
                Array.from(this.metrics.task_types.entries()).map(([taskType, metrics]) => [
                    taskType,
                    {
                        ...metrics,
                        success_rate: metrics.total_executions > 0 
                            ? (metrics.successful_executions / metrics.total_executions * 100)
                            : 0,
                        average_duration: Math.round(metrics.average_duration)
                    }
                ])
            ),
            recent_performance: this.metrics.performance_metrics.slice(-100) // Last 100 requests
        };
    }
    
    /**
     * Reset metrics (useful for testing or maintenance)
     */
    resetMetrics() {
        this.metrics = {
            total_requests: 0,
            successful_requests: 0,
            failed_requests: 0,
            average_response_time: 0,
            agent_interactions: new Map(),
            task_types: new Map(),
            performance_metrics: []
        };
        
        logger.info('A2A metrics reset');
    }
    
    /**
     * Get active traces information
     */
    getActiveTraces() {
        return Array.from(this.activeTraces.entries()).map(([traceId, trace]) => ({
            traceId,
            ...trace,
            duration: Date.now() - trace.startTime
        }));
    }
    
    /**
     * Generate monitoring dashboard data
     */
    getDashboardData() {
        const metrics = this.getMetrics();
        const now = new Date();
        
        // Calculate recent trends (last hour)
        const recentMetrics = this.metrics.performance_metrics.filter(
            m => new Date(m.timestamp) > new Date(now - 60 * 60 * 1000)
        );
        
        const successRate = metrics.overview.success_rate;
        const avgResponseTime = metrics.overview.average_response_time;
        
        return {
            status: {
                overall: successRate > 95 ? 'healthy' : successRate > 80 ? 'warning' : 'critical',
                success_rate: successRate,
                average_response_time: avgResponseTime,
                active_requests: this.activeTraces.size,
                total_requests: metrics.overview.total_requests
            },
            trends: {
                requests_last_hour: recentMetrics.length,
                avg_response_time_trend: this._calculateTrend(recentMetrics, 'duration'),
                success_rate_trend: this._calculateSuccessRateTrend(recentMetrics)
            },
            top_agents: Object.entries(metrics.agents)
                .sort(([,a], [,b]) => b.total_requests - a.total_requests)
                .slice(0, 10),
            top_task_types: Object.entries(metrics.task_types)
                .sort(([,a], [,b]) => b.total_executions - a.total_executions)
                .slice(0, 10),
            alerts: this._generateAlerts(metrics)
        };
    }
    
    /**
     * Calculate trend for numeric values
     */
    _calculateTrend(data, field) {
        if (data.length < 2) return 0;
        
        const recent = data.slice(-Math.min(20, Math.floor(data.length / 2)));
        const older = data.slice(0, Math.max(20, Math.floor(data.length / 2)));
        
        const recentAvg = recent.reduce((sum, item) => sum + item[field], 0) / recent.length;
        const olderAvg = older.reduce((sum, item) => sum + item[field], 0) / older.length;
        
        return ((recentAvg - olderAvg) / olderAvg * 100);
    }
    
    /**
     * Calculate success rate trend
     */
    _calculateSuccessRateTrend(data) {
        if (data.length < 2) return 0;
        
        const recent = data.slice(-Math.min(20, Math.floor(data.length / 2)));
        const older = data.slice(0, Math.max(20, Math.floor(data.length / 2)));
        
        const recentSuccessRate = recent.filter(item => item.success).length / recent.length * 100;
        const olderSuccessRate = older.filter(item => item.success).length / older.length * 100;
        
        return recentSuccessRate - olderSuccessRate;
    }
    
    /**
     * Generate system alerts based on metrics
     */
    _generateAlerts(metrics) {
        const alerts = [];
        
        // High error rate alert
        if (metrics.overview.success_rate < 90) {
            alerts.push({
                level: 'warning',
                type: 'high_error_rate',
                message: `Success rate is ${metrics.overview.success_rate.toFixed(2)}% (below 90%)`,
                timestamp: new Date().toISOString()
            });
        }
        
        // High response time alert
        if (metrics.overview.average_response_time > 5000) {
            alerts.push({
                level: 'warning',
                type: 'high_response_time',
                message: `Average response time is ${metrics.overview.average_response_time}ms (above 5s)`,
                timestamp: new Date().toISOString()
            });
        }
        
        // Too many active requests
        if (this.activeTraces.size > 100) {
            alerts.push({
                level: 'critical',
                type: 'high_concurrent_requests',
                message: `${this.activeTraces.size} active requests (above 100)`,
                timestamp: new Date().toISOString()
            });
        }
        
        return alerts;
    }
}

// Create singleton instance
const a2aMonitoring = new A2AMonitoring();

module.exports = {
    a2aMonitoring,
    monitorA2ARequest: a2aMonitoring.monitorA2ARequest.bind(a2aMonitoring)
};
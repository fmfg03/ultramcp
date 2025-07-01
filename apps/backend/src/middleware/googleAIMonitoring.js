/**
 * Google AI Monitoring Middleware - Enhanced monitoring for Google AI/Gemini integration
 * Provides comprehensive observability for Google AI model usage, performance, and costs
 */

const logger = require('../utils/logger');
const { v4: uuidv4 } = require('uuid');

// Langwatch integration (optional)
let langwatch;
try {
    langwatch = require('langwatch');
} catch (error) {
    logger.debug('Langwatch not available for Google AI monitoring');
}

class GoogleAIMonitoring {
    constructor() {
        this.metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalCost: 0,
            modelUsage: new Map(),
            taskTypeStats: new Map(),
            performanceMetrics: [],
            safetyViolations: 0,
            functionCallsExecuted: 0,
            embeddingsGenerated: 0,
            imagesAnalyzed: 0
        };
        
        this.activeRequests = new Map();
        this.costThresholds = {
            warning: 10.0,    // $10 warning threshold
            critical: 50.0    // $50 critical threshold
        };
        
        this.modelPricing = {
            'gemini-1.5-pro-latest': { input: 3.50, output: 10.50 },
            'gemini-1.5-flash-latest': { input: 0.35, output: 0.70 },
            'gemini-1.0-pro': { input: 0.50, output: 1.50 },
            'text-embedding-004': { input: 0.20, output: null }
        };
        
        this.startPeriodicReporting();
    }
    
    /**
     * Track the start of a Google AI request
     */
    trackRequestStart(requestData) {
        const requestId = requestData.requestId || uuidv4();
        const startTime = Date.now();
        
        const trackingData = {
            requestId,
            startTime,
            model: requestData.model,
            taskType: requestData.taskType || 'general',
            hasImages: !!requestData.images?.length,
            hasFunctions: !!requestData.functions?.length,
            inputTokensEstimate: this._estimateTokens(requestData.input),
            langwatchTrace: null
        };
        
        // Start Langwatch trace if available
        if (langwatch && process.env.LANGWATCH_API_KEY) {
            try {
                const trace = langwatch.trace({
                    id: requestId,
                    metadata: {
                        provider: 'google_ai',
                        model: requestData.model,
                        task_type: requestData.taskType,
                        has_images: trackingData.hasImages,
                        has_functions: trackingData.hasFunctions
                    }
                });
                trackingData.langwatchTrace = trace;
            } catch (error) {
                logger.debug('Failed to start Langwatch trace for Google AI', { error: error.message });
            }
        }
        
        this.activeRequests.set(requestId, trackingData);
        this.metrics.totalRequests++;
        
        logger.info('Google AI request started', {
            requestId,
            model: requestData.model,
            taskType: requestData.taskType,
            hasImages: trackingData.hasImages,
            hasFunctions: trackingData.hasFunctions
        });
        
        return requestId;
    }
    
    /**
     * Track the completion of a Google AI request
     */
    trackRequestComplete(requestId, responseData) {
        const tracking = this.activeRequests.get(requestId);
        if (!tracking) {
            logger.warn('Tracking data not found for request', { requestId });
            return;
        }
        
        const duration = Date.now() - tracking.startTime;
        const success = responseData.success !== false;
        
        // Extract response details
        const usage = responseData.result?.usage || {};
        const model = tracking.model;
        const taskType = tracking.taskType;
        
        // Calculate cost
        const cost = this._calculateCost(model, usage);
        
        // Update metrics
        if (success) {
            this.metrics.successfulRequests++;
        } else {
            this.metrics.failedRequests++;
        }
        
        this.metrics.totalCost += cost;
        
        // Update model usage statistics
        if (!this.metrics.modelUsage.has(model)) {
            this.metrics.modelUsage.set(model, {
                requests: 0,
                totalTokens: 0,
                totalCost: 0,
                averageLatency: 0,
                successRate: 0,
                errors: []
            });
        }
        
        const modelStats = this.metrics.modelUsage.get(model);
        modelStats.requests++;
        modelStats.totalTokens += usage.totalTokens || 0;
        modelStats.totalCost += cost;
        modelStats.averageLatency = ((modelStats.averageLatency * (modelStats.requests - 1)) + duration) / modelStats.requests;
        modelStats.successRate = (modelStats.successRate * (modelStats.requests - 1) + (success ? 1 : 0)) / modelStats.requests;
        
        if (!success && responseData.error) {
            modelStats.errors.push({
                timestamp: new Date().toISOString(),
                error: responseData.error,
                requestId
            });
            
            // Keep only last 10 errors per model
            if (modelStats.errors.length > 10) {
                modelStats.errors = modelStats.errors.slice(-10);
            }
        }
        
        // Update task type statistics
        if (!this.metrics.taskTypeStats.has(taskType)) {
            this.metrics.taskTypeStats.set(taskType, {
                requests: 0,
                averageDuration: 0,
                averageCost: 0,
                successRate: 0,
                preferredModel: model
            });
        }
        
        const taskStats = this.metrics.taskTypeStats.get(taskType);
        taskStats.requests++;
        taskStats.averageDuration = ((taskStats.averageDuration * (taskStats.requests - 1)) + duration) / taskStats.requests;
        taskStats.averageCost = ((taskStats.averageCost * (taskStats.requests - 1)) + cost) / taskStats.requests;
        taskStats.successRate = (taskStats.successRate * (taskStats.requests - 1) + (success ? 1 : 0)) / taskStats.requests;
        
        // Track specific feature usage
        if (tracking.hasImages) {
            this.metrics.imagesAnalyzed += responseData.result?.imageCount || tracking.hasImages ? 1 : 0;
        }
        
        if (tracking.hasFunctions) {
            this.metrics.functionCallsExecuted += responseData.result?.functionCalls?.length || 0;
        }
        
        if (taskType === 'embedding_generation') {
            this.metrics.embeddingsGenerated += responseData.result?.total_texts || 0;
        }
        
        // Track safety violations
        if (responseData.result?.safetyRatings?.some(rating => rating.probability === 'HIGH')) {
            this.metrics.safetyViolations++;
        }
        
        // Store performance metrics
        const performanceData = {
            timestamp: new Date().toISOString(),
            requestId,
            model,
            taskType,
            duration,
            cost,
            success,
            inputTokens: usage.promptTokens || 0,
            outputTokens: usage.completionTokens || 0,
            totalTokens: usage.totalTokens || 0,
            hasImages: tracking.hasImages,
            hasFunctions: tracking.hasFunctions,
            safetyViolation: responseData.result?.safetyRatings?.some(rating => rating.probability === 'HIGH') || false
        };
        
        this.metrics.performanceMetrics.push(performanceData);
        
        // Keep only last 1000 performance metrics
        if (this.metrics.performanceMetrics.length > 1000) {
            this.metrics.performanceMetrics = this.metrics.performanceMetrics.slice(-1000);
        }
        
        // Complete Langwatch trace
        if (tracking.langwatchTrace) {
            try {
                tracking.langwatchTrace.end({
                    output: responseData.result,
                    metadata: {
                        duration,
                        cost,
                        success,
                        usage,
                        safety_violation: performanceData.safetyViolation
                    }
                });
            } catch (error) {
                logger.debug('Failed to end Langwatch trace', { error: error.message });
            }
        }
        
        // Log completion
        logger.info('Google AI request completed', {
            requestId,
            model,
            taskType,
            duration,
            cost: cost.toFixed(6),
            success,
            tokens: usage.totalTokens || 0
        });
        
        // Check cost thresholds
        this._checkCostThresholds();
        
        // Clean up
        this.activeRequests.delete(requestId);
        
        return performanceData;
    }
    
    /**
     * Get comprehensive monitoring statistics
     */
    getStatistics() {
        const now = new Date();
        const oneHourAgo = new Date(now - 60 * 60 * 1000);
        const oneDayAgo = new Date(now - 24 * 60 * 60 * 1000);
        
        // Recent metrics
        const recentMetrics = this.metrics.performanceMetrics.filter(
            m => new Date(m.timestamp) > oneHourAgo
        );
        
        const dailyMetrics = this.metrics.performanceMetrics.filter(
            m => new Date(m.timestamp) > oneDayAgo
        );
        
        return {
            overview: {
                totalRequests: this.metrics.totalRequests,
                successfulRequests: this.metrics.successfulRequests,
                failedRequests: this.metrics.failedRequests,
                successRate: this.metrics.totalRequests > 0 
                    ? (this.metrics.successfulRequests / this.metrics.totalRequests * 100).toFixed(2) + '%'
                    : '0%',
                totalCost: this.metrics.totalCost.toFixed(4),
                averageCostPerRequest: this.metrics.totalRequests > 0 
                    ? (this.metrics.totalCost / this.metrics.totalRequests).toFixed(6)
                    : '0',
                activeRequests: this.activeRequests.size
            },
            
            usage: {
                safetyViolations: this.metrics.safetyViolations,
                functionCallsExecuted: this.metrics.functionCallsExecuted,
                embeddingsGenerated: this.metrics.embeddingsGenerated,
                imagesAnalyzed: this.metrics.imagesAnalyzed
            },
            
            models: Object.fromEntries(
                Array.from(this.metrics.modelUsage.entries()).map(([model, stats]) => [
                    model,
                    {
                        ...stats,
                        averageLatency: Math.round(stats.averageLatency),
                        successRate: (stats.successRate * 100).toFixed(2) + '%',
                        totalCost: stats.totalCost.toFixed(4),
                        averageCostPerRequest: stats.requests > 0 
                            ? (stats.totalCost / stats.requests).toFixed(6)
                            : '0'
                    }
                ])
            ),
            
            taskTypes: Object.fromEntries(
                Array.from(this.metrics.taskTypeStats.entries()).map(([task, stats]) => [
                    task,
                    {
                        ...stats,
                        averageDuration: Math.round(stats.averageDuration),
                        successRate: (stats.successRate * 100).toFixed(2) + '%',
                        averageCost: stats.averageCost.toFixed(6)
                    }
                ])
            ),
            
            trends: {
                lastHour: {
                    requests: recentMetrics.length,
                    averageDuration: recentMetrics.length > 0 
                        ? Math.round(recentMetrics.reduce((sum, m) => sum + m.duration, 0) / recentMetrics.length)
                        : 0,
                    cost: recentMetrics.reduce((sum, m) => sum + m.cost, 0).toFixed(4)
                },
                lastDay: {
                    requests: dailyMetrics.length,
                    averageDuration: dailyMetrics.length > 0 
                        ? Math.round(dailyMetrics.reduce((sum, m) => sum + m.duration, 0) / dailyMetrics.length)
                        : 0,
                    cost: dailyMetrics.reduce((sum, m) => sum + m.cost, 0).toFixed(4)
                }
            },
            
            alerts: this._generateAlerts()
        };
    }
    
    /**
     * Get model performance comparison
     */
    getModelComparison() {
        const models = Array.from(this.metrics.modelUsage.entries());
        
        return models.map(([model, stats]) => ({
            model,
            requests: stats.requests,
            successRate: (stats.successRate * 100).toFixed(2),
            averageLatency: Math.round(stats.averageLatency),
            totalCost: stats.totalCost.toFixed(4),
            costEfficiency: stats.requests > 0 
                ? (stats.successRate / (stats.totalCost / stats.requests)).toFixed(2)
                : '0',
            pricing: this.modelPricing[model] || { input: 0, output: 0 }
        })).sort((a, b) => b.requests - a.requests);
    }
    
    /**
     * Get cost analysis
     */
    getCostAnalysis() {
        const dailyMetrics = this.metrics.performanceMetrics.filter(
            m => new Date(m.timestamp) > new Date(Date.now() - 24 * 60 * 60 * 1000)
        );
        
        const costByModel = new Map();
        const costByTask = new Map();
        const costByHour = new Map();
        
        dailyMetrics.forEach(metric => {
            // By model
            const modelCost = costByModel.get(metric.model) || 0;
            costByModel.set(metric.model, modelCost + metric.cost);
            
            // By task
            const taskCost = costByTask.get(metric.taskType) || 0;
            costByTask.set(metric.taskType, taskCost + metric.cost);
            
            // By hour
            const hour = new Date(metric.timestamp).getHours();
            const hourCost = costByHour.get(hour) || 0;
            costByHour.set(hour, hourCost + metric.cost);
        });
        
        return {
            dailyTotal: dailyMetrics.reduce((sum, m) => sum + m.cost, 0).toFixed(4),
            projectedMonthly: (dailyMetrics.reduce((sum, m) => sum + m.cost, 0) * 30).toFixed(2),
            byModel: Object.fromEntries(
                Array.from(costByModel.entries()).map(([model, cost]) => [model, cost.toFixed(4)])
            ),
            byTask: Object.fromEntries(
                Array.from(costByTask.entries()).map(([task, cost]) => [task, cost.toFixed(4)])
            ),
            byHour: Object.fromEntries(
                Array.from(costByHour.entries()).map(([hour, cost]) => [hour, cost.toFixed(4)])
            ),
            thresholds: this.costThresholds
        };
    }
    
    /**
     * Get safety analysis
     */
    getSafetyAnalysis() {
        const safetyMetrics = this.metrics.performanceMetrics.filter(m => m.safetyViolation);
        
        const violationsByModel = new Map();
        const violationsByTask = new Map();
        
        safetyMetrics.forEach(metric => {
            // By model
            const modelViolations = violationsByModel.get(metric.model) || 0;
            violationsByModel.set(metric.model, modelViolations + 1);
            
            // By task
            const taskViolations = violationsByTask.get(metric.taskType) || 0;
            violationsByTask.set(metric.taskType, taskViolations + 1);
        });
        
        return {
            totalViolations: this.metrics.safetyViolations,
            violationRate: this.metrics.totalRequests > 0 
                ? (this.metrics.safetyViolations / this.metrics.totalRequests * 100).toFixed(2) + '%'
                : '0%',
            byModel: Object.fromEntries(violationsByModel),
            byTask: Object.fromEntries(violationsByTask),
            recentViolations: safetyMetrics.slice(-10).map(m => ({
                timestamp: m.timestamp,
                model: m.model,
                taskType: m.taskType,
                requestId: m.requestId
            }))
        };
    }
    
    /**
     * Reset metrics (for testing or maintenance)
     */
    resetMetrics() {
        this.metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalCost: 0,
            modelUsage: new Map(),
            taskTypeStats: new Map(),
            performanceMetrics: [],
            safetyViolations: 0,
            functionCallsExecuted: 0,
            embeddingsGenerated: 0,
            imagesAnalyzed: 0
        };
        
        this.activeRequests.clear();
        logger.info('Google AI monitoring metrics reset');
    }
    
    // Private helper methods
    
    _estimateTokens(input) {
        if (!input) return 0;
        if (typeof input === 'string') {
            return Math.ceil(input.length / 4); // Rough estimation
        }
        if (Array.isArray(input)) {
            return input.reduce((total, item) => {
                if (typeof item === 'string') return total + Math.ceil(item.length / 4);
                if (item.content) return total + Math.ceil(item.content.length / 4);
                return total;
            }, 0);
        }
        return 0;
    }
    
    _calculateCost(model, usage) {
        const pricing = this.modelPricing[model];
        if (!pricing || !usage) return 0;
        
        const inputCost = (usage.promptTokens / 1000000) * pricing.input;
        const outputCost = pricing.output ? (usage.completionTokens / 1000000) * pricing.output : 0;
        
        return inputCost + outputCost;
    }
    
    _checkCostThresholds() {
        if (this.metrics.totalCost > this.costThresholds.critical) {
            logger.error('Google AI cost threshold exceeded', {
                totalCost: this.metrics.totalCost,
                threshold: this.costThresholds.critical,
                level: 'critical'
            });
        } else if (this.metrics.totalCost > this.costThresholds.warning) {
            logger.warn('Google AI cost threshold warning', {
                totalCost: this.metrics.totalCost,
                threshold: this.costThresholds.warning,
                level: 'warning'
            });
        }
    }
    
    _generateAlerts() {
        const alerts = [];
        
        // High cost alert
        if (this.metrics.totalCost > this.costThresholds.warning) {
            alerts.push({
                type: 'cost',
                level: this.metrics.totalCost > this.costThresholds.critical ? 'critical' : 'warning',
                message: `Total cost ($${this.metrics.totalCost.toFixed(2)}) exceeds threshold`,
                timestamp: new Date().toISOString()
            });
        }
        
        // High error rate alert
        const errorRate = this.metrics.totalRequests > 0 
            ? (this.metrics.failedRequests / this.metrics.totalRequests)
            : 0;
        
        if (errorRate > 0.1) { // 10% error rate
            alerts.push({
                type: 'error_rate',
                level: errorRate > 0.2 ? 'critical' : 'warning',
                message: `High error rate: ${(errorRate * 100).toFixed(2)}%`,
                timestamp: new Date().toISOString()
            });
        }
        
        // Safety violations alert
        if (this.metrics.safetyViolations > 5) {
            alerts.push({
                type: 'safety',
                level: 'warning',
                message: `${this.metrics.safetyViolations} safety violations detected`,
                timestamp: new Date().toISOString()
            });
        }
        
        return alerts;
    }
    
    startPeriodicReporting() {
        // Log summary every 5 minutes
        setInterval(() => {
            if (this.metrics.totalRequests > 0) {
                logger.info('Google AI periodic report', {
                    totalRequests: this.metrics.totalRequests,
                    successRate: (this.metrics.successfulRequests / this.metrics.totalRequests * 100).toFixed(2) + '%',
                    totalCost: this.metrics.totalCost.toFixed(4),
                    activeRequests: this.activeRequests.size,
                    uniqueModels: this.metrics.modelUsage.size
                });
            }
        }, 300000); // 5 minutes
    }
}

// Create singleton instance
const googleAIMonitoring = new GoogleAIMonitoring();

module.exports = {
    googleAIMonitoring,
    trackGoogleAIRequest: (requestData) => googleAIMonitoring.trackRequestStart(requestData),
    trackGoogleAICompletion: (requestId, responseData) => googleAIMonitoring.trackRequestComplete(requestId, responseData)
};
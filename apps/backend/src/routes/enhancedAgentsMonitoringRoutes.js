/**
 * Enhanced Agents Monitoring Routes - REST API for monitoring and observability
 * 
 * Provides comprehensive monitoring endpoints for:
 * - LangGraph workflow monitoring
 * - Agent performance analytics
 * - System health monitoring
 * - Real-time dashboards
 * - Alert management
 */

const express = require('express');
const router = express.Router();
const { query, validationResult } = require('express-validator');
const logger = require('../utils/logger');

// Mock monitoring service - will integrate with Python service
class EnhancedAgentsMonitoringService {
    constructor() {
        this.mockData = this._generateMockData();
    }

    _generateMockData() {
        return {
            systemHealth: {
                overall_status: "healthy",
                components: {
                    workflows: {
                        status: "healthy",
                        active_workflows: 8,
                        total_processed: 1247
                    },
                    agents: {
                        status: "healthy",
                        healthy_agents: 12,
                        total_agents: 12
                    },
                    error_tracking: {
                        status: "healthy",
                        error_rate: 2.3,
                        failed_workflows: 28
                    }
                },
                metrics: {
                    total_workflows: 1247,
                    successful_workflows: 1219,
                    failed_workflows: 28,
                    avg_workflow_duration: 3.2,
                    total_node_executions: 15894,
                    active_workflows: 8,
                    total_agents: 12
                },
                alerts: [],
                timestamp: new Date().toISOString()
            },
            performanceAnalytics: {
                time_range: 3600,
                agent_performance: {
                    "enhanced_sam_user_123": {
                        agent_type: "sam",
                        total_conversations: 156,
                        success_rate: 97.4,
                        avg_response_time: 1.8,
                        tool_executions: 89,
                        collaboration_events: 23,
                        health_status: "healthy"
                    },
                    "enhanced_manus_user_123": {
                        agent_type: "manus",
                        total_conversations: 78,
                        success_rate: 94.9,
                        avg_response_time: 4.2,
                        tool_executions: 234,
                        collaboration_events: 23,
                        health_status: "healthy"
                    }
                },
                workflow_patterns: {
                    total_workflows: 234,
                    avg_duration: 3.4,
                    success_rate: 96.2,
                    avg_nodes_per_workflow: 5.7,
                    most_common_nodes: {
                        "context_retrieval": 234,
                        "enhanced_agent": 234,
                        "memory_storage": 234,
                        "tool_execution": 156,
                        "collaboration": 67
                    },
                    collaboration_frequency: 67
                },
                collaboration_analysis: {
                    "sam_collaboration": {
                        count: 34,
                        avg_duration: 6.8
                    },
                    "manus_collaboration": {
                        count: 33,
                        avg_duration: 8.2
                    }
                },
                timestamp: new Date().toISOString()
            },
            workflowMetrics: {
                active: 8,
                completed_today: 89,
                avg_execution_time: 3.2,
                node_performance: {
                    "context_retrieval": { avg_duration: 0.8, success_rate: 99.1 },
                    "enhanced_agent": { avg_duration: 2.1, success_rate: 97.8 },
                    "tool_execution": { avg_duration: 1.5, success_rate: 95.2 },
                    "collaboration": { avg_duration: 3.4, success_rate: 94.6 },
                    "memory_storage": { avg_duration: 0.3, success_rate: 99.8 }
                },
                decision_patterns: {
                    "respond": 45,
                    "search_memory": 23,
                    "execute_analysis": 18,
                    "initiate_collaboration": 12,
                    "store_information": 34
                }
            },
            agentMetrics: {
                sam_agents: {
                    total: 6,
                    healthy: 6,
                    avg_response_time: 1.8,
                    knowledge_graph_updates: 456,
                    collaboration_events: 89,
                    context_utilization_rate: 0.87
                },
                manus_agents: {
                    total: 6,
                    healthy: 6,
                    avg_task_duration: 4.2,
                    tools_executed: 567,
                    workflow_efficiency: 0.94,
                    resource_utilization: 0.78
                }
            },
            alerts: [
                {
                    alert_id: "alert_12345",
                    severity: "warning",
                    component: "workflow_duration",
                    message: "Average workflow duration increased by 15% in last hour",
                    timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
                    resolved: false
                }
            ]
        };
    }

    async getSystemHealth() {
        return this.mockData.systemHealth;
    }

    async getPerformanceAnalytics(timeRange = 3600, agentType = null) {
        const analytics = { ...this.mockData.performanceAnalytics };
        analytics.time_range = timeRange;
        
        if (agentType) {
            // Filter by agent type
            const filteredPerformance = {};
            for (const [agentId, metrics] of Object.entries(analytics.agent_performance)) {
                if (metrics.agent_type === agentType) {
                    filteredPerformance[agentId] = metrics;
                }
            }
            analytics.agent_performance = filteredPerformance;
        }
        
        return analytics;
    }

    async getWorkflowMetrics() {
        return this.mockData.workflowMetrics;
    }

    async getAgentMetrics() {
        return this.mockData.agentMetrics;
    }

    async getMonitoringDashboard() {
        return {
            system_overview: this.mockData.systemHealth,
            performance_analytics: this.mockData.performanceAnalytics,
            workflow_metrics: this.mockData.workflowMetrics,
            agent_metrics: this.mockData.agentMetrics,
            active_workflows: this.mockData.systemHealth.metrics.active_workflows,
            total_agents: this.mockData.systemHealth.metrics.total_agents,
            recent_alerts: this.mockData.alerts,
            system_stats: {
                total_workflows: this.mockData.systemHealth.metrics.total_workflows,
                successful_workflows: this.mockData.systemHealth.metrics.successful_workflows,
                failed_workflows: this.mockData.systemHealth.metrics.failed_workflows,
                avg_workflow_duration: this.mockData.systemHealth.metrics.avg_workflow_duration,
                uptime: 86400 // 24 hours in seconds
            },
            timestamp: new Date().toISOString()
        };
    }

    async getActiveWorkflows() {
        return {
            count: 8,
            workflows: [
                {
                    workflow_id: "wf_sam_123_20241201_143022",
                    agent_type: "sam",
                    agent_id: "enhanced_sam_user_123",
                    user_id: "user_123",
                    start_time: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
                    current_node: "enhanced_agent",
                    progress: 60,
                    estimated_remaining: 120
                },
                {
                    workflow_id: "wf_manus_456_20241201_143045",
                    agent_type: "manus",
                    agent_id: "enhanced_manus_user_456",
                    user_id: "user_456",
                    start_time: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
                    current_node: "task_execution",
                    progress: 75,
                    estimated_remaining: 180
                }
            ]
        };
    }

    async getAlerts(resolved = false) {
        return this.mockData.alerts.filter(alert => alert.resolved === resolved);
    }

    async resolveAlert(alertId) {
        const alert = this.mockData.alerts.find(a => a.alert_id === alertId);
        if (alert) {
            alert.resolved = true;
            alert.resolution_time = new Date().toISOString();
            return { success: true, alert };
        }
        return { success: false, error: "Alert not found" };
    }
}

// Create service instance
const monitoringService = new EnhancedAgentsMonitoringService();

// Validation middleware
const validateTimeRange = [
    query('time_range').optional().isInt({ min: 60, max: 86400 }).withMessage('Time range must be between 60 and 86400 seconds'),
    query('agent_type').optional().isIn(['sam', 'manus']).withMessage('Agent type must be sam or manus')
];

const validateAlertQuery = [
    query('resolved').optional().isBoolean().withMessage('Resolved must be a boolean'),
    query('severity').optional().isIn(['info', 'warning', 'error', 'critical']).withMessage('Invalid severity level')
];

// Routes

/**
 * GET /api/monitoring/dashboard
 * Get comprehensive monitoring dashboard
 */
router.get('/dashboard', async (req, res, next) => {
    try {
        const dashboard = await monitoringService.getMonitoringDashboard();
        
        logger.info('📊 Monitoring dashboard accessed');
        
        res.json({
            success: true,
            dashboard,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error('Monitoring dashboard failed', { error: error.message });
        next(error);
    }
});

/**
 * GET /api/monitoring/health
 * Get system health status
 */
router.get('/health', async (req, res, next) => {
    try {
        const health = await monitoringService.getSystemHealth();
        
        res.json({
            success: true,
            health,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error('System health check failed', { error: error.message });
        next(error);
    }
});

/**
 * GET /api/monitoring/performance
 * Get performance analytics
 */
router.get('/performance', validateTimeRange, async (req, res, next) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const timeRange = parseInt(req.query.time_range) || 3600;
        const agentType = req.query.agent_type;
        
        const analytics = await monitoringService.getPerformanceAnalytics(timeRange, agentType);
        
        logger.info('📈 Performance analytics accessed', {
            time_range: timeRange,
            agent_type: agentType
        });
        
        res.json({
            success: true,
            analytics,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error('Performance analytics failed', { error: error.message });
        next(error);
    }
});

/**
 * GET /api/monitoring/workflows
 * Get workflow metrics and patterns
 */
router.get('/workflows', async (req, res, next) => {
    try {
        const metrics = await monitoringService.getWorkflowMetrics();
        
        res.json({
            success: true,
            metrics,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error('Workflow metrics failed', { error: error.message });
        next(error);
    }
});

/**
 * GET /api/monitoring/workflows/active
 * Get currently active workflows
 */
router.get('/workflows/active', async (req, res, next) => {
    try {
        const activeWorkflows = await monitoringService.getActiveWorkflows();
        
        res.json({
            success: true,
            ...activeWorkflows,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error('Active workflows query failed', { error: error.message });
        next(error);
    }
});

/**
 * GET /api/monitoring/agents
 * Get agent performance metrics
 */
router.get('/agents', async (req, res, next) => {
    try {
        const metrics = await monitoringService.getAgentMetrics();
        
        res.json({
            success: true,
            metrics,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error('Agent metrics failed', { error: error.message });
        next(error);
    }
});

/**
 * GET /api/monitoring/alerts
 * Get system alerts
 */
router.get('/alerts', validateAlertQuery, async (req, res, next) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const resolved = req.query.resolved === 'true';
        const alerts = await monitoringService.getAlerts(resolved);
        
        res.json({
            success: true,
            alerts,
            count: alerts.length,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        logger.error('Alerts query failed', { error: error.message });
        next(error);
    }
});

/**
 * POST /api/monitoring/alerts/:alertId/resolve
 * Resolve a system alert
 */
router.post('/alerts/:alertId/resolve', async (req, res, next) => {
    try {
        const { alertId } = req.params;
        const result = await monitoringService.resolveAlert(alertId);
        
        if (result.success) {
            logger.info('🔧 Alert resolved', { alert_id: alertId });
            res.json({
                success: true,
                message: 'Alert resolved successfully',
                alert: result.alert,
                timestamp: new Date().toISOString()
            });
        } else {
            res.status(404).json({
                success: false,
                error: result.error,
                timestamp: new Date().toISOString()
            });
        }
        
    } catch (error) {
        logger.error('Alert resolution failed', { error: error.message });
        next(error);
    }
});

/**
 * GET /api/monitoring/realtime
 * Get real-time monitoring data (simplified)
 */
router.get('/realtime', async (req, res, next) => {
    try {
        const realtimeData = {
            active_workflows: 8,
            current_load: {
                sam_agents: 6,
                manus_agents: 6,
                avg_response_time: 2.1,
                requests_per_minute: 23
            },
            recent_activity: [
                {
                    timestamp: new Date(Date.now() - 30000).toISOString(),
                    event: "workflow_completed",
                    agent_type: "sam",
                    duration: 2.8
                },
                {
                    timestamp: new Date(Date.now() - 45000).toISOString(),
                    event: "collaboration_started", 
                    agents: ["sam", "manus"],
                    task_type: "analysis_execution"
                },
                {
                    timestamp: new Date(Date.now() - 60000).toISOString(),
                    event: "tool_execution",
                    agent_type: "manus",
                    tool: "analysis_tool"
                }
            ],
            system_metrics: {
                cpu_usage: 45.2,
                memory_usage: 68.7,
                network_io: 1.2,
                disk_io: 0.8
            },
            timestamp: new Date().toISOString()
        };
        
        res.json({
            success: true,
            data: realtimeData
        });
        
    } catch (error) {
        logger.error('Real-time data failed', { error: error.message });
        next(error);
    }
});

module.exports = router;
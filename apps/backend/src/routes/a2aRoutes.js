/**
 * A2A Routes - REST API routes for Agent-to-Agent communication
 * Provides HTTP endpoints for A2A protocol integration
 */

const express = require('express');
const router = express.Router();
const a2aController = require('../controllers/a2aController');
const { validateA2ARequest, validateDelegationRequest } = require('../validation/a2aSchemas');
const validationMiddleware = require('../middleware/validationMiddleware');
const authMiddleware = require('../middleware/authMiddleware');
const { monitorA2ARequest, a2aMonitoring } = require('../middleware/a2aMonitoring');

// Apply monitoring middleware to all A2A routes
router.use(monitorA2ARequest);

// Apply authentication middleware to all A2A routes (except monitoring endpoints)
router.use((req, res, next) => {
    // Skip auth for monitoring endpoints
    if (req.path.includes('/monitoring') || req.path.includes('/metrics')) {
        return next();
    }
    return authMiddleware.protectRoute(req, res, next);
});

/**
 * POST /api/a2a/task
 * Handle incoming A2A task delegation
 */
router.post('/task', 
    validationMiddleware(validateA2ARequest),
    a2aController.handleTaskDelegation.bind(a2aController)
);

/**
 * POST /api/a2a/delegate
 * Delegate task to another A2A agent
 */
router.post('/delegate',
    validationMiddleware(validateDelegationRequest),
    a2aController.delegateToAgent.bind(a2aController)
);

/**
 * GET /api/a2a/discover
 * Discover available A2A agents
 * Query params: capabilities (comma-separated list)
 */
router.get('/discover',
    a2aController.discoverAgents.bind(a2aController)
);

/**
 * GET /api/a2a/status
 * Get A2A service status and metrics
 */
router.get('/status',
    a2aController.getStatus.bind(a2aController)
);

/**
 * POST /api/a2a/initialize
 * Initialize A2A service manually
 */
router.post('/initialize',
    a2aController.initializeService.bind(a2aController)
);

/**
 * POST /api/a2a/shutdown
 * Shutdown A2A service
 */
router.post('/shutdown',
    a2aController.shutdownService.bind(a2aController)
);

/**
 * GET /api/a2a/metrics
 * Get comprehensive A2A performance metrics
 */
router.get('/metrics',
    a2aController.getMetrics.bind(a2aController)
);

/**
 * POST /api/a2a/workflow
 * Execute complex multi-agent workflows
 */
router.post('/workflow',
    validationMiddleware(validateWorkflowRequest),
    async (req, res, next) => {
        try {
            const result = await a2aController.handleTaskDelegation({
                body: {
                    task_type: 'multi_agent_workflow',
                    payload: req.body,
                    requester_id: req.user?.id || 'api_user',
                    priority: req.body.priority || 5
                }
            }, res, next);
        } catch (error) {
            next(error);
        }
    }
);

/**
 * POST /api/a2a/coordinate
 * Coordinate multiple agents for a specific task
 */
router.post('/coordinate',
    validationMiddleware(validateCoordinationRequest),
    async (req, res, next) => {
        try {
            const result = await a2aController.handleTaskDelegation({
                body: {
                    task_type: 'agent_coordination',
                    payload: req.body,
                    requester_id: req.user?.id || 'api_user',
                    priority: req.body.priority || 5
                }
            }, res, next);
        } catch (error) {
            next(error);
        }
    }
);

/**
 * GET /api/a2a/agents/:agentId/status
 * Get specific agent status
 */
router.get('/agents/:agentId/status',
    async (req, res, next) => {
        try {
            const { agentId } = req.params;
            
            if (!a2aController.a2aService) {
                return res.status(400).json({
                    success: false,
                    error: 'A2A service not initialized'
                });
            }
            
            const agentLoads = await a2aController.a2aService.getAgentLoads();
            const agentStatus = agentLoads[agentId];
            
            if (!agentStatus) {
                return res.status(404).json({
                    success: false,
                    error: 'Agent not found'
                });
            }
            
            res.json({
                success: true,
                agent_id: agentId,
                status: agentStatus,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            next(error);
        }
    }
);

/**
 * POST /api/a2a/agents/:agentId/ping
 * Ping specific agent
 */
router.post('/agents/:agentId/ping',
    async (req, res, next) => {
        try {
            const { agentId } = req.params;
            
            if (!a2aController.a2aService) {
                return res.status(400).json({
                    success: false,
                    error: 'A2A service not initialized'
                });
            }
            
            // Get agent info
            const connectedAgents = a2aController.a2aService.connectedAgents;
            const agentInfo = connectedAgents.get(agentId);
            
            if (!agentInfo) {
                return res.status(404).json({
                    success: false,
                    error: 'Agent not found in connected agents'
                });
            }
            
            // Ping the agent
            const axios = require('axios');
            const startTime = Date.now();
            
            try {
                const response = await axios.get(
                    `${agentInfo.endpoints?.health || agentInfo.endpoint}/health`,
                    { timeout: 5000 }
                );
                
                const responseTime = Date.now() - startTime;
                
                res.json({
                    success: true,
                    agent_id: agentId,
                    ping_successful: true,
                    response_time: responseTime,
                    agent_status: response.data,
                    timestamp: new Date().toISOString()
                });
                
            } catch (error) {
                const responseTime = Date.now() - startTime;
                
                res.json({
                    success: true,
                    agent_id: agentId,
                    ping_successful: false,
                    response_time: responseTime,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            }
            
        } catch (error) {
            next(error);
        }
    }
);

/**
 * GET /api/a2a/monitoring/dashboard
 * Get monitoring dashboard data
 */
router.get('/monitoring/dashboard',
    (req, res, next) => {
        try {
            const dashboardData = a2aMonitoring.getDashboardData();
            res.json({
                success: true,
                dashboard: dashboardData,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            next(error);
        }
    }
);

/**
 * GET /api/a2a/monitoring/traces
 * Get active traces information
 */
router.get('/monitoring/traces',
    (req, res, next) => {
        try {
            const activeTraces = a2aMonitoring.getActiveTraces();
            res.json({
                success: true,
                active_traces: activeTraces,
                count: activeTraces.length,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            next(error);
        }
    }
);

/**
 * POST /api/a2a/monitoring/reset
 * Reset monitoring metrics
 */
router.post('/monitoring/reset',
    authMiddleware.protectRoute, // Require auth for reset
    (req, res, next) => {
        try {
            a2aMonitoring.resetMetrics();
            res.json({
                success: true,
                message: 'A2A monitoring metrics reset successfully',
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            next(error);
        }
    }
);

/**
 * WebSocket endpoint for real-time A2A communication
 * This would be handled separately in the WebSocket server setup
 */

// Validation schemas for specific A2A endpoints
function validateWorkflowRequest(req, res, next) {
    const Joi = require('joi');
    
    const schema = Joi.object({
        workflow_steps: Joi.array().items(
            Joi.object({
                id: Joi.string().optional(),
                task_data: Joi.object().required(),
                required_capabilities: Joi.array().items(Joi.string()).optional(),
                delegate_to_a2a: Joi.boolean().default(false),
                execution_mode: Joi.string().valid('delegate', 'local').default('delegate')
            })
        ).required(),
        coordination_type: Joi.string().valid('sequential', 'parallel').default('sequential'),
        priority: Joi.number().min(1).max(10).default(5),
        timeout: Joi.number().positive().optional()
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

function validateCoordinationRequest(req, res, next) {
    const Joi = require('joi');
    
    const schema = Joi.object({
        coordination_plan: Joi.object({
            agents: Joi.array().items(
                Joi.object({
                    agent_id: Joi.string().optional(),
                    capabilities: Joi.array().items(Joi.string()).required(),
                    task: Joi.object().required(),
                    role: Joi.string().optional()
                })
            ).required()
        }).required(),
        sync_mode: Joi.string().valid('parallel', 'sequential').default('sequential'),
        priority: Joi.number().min(1).max(10).default(5),
        timeout: Joi.number().positive().optional()
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

module.exports = router;
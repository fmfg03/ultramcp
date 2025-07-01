/**
 * Swarm Intelligence Routes - REST API routes for advanced P2P agent networks
 * Provides comprehensive routing for swarm intelligence operations
 * 
 * Features:
 * - Agent registration and management
 * - Collective decision making
 * - Emergent intelligence problem solving
 * - Swarm optimization algorithms
 * - Real-time monitoring and visualization
 */

const express = require('express');
const router = express.Router();
const swarmController = require('../controllers/swarmController');
const validationMiddleware = require('../middleware/validationMiddleware');
const authMiddleware = require('../middleware/authMiddleware');
const Joi = require('joi');

// Apply authentication middleware to all swarm routes
router.use(authMiddleware.protectRoute);

/**
 * POST /api/swarm/agents/register
 * Register a new agent in the swarm
 */
router.post('/agents/register',
    validationMiddleware(validateAgentRegistration),
    swarmController.registerAgent.bind(swarmController)
);

/**
 * GET /api/swarm/agents
 * Get active agents in the swarm
 */
router.get('/agents',
    swarmController.getActiveAgents.bind(swarmController)
);

/**
 * POST /api/swarm/decisions/collective
 * Initiate collective decision making
 */
router.post('/decisions/collective',
    validationMiddleware(validateCollectiveDecision),
    swarmController.makeCollectiveDecision.bind(swarmController)
);

/**
 * POST /api/swarm/intelligence/emergent
 * Solve problems with emergent intelligence
 */
router.post('/intelligence/emergent',
    validationMiddleware(validateEmergentIntelligence),
    swarmController.solveWithEmergence.bind(swarmController)
);

/**
 * POST /api/swarm/optimization
 * Optimize parameters using swarm algorithms
 */
router.post('/optimization',
    validationMiddleware(validateOptimization),
    swarmController.optimizeParameters.bind(swarmController)
);

/**
 * GET /api/swarm/topology
 * Get swarm topology and network visualization
 */
router.get('/topology',
    swarmController.getSwarmTopology.bind(swarmController)
);

/**
 * GET /api/swarm/metrics
 * Get comprehensive swarm metrics and statistics
 */
router.get('/metrics',
    swarmController.getSwarmMetrics.bind(swarmController)
);

/**
 * POST /api/swarm/instances
 * Create a new swarm instance
 */
router.post('/instances',
    validationMiddleware(validateSwarmInstance),
    swarmController.createSwarmInstance.bind(swarmController)
);

/**
 * GET /api/swarm/instances
 * Get all swarm instances
 */
router.get('/instances',
    swarmController.getSwarmInstances.bind(swarmController)
);

/**
 * GET /api/swarm/health
 * Health check for swarm intelligence service
 */
router.get('/health',
    swarmController.healthCheck.bind(swarmController)
);

/**
 * POST /api/swarm/reset
 * Reset swarm metrics (admin only)
 */
router.post('/reset',
    // authMiddleware.requireRole('admin'), // Uncomment when role-based auth is implemented
    validationMiddleware(validateSwarmReset),
    swarmController.resetSwarm.bind(swarmController)
);

// Validation schemas

function validateAgentRegistration(req, res, next) {
    const schema = Joi.object({
        id: Joi.string().optional(),
        
        type: Joi.string().valid(
            'generic',
            'coordinator',
            'analyst',
            'executor',
            'memory_keeper',
            'specialist',
            'learner',
            'optimizer'
        ).default('generic'),
        
        capabilities: Joi.array().items(
            Joi.string().valid(
                'orchestration',
                'coordination',
                'analysis',
                'reasoning',
                'execution',
                'action',
                'memory',
                'storage',
                'learning',
                'optimization',
                'communication',
                'monitoring',
                'decision_making',
                'problem_solving',
                'pattern_recognition',
                'data_processing'
            )
        ).min(1).required(),
        
        metadata: Joi.object({
            name: Joi.string().optional(),
            description: Joi.string().optional(),
            version: Joi.string().optional(),
            owner: Joi.string().optional(),
            tags: Joi.array().items(Joi.string()).optional(),
            config: Joi.object().optional()
        }).optional()
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Agent registration validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

function validateCollectiveDecision(req, res, next) {
    const schema = Joi.object({
        proposal: Joi.object({
            type: Joi.string().required(),
            title: Joi.string().required(),
            description: Joi.string().optional(),
            data: Joi.any().optional(),
            priority: Joi.string().valid('low', 'medium', 'high', 'critical').default('medium'),
            deadline: Joi.date().optional()
        }).required(),
        
        consensusThreshold: Joi.number().min(0.1).max(1.0).default(0.67),
        timeout: Joi.number().min(1000).max(300000).default(30000), // 1s to 5min
        maxRounds: Joi.number().min(1).max(10).default(3),
        
        requiredCapabilities: Joi.array().items(Joi.string()).optional()
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Collective decision validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

function validateEmergentIntelligence(req, res, next) {
    const schema = Joi.object({
        problem: Joi.object({
            type: Joi.string().required(),
            title: Joi.string().required(),
            description: Joi.string().optional(),
            data: Joi.any().optional(),
            constraints: Joi.object().optional(),
            objectives: Joi.array().items(Joi.string()).optional(),
            complexity: Joi.string().valid('low', 'medium', 'high', 'extreme').default('medium')
        }).required(),
        
        maxIterations: Joi.number().min(1).max(100).default(10),
        diversityThreshold: Joi.number().min(0.1).max(1.0).default(0.3),
        convergenceThreshold: Joi.number().min(0.1).max(1.0).default(0.8)
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Emergent intelligence validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

function validateOptimization(req, res, next) {
    const schema = Joi.object({
        method: Joi.string().valid('pso', 'aco').default('pso'),
        
        searchSpace: Joi.array().items(
            Joi.object({
                min: Joi.number().required(),
                max: Joi.number().required(),
                name: Joi.string().optional()
            })
        ).min(1).required(),
        
        objectiveFunction: Joi.any().optional(), // Will be handled by the controller
        
        // PSO parameters
        iterations: Joi.number().min(1).max(1000).default(100),
        inertia: Joi.number().min(0.1).max(2.0).default(0.9),
        cognitiveWeight: Joi.number().min(0.1).max(5.0).default(2.0),
        socialWeight: Joi.number().min(0.1).max(5.0).default(2.0),
        
        // ACO parameters
        pheromoneDecay: Joi.number().min(0.01).max(0.99).default(0.1),
        alpha: Joi.number().min(0.1).max(5.0).default(1.0),
        beta: Joi.number().min(0.1).max(5.0).default(2.0)
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Optimization validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

function validateSwarmInstance(req, res, next) {
    const schema = Joi.object({
        name: Joi.string().min(1).max(50).pattern(/^[a-zA-Z0-9_-]+$/).required(),
        
        maxAgents: Joi.number().min(1).max(1000).default(50),
        heartbeatInterval: Joi.number().min(1000).max(60000).default(5000),
        consensusThreshold: Joi.number().min(0.1).max(1.0).default(0.67),
        emergenceThreshold: Joi.number().min(0.1).max(1.0).default(0.8),
        autoOrganization: Joi.boolean().default(true),
        p2pNetworking: Joi.boolean().default(true)
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Swarm instance validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

function validateSwarmReset(req, res, next) {
    const schema = Joi.object({
        instanceName: Joi.string().optional(),
        confirmReset: Joi.boolean().default(false)
    });
    
    const { error } = schema.validate(req.body);
    if (error) {
        return res.status(400).json({
            success: false,
            error: 'Swarm reset validation error',
            details: error.details[0].message
        });
    }
    
    next();
}

module.exports = router;
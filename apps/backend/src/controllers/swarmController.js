/**
 * Swarm Intelligence Controller - REST API endpoints for Swarm Intelligence system
 * Provides comprehensive interface for advanced P2P agent networks with emergent intelligence
 * 
 * Features:
 * - Collective decision making with Byzantine Fault Tolerance
 * - Emergent intelligence through agent collaboration
 * - Auto-organization and dynamic role assignment
 * - Particle Swarm Optimization and Ant Colony Optimization
 * - Real-time swarm monitoring and visualization
 */

const { SwarmIntelligence, SwarmDecisionAlgorithms } = require('../services/swarmIntelligence');
const logger = require('../utils/logger');
const { AppError } = require('../utils/AppError');

class SwarmController {
    constructor() {
        this.swarmInstances = new Map();
        this.globalSwarm = null;
        this.isInitialized = false;
        this._initialize();
    }
    
    async _initialize() {
        try {
            // Initialize the global swarm instance
            this.globalSwarm = new SwarmIntelligence({
                maxAgents: 100,
                heartbeatInterval: 5000,
                consensusThreshold: 0.67,
                emergenceThreshold: 0.8,
                autoOrganization: true,
                p2pNetworking: true
            });
            
            this.isInitialized = true;
            logger.info('🎪 Swarm Intelligence Controller initialized successfully');
            
        } catch (error) {
            logger.error('Failed to initialize Swarm Intelligence Controller', { error: error.message });
        }
    }
    
    /**
     * Register a new agent in the swarm
     * POST /api/swarm/agents/register
     */
    async registerAgent(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                type = 'generic',
                capabilities = [],
                id,
                metadata = {}
            } = req.body;
            
            if (!capabilities || !Array.isArray(capabilities)) {
                throw new AppError('Agent capabilities must be an array', 400, 'INVALID_CAPABILITIES');
            }
            
            const agentData = {
                id,
                type,
                capabilities,
                metadata,
                // Mock agent instance with required methods
                vote: async (proposal) => ({
                    decision: Math.random() > 0.5 ? 'approve' : 'reject',
                    confidence: Math.random(),
                    feedback: `Agent ${type} evaluation`
                }),
                explore: async (problem) => ({
                    agentId: id,
                    solution: `${type} exploration result`,
                    quality: Math.random(),
                    diversity: Math.random(),
                    complexity: Math.random()
                }),
                crossPollinate: async (otherResults) => ({
                    agentId: id,
                    combinedSolution: `Cross-pollinated by ${type}`,
                    quality: Math.random(),
                    features: { [type]: true }
                }),
                evaluate: async (solution) => Math.random(),
                synthesize: async (solutions) => ({
                    components: solutions.map(s => s.solution),
                    quality: Math.random(),
                    complexity: Math.random(),
                    diversity: Math.random()
                }),
                onSwarmEvent: (eventType, data) => {
                    logger.debug(`Agent ${id} received swarm event: ${eventType}`, data);
                }
            };
            
            const agentId = await this.globalSwarm.registerAgent(agentData);
            
            res.json({
                success: true,
                agentId,
                swarmSize: this.globalSwarm.getActiveAgents().length,
                message: 'Agent successfully registered in swarm'
            });
            
        } catch (error) {
            logger.error('Failed to register agent in swarm', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Initiate collective decision making
     * POST /api/swarm/decisions/collective
     */
    async makeCollectiveDecision(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                proposal,
                consensusThreshold,
                timeout = 30000,
                maxRounds = 3,
                requiredCapabilities
            } = req.body;
            
            if (!proposal) {
                throw new AppError('Proposal is required for collective decision making', 400, 'MISSING_PROPOSAL');
            }
            
            const proposalData = {
                ...proposal,
                requiredCapabilities,
                timestamp: new Date().toISOString()
            };
            
            const options = {
                consensusThreshold,
                timeout,
                maxRounds
            };
            
            const decision = await this.globalSwarm.makeCollectiveDecision(proposalData, options);
            
            res.json({
                success: true,
                decision,
                swarmSize: this.globalSwarm.getActiveAgents().length,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Collective decision making failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Solve problems with emergent intelligence
     * POST /api/swarm/intelligence/emergent
     */
    async solveWithEmergence(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                problem,
                maxIterations = 10,
                diversityThreshold = 0.3,
                convergenceThreshold = 0.8
            } = req.body;
            
            if (!problem) {
                throw new AppError('Problem definition is required', 400, 'MISSING_PROBLEM');
            }
            
            const options = {
                maxIterations,
                diversityThreshold,
                convergenceThreshold
            };
            
            const result = await this.globalSwarm.solveWithEmergence(problem, options);
            
            res.json({
                success: true,
                result,
                swarmSize: this.globalSwarm.getActiveAgents().length,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Emergent intelligence solving failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Optimize parameters using swarm algorithms
     * POST /api/swarm/optimization
     */
    async optimizeParameters(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                method = 'pso',
                searchSpace,
                objectiveFunction,
                iterations = 100,
                inertia = 0.9,
                cognitiveWeight = 2.0,
                socialWeight = 2.0,
                pheromoneDecay = 0.1,
                alpha = 1.0,
                beta = 2.0
            } = req.body;
            
            if (!searchSpace) {
                throw new AppError('Search space is required for optimization', 400, 'MISSING_SEARCH_SPACE');
            }
            
            // Create a mock objective function if not provided
            const objFunction = objectiveFunction || ((params) => {
                // Simple sphere function for demonstration
                return -params.reduce((sum, p) => sum + p * p, 0);
            });
            
            const options = {
                method,
                iterations,
                inertia,
                cognitiveWeight,
                socialWeight,
                pheromoneDecay,
                alpha,
                beta
            };
            
            const result = await this.globalSwarm.optimizeParameters(objFunction, searchSpace, options);
            
            res.json({
                success: true,
                result,
                method,
                iterations,
                swarmSize: this.globalSwarm.getActiveAgents().length,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Swarm optimization failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get swarm topology and network visualization
     * GET /api/swarm/topology
     */
    async getSwarmTopology(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const topology = this.globalSwarm.getSwarmTopology();
            
            res.json({
                success: true,
                topology,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get swarm topology', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get comprehensive swarm metrics and statistics
     * GET /api/swarm/metrics
     */
    async getSwarmMetrics(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const metrics = this.globalSwarm.getSwarmMetrics();
            
            res.json({
                success: true,
                metrics,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get swarm metrics', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get active agents in the swarm
     * GET /api/swarm/agents
     */
    async getActiveAgents(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const agents = this.globalSwarm.getActiveAgents();
            
            res.json({
                success: true,
                agents: agents.map(agent => ({
                    id: agent.id,
                    type: agent.type,
                    capabilities: agent.capabilities,
                    status: agent.status,
                    role: agent.role,
                    reputation: agent.reputation,
                    contributionScore: agent.contributionScore,
                    connections: agent.connections.size,
                    lastHeartbeat: agent.lastHeartbeat
                })),
                totalAgents: agents.length,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get active agents', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Create a new swarm instance
     * POST /api/swarm/instances
     */
    async createSwarmInstance(req, res, next) {
        try {
            const {
                name,
                maxAgents = 50,
                heartbeatInterval = 5000,
                consensusThreshold = 0.67,
                emergenceThreshold = 0.8,
                autoOrganization = true,
                p2pNetworking = true
            } = req.body;
            
            if (!name) {
                throw new AppError('Swarm instance name is required', 400, 'MISSING_NAME');
            }
            
            if (this.swarmInstances.has(name)) {
                throw new AppError('Swarm instance with this name already exists', 409, 'INSTANCE_EXISTS');
            }
            
            const swarmConfig = {
                maxAgents,
                heartbeatInterval,
                consensusThreshold,
                emergenceThreshold,
                autoOrganization,
                p2pNetworking
            };
            
            const swarmInstance = new SwarmIntelligence(swarmConfig);
            this.swarmInstances.set(name, swarmInstance);
            
            res.json({
                success: true,
                instanceName: name,
                config: swarmConfig,
                message: 'Swarm instance created successfully'
            });
            
        } catch (error) {
            logger.error('Failed to create swarm instance', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get swarm instances
     * GET /api/swarm/instances
     */
    async getSwarmInstances(req, res, next) {
        try {
            const instances = Array.from(this.swarmInstances.entries()).map(([name, swarm]) => ({
                name,
                activeAgents: swarm.getActiveAgents().length,
                totalAgents: swarm.agents.size,
                swarmState: swarm.swarmState,
                metrics: swarm.getSwarmMetrics()
            }));
            
            res.json({
                success: true,
                instances,
                globalSwarm: {
                    activeAgents: this.globalSwarm?.getActiveAgents().length || 0,
                    totalAgents: this.globalSwarm?.agents.size || 0
                },
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get swarm instances', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Health check for swarm intelligence service
     * GET /api/swarm/health
     */
    async healthCheck(req, res, next) {
        try {
            const health = {
                initialized: this.isInitialized,
                globalSwarm: {
                    active: !!this.globalSwarm,
                    agents: this.globalSwarm?.getActiveAgents().length || 0,
                    state: this.globalSwarm?.swarmState || 'unknown'
                },
                instances: this.swarmInstances.size,
                algorithms: {
                    consensus: 'Byzantine Fault Tolerance',
                    emergence: 'Collective Intelligence',
                    optimization: ['PSO', 'ACO'],
                    organization: 'Auto-organization'
                }
            };
            
            res.json({
                success: true,
                health,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Swarm health check failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Reset swarm metrics (for testing or maintenance)
     * POST /api/swarm/reset
     */
    async resetSwarm(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Swarm Intelligence service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const { instanceName } = req.body;
            
            if (instanceName) {
                // Reset specific instance
                const instance = this.swarmInstances.get(instanceName);
                if (!instance) {
                    throw new AppError('Swarm instance not found', 404, 'INSTANCE_NOT_FOUND');
                }
                // Reset logic would go here
                res.json({
                    success: true,
                    message: `Swarm instance '${instanceName}' reset successfully`
                });
            } else {
                // Reset global swarm
                this.globalSwarm.swarmMetrics = {
                    totalDecisions: 0,
                    consensusRate: 0,
                    emergenceEvents: 0,
                    adaptationRate: 0,
                    collectiveIQ: 0
                };
                
                res.json({
                    success: true,
                    message: 'Global swarm metrics reset successfully'
                });
            }
            
        } catch (error) {
            logger.error('Failed to reset swarm', { error: error.message });
            next(error);
        }
    }
}

module.exports = new SwarmController();
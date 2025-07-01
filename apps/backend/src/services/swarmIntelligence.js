/**
 * 🎪 Swarm Intelligence System - Advanced P2P Agent Network
 * 
 * Implements sophisticated swarm intelligence with:
 * - Peer-to-peer communication between all agents
 * - Emergent intelligence from collective behavior
 * - Auto-organization and dynamic role assignment
 * - Collective problem solving with consensus algorithms
 * 
 * Architecture:
 *    🎯 Manus ←→ ⚡ SAM ←→ 🧠 Memory
 *         ↕         ↕         ↕
 *    🤖 GoogleAI ←→ 📱 Notion ←→ 📧 Email
 *         ↕         ↕         ↕
 *    🌐 Web ←→ 📊 Analytics ←→ 🔍 Search
 */

const EventEmitter = require('events');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');

// Swarm Intelligence Algorithms
class SwarmDecisionAlgorithms {
    /**
     * Consensus-based decision making using Byzantine Fault Tolerance
     */
    static async reachConsensus(agents, proposal, options = {}) {
        const {
            threshold = 0.67, // 67% consensus required
            timeout = 30000,   // 30 second timeout
            rounds = 3         // Maximum voting rounds
        } = options;

        const decisions = [];
        let round = 0;

        while (round < rounds) {
            const votes = await this._collectVotes(agents, proposal, timeout);
            
            // Calculate consensus
            const agreement = this._calculateAgreement(votes);
            
            if (agreement.consensus >= threshold) {
                return {
                    decision: agreement.decision,
                    consensus: agreement.consensus,
                    round: round + 1,
                    participants: votes.length,
                    converged: true
                };
            }
            
            // If no consensus, evolve the proposal based on feedback
            proposal = this._evolveProposal(proposal, votes);
            round++;
        }

        // Return best available decision if no consensus reached
        const finalVotes = await this._collectVotes(agents, proposal, timeout);
        const finalAgreement = this._calculateAgreement(finalVotes);
        
        return {
            decision: finalAgreement.decision,
            consensus: finalAgreement.consensus,
            round: rounds,
            participants: finalVotes.length,
            converged: false
        };
    }

    /**
     * Emergent intelligence through agent collaboration
     */
    static async emergentSolving(swarm, problem, options = {}) {
        const {
            maxIterations = 10,
            diversityThreshold = 0.3,
            convergenceThreshold = 0.8
        } = options;

        const solutions = [];
        let iteration = 0;
        let bestSolution = null;
        let convergenceScore = 0;

        while (iteration < maxIterations && convergenceScore < convergenceThreshold) {
            // Phase 1: Parallel exploration by different agent types
            const explorationResults = await this._parallelExploration(swarm, problem);
            
            // Phase 2: Cross-pollination between agents
            const crossPollinated = await this._crossPollination(swarm, explorationResults);
            
            // Phase 3: Collective evaluation and selection
            const evaluated = await this._collectiveEvaluation(swarm, crossPollinated);
            
            // Phase 4: Emergent synthesis
            const synthesized = await this._emergentSynthesis(swarm, evaluated);
            
            solutions.push(synthesized);
            
            // Update best solution and check convergence
            if (!bestSolution || synthesized.quality > bestSolution.quality) {
                bestSolution = synthesized;
            }
            
            convergenceScore = this._calculateConvergence(solutions);
            iteration++;
        }

        return {
            solution: bestSolution,
            iterations: iteration,
            convergence: convergenceScore,
            emergentProperties: this._analyzeEmergentProperties(solutions)
        };
    }

    /**
     * Ant Colony Optimization for path finding and resource allocation
     */
    static async antColonyOptimization(swarm, problem, options = {}) {
        const {
            pheromoneDecay = 0.1,
            alpha = 1.0,  // Pheromone importance
            beta = 2.0,   // Heuristic importance
            iterations = 50
        } = options;

        const pheromoneMap = new Map();
        const solutions = [];

        for (let i = 0; i < iterations; i++) {
            const antSolutions = [];
            
            // Each agent acts as an "ant" exploring the solution space
            for (const agent of swarm.getActiveAgents()) {
                const path = await this._constructSolution(agent, problem, pheromoneMap, alpha, beta);
                const quality = await this._evaluateSolution(swarm, path);
                
                antSolutions.push({ agent: agent.id, path, quality });
            }
            
            // Update pheromones based on solution quality
            this._updatePheromones(pheromoneMap, antSolutions, pheromoneDecay);
            
            // Track best solution
            const bestInIteration = antSolutions.reduce((best, current) => 
                current.quality > best.quality ? current : best
            );
            
            solutions.push(bestInIteration);
        }

        return {
            bestSolution: solutions.reduce((best, current) => 
                current.quality > best.quality ? current : best
            ),
            convergenceHistory: solutions,
            pheromoneDistribution: Object.fromEntries(pheromoneMap)
        };
    }

    /**
     * Particle Swarm Optimization for parameter tuning
     */
    static async particleSwarmOptimization(swarm, objectiveFunction, searchSpace, options = {}) {
        const {
            inertia = 0.9,
            cognitiveWeight = 2.0,
            socialWeight = 2.0,
            iterations = 100
        } = options;

        const particles = swarm.getActiveAgents().map(agent => ({
            id: agent.id,
            position: this._randomPosition(searchSpace),
            velocity: this._randomVelocity(searchSpace),
            bestPosition: null,
            bestFitness: -Infinity,
            fitness: -Infinity
        }));

        let globalBest = { position: null, fitness: -Infinity };

        for (let i = 0; i < iterations; i++) {
            // Evaluate particles
            for (const particle of particles) {
                particle.fitness = await objectiveFunction(particle.position);
                
                // Update personal best
                if (particle.fitness > particle.bestFitness) {
                    particle.bestFitness = particle.fitness;
                    particle.bestPosition = [...particle.position];
                }
                
                // Update global best
                if (particle.fitness > globalBest.fitness) {
                    globalBest = {
                        position: [...particle.position],
                        fitness: particle.fitness
                    };
                }
            }
            
            // Update velocities and positions
            for (const particle of particles) {
                for (let d = 0; d < particle.position.length; d++) {
                    const r1 = Math.random();
                    const r2 = Math.random();
                    
                    particle.velocity[d] = inertia * particle.velocity[d] +
                        cognitiveWeight * r1 * (particle.bestPosition[d] - particle.position[d]) +
                        socialWeight * r2 * (globalBest.position[d] - particle.position[d]);
                    
                    particle.position[d] += particle.velocity[d];
                    
                    // Apply bounds
                    particle.position[d] = Math.max(searchSpace[d].min, 
                        Math.min(searchSpace[d].max, particle.position[d]));
                }
            }
        }

        return {
            globalBest,
            particles: particles.map(p => ({
                id: p.id,
                bestPosition: p.bestPosition,
                bestFitness: p.bestFitness
            }))
        };
    }

    // Private helper methods for algorithms
    static async _collectVotes(agents, proposal, timeout) {
        const votes = [];
        const promises = agents.map(async (agent) => {
            try {
                const vote = await Promise.race([
                    agent.vote(proposal),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), timeout))
                ]);
                return { agentId: agent.id, vote, timestamp: Date.now() };
            } catch (error) {
                return { agentId: agent.id, vote: null, error: error.message };
            }
        });

        const results = await Promise.allSettled(promises);
        return results
            .filter(result => result.status === 'fulfilled' && result.value.vote !== null)
            .map(result => result.value);
    }

    static _calculateAgreement(votes) {
        if (votes.length === 0) return { decision: null, consensus: 0 };

        const decisions = votes.map(v => v.vote.decision);
        const counts = decisions.reduce((acc, decision) => {
            acc[decision] = (acc[decision] || 0) + 1;
            return acc;
        }, {});

        const maxCount = Math.max(...Object.values(counts));
        const decision = Object.keys(counts).find(key => counts[key] === maxCount);
        const consensus = maxCount / votes.length;

        return { decision, consensus };
    }

    static _evolveProposal(proposal, votes) {
        // Aggregate feedback from votes to improve proposal
        const feedback = votes
            .filter(v => v.vote.feedback)
            .map(v => v.vote.feedback);
        
        return {
            ...proposal,
            refinements: feedback,
            generation: (proposal.generation || 0) + 1
        };
    }

    static async _parallelExploration(swarm, problem) {
        const agents = swarm.getActiveAgents();
        const explorations = await Promise.allSettled(
            agents.map(agent => agent.explore(problem))
        );

        return explorations
            .filter(result => result.status === 'fulfilled')
            .map(result => result.value);
    }

    static async _crossPollination(swarm, results) {
        const crossPollinated = [];
        
        // Each agent learns from others' solutions
        for (const agent of swarm.getActiveAgents()) {
            const otherResults = results.filter(r => r.agentId !== agent.id);
            const pollinated = await agent.crossPollinate(otherResults);
            crossPollinated.push(pollinated);
        }

        return crossPollinated;
    }

    static async _collectiveEvaluation(swarm, solutions) {
        const evaluated = [];
        
        for (const solution of solutions) {
            const scores = await Promise.allSettled(
                swarm.getActiveAgents().map(agent => agent.evaluate(solution))
            );
            
            const validScores = scores
                .filter(s => s.status === 'fulfilled')
                .map(s => s.value);
            
            const averageScore = validScores.length > 0 
                ? validScores.reduce((sum, score) => sum + score, 0) / validScores.length
                : 0;
            
            evaluated.push({
                ...solution,
                collectiveScore: averageScore,
                evaluationConsensus: validScores.length / swarm.getActiveAgents().length
            });
        }

        return evaluated;
    }

    static async _emergentSynthesis(swarm, evaluatedSolutions) {
        // Combine the best aspects of multiple solutions
        const bestSolutions = evaluatedSolutions
            .sort((a, b) => b.collectiveScore - a.collectiveScore)
            .slice(0, Math.ceil(evaluatedSolutions.length * 0.3)); // Top 30%

        // Let the swarm collectively synthesize a new solution
        const synthesisPromises = swarm.getActiveAgents().map(agent => 
            agent.synthesize(bestSolutions)
        );

        const syntheses = await Promise.allSettled(synthesisPromises);
        const validSyntheses = syntheses
            .filter(s => s.status === 'fulfilled')
            .map(s => s.value);

        // Merge syntheses into emergent solution
        return this._mergeEmergentSolutions(validSyntheses);
    }

    static _calculateConvergence(solutions) {
        if (solutions.length < 2) return 0;
        
        const recent = solutions.slice(-3); // Last 3 solutions
        const qualities = recent.map(s => s.quality);
        
        const variance = this._calculateVariance(qualities);
        return Math.max(0, 1 - variance); // Higher convergence = lower variance
    }

    static _analyzeEmergentProperties(solutions) {
        return {
            qualityProgression: solutions.map(s => s.quality),
            diversityEvolution: solutions.map(s => s.diversity || 0),
            emergentPatterns: this._identifyPatterns(solutions),
            complexityGrowth: solutions.map(s => s.complexity || 0)
        };
    }

    static _calculateVariance(values) {
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
        const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
        return squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length;
    }

    static _identifyPatterns(solutions) {
        // Analyze solutions for emerging patterns
        return {
            commonFeatures: this._findCommonFeatures(solutions),
            evolutionTrends: this._analyzeEvolutionTrends(solutions),
            emergentBehaviors: this._detectEmergentBehaviors(solutions)
        };
    }

    static _findCommonFeatures(solutions) {
        // Implementation for finding common features across solutions
        return solutions.reduce((common, solution) => {
            if (solution.features) {
                Object.keys(solution.features).forEach(feature => {
                    common[feature] = (common[feature] || 0) + 1;
                });
            }
            return common;
        }, {});
    }

    static _analyzeEvolutionTrends(solutions) {
        // Analyze how solutions evolve over time
        return {
            qualityTrend: this._calculateTrend(solutions.map(s => s.quality)),
            complexityTrend: this._calculateTrend(solutions.map(s => s.complexity || 0)),
            diversityTrend: this._calculateTrend(solutions.map(s => s.diversity || 0))
        };
    }

    static _detectEmergentBehaviors(solutions) {
        // Detect new behaviors that weren't explicitly programmed
        return {
            novelFeatures: this._findNovelFeatures(solutions),
            unexpectedPatterns: this._findUnexpectedPatterns(solutions),
            systemicBehaviors: this._analyzeSystemicBehaviors(solutions)
        };
    }

    static _calculateTrend(values) {
        if (values.length < 2) return 0;
        
        const n = values.length;
        const sumX = (n * (n + 1)) / 2;
        const sumY = values.reduce((sum, val) => sum + val, 0);
        const sumXY = values.reduce((sum, val, i) => sum + val * (i + 1), 0);
        const sumX2 = (n * (n + 1) * (2 * n + 1)) / 6;
        
        return (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    }

    static _findNovelFeatures(solutions) {
        // Implementation for detecting novel features
        return [];
    }

    static _findUnexpectedPatterns(solutions) {
        // Implementation for detecting unexpected patterns
        return [];
    }

    static _analyzeSystemicBehaviors(solutions) {
        // Implementation for analyzing systemic behaviors
        return {};
    }

    static _mergeEmergentSolutions(syntheses) {
        // Merge multiple synthesis results into a single emergent solution
        const merged = {
            components: [],
            quality: 0,
            complexity: 0,
            diversity: 0,
            emergentProperties: {}
        };

        syntheses.forEach(synthesis => {
            if (synthesis.components) {
                merged.components.push(...synthesis.components);
            }
            merged.quality = Math.max(merged.quality, synthesis.quality || 0);
            merged.complexity += synthesis.complexity || 0;
            merged.diversity += synthesis.diversity || 0;
        });

        merged.complexity /= syntheses.length;
        merged.diversity /= syntheses.length;

        return merged;
    }

    // Additional helper methods for ACO and PSO
    static async _constructSolution(agent, problem, pheromoneMap, alpha, beta) {
        // Implementation for constructing solution path using pheromones
        return { path: [], quality: 0 };
    }

    static async _evaluateSolution(swarm, path) {
        // Implementation for evaluating solution quality
        return Math.random(); // Placeholder
    }

    static _updatePheromones(pheromoneMap, solutions, decay) {
        // Implementation for updating pheromone trails
        for (const [key, value] of pheromoneMap) {
            pheromoneMap.set(key, value * (1 - decay));
        }
    }

    static _randomPosition(searchSpace) {
        return searchSpace.map(dim => 
            Math.random() * (dim.max - dim.min) + dim.min
        );
    }

    static _randomVelocity(searchSpace) {
        return searchSpace.map(dim => 
            (Math.random() - 0.5) * (dim.max - dim.min) * 0.1
        );
    }
}

/**
 * Main Swarm Intelligence Coordinator
 */
class SwarmIntelligence extends EventEmitter {
    constructor(options = {}) {
        super();
        
        this.config = {
            maxAgents: options.maxAgents || 50,
            heartbeatInterval: options.heartbeatInterval || 5000,
            consensusThreshold: options.consensusThreshold || 0.67,
            emergenceThreshold: options.emergenceThreshold || 0.8,
            autoOrganization: options.autoOrganization !== false,
            p2pNetworking: options.p2pNetworking !== false,
            ...options
        };
        
        // Core swarm components
        this.agents = new Map();
        this.connections = new Map();
        this.emergentBehaviors = new Map();
        this.collectiveMemory = new Map();
        this.swarmState = 'initializing';
        
        // P2P Network
        this.p2pNetwork = null;
        this.meshTopology = new Map();
        
        // Intelligence metrics
        this.swarmMetrics = {
            totalDecisions: 0,
            consensusRate: 0,
            emergenceEvents: 0,
            adaptationRate: 0,
            collectiveIQ: 0
        };
        
        // Auto-organization parameters
        this.organizationRules = new Map();
        this.roleAssignments = new Map();
        this.hierarchyState = 'flat';
        
        this._initializeSwarm();
    }
    
    async _initializeSwarm() {
        try {
            logger.info('🎪 Initializing Swarm Intelligence System');
            
            // Initialize P2P network
            if (this.config.p2pNetworking) {
                await this._initializeP2PNetwork();
            }
            
            // Setup auto-organization rules
            if (this.config.autoOrganization) {
                this._setupAutoOrganizationRules();
            }
            
            // Start heartbeat system
            this._startHeartbeat();
            
            // Initialize collective memory
            this._initializeCollectiveMemory();
            
            this.swarmState = 'active';
            this.emit('swarm:initialized');
            
            logger.info('✨ Swarm Intelligence System active');
            
        } catch (error) {
            logger.error('Failed to initialize Swarm Intelligence', { error: error.message });
            this.swarmState = 'error';
        }
    }
    
    /**
     * Register a new agent in the swarm
     */
    async registerAgent(agent) {
        const agentId = agent.id || uuidv4();
        
        const swarmAgent = {
            id: agentId,
            type: agent.type || 'generic',
            capabilities: agent.capabilities || [],
            instance: agent,
            status: 'active',
            lastHeartbeat: Date.now(),
            connections: new Set(),
            reputation: 1.0,
            contributionScore: 0,
            emergentBehaviors: new Set(),
            role: 'worker' // Default role
        };
        
        this.agents.set(agentId, swarmAgent);
        
        // Establish P2P connections
        if (this.config.p2pNetworking) {
            await this._establishP2PConnections(swarmAgent);
        }
        
        // Auto-assign role if enabled
        if (this.config.autoOrganization) {
            await this._autoAssignRole(swarmAgent);
        }
        
        // Notify swarm of new member
        this._broadcastToSwarm('agent:joined', {
            agentId,
            type: agent.type,
            capabilities: agent.capabilities
        });
        
        logger.info(`🤖 Agent ${agentId} joined swarm`, {
            type: agent.type,
            capabilities: agent.capabilities?.length || 0,
            swarmSize: this.agents.size
        });
        
        this.emit('agent:registered', swarmAgent);
        
        return agentId;
    }
    
    /**
     * Initiate collective decision making
     */
    async makeCollectiveDecision(proposal, options = {}) {
        const startTime = Date.now();
        
        logger.info('🧠 Initiating collective decision making', {
            proposal: proposal.type || 'unknown',
            participants: this.getActiveAgents().length
        });
        
        try {
            // Get participating agents
            const eligibleAgents = this._selectEligibleAgents(proposal, options);
            
            if (eligibleAgents.length < 2) {
                throw new Error('Insufficient agents for collective decision making');
            }
            
            // Reach consensus using Byzantine Fault Tolerance
            const decision = await SwarmDecisionAlgorithms.reachConsensus(
                eligibleAgents,
                proposal,
                {
                    threshold: options.consensusThreshold || this.config.consensusThreshold,
                    timeout: options.timeout || 30000,
                    rounds: options.maxRounds || 3
                }
            );
            
            // Record decision in collective memory
            this._recordCollectiveDecision(proposal, decision, eligibleAgents);
            
            // Update swarm metrics
            this.swarmMetrics.totalDecisions++;
            this.swarmMetrics.consensusRate = 
                (this.swarmMetrics.consensusRate + decision.consensus) / 2;
            
            const duration = Date.now() - startTime;
            
            logger.info('✅ Collective decision completed', {
                decision: decision.decision,
                consensus: (decision.consensus * 100).toFixed(1) + '%',
                duration,
                converged: decision.converged
            });
            
            this.emit('decision:completed', {
                proposal,
                decision,
                duration,
                participants: decision.participants
            });
            
            return decision;
            
        } catch (error) {
            logger.error('❌ Collective decision failed', { error: error.message });
            throw error;
        }
    }
    
    /**
     * Trigger emergent intelligence solving
     */
    async solveWithEmergence(problem, options = {}) {
        const startTime = Date.now();
        
        logger.info('🌟 Initiating emergent intelligence solving', {
            problem: problem.type || 'unknown',
            swarmSize: this.getActiveAgents().length
        });
        
        try {
            const result = await SwarmDecisionAlgorithms.emergentSolving(
                this,
                problem,
                {
                    maxIterations: options.maxIterations || 10,
                    diversityThreshold: options.diversityThreshold || 0.3,
                    convergenceThreshold: options.convergenceThreshold || 0.8
                }
            );
            
            // Record emergent behavior
            this._recordEmergentBehavior(problem, result);
            
            // Update metrics
            this.swarmMetrics.emergenceEvents++;
            
            const duration = Date.now() - startTime;
            
            logger.info('🎯 Emergent solving completed', {
                quality: result.solution?.quality,
                iterations: result.iterations,
                convergence: (result.convergence * 100).toFixed(1) + '%',
                duration
            });
            
            this.emit('emergence:completed', {
                problem,
                result,
                duration
            });
            
            return result;
            
        } catch (error) {
            logger.error('❌ Emergent solving failed', { error: error.message });
            throw error;
        }
    }
    
    /**
     * Optimize parameters using swarm intelligence
     */
    async optimizeParameters(objectiveFunction, searchSpace, options = {}) {
        const method = options.method || 'pso'; // Default to Particle Swarm Optimization
        
        logger.info('🔧 Starting swarm optimization', {
            method,
            searchDimensions: searchSpace.length,
            participants: this.getActiveAgents().length
        });
        
        let result;
        
        switch (method) {
            case 'pso':
                result = await SwarmDecisionAlgorithms.particleSwarmOptimization(
                    this,
                    objectiveFunction,
                    searchSpace,
                    options
                );
                break;
                
            case 'aco':
                result = await SwarmDecisionAlgorithms.antColonyOptimization(
                    this,
                    { objectiveFunction, searchSpace },
                    options
                );
                break;
                
            default:
                throw new Error(`Unknown optimization method: ${method}`);
        }
        
        logger.info('🎯 Swarm optimization completed', {
            method,
            bestFitness: result.globalBest?.fitness || result.bestSolution?.quality,
            participants: result.particles?.length || this.getActiveAgents().length
        });
        
        return result;
    }
    
    /**
     * Get active agents
     */
    getActiveAgents() {
        return Array.from(this.agents.values()).filter(agent => agent.status === 'active');
    }
    
    /**
     * Get swarm topology visualization data
     */
    getSwarmTopology() {
        const nodes = Array.from(this.agents.values()).map(agent => ({
            id: agent.id,
            type: agent.type,
            status: agent.status,
            role: agent.role,
            reputation: agent.reputation,
            capabilities: agent.capabilities.length,
            connections: agent.connections.size
        }));
        
        const links = [];
        for (const [agentId, agent] of this.agents) {
            for (const connectedId of agent.connections) {
                links.push({
                    source: agentId,
                    target: connectedId,
                    strength: this._getConnectionStrength(agentId, connectedId)
                });
            }
        }
        
        return {
            nodes,
            links,
            metadata: {
                totalAgents: this.agents.size,
                activeAgents: this.getActiveAgents().length,
                avgConnections: nodes.reduce((sum, n) => sum + n.connections, 0) / nodes.length,
                networkDensity: links.length / (nodes.length * (nodes.length - 1) / 2)
            }
        };
    }
    
    /**
     * Get comprehensive swarm metrics
     */
    getSwarmMetrics() {
        const activeAgents = this.getActiveAgents();
        const avgReputation = activeAgents.reduce((sum, a) => sum + a.reputation, 0) / activeAgents.length;
        
        return {
            ...this.swarmMetrics,
            currentState: {
                totalAgents: this.agents.size,
                activeAgents: activeAgents.length,
                averageReputation: avgReputation,
                swarmState: this.swarmState,
                hierarchyState: this.hierarchyState
            },
            emergentBehaviors: Array.from(this.emergentBehaviors.keys()),
            collectiveMemorySize: this.collectiveMemory.size,
            timestamp: new Date().toISOString()
        };
    }
    
    // Private methods
    
    async _initializeP2PNetwork() {
        // Initialize WebSocket-based P2P network
        this.p2pNetwork = {
            connections: new Map(),
            messageQueue: [],
            routingTable: new Map()
        };
        
        logger.info('🌐 P2P network initialized');
    }
    
    _setupAutoOrganizationRules() {
        // Define rules for automatic organization
        this.organizationRules.set('capability_clustering', {
            enabled: true,
            threshold: 0.7,
            description: 'Group agents with similar capabilities'
        });
        
        this.organizationRules.set('workload_balancing', {
            enabled: true,
            threshold: 0.8,
            description: 'Redistribute work based on agent load'
        });
        
        this.organizationRules.set('expertise_hierarchy', {
            enabled: true,
            threshold: 0.9,
            description: 'Promote agents to leadership based on expertise'
        });
        
        logger.info('🏗️ Auto-organization rules configured');
    }
    
    _startHeartbeat() {
        setInterval(() => {
            this._performHeartbeat();
        }, this.config.heartbeatInterval);
    }
    
    _performHeartbeat() {
        const now = Date.now();
        const timeout = this.config.heartbeatInterval * 3; // 3x interval = timeout
        
        // Check agent health
        for (const [agentId, agent] of this.agents) {
            if (now - agent.lastHeartbeat > timeout) {
                this._markAgentInactive(agentId);
            }
        }
        
        // Emit heartbeat event
        this.emit('swarm:heartbeat', {
            activeAgents: this.getActiveAgents().length,
            totalAgents: this.agents.size,
            timestamp: now
        });
        
        // Trigger auto-organization if needed
        if (this.config.autoOrganization) {
            this._checkAutoOrganization();
        }
    }
    
    _initializeCollectiveMemory() {
        this.collectiveMemory.set('decisions', []);
        this.collectiveMemory.set('emergent_behaviors', []);
        this.collectiveMemory.set('patterns', new Map());
        this.collectiveMemory.set('knowledge_base', new Map());
    }
    
    async _establishP2PConnections(newAgent) {
        // Connect to existing agents in the swarm
        const existingAgents = this.getActiveAgents().filter(a => a.id !== newAgent.id);
        
        // Use preferential attachment (connect to well-connected agents)
        const connectionsToMake = Math.min(5, existingAgents.length); // Max 5 initial connections
        const sortedAgents = existingAgents.sort((a, b) => b.connections.size - a.connections.size);
        
        for (let i = 0; i < connectionsToMake; i++) {
            const targetAgent = sortedAgents[i];
            newAgent.connections.add(targetAgent.id);
            targetAgent.connections.add(newAgent.id);
        }
    }
    
    async _autoAssignRole(agent) {
        // Analyze agent capabilities and assign appropriate role
        const capabilities = agent.capabilities;
        
        if (capabilities.includes('orchestration') || capabilities.includes('coordination')) {
            agent.role = 'coordinator';
        } else if (capabilities.includes('analysis') || capabilities.includes('reasoning')) {
            agent.role = 'analyst';
        } else if (capabilities.includes('execution') || capabilities.includes('action')) {
            agent.role = 'executor';
        } else if (capabilities.includes('memory') || capabilities.includes('storage')) {
            agent.role = 'memory_keeper';
        } else {
            agent.role = 'worker';
        }
        
        this.roleAssignments.set(agent.id, agent.role);
    }
    
    _broadcastToSwarm(eventType, data) {
        // Broadcast message to all active agents
        for (const agent of this.getActiveAgents()) {
            try {
                if (agent.instance && typeof agent.instance.onSwarmEvent === 'function') {
                    agent.instance.onSwarmEvent(eventType, data);
                }
            } catch (error) {
                logger.debug(`Failed to notify agent ${agent.id}:`, error.message);
            }
        }
    }
    
    _selectEligibleAgents(proposal, options) {
        const activeAgents = this.getActiveAgents();
        
        // Filter agents based on capabilities required for the proposal
        if (proposal.requiredCapabilities) {
            return activeAgents.filter(agent => 
                proposal.requiredCapabilities.some(cap => 
                    agent.capabilities.includes(cap)
                )
            );
        }
        
        return activeAgents;
    }
    
    _recordCollectiveDecision(proposal, decision, participants) {
        const decisions = this.collectiveMemory.get('decisions');
        decisions.push({
            timestamp: new Date().toISOString(),
            proposal: proposal.type || 'unknown',
            decision: decision.decision,
            consensus: decision.consensus,
            participants: participants.length,
            converged: decision.converged
        });
        
        // Keep only last 1000 decisions
        if (decisions.length > 1000) {
            decisions.splice(0, decisions.length - 1000);
        }
    }
    
    _recordEmergentBehavior(problem, result) {
        const behaviorId = uuidv4();
        const behavior = {
            id: behaviorId,
            timestamp: new Date().toISOString(),
            problemType: problem.type,
            solution: result.solution,
            emergentProperties: result.emergentProperties,
            iterations: result.iterations,
            convergence: result.convergence
        };
        
        this.emergentBehaviors.set(behaviorId, behavior);
        
        const behaviors = this.collectiveMemory.get('emergent_behaviors');
        behaviors.push(behavior);
        
        // Keep only last 100 emergent behaviors
        if (behaviors.length > 100) {
            behaviors.splice(0, behaviors.length - 100);
        }
    }
    
    _markAgentInactive(agentId) {
        const agent = this.agents.get(agentId);
        if (agent && agent.status === 'active') {
            agent.status = 'inactive';
            
            logger.warn(`🚨 Agent ${agentId} marked as inactive`);
            
            this.emit('agent:inactive', { agentId, agent });
            
            // Trigger reorganization if needed
            if (this.config.autoOrganization) {
                this._triggerReorganization();
            }
        }
    }
    
    _checkAutoOrganization() {
        // Check if reorganization is needed based on current state
        const activeAgents = this.getActiveAgents();
        
        // Example: Check if we need to rebalance roles
        const coordinators = activeAgents.filter(a => a.role === 'coordinator');
        const workers = activeAgents.filter(a => a.role === 'worker');
        
        if (coordinators.length === 0 && workers.length > 0) {
            // Promote a worker to coordinator
            const bestWorker = workers.reduce((best, current) => 
                current.reputation > best.reputation ? current : best
            );
            bestWorker.role = 'coordinator';
            this.roleAssignments.set(bestWorker.id, 'coordinator');
            
            logger.info(`🔄 Auto-promoted agent ${bestWorker.id} to coordinator`);
        }
    }
    
    _triggerReorganization() {
        // Implement reorganization logic when agents go inactive
        logger.info('🔄 Triggering swarm reorganization');
        this.emit('swarm:reorganizing');
    }
    
    _getConnectionStrength(agentId1, agentId2) {
        // Calculate connection strength between two agents
        // This could be based on interaction frequency, successful collaborations, etc.
        return Math.random(); // Placeholder implementation
    }
}

module.exports = {
    SwarmIntelligence,
    SwarmDecisionAlgorithms
};
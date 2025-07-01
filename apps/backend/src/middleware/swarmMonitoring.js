/**
 * Swarm Intelligence Monitoring Middleware - Enhanced monitoring for swarm operations
 * Provides comprehensive observability for swarm intelligence systems
 * 
 * Features:
 * - Real-time swarm metrics collection
 * - Agent performance tracking
 * - Decision quality analysis
 * - Emergence pattern detection
 * - Network topology monitoring
 * - Cost and efficiency analysis
 */

const logger = require('../utils/logger');
const { v4: uuidv4 } = require('uuid');
const EventEmitter = require('events');

// Langwatch integration (optional)
let langwatch;
try {
    langwatch = require('langwatch');
} catch (error) {
    logger.debug('Langwatch not available for swarm monitoring');
}

class SwarmMonitoring extends EventEmitter {
    constructor() {
        super();
        
        this.metrics = {
            totalOperations: 0,
            successfulOperations: 0,
            failedOperations: 0,
            totalAgents: 0,
            activeDecisions: 0,
            emergenceEvents: 0,
            optimizationRuns: 0,
            consensusSuccessRate: 0,
            averageConvergenceTime: 0,
            networkDensity: 0,
            adaptabilityScore: 0
        };
        
        this.agentMetrics = new Map();
        this.decisionHistory = [];
        this.emergencePatterns = [];
        this.optimizationResults = [];
        this.networkTopologyHistory = [];
        this.activeOperations = new Map();
        
        this.thresholds = {
            lowConsensusRate: 0.5,
            slowConvergence: 30000, // 30 seconds
            networkFragmentation: 0.3,
            agentInactivityTimeout: 60000 // 1 minute
        };
        
        this.startPeriodicAnalysis();
    }
    
    /**
     * Track the start of a swarm operation
     */
    trackOperationStart(operationType, operationData) {
        const operationId = operationData.operationId || uuidv4();
        const startTime = Date.now();
        
        const tracking = {
            operationId,
            type: operationType,
            startTime,
            data: operationData,
            agents: operationData.agents || [],
            langwatchTrace: null
        };
        
        // Start Langwatch trace if available
        if (langwatch && process.env.LANGWATCH_API_KEY) {
            try {
                const trace = langwatch.trace({
                    id: operationId,
                    metadata: {
                        provider: 'swarm_intelligence',
                        operation_type: operationType,
                        agent_count: tracking.agents.length,
                        swarm_size: operationData.swarmSize || 0
                    }
                });
                tracking.langwatchTrace = trace;
            } catch (error) {
                logger.debug('Failed to start Langwatch trace for swarm operation', { error: error.message });
            }
        }
        
        this.activeOperations.set(operationId, tracking);
        this.metrics.totalOperations++;
        
        logger.info('Swarm operation started', {
            operationId,
            type: operationType,
            agentCount: tracking.agents.length,
            swarmSize: operationData.swarmSize
        });
        
        this.emit('operation:started', tracking);
        
        return operationId;
    }
    
    /**
     * Track the completion of a swarm operation
     */
    trackOperationComplete(operationId, result) {
        const tracking = this.activeOperations.get(operationId);
        if (!tracking) {
            logger.warn('Operation tracking data not found', { operationId });
            return;
        }
        
        const duration = Date.now() - tracking.startTime;
        const success = result.success !== false;
        
        // Update metrics
        if (success) {
            this.metrics.successfulOperations++;
        } else {
            this.metrics.failedOperations++;
        }
        
        // Process specific operation types
        switch (tracking.type) {
            case 'collective_decision':
                this._processDecisionResult(tracking, result, duration);
                break;
            case 'emergent_intelligence':
                this._processEmergenceResult(tracking, result, duration);
                break;
            case 'optimization':
                this._processOptimizationResult(tracking, result, duration);
                break;
            case 'agent_registration':
                this._processAgentRegistration(tracking, result);
                break;
        }
        
        // Complete Langwatch trace
        if (tracking.langwatchTrace) {
            try {
                tracking.langwatchTrace.end({
                    output: result,
                    metadata: {
                        duration,
                        success,
                        agents_involved: tracking.agents.length
                    }
                });
            } catch (error) {
                logger.debug('Failed to end Langwatch trace', { error: error.message });
            }
        }
        
        logger.info('Swarm operation completed', {
            operationId,
            type: tracking.type,
            duration,
            success,
            agentCount: tracking.agents.length
        });
        
        this.emit('operation:completed', {
            ...tracking,
            result,
            duration,
            success
        });
        
        // Clean up
        this.activeOperations.delete(operationId);
        
        return { tracking, result, duration, success };
    }
    
    /**
     * Track agent performance and contribution
     */
    trackAgentPerformance(agentId, performance) {
        if (!this.agentMetrics.has(agentId)) {
            this.agentMetrics.set(agentId, {
                totalContributions: 0,
                successfulContributions: 0,
                averageResponseTime: 0,
                reputationScore: 1.0,
                specializations: new Set(),
                connectionQuality: 0,
                lastActivity: Date.now()
            });
        }
        
        const metrics = this.agentMetrics.get(agentId);
        metrics.totalContributions++;
        
        if (performance.success) {
            metrics.successfulContributions++;
        }
        
        // Update average response time
        if (performance.responseTime) {
            metrics.averageResponseTime = 
                (metrics.averageResponseTime * (metrics.totalContributions - 1) + performance.responseTime) 
                / metrics.totalContributions;
        }
        
        // Update reputation based on performance
        const successRate = metrics.successfulContributions / metrics.totalContributions;
        metrics.reputationScore = successRate * (performance.quality || 1.0);
        
        // Track specializations
        if (performance.capabilities) {
            performance.capabilities.forEach(cap => metrics.specializations.add(cap));
        }
        
        metrics.lastActivity = Date.now();
        
        this.emit('agent:performance_updated', { agentId, metrics, performance });
    }
    
    /**
     * Detect and analyze emergence patterns
     */
    analyzeEmergencePatterns() {
        const recentEmergence = this.emergencePatterns.slice(-10);
        
        if (recentEmergence.length < 3) return null;
        
        const patterns = {
            convergenceAcceleration: this._detectConvergenceAcceleration(recentEmergence),
            qualityImprovement: this._detectQualityImprovement(recentEmergence),
            complexityEvolution: this._detectComplexityEvolution(recentEmergence),
            noveltyGeneration: this._detectNoveltyGeneration(recentEmergence)
        };
        
        logger.info('Emergence patterns analyzed', patterns);
        this.emit('emergence:patterns_detected', patterns);
        
        return patterns;
    }
    
    /**
     * Monitor network topology and connectivity
     */
    monitorNetworkTopology(topology) {
        const analysis = {
            timestamp: new Date().toISOString(),
            nodeCount: topology.nodes.length,
            edgeCount: topology.links.length,
            averageConnections: topology.metadata.avgConnections,
            networkDensity: topology.metadata.networkDensity,
            clusters: this._detectClusters(topology),
            centralityMeasures: this._calculateCentrality(topology),
            fragmentationRisk: this._assessFragmentationRisk(topology)
        };
        
        this.networkTopologyHistory.push(analysis);
        
        // Keep only last 100 topology snapshots
        if (this.networkTopologyHistory.length > 100) {
            this.networkTopologyHistory = this.networkTopologyHistory.slice(-100);
        }
        
        this.metrics.networkDensity = analysis.networkDensity;
        
        // Check for fragmentation alerts
        if (analysis.fragmentationRisk > this.thresholds.networkFragmentation) {
            logger.warn('Network fragmentation risk detected', analysis);
            this.emit('network:fragmentation_risk', analysis);
        }
        
        this.emit('network:topology_updated', analysis);
        
        return analysis;
    }
    
    /**
     * Get comprehensive monitoring statistics
     */
    getStatistics() {
        const now = Date.now();
        const oneHourAgo = now - 60 * 60 * 1000;
        
        // Recent operations
        const recentDecisions = this.decisionHistory.filter(d => 
            new Date(d.timestamp).getTime() > oneHourAgo
        );
        
        // Agent statistics
        const agentStats = Array.from(this.agentMetrics.entries()).map(([id, metrics]) => ({
            id,
            contributions: metrics.totalContributions,
            successRate: metrics.totalContributions > 0 
                ? (metrics.successfulContributions / metrics.totalContributions * 100).toFixed(2) + '%'
                : '0%',
            reputation: metrics.reputationScore.toFixed(3),
            avgResponseTime: Math.round(metrics.averageResponseTime),
            specializations: Array.from(metrics.specializations),
            isActive: (now - metrics.lastActivity) < this.thresholds.agentInactivityTimeout
        }));
        
        return {
            overview: {
                totalOperations: this.metrics.totalOperations,
                successfulOperations: this.metrics.successfulOperations,
                failedOperations: this.metrics.failedOperations,
                successRate: this.metrics.totalOperations > 0 
                    ? (this.metrics.successfulOperations / this.metrics.totalOperations * 100).toFixed(2) + '%'
                    : '0%',
                activeOperations: this.activeOperations.size
            },
            
            swarm: {
                totalAgents: this.metrics.totalAgents,
                activeAgents: agentStats.filter(a => a.isActive).length,
                emergenceEvents: this.metrics.emergenceEvents,
                optimizationRuns: this.metrics.optimizationRuns,
                networkDensity: this.metrics.networkDensity.toFixed(3),
                adaptabilityScore: this.metrics.adaptabilityScore.toFixed(3)
            },
            
            decisions: {
                total: this.decisionHistory.length,
                recentHour: recentDecisions.length,
                consensusSuccessRate: (this.metrics.consensusSuccessRate * 100).toFixed(2) + '%',
                averageConvergenceTime: Math.round(this.metrics.averageConvergenceTime) + 'ms'
            },
            
            agents: agentStats,
            
            emergence: {
                totalEvents: this.emergencePatterns.length,
                recentPatterns: this.emergencePatterns.slice(-5),
                patterns: this.analyzeEmergencePatterns()
            },
            
            network: {
                currentTopology: this.networkTopologyHistory.slice(-1)[0],
                topologyHistory: this.networkTopologyHistory.slice(-10)
            },
            
            alerts: this._generateAlerts()
        };
    }
    
    /**
     * Reset monitoring metrics
     */
    resetMetrics() {
        this.metrics = {
            totalOperations: 0,
            successfulOperations: 0,
            failedOperations: 0,
            totalAgents: 0,
            activeDecisions: 0,
            emergenceEvents: 0,
            optimizationRuns: 0,
            consensusSuccessRate: 0,
            averageConvergenceTime: 0,
            networkDensity: 0,
            adaptabilityScore: 0
        };
        
        this.agentMetrics.clear();
        this.decisionHistory = [];
        this.emergencePatterns = [];
        this.optimizationResults = [];
        this.networkTopologyHistory = [];
        this.activeOperations.clear();
        
        logger.info('Swarm monitoring metrics reset');
        this.emit('metrics:reset');
    }
    
    // Private helper methods
    
    _processDecisionResult(tracking, result, duration) {
        const decision = {
            operationId: tracking.operationId,
            timestamp: new Date().toISOString(),
            duration,
            consensus: result.decision?.consensus || 0,
            converged: result.decision?.converged || false,
            participants: result.decision?.participants || 0,
            proposal: tracking.data.proposal?.type || 'unknown'
        };
        
        this.decisionHistory.push(decision);
        
        // Keep only last 1000 decisions
        if (this.decisionHistory.length > 1000) {
            this.decisionHistory = this.decisionHistory.slice(-1000);
        }
        
        // Update consensus metrics
        const consensusDecisions = this.decisionHistory.filter(d => d.converged);
        this.metrics.consensusSuccessRate = consensusDecisions.length / this.decisionHistory.length;
        
        const avgConvergence = this.decisionHistory
            .filter(d => d.converged)
            .reduce((sum, d) => sum + d.duration, 0) / consensusDecisions.length;
        this.metrics.averageConvergenceTime = avgConvergence || 0;
    }
    
    _processEmergenceResult(tracking, result, duration) {
        const emergence = {
            operationId: tracking.operationId,
            timestamp: new Date().toISOString(),
            duration,
            iterations: result.result?.iterations || 0,
            convergence: result.result?.convergence || 0,
            quality: result.result?.solution?.quality || 0,
            emergentProperties: result.result?.emergentProperties || {},
            problemType: tracking.data.problem?.type || 'unknown'
        };
        
        this.emergencePatterns.push(emergence);
        this.metrics.emergenceEvents++;
        
        // Keep only last 100 emergence events
        if (this.emergencePatterns.length > 100) {
            this.emergencePatterns = this.emergencePatterns.slice(-100);
        }
    }
    
    _processOptimizationResult(tracking, result, duration) {
        const optimization = {
            operationId: tracking.operationId,
            timestamp: new Date().toISOString(),
            duration,
            method: tracking.data.method || 'unknown',
            bestFitness: result.result?.globalBest?.fitness || result.result?.bestSolution?.quality || 0,
            iterations: tracking.data.iterations || 0,
            convergence: result.result?.convergence || 0
        };
        
        this.optimizationResults.push(optimization);
        this.metrics.optimizationRuns++;
        
        // Keep only last 100 optimization runs
        if (this.optimizationResults.length > 100) {
            this.optimizationResults = this.optimizationResults.slice(-100);
        }
    }
    
    _processAgentRegistration(tracking, result) {
        if (result.success) {
            this.metrics.totalAgents++;
        }
    }
    
    _detectConvergenceAcceleration(patterns) {
        if (patterns.length < 3) return false;
        
        const recentIterations = patterns.slice(-3).map(p => p.iterations);
        return recentIterations[2] < recentIterations[1] && recentIterations[1] < recentIterations[0];
    }
    
    _detectQualityImprovement(patterns) {
        if (patterns.length < 3) return false;
        
        const recentQualities = patterns.slice(-3).map(p => p.quality);
        return recentQualities[2] > recentQualities[1] && recentQualities[1] > recentQualities[0];
    }
    
    _detectComplexityEvolution(patterns) {
        // Analyze if solutions are becoming more sophisticated
        return patterns.slice(-5).some(p => 
            p.emergentProperties.complexityGrowth && 
            p.emergentProperties.complexityGrowth.some(c => c > 0.8)
        );
    }
    
    _detectNoveltyGeneration(patterns) {
        // Check for novel features in recent patterns
        return patterns.slice(-3).some(p => 
            p.emergentProperties.emergentPatterns?.novelFeatures?.length > 0
        );
    }
    
    _detectClusters(topology) {
        // Simple clustering based on connection density
        const clusters = [];
        const visited = new Set();
        
        topology.nodes.forEach(node => {
            if (!visited.has(node.id)) {
                const cluster = this._dfsCluster(node, topology, visited);
                if (cluster.length > 1) {
                    clusters.push(cluster);
                }
            }
        });
        
        return clusters;
    }
    
    _dfsCluster(startNode, topology, visited) {
        const cluster = [];
        const stack = [startNode];
        
        while (stack.length > 0) {
            const node = stack.pop();
            if (!visited.has(node.id)) {
                visited.add(node.id);
                cluster.push(node.id);
                
                // Find connected nodes
                const connections = topology.links
                    .filter(link => link.source === node.id || link.target === node.id)
                    .map(link => link.source === node.id ? link.target : link.source);
                
                connections.forEach(connectedId => {
                    const connectedNode = topology.nodes.find(n => n.id === connectedId);
                    if (connectedNode && !visited.has(connectedId)) {
                        stack.push(connectedNode);
                    }
                });
            }
        }
        
        return cluster;
    }
    
    _calculateCentrality(topology) {
        // Simple degree centrality calculation
        const centrality = new Map();
        
        topology.nodes.forEach(node => {
            const degree = topology.links.filter(link => 
                link.source === node.id || link.target === node.id
            ).length;
            centrality.set(node.id, degree);
        });
        
        return Object.fromEntries(centrality);
    }
    
    _assessFragmentationRisk(topology) {
        const clusters = this._detectClusters(topology);
        const largestCluster = Math.max(...clusters.map(c => c.length), 0);
        return 1 - (largestCluster / topology.nodes.length);
    }
    
    _generateAlerts() {
        const alerts = [];
        
        // Low consensus rate alert
        if (this.metrics.consensusSuccessRate < this.thresholds.lowConsensusRate) {
            alerts.push({
                type: 'consensus',
                level: 'warning',
                message: `Low consensus success rate: ${(this.metrics.consensusSuccessRate * 100).toFixed(2)}%`,
                timestamp: new Date().toISOString()
            });
        }
        
        // Slow convergence alert
        if (this.metrics.averageConvergenceTime > this.thresholds.slowConvergence) {
            alerts.push({
                type: 'performance',
                level: 'warning',
                message: `Slow convergence detected: ${Math.round(this.metrics.averageConvergenceTime)}ms average`,
                timestamp: new Date().toISOString()
            });
        }
        
        // Network fragmentation alert
        if (this.metrics.networkDensity < this.thresholds.networkFragmentation) {
            alerts.push({
                type: 'network',
                level: 'critical',
                message: `Network fragmentation risk: density ${this.metrics.networkDensity.toFixed(3)}`,
                timestamp: new Date().toISOString()
            });
        }
        
        return alerts;
    }
    
    startPeriodicAnalysis() {
        // Analyze patterns every 2 minutes
        setInterval(() => {
            this.analyzeEmergencePatterns();
        }, 120000);
        
        // Log summary every 5 minutes
        setInterval(() => {
            if (this.metrics.totalOperations > 0) {
                logger.info('Swarm monitoring periodic report', {
                    totalOperations: this.metrics.totalOperations,
                    successRate: (this.metrics.successfulOperations / this.metrics.totalOperations * 100).toFixed(2) + '%',
                    activeOperations: this.activeOperations.size,
                    totalAgents: this.metrics.totalAgents,
                    emergenceEvents: this.metrics.emergenceEvents
                });
            }
        }, 300000);
    }
}

// Create singleton instance
const swarmMonitoring = new SwarmMonitoring();

module.exports = {
    swarmMonitoring,
    trackSwarmOperation: (operationType, operationData) => swarmMonitoring.trackOperationStart(operationType, operationData),
    trackSwarmCompletion: (operationId, result) => swarmMonitoring.trackOperationComplete(operationId, result),
    trackAgentPerformance: (agentId, performance) => swarmMonitoring.trackAgentPerformance(agentId, performance),
    monitorNetworkTopology: (topology) => swarmMonitoring.monitorNetworkTopology(topology)
};
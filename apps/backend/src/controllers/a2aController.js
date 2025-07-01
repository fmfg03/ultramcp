/**
 * A2A Controller - HTTP endpoints for Agent-to-Agent communication
 * Provides REST API interface for A2A protocol integration
 */

const A2AService = require('../services/a2aService');
const logger = require('../utils/logger');
const { AppError } = require('../utils/AppError');

class A2AController {
    constructor() {
        this.a2aService = null;
    }
    
    /**
     * Initialize A2A service
     */
    async initializeA2AService(config = {}) {
        if (!this.a2aService) {
            this.a2aService = new A2AService(config);
            await this.a2aService.initialize();
        }
        return this.a2aService;
    }
    
    /**
     * Handle incoming A2A task delegation
     * POST /api/a2a/task
     */
    async handleTaskDelegation(req, res, next) {
        try {
            const { task_type, payload, requester_id, priority, timeout } = req.body;
            
            if (!task_type || !payload) {
                throw new AppError('Missing required fields: task_type, payload', 400, 'INVALID_A2A_REQUEST');
            }
            
            // Ensure A2A service is initialized
            if (!this.a2aService) {
                await this.initializeA2AService();
            }
            
            const taskId = require('uuid').v4();
            const startTime = Date.now();
            
            logger.info('Processing A2A task delegation', {
                taskId,
                taskType: task_type,
                requesterId: requester_id,
                priority
            });
            
            // Process the task based on type
            let result;
            switch (task_type) {
                case 'mcp_orchestration':
                    result = await this._handleMCPOrchestration(payload);
                    break;
                    
                case 'multi_agent_workflow':
                    result = await this._handleMultiAgentWorkflow(payload);
                    break;
                    
                case 'agent_discovery':
                    result = await this._handleAgentDiscovery(payload);
                    break;
                    
                case 'resource_allocation':
                    result = await this._handleResourceAllocation(payload);
                    break;
                    
                case 'health_check':
                    result = await this._handleHealthCheck(payload);
                    break;
                    
                default:
                    // Delegate to MCP orchestration for unknown types
                    result = await this._delegateToMCP(payload);
                    break;
            }
            
            const duration = Date.now() - startTime;
            
            res.json({
                success: true,
                task_id: taskId,
                task_type,
                result,
                duration,
                processed_by: 'supermcp_orchestrator',
                timestamp: new Date().toISOString()
            });
            
            logger.info('A2A task completed successfully', {
                taskId,
                taskType: task_type,
                duration
            });
            
        } catch (error) {
            logger.error('A2A task delegation failed', {
                error: error.message,
                taskType: req.body?.task_type
            });
            next(error);
        }
    }
    
    /**
     * Delegate task to another A2A agent
     * POST /api/a2a/delegate
     */
    async delegateToAgent(req, res, next) {
        try {
            const { target_capabilities, task_data, options = {} } = req.body;
            
            if (!target_capabilities || !task_data) {
                throw new AppError('Missing required fields: target_capabilities, task_data', 400, 'INVALID_DELEGATION_REQUEST');
            }
            
            if (!this.a2aService) {
                await this.initializeA2AService();
            }
            
            const result = await this.a2aService.delegateTask(
                target_capabilities,
                task_data,
                options
            );
            
            res.json({
                success: true,
                delegation_result: result,
                target_capabilities,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('A2A delegation failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Discover available A2A agents
     * GET /api/a2a/discover
     */
    async discoverAgents(req, res, next) {
        try {
            const { capabilities } = req.query;
            const capabilitiesArray = capabilities ? capabilities.split(',') : null;
            
            if (!this.a2aService) {
                await this.initializeA2AService();
            }
            
            const agents = await this.a2aService.discoverAgents(capabilitiesArray);
            
            res.json({
                success: true,
                agents,
                discovery_timestamp: new Date().toISOString(),
                total_agents: agents.length
            });
            
        } catch (error) {
            logger.error('Agent discovery failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get A2A service status and metrics
     * GET /api/a2a/status
     */
    async getStatus(req, res, next) {
        try {
            if (!this.a2aService) {
                return res.json({
                    success: true,
                    status: 'not_initialized',
                    message: 'A2A service not yet initialized'
                });
            }
            
            const status = this.a2aService.getStatus();
            const agentLoads = await this.a2aService.getAgentLoads();
            
            res.json({
                success: true,
                status,
                agent_loads: agentLoads,
                system_metrics: {
                    uptime: process.uptime(),
                    memory_usage: process.memoryUsage(),
                    cpu_usage: process.cpuUsage()
                }
            });
            
        } catch (error) {
            logger.error('Failed to get A2A status', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Initialize A2A service manually
     * POST /api/a2a/initialize
     */
    async initializeService(req, res, next) {
        try {
            const config = req.body || {};
            
            if (this.a2aService) {
                return res.json({
                    success: true,
                    message: 'A2A service already initialized',
                    status: this.a2aService.getStatus()
                });
            }
            
            this.a2aService = new A2AService(config);
            await this.a2aService.initialize();
            
            res.json({
                success: true,
                message: 'A2A service initialized successfully',
                status: this.a2aService.getStatus()
            });
            
        } catch (error) {
            logger.error('A2A service initialization failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Shutdown A2A service
     * POST /api/a2a/shutdown
     */
    async shutdownService(req, res, next) {
        try {
            if (!this.a2aService) {
                return res.json({
                    success: true,
                    message: 'A2A service was not running'
                });
            }
            
            await this.a2aService.shutdown();
            this.a2aService = null;
            
            res.json({
                success: true,
                message: 'A2A service shutdown completed'
            });
            
        } catch (error) {
            logger.error('A2A service shutdown failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get agent performance metrics
     * GET /api/a2a/metrics
     */
    async getMetrics(req, res, next) {
        try {
            if (!this.a2aService) {
                throw new AppError('A2A service not initialized', 400, 'SERVICE_NOT_INITIALIZED');
            }
            
            const agentLoads = await this.a2aService.getAgentLoads();
            const status = this.a2aService.getStatus();
            
            // Calculate aggregate metrics
            const aggregateMetrics = {
                total_agents: Object.keys(agentLoads).length,
                healthy_agents: Object.values(agentLoads).filter(a => a.status === 'healthy').length,
                average_load: Object.values(agentLoads).reduce((sum, a) => sum + (a.load_score || 0), 0) / Object.keys(agentLoads).length,
                total_active_tasks: Object.values(agentLoads).reduce((sum, a) => sum + (a.active_tasks || 0), 0),
                system_load: status.load_score,
                uptime: status.uptime
            };
            
            res.json({
                success: true,
                metrics: {
                    aggregate: aggregateMetrics,
                    agents: agentLoads,
                    service_status: status
                },
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get A2A metrics', { error: error.message });
            next(error);
        }
    }
    
    // Private helper methods
    
    async _handleMCPOrchestration(payload) {
        const orchestrationService = require('../services/orchestrationService');
        
        return await orchestrationService.processTask({
            message: payload.message || payload.query,
            sessionId: payload.session_id || require('uuid').v4(),
            context: { ...payload.context, a2a_enabled: true },
            enableA2A: true
        });
    }
    
    async _handleMultiAgentWorkflow(payload) {
        const { workflow_steps, coordination_type = 'sequential' } = payload;
        const results = [];
        
        if (coordination_type === 'parallel') {
            // Execute all steps in parallel
            const promises = workflow_steps.map(async (step) => {
                if (step.delegate_to_a2a) {
                    return await this.a2aService.delegateTask(
                        step.required_capabilities,
                        step.task_data
                    );
                } else {
                    return await this._delegateToMCP(step.task_data);
                }
            });
            
            const parallelResults = await Promise.allSettled(promises);
            parallelResults.forEach((result, index) => {
                results.push({
                    step_id: workflow_steps[index].id || index,
                    status: result.status,
                    result: result.value || result.reason
                });
            });
        } else {
            // Execute sequentially
            for (const step of workflow_steps) {
                try {
                    let stepResult;
                    if (step.delegate_to_a2a) {
                        stepResult = await this.a2aService.delegateTask(
                            step.required_capabilities,
                            step.task_data
                        );
                    } else {
                        stepResult = await this._delegateToMCP(step.task_data);
                    }
                    
                    results.push({
                        step_id: step.id || results.length,
                        status: 'fulfilled',
                        result: stepResult
                    });
                } catch (error) {
                    results.push({
                        step_id: step.id || results.length,
                        status: 'rejected',
                        error: error.message
                    });
                }
            }
        }
        
        return {
            workflow_completed: true,
            coordination_type,
            steps_executed: workflow_steps.length,
            results
        };
    }
    
    async _handleAgentDiscovery(payload) {
        const { capabilities, include_load_info = true } = payload;
        
        const agents = await this.a2aService.discoverAgents(capabilities);
        
        if (include_load_info) {
            const agentLoads = await this.a2aService.getAgentLoads();
            agents.forEach(agent => {
                agent.load_info = agentLoads[agent.agent_id] || { status: 'unknown' };
            });
        }
        
        return {
            discovery_completed: true,
            agents,
            total_discovered: agents.length,
            capabilities_filter: capabilities
        };
    }
    
    async _handleResourceAllocation(payload) {
        // This would integrate with the resource allocation logic in A2AService
        const agentLoads = await this.a2aService.getAgentLoads();
        
        const allocation = this.a2aService._calculateLoadBalancedAllocation(
            agentLoads,
            payload.constraints || {}
        );
        
        return {
            resource_allocation_completed: true,
            allocation,
            current_loads: agentLoads
        };
    }
    
    async _handleHealthCheck(payload) {
        const status = this.a2aService.getStatus();
        const agentLoads = await this.a2aService.getAgentLoads();
        
        return {
            health_check_completed: true,
            service_status: status,
            agent_health: agentLoads,
            overall_health: status.is_registered && status.websocket_connected ? 'healthy' : 'degraded'
        };
    }
    
    async _delegateToMCP(payload) {
        const orchestrationService = require('../services/orchestrationService');
        
        return await orchestrationService.processTask({
            message: payload.message || payload.query || 'Execute task',
            sessionId: payload.session_id || require('uuid').v4(),
            context: payload.context || {}
        });
    }
}

module.exports = new A2AController();
/**
 * Agent-to-Agent (A2A) Service Integration for SUPERmcp
 * Provides comprehensive A2A protocol support within the MCP ecosystem
 * 
 * Features:
 * - Agent discovery and registration
 * - Task delegation and routing
 * - Load balancing and failover
 * - Real-time communication
 * - Monitoring and analytics
 */

const axios = require('axios');
const WebSocket = require('ws');
const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');
const { retryOperation } = require('../utils/retryUtils');

class A2AService extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            a2aServerUrl: config.a2aServerUrl || 'http://localhost:8200',
            agentId: config.agentId || 'supermcp_orchestrator',
            agentName: config.agentName || 'SUPERmcp Orchestrator',
            capabilities: config.capabilities || [
                'orchestration', 'mcp_integration', 'multi_agent_coordination',
                'workflow_management', 'resource_allocation', 'monitoring'
            ],
            heartbeatInterval: config.heartbeatInterval || 30000,
            maxRetries: config.maxRetries || 3,
            taskTimeout: config.taskTimeout || 300000, // 5 minutes
            ...config
        };
        
        this.isRegistered = false;
        this.connectedAgents = new Map();
        this.activeTasks = new Map();
        this.agentMetrics = new Map();
        this.wsConnection = null;
        this.heartbeatTimer = null;
        
        this._setupEventHandlers();
    }
    
    /**
     * Initialize A2A service and register with central server
     */
    async initialize() {
        try {
            logger.info('Initializing A2A service...', { agentId: this.config.agentId });
            
            // Register agent with A2A server
            await this.registerAgent();
            
            // Establish WebSocket connection for real-time communication
            await this.connectWebSocket();
            
            // Start heartbeat mechanism
            this.startHeartbeat();
            
            // Discover existing agents
            await this.discoverAgents();
            
            logger.info('A2A service initialized successfully', {
                agentId: this.config.agentId,
                registeredAgents: this.connectedAgents.size
            });
            
            this.emit('initialized');
            return true;
            
        } catch (error) {
            logger.error('Failed to initialize A2A service', { error: error.message });
            throw error;
        }
    }
    
    /**
     * Register this agent with the A2A central server
     */
    async registerAgent() {
        const agentCard = {
            agent_id: this.config.agentId,
            name: this.config.agentName,
            version: '2.0.0',
            capabilities: this.config.capabilities,
            protocols: ['mcp', 'a2a', 'websocket'],
            endpoints: {
                a2a: `http://localhost:3000/api/a2a`,
                health: `http://localhost:3000/health`,
                websocket: `ws://localhost:3000/ws/a2a`
            },
            metadata: {
                description: 'SUPERmcp orchestrator with full MCP and A2A integration',
                max_concurrent_tasks: 1000,
                specialization: 'orchestration',
                mcp_version: '3.1.0',
                langwatch_enabled: true,
                voice_enabled: true
            }
        };
        
        try {
            const response = await retryOperation(async () => {
                return await axios.post(`${this.config.a2aServerUrl}/agents/register`, agentCard, {
                    timeout: 10000,
                    headers: { 'Content-Type': 'application/json' }
                });
            }, this.config.maxRetries);
            
            if (response.status === 200) {
                this.isRegistered = true;
                logger.info('Agent registered successfully with A2A server', {
                    agentId: this.config.agentId,
                    serverUrl: this.config.a2aServerUrl
                });
                return true;
            }
        } catch (error) {
            logger.error('Failed to register agent with A2A server', {
                error: error.message,
                agentId: this.config.agentId
            });
            throw error;
        }
    }
    
    /**
     * Establish WebSocket connection for real-time A2A communication
     */
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                const wsUrl = `${this.config.a2aServerUrl.replace('http', 'ws')}/ws/agents/${this.config.agentId}`;
                this.wsConnection = new WebSocket(wsUrl);
                
                this.wsConnection.on('open', () => {
                    logger.info('WebSocket connection established', { agentId: this.config.agentId });
                    this.emit('websocket_connected');
                    resolve();
                });
                
                this.wsConnection.on('message', (data) => {
                    this._handleWebSocketMessage(JSON.parse(data.toString()));
                });
                
                this.wsConnection.on('close', () => {
                    logger.warn('WebSocket connection closed', { agentId: this.config.agentId });
                    this.emit('websocket_disconnected');
                    // Attempt reconnection after 5 seconds
                    setTimeout(() => this.connectWebSocket(), 5000);
                });
                
                this.wsConnection.on('error', (error) => {
                    logger.error('WebSocket connection error', { error: error.message });
                    reject(error);
                });
                
            } catch (error) {
                reject(error);
            }
        });
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    _handleWebSocketMessage(message) {
        const { type, payload, task_id } = message;
        
        switch (type) {
            case 'task_delegation':
                this._handleTaskDelegation(payload, task_id);
                break;
            case 'agent_discovery':
                this._handleAgentDiscovery(payload);
                break;
            case 'heartbeat_response':
                this._handleHeartbeatResponse(payload);
                break;
            case 'system_notification':
                this._handleSystemNotification(payload);
                break;
            default:
                logger.debug('Unknown WebSocket message type', { type, payload });
        }
    }
    
    /**
     * Handle incoming task delegation via A2A
     */
    async _handleTaskDelegation(taskData, taskId) {
        try {
            logger.info('Received A2A task delegation', { taskId, taskType: taskData.task_type });
            
            const startTime = Date.now();
            const task = {
                id: taskId,
                type: taskData.task_type,
                payload: taskData.payload,
                requester: taskData.requester_id,
                priority: taskData.priority || 5,
                timeout: taskData.timeout || this.config.taskTimeout,
                startTime
            };
            
            this.activeTasks.set(taskId, task);
            
            // Process task based on type
            let result;
            switch (task.type) {
                case 'mcp_orchestration':
                    result = await this._handleMCPOrchestration(task.payload);
                    break;
                case 'multi_agent_workflow':
                    result = await this._handleMultiAgentWorkflow(task.payload);
                    break;
                case 'resource_allocation':
                    result = await this._handleResourceAllocation(task.payload);
                    break;
                case 'agent_coordination':
                    result = await this._handleAgentCoordination(task.payload);
                    break;
                default:
                    // Delegate to MCP system for unknown task types
                    result = await this._delegateToMCP(task);
            }
            
            // Record task completion metrics
            const duration = Date.now() - startTime;
            this._recordTaskMetrics(taskId, task.type, duration, true);
            
            // Send result back via WebSocket
            this._sendWebSocketMessage({
                type: 'task_result',
                task_id: taskId,
                result: {
                    success: true,
                    data: result,
                    duration,
                    agent_id: this.config.agentId
                }
            });
            
            this.activeTasks.delete(taskId);
            
        } catch (error) {
            logger.error('Failed to handle A2A task delegation', {
                error: error.message,
                taskId,
                taskType: taskData.task_type
            });
            
            this._recordTaskMetrics(taskId, taskData.task_type, Date.now() - Date.now(), false);
            
            this._sendWebSocketMessage({
                type: 'task_result',
                task_id: taskId,
                result: {
                    success: false,
                    error: error.message,
                    agent_id: this.config.agentId
                }
            });
            
            this.activeTasks.delete(taskId);
        }
    }
    
    /**
     * Handle MCP orchestration tasks
     */
    async _handleMCPOrchestration(payload) {
        // Integrate with existing MCP orchestration service
        const orchestrationService = require('./orchestrationService');
        
        return await orchestrationService.processTask({
            message: payload.message || payload.query,
            sessionId: payload.session_id || uuidv4(),
            context: payload.context || {},
            enableA2A: true,
            a2aService: this
        });
    }
    
    /**
     * Handle multi-agent workflow coordination
     */
    async _handleMultiAgentWorkflow(payload) {
        const { workflow_steps, coordination_type } = payload;
        const results = [];
        
        for (const step of workflow_steps) {
            const { agent_capabilities, task_data, execution_mode } = step;
            
            if (execution_mode === 'delegate') {
                // Delegate to appropriate A2A agent
                const delegationResult = await this.delegateTask(agent_capabilities, task_data);
                results.push({
                    step_id: step.id,
                    delegated: true,
                    result: delegationResult
                });
            } else {
                // Execute locally via MCP
                const localResult = await this._delegateToMCP({ payload: task_data });
                results.push({
                    step_id: step.id,
                    delegated: false,
                    result: localResult
                });
            }
        }
        
        return {
            workflow_completed: true,
            coordination_type,
            steps_executed: workflow_steps.length,
            results
        };
    }
    
    /**
     * Handle resource allocation tasks
     */
    async _handleResourceAllocation(payload) {
        const { resource_type, allocation_strategy, constraints } = payload;
        
        // Get current agent loads
        const agentLoads = await this.getAgentLoads();
        
        // Calculate optimal allocation based on strategy
        let allocation;
        switch (allocation_strategy) {
            case 'load_balanced':
                allocation = this._calculateLoadBalancedAllocation(agentLoads, constraints);
                break;
            case 'capability_based':
                allocation = this._calculateCapabilityBasedAllocation(agentLoads, constraints);
                break;
            case 'priority_based':
                allocation = this._calculatePriorityBasedAllocation(agentLoads, constraints);
                break;
            default:
                allocation = this._calculateDefaultAllocation(agentLoads, constraints);
        }
        
        return {
            resource_allocation_completed: true,
            strategy: allocation_strategy,
            allocation,
            agent_loads: agentLoads
        };
    }
    
    /**
     * Handle agent coordination tasks
     */
    async _handleAgentCoordination(payload) {
        const { coordination_plan, sync_mode } = payload;
        const coordinationResults = {};
        
        if (sync_mode === 'parallel') {
            // Execute all agent tasks in parallel
            const promises = coordination_plan.agents.map(async (agentSpec) => {
                const result = await this.delegateTask(
                    agentSpec.capabilities,
                    agentSpec.task
                );
                return { agent_id: agentSpec.agent_id, result };
            });
            
            const results = await Promise.allSettled(promises);
            results.forEach((result, index) => {
                const agentId = coordination_plan.agents[index].agent_id;
                coordinationResults[agentId] = {
                    status: result.status,
                    value: result.value || result.reason
                };
            });
        } else {
            // Execute sequentially
            for (const agentSpec of coordination_plan.agents) {
                const result = await this.delegateTask(
                    agentSpec.capabilities,
                    agentSpec.task
                );
                coordinationResults[agentSpec.agent_id] = result;
            }
        }
        
        return {
            coordination_completed: true,
            sync_mode,
            agents_coordinated: coordination_plan.agents.length,
            results: coordinationResults
        };
    }
    
    /**
     * Delegate task to another A2A agent
     */
    async delegateTask(targetCapabilities, taskData, options = {}) {
        try {
            const taskId = uuidv4();
            const delegationPayload = {
                task_id: taskId,
                task_type: taskData.task_type || 'general',
                payload: taskData,
                requester_id: this.config.agentId,
                required_capabilities: targetCapabilities,
                priority: options.priority || 5,
                timeout: options.timeout || this.config.taskTimeout,
                delegation_timestamp: new Date().toISOString()
            };
            
            const response = await retryOperation(async () => {
                return await axios.post(
                    `${this.config.a2aServerUrl}/a2a/delegate`,
                    delegationPayload,
                    { timeout: options.timeout || this.config.taskTimeout }
                );
            }, this.config.maxRetries);
            
            if (response.status === 200) {
                logger.info('Task delegated successfully via A2A', {
                    taskId,
                    targetCapabilities,
                    assignedAgent: response.data.assigned_agent
                });
                
                return response.data;
            }
            
        } catch (error) {
            logger.error('Failed to delegate task via A2A', {
                error: error.message,
                targetCapabilities,
                taskData: taskData.task_type
            });
            
            // Fallback to local MCP execution
            logger.info('Falling back to local MCP execution');
            return await this._delegateToMCP({ payload: taskData });
        }
    }
    
    /**
     * Delegate to existing MCP system
     */
    async _delegateToMCP(task) {
        try {
            const orchestrationService = require('./orchestrationService');
            return await orchestrationService.processTask({
                message: task.payload.message || task.payload.query || 'Execute task',
                sessionId: task.payload.session_id || uuidv4(),
                context: task.payload.context || {}
            });
        } catch (error) {
            logger.error('MCP delegation failed', { error: error.message });
            return {
                success: false,
                error: `MCP delegation failed: ${error.message}`,
                fallback_executed: true
            };
        }
    }
    
    /**
     * Discover available A2A agents
     */
    async discoverAgents(capabilities = null) {
        try {
            const discoveryPayload = {
                requester_id: this.config.agentId,
                capabilities: capabilities || this.config.capabilities
            };
            
            const response = await axios.post(
                `${this.config.a2aServerUrl}/a2a/discover`,
                discoveryPayload,
                { timeout: 10000 }
            );
            
            if (response.status === 200) {
                const agents = response.data.agents || [];
                this.connectedAgents.clear();
                
                agents.forEach(agent => {
                    this.connectedAgents.set(agent.agent_id, {
                        ...agent,
                        last_seen: new Date(),
                        status: 'available'
                    });
                });
                
                logger.info('Agent discovery completed', {
                    discoveredAgents: agents.length,
                    agentIds: agents.map(a => a.agent_id)
                });
                
                this.emit('agents_discovered', agents);
                return agents;
            }
            
        } catch (error) {
            logger.error('Agent discovery failed', { error: error.message });
            return [];
        }
    }
    
    /**
     * Get current load metrics for all connected agents
     */
    async getAgentLoads() {
        const loads = {};
        
        for (const [agentId, agentInfo] of this.connectedAgents) {
            try {
                const response = await axios.get(
                    `${agentInfo.endpoints?.health || agentInfo.endpoint}/health`,
                    { timeout: 5000 }
                );
                
                loads[agentId] = {
                    status: response.data.status,
                    load_score: response.data.load_score || 0,
                    active_tasks: response.data.active_tasks || 0,
                    capabilities: agentInfo.capabilities,
                    last_heartbeat: agentInfo.last_seen
                };
            } catch (error) {
                loads[agentId] = {
                    status: 'unreachable',
                    load_score: 1.0,
                    error: error.message
                };
            }
        }
        
        return loads;
    }
    
    /**
     * Start heartbeat mechanism
     */
    startHeartbeat() {
        this.heartbeatTimer = setInterval(async () => {
            await this.sendHeartbeat();
        }, this.config.heartbeatInterval);
        
        logger.debug('Heartbeat mechanism started', {
            interval: this.config.heartbeatInterval
        });
    }
    
    /**
     * Send heartbeat to A2A server
     */
    async sendHeartbeat() {
        try {
            const heartbeatData = {
                agent_id: this.config.agentId,
                load_score: this.calculateLoadScore(),
                active_tasks: this.activeTasks.size,
                connected_agents: this.connectedAgents.size,
                status: 'healthy',
                timestamp: new Date().toISOString()
            };
            
            await axios.post(
                `${this.config.a2aServerUrl}/agents/${this.config.agentId}/heartbeat`,
                heartbeatData,
                { timeout: 5000 }
            );
            
            logger.debug('Heartbeat sent successfully', {
                loadScore: heartbeatData.load_score,
                activeTasks: heartbeatData.active_tasks
            });
            
        } catch (error) {
            logger.debug('Heartbeat failed', { error: error.message });
        }
    }
    
    /**
     * Calculate current load score
     */
    calculateLoadScore() {
        const maxTasks = 100; // Configurable maximum
        const currentLoad = this.activeTasks.size / maxTasks;
        return Math.min(currentLoad, 1.0);
    }
    
    /**
     * Record task execution metrics
     */
    _recordTaskMetrics(taskId, taskType, duration, success) {
        const metrics = {
            task_id: taskId,
            task_type: taskType,
            duration,
            success,
            timestamp: new Date().toISOString(),
            agent_id: this.config.agentId
        };
        
        this.agentMetrics.set(taskId, metrics);
        
        // Emit metrics event for external monitoring
        this.emit('task_metrics', metrics);
        
        logger.debug('Task metrics recorded', metrics);
    }
    
    /**
     * Send WebSocket message
     */
    _sendWebSocketMessage(message) {
        if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
            this.wsConnection.send(JSON.stringify(message));
        }
    }
    
    /**
     * Setup event handlers
     */
    _setupEventHandlers() {
        this.on('task_metrics', (metrics) => {
            // Integration with monitoring system
            logger.info('A2A task completed', {
                taskType: metrics.task_type,
                duration: metrics.duration,
                success: metrics.success
            });
        });
        
        this.on('agents_discovered', (agents) => {
            logger.info('A2A agent discovery update', {
                totalAgents: agents.length,
                newAgents: agents.filter(a => !this.connectedAgents.has(a.agent_id)).length
            });
        });
    }
    
    /**
     * Resource allocation calculation methods
     */
    _calculateLoadBalancedAllocation(agentLoads, constraints) {
        // Sort agents by load score (ascending)
        const sortedAgents = Object.entries(agentLoads)
            .sort(([,a], [,b]) => a.load_score - b.load_score)
            .filter(([,agent]) => agent.status === 'healthy');
            
        return {
            strategy: 'load_balanced',
            recommended_agents: sortedAgents.slice(0, constraints.max_agents || 3),
            load_distribution: sortedAgents.map(([id, agent]) => ({
                agent_id: id,
                current_load: agent.load_score,
                recommended_allocation: Math.max(0, 1 - agent.load_score)
            }))
        };
    }
    
    _calculateCapabilityBasedAllocation(agentLoads, constraints) {
        const requiredCapabilities = constraints.required_capabilities || [];
        const matchingAgents = Object.entries(agentLoads)
            .filter(([id, agent]) => {
                return agent.capabilities && 
                       requiredCapabilities.some(cap => agent.capabilities.includes(cap));
            })
            .sort(([,a], [,b]) => a.load_score - b.load_score);
            
        return {
            strategy: 'capability_based',
            matching_agents: matchingAgents,
            capability_coverage: requiredCapabilities.map(cap => ({
                capability: cap,
                available_agents: matchingAgents.filter(([,agent]) => 
                    agent.capabilities.includes(cap)).length
            }))
        };
    }
    
    _calculatePriorityBasedAllocation(agentLoads, constraints) {
        const priority = constraints.priority || 5;
        const priorityFactors = {
            1: 0.9, // High priority gets best agents
            5: 0.5, // Normal priority
            10: 0.1 // Low priority gets remaining capacity
        };
        
        const factor = priorityFactors[priority] || 0.5;
        const availableAgents = Object.entries(agentLoads)
            .filter(([,agent]) => agent.load_score < factor)
            .sort(([,a], [,b]) => a.load_score - b.load_score);
            
        return {
            strategy: 'priority_based',
            priority_level: priority,
            allocation_factor: factor,
            available_agents: availableAgents
        };
    }
    
    _calculateDefaultAllocation(agentLoads, constraints) {
        return this._calculateLoadBalancedAllocation(agentLoads, constraints);
    }
    
    /**
     * Cleanup resources
     */
    async shutdown() {
        logger.info('Shutting down A2A service', { agentId: this.config.agentId });
        
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }
        
        if (this.wsConnection) {
            this.wsConnection.close();
        }
        
        // Cancel active tasks
        for (const [taskId, task] of this.activeTasks) {
            logger.warn('Cancelling active task during shutdown', { taskId, taskType: task.type });
        }
        
        this.activeTasks.clear();
        this.connectedAgents.clear();
        
        this.emit('shutdown');
    }
    
    /**
     * Get service status and metrics
     */
    getStatus() {
        return {
            agent_id: this.config.agentId,
            is_registered: this.isRegistered,
            connected_agents: this.connectedAgents.size,
            active_tasks: this.activeTasks.size,
            load_score: this.calculateLoadScore(),
            uptime: process.uptime(),
            metrics_count: this.agentMetrics.size,
            websocket_connected: this.wsConnection?.readyState === WebSocket.OPEN,
            last_heartbeat: new Date().toISOString()
        };
    }
}

module.exports = A2AService;
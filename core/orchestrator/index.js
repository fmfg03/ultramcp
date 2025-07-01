#!/usr/bin/env node
/**
 * UltraMCP Core Orchestrator
 * 
 * The main orchestration engine that connects all UltraMCP components
 * into a cohesive, event-driven system with intelligent workflow coordination.
 */

const EventBus = require('./eventBus');
const ServiceRegistry = require('./serviceRegistry');
const WorkflowEngine = require('./workflowEngine');
const StateManager = require('./stateManager');
const ContextManager = require('./contextManager');
const PluginLoader = require('./pluginLoader');
const { generateTaskId, loadConfig } = require('../utils');

class UltraMCPOrchestrator {
    constructor(config = {}) {
        this.config = {
            mode: config.mode || 'development',
            maxConcurrentTasks: config.maxConcurrentTasks || 100,
            defaultTimeout: config.defaultTimeout || 300000, // 5 minutes
            healthMonitoring: {
                interval: 30000, // 30 seconds
                retryAttempts: 3,
                ...config.healthMonitoring
            },
            ...config
        };

        // Core components
        this.eventBus = new EventBus(this.config.eventBus);
        this.serviceRegistry = new ServiceRegistry(this.eventBus);
        this.workflowEngine = new WorkflowEngine(this.serviceRegistry, this.eventBus);
        this.stateManager = new StateManager(this.config.stateManager);
        this.contextManager = new ContextManager();
        this.pluginLoader = new PluginLoader(this);

        // State tracking
        this.initialized = false;
        this.activeTasks = new Map();
        this.metrics = {
            tasksProcessed: 0,
            tasksSucceeded: 0,
            tasksFailed: 0,
            averageProcessingTime: 0,
            startTime: Date.now()
        };

        this.setupEventListeners();
        this.startHealthMonitoring();
    }

    /**
     * Initialize the orchestrator and all components
     */
    async initialize() {
        try {
            console.log('🚀 Initializing UltraMCP Orchestrator...');

            // 1. Load all services
            console.log('📡 Discovering services...');
            await this.serviceRegistry.discoverServices();
            
            // 2. Load plugins
            console.log('🔌 Loading plugins...');
            await this.pluginLoader.loadPlugins();
            
            // 3. Initialize workflow definitions
            console.log('⚡ Loading workflows...');
            await this.workflowEngine.loadWorkflows();
            
            // 4. Initialize state management
            console.log('💾 Initializing state management...');
            await this.stateManager.initialize();

            this.initialized = true;
            this.eventBus.emit('orchestrator.ready', {
                services: this.serviceRegistry.getServiceCount(),
                workflows: this.workflowEngine.getWorkflowCount(),
                plugins: this.pluginLoader.getPluginCount()
            });

            console.log('✅ UltraMCP Orchestrator initialized successfully');
            
            return {
                status: 'ready',
                services: this.serviceRegistry.getServiceCount(),
                workflows: this.workflowEngine.getWorkflowCount(),
                plugins: this.pluginLoader.getPluginCount()
            };

        } catch (error) {
            console.error('❌ Failed to initialize UltraMCP Orchestrator:', error);
            this.eventBus.emit('orchestrator.initialization.failed', { error: error.message });
            throw error;
        }
    }

    /**
     * Process a task through the orchestration system
     */
    async processTask(task, userContext = {}) {
        if (!this.initialized) {
            throw new Error('Orchestrator not initialized');
        }

        const taskId = task.id || generateTaskId();
        const context = this.contextManager.createContext(taskId, userContext);
        
        // Check concurrent task limit
        if (this.activeTasks.size >= this.config.maxConcurrentTasks) {
            throw new Error('Maximum concurrent tasks limit reached');
        }

        this.activeTasks.set(taskId, {
            task,
            context,
            startTime: Date.now(),
            status: 'processing'
        });

        try {
            // 1. Task preprocessing and validation
            this.eventBus.emitTaskEvent(taskId, 'received', { task, context });
            const validatedTask = await this.preprocessTask(task, context);
            
            // 2. Workflow selection
            this.eventBus.emitTaskEvent(taskId, 'workflow.selecting', {});
            const workflow = await this.workflowEngine.selectWorkflow(validatedTask, context);
            
            // 3. Execute workflow
            this.eventBus.emitTaskEvent(taskId, 'workflow.started', { 
                workflowId: workflow.id,
                workflowName: workflow.name 
            });
            
            const result = await Promise.race([
                this.workflowEngine.execute(workflow, validatedTask, context),
                this.createTimeoutPromise(taskId)
            ]);
            
            // 4. Post-processing and result formatting
            const finalResult = await this.postprocessResult(result, context);
            
            // 5. Update metrics and cleanup
            this.updateMetrics(taskId, true, Date.now() - this.activeTasks.get(taskId).startTime);
            this.eventBus.emitTaskEvent(taskId, 'completed', { result: finalResult });
            
            return finalResult;
            
        } catch (error) {
            this.updateMetrics(taskId, false, Date.now() - this.activeTasks.get(taskId).startTime);
            this.eventBus.emitTaskEvent(taskId, 'failed', { 
                error: error.message,
                code: error.code || 'EXECUTION_ERROR'
            });
            
            // Add error to context for debugging
            this.contextManager.addError(taskId, error);
            
            throw this.createStandardError(error, taskId);
            
        } finally {
            this.activeTasks.delete(taskId);
            
            // Schedule context cleanup (delayed to allow for result retrieval)
            setTimeout(() => {
                this.contextManager.cleanup(taskId);
            }, 60000); // 1 minute delay
        }
    }

    /**
     * Preprocess and validate task input
     */
    async preprocessTask(task, context) {
        // Validate required fields
        if (!task.content && !task.message && !task.input) {
            throw new Error('Task must contain content, message, or input field');
        }

        // Normalize task format
        const normalizedTask = {
            id: task.id || context.taskId,
            type: task.type || 'general',
            content: task.content || task.message || task.input,
            context: task.context || {},
            workflowId: task.workflowId,
            participants: task.participants || [],
            tools: task.tools || [],
            metadata: {
                source: context.request?.userAgent || 'unknown',
                timestamp: new Date().toISOString(),
                ...task.metadata
            }
        };

        // Add preprocessing step to context
        this.contextManager.addExecutionStep(context.taskId, {
            step: 'preprocessing',
            action: 'task_normalized',
            details: { originalType: task.type, normalizedType: normalizedTask.type }
        });

        return normalizedTask;
    }

    /**
     * Post-process result before returning to user
     */
    async postprocessResult(result, context) {
        // Add execution metrics
        const metrics = this.contextManager.getExecutionMetrics(context.taskId);
        
        const finalResult = {
            success: true,
            data: result,
            metadata: {
                taskId: context.taskId,
                executionTime: metrics.totalDuration,
                servicesUsed: metrics.serviceCount,
                stepsCompleted: metrics.stepCount,
                successRate: metrics.successRate,
                timestamp: new Date().toISOString()
            }
        };

        // Store result in state for potential retrieval
        this.stateManager.setTask(context.taskId, 'result', finalResult);

        return finalResult;
    }

    /**
     * Create timeout promise for task execution
     */
    createTimeoutPromise(taskId) {
        return new Promise((_, reject) => {
            setTimeout(() => {
                reject(new Error(`Task ${taskId} timed out after ${this.config.defaultTimeout}ms`));
            }, this.config.defaultTimeout);
        });
    }

    /**
     * Create standardized error response
     */
    createStandardError(error, taskId) {
        const standardError = new Error(error.message);
        standardError.code = error.code || 'ORCHESTRATOR_ERROR';
        standardError.taskId = taskId;
        standardError.timestamp = new Date().toISOString();
        standardError.originalError = error;
        return standardError;
    }

    /**
     * Update internal metrics
     */
    updateMetrics(taskId, success, duration) {
        this.metrics.tasksProcessed++;
        
        if (success) {
            this.metrics.tasksSucceeded++;
        } else {
            this.metrics.tasksFailed++;
        }
        
        // Calculate rolling average
        const currentAvg = this.metrics.averageProcessingTime;
        const count = this.metrics.tasksProcessed;
        this.metrics.averageProcessingTime = ((currentAvg * (count - 1)) + duration) / count;
    }

    /**
     * Setup event listeners for orchestrator management
     */
    setupEventListeners() {
        // Service health monitoring
        this.eventBus.on('service.health.check', this.handleHealthCheck.bind(this));
        this.eventBus.on('service.failed', this.handleServiceFailure.bind(this));
        this.eventBus.on('service.recovered', this.handleServiceRecovery.bind(this));
        
        // Workflow events
        this.eventBus.on('workflow.step.completed', this.handleStepCompleted.bind(this));
        this.eventBus.on('workflow.failed', this.handleWorkflowFailure.bind(this));
        
        // State management events
        this.eventBus.on('state.update', this.handleStateUpdate.bind(this));
        
        // System events
        this.eventBus.on('system.overload', this.handleSystemOverload.bind(this));
        this.eventBus.on('system.recovery', this.handleSystemRecovery.bind(this));
    }

    /**
     * Event handlers
     */
    handleHealthCheck(eventData) {
        const { serviceId } = eventData.data;
        console.log(`🔍 Health check requested for service: ${serviceId}`);
    }

    handleServiceFailure(eventData) {
        const { serviceId, error } = eventData.data;
        console.warn(`⚠️ Service failure detected: ${serviceId} - ${error}`);
        
        // Could implement automatic failover logic here
        this.stateManager.setGlobal(`service.${serviceId}.status`, 'failed');
    }

    handleServiceRecovery(eventData) {
        const { serviceId } = eventData.data;
        console.log(`✅ Service recovered: ${serviceId}`);
        this.stateManager.setGlobal(`service.${serviceId}.status`, 'healthy');
    }

    handleStepCompleted(eventData) {
        const { executionId, step, result } = eventData.data;
        console.log(`✓ Workflow step completed: ${step} in execution ${executionId}`);
    }

    handleWorkflowFailure(eventData) {
        const { workflowId, executionId, error } = eventData.data;
        console.error(`❌ Workflow failed: ${workflowId} (${executionId}) - ${error}`);
    }

    handleStateUpdate(eventData) {
        const { key, value } = eventData.data;
        console.log(`📊 State updated: ${key} = ${JSON.stringify(value).substring(0, 100)}`);
    }

    handleSystemOverload(eventData) {
        console.warn('⚠️ System overload detected - implementing backpressure');
        // Could implement rate limiting or request queuing here
    }

    handleSystemRecovery(eventData) {
        console.log('✅ System recovered from overload');
    }

    /**
     * Start health monitoring for services
     */
    startHealthMonitoring() {
        if (this.healthMonitoringInterval) {
            clearInterval(this.healthMonitoringInterval);
        }

        this.healthMonitoringInterval = setInterval(async () => {
            try {
                await this.serviceRegistry.performHealthChecks();
                
                // Check system load
                const activeTaskCount = this.activeTasks.size;
                const systemLoad = activeTaskCount / this.config.maxConcurrentTasks;
                
                if (systemLoad > 0.9) {
                    this.eventBus.emit('system.overload', { 
                        load: systemLoad,
                        activeTasks: activeTaskCount,
                        maxTasks: this.config.maxConcurrentTasks
                    });
                } else if (systemLoad < 0.5 && this.stateManager.getGlobal('system.overloaded')) {
                    this.eventBus.emit('system.recovery', { load: systemLoad });
                    this.stateManager.setGlobal('system.overloaded', false);
                }
                
            } catch (error) {
                console.error('Health monitoring error:', error);
            }
        }, this.config.healthMonitoring.interval);
    }

    /**
     * Get system status and metrics
     */
    getStatus() {
        return {
            status: this.initialized ? 'ready' : 'initializing',
            uptime: Date.now() - this.metrics.startTime,
            services: this.serviceRegistry.getHealthStatus(),
            workflows: {
                total: this.workflowEngine.getWorkflowCount(),
                active: this.workflowEngine.getActiveWorkflowCount()
            },
            tasks: {
                active: this.activeTasks.size,
                total: this.metrics.tasksProcessed,
                succeeded: this.metrics.tasksSucceeded,
                failed: this.metrics.tasksFailed,
                successRate: this.metrics.tasksProcessed > 0 ? 
                    this.metrics.tasksSucceeded / this.metrics.tasksProcessed : 0
            },
            performance: {
                averageProcessingTime: this.metrics.averageProcessingTime,
                systemLoad: this.activeTasks.size / this.config.maxConcurrentTasks
            },
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Get active task information
     */
    getActiveTasks() {
        const tasks = [];
        for (const [taskId, taskInfo] of this.activeTasks) {
            tasks.push({
                taskId,
                type: taskInfo.task.type,
                status: taskInfo.status,
                duration: Date.now() - taskInfo.startTime,
                startTime: new Date(taskInfo.startTime).toISOString()
            });
        }
        return tasks;
    }

    /**
     * Emergency shutdown of specific task
     */
    async cancelTask(taskId) {
        const taskInfo = this.activeTasks.get(taskId);
        if (!taskInfo) {
            throw new Error(`Task ${taskId} not found`);
        }

        this.eventBus.emitTaskEvent(taskId, 'cancelled', { reason: 'manual_cancellation' });
        this.activeTasks.delete(taskId);
        this.contextManager.cleanup(taskId);
        
        return { taskId, status: 'cancelled' };
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        console.log('🛑 Shutting down UltraMCP Orchestrator...');
        
        // Stop health monitoring
        if (this.healthMonitoringInterval) {
            clearInterval(this.healthMonitoringInterval);
        }

        // Wait for active tasks to complete (with timeout)
        const shutdownTimeout = 30000; // 30 seconds
        const startTime = Date.now();
        
        while (this.activeTasks.size > 0 && (Date.now() - startTime) < shutdownTimeout) {
            console.log(`⏳ Waiting for ${this.activeTasks.size} active tasks to complete...`);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        // Force cleanup remaining tasks
        if (this.activeTasks.size > 0) {
            console.warn(`⚠️ Force cancelling ${this.activeTasks.size} remaining tasks`);
            for (const taskId of this.activeTasks.keys()) {
                await this.cancelTask(taskId);
            }
        }

        // Shutdown components
        await this.stateManager.shutdown();
        await this.serviceRegistry.shutdown();
        
        this.eventBus.emit('orchestrator.shutdown', {
            tasksProcessed: this.metrics.tasksProcessed,
            uptime: Date.now() - this.metrics.startTime
        });

        console.log('✅ UltraMCP Orchestrator shutdown complete');
    }
}

module.exports = UltraMCPOrchestrator;
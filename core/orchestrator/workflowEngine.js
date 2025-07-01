/**
 * Workflow Engine for UltraMCP
 * 
 * Manages workflow selection, execution, and coordination across services.
 * Supports both predefined workflows and dynamic workflow generation.
 */

const fs = require('fs').promises;
const path = require('path');
const yaml = require('js-yaml');
const { generateExecutionId, loadConfig, retry, withTimeout } = require('../utils');

class WorkflowEngine {
    constructor(serviceRegistry, eventBus) {
        this.serviceRegistry = serviceRegistry;
        this.eventBus = eventBus;
        this.workflows = new Map();
        this.activeWorkflows = new Map();
        this.workflowMetrics = new Map();
        
        this.config = {
            workflowDirectories: ['./workflows', './services/*/workflows'],
            defaultTimeout: 300000, // 5 minutes
            maxConcurrentWorkflows: 50,
            enableDynamicGeneration: true
        };
    }

    /**
     * Load all workflow definitions
     */
    async loadWorkflows() {
        console.log('⚡ Loading workflow definitions...');
        
        for (const directory of this.config.workflowDirectories) {
            try {
                await this.loadWorkflowsFromDirectory(directory);
            } catch (error) {
                console.warn(`Warning: Could not load workflows from ${directory}:`, error.message);
            }
        }
        
        // Add built-in workflows
        this.addBuiltInWorkflows();
        
        console.log(`✅ Loaded ${this.workflows.size} workflow definitions`);
        this.eventBus.emitSystemEvent('workflows.loaded', {
            count: this.workflows.size,
            workflows: Array.from(this.workflows.keys())
        });
    }

    /**
     * Load workflows from a specific directory
     */
    async loadWorkflowsFromDirectory(directory) {
        try {
            // Handle glob patterns
            if (directory.includes('*')) {
                const globPattern = directory;
                const baseDir = globPattern.split('*')[0];
                const subPattern = globPattern.split('*')[1];
                
                const entries = await fs.readdir(baseDir, { withFileTypes: true });
                for (const entry of entries) {
                    if (entry.isDirectory()) {
                        const fullPath = path.join(baseDir, entry.name, subPattern);
                        try {
                            await this.loadWorkflowsFromDirectory(fullPath);
                        } catch (error) {
                            // Continue if specific service doesn't have workflows
                        }
                    }
                }
                return;
            }
            
            const entries = await fs.readdir(directory, { withFileTypes: true });
            
            for (const entry of entries) {
                if (entry.isFile() && (entry.name.endsWith('.yml') || entry.name.endsWith('.yaml'))) {
                    const workflowPath = path.join(directory, entry.name);
                    await this.loadWorkflowFromFile(workflowPath);
                }
            }
        } catch (error) {
            if (error.code !== 'ENOENT') {
                throw error;
            }
        }
    }

    /**
     * Load a single workflow from file
     */
    async loadWorkflowFromFile(filePath) {
        try {
            const content = await fs.readFile(filePath, 'utf8');
            const workflow = yaml.load(content);
            
            // Validate workflow
            this.validateWorkflow(workflow);
            
            // Initialize metrics
            this.workflowMetrics.set(workflow.id, {
                executionCount: 0,
                successCount: 0,
                failureCount: 0,
                averageExecutionTime: 0,
                lastExecuted: null
            });
            
            this.workflows.set(workflow.id, workflow);
            console.log(`📋 Loaded workflow: ${workflow.id} (${workflow.name})`);
            
        } catch (error) {
            console.warn(`Failed to load workflow from ${filePath}:`, error.message);
        }
    }

    /**
     * Add built-in workflows
     */
    addBuiltInWorkflows() {
        // Simple chat workflow
        const simpleChatWorkflow = {
            id: 'simple-chat',
            name: 'Simple LLM Chat',
            description: 'Basic single-LLM interaction',
            triggers: {
                taskTypes: ['chat', 'question', 'general'],
                patterns: ['.*'],
                context: { simple: true }
            },
            steps: [
                {
                    id: 'llm_response',
                    service: 'llm-provider',
                    input: 'task',
                    output: 'response',
                    config: {
                        provider: 'auto',
                        temperature: 0.7
                    }
                }
            ],
            output: 'response',
            metadata: {
                version: '1.0',
                complexity: 'low',
                fallback: true
            }
        };
        
        // Debate session workflow
        const debateWorkflow = {
            id: 'debate-session',
            name: 'CoD Protocol Debate Session',
            description: 'Multi-LLM debate with consensus building',
            triggers: {
                taskTypes: ['debate', 'discussion', 'analysis'],
                patterns: ['debate.*', 'discuss.*', 'analyze.*from.*perspectives'],
                context: { requiresConsensus: true }
            },
            steps: [
                {
                    id: 'preprocess',
                    service: 'input-preprocessor',
                    input: 'task',
                    output: 'preprocessed_task',
                    optional: true
                },
                {
                    id: 'debate',
                    service: 'cod-protocol',
                    input: 'preprocessed_task',
                    output: 'debate_result',
                    config: {
                        max_rounds: 3,
                        consensus_threshold: 0.75,
                        enable_shadow_llm: true,
                        enable_auditor: true
                    }
                },
                {
                    id: 'format_result',
                    service: 'result-formatter',
                    input: 'debate_result',
                    output: 'final_result',
                    optional: true
                }
            ],
            output: 'final_result',
            metadata: {
                version: '1.0',
                complexity: 'high'
            }
        };
        
        // Multi-agent coordination workflow
        const multiAgentWorkflow = {
            id: 'multi-agent',
            name: 'Multi-Agent Coordination',
            description: 'Coordinate multiple specialized agents',
            triggers: {
                taskTypes: ['complex-analysis', 'multi-step'],
                patterns: ['.*step.*by.*step.*', '.*comprehensive.*analysis.*']
            },
            steps: [
                {
                    id: 'task_decomposition',
                    service: 'task-decomposer',
                    input: 'task',
                    output: 'subtasks'
                },
                {
                    id: 'parallel_execution',
                    type: 'parallel',
                    steps: [
                        {
                            id: 'analysis_agent',
                            service: 'analysis-agent',
                            input: 'subtasks.analysis',
                            output: 'analysis_result'
                        },
                        {
                            id: 'reasoning_agent',
                            service: 'reasoning-agent',
                            input: 'subtasks.reasoning',
                            output: 'reasoning_result'
                        },
                        {
                            id: 'synthesis_agent',
                            service: 'synthesis-agent',
                            input: 'subtasks.synthesis',
                            output: 'synthesis_result'
                        }
                    ]
                },
                {
                    id: 'result_fusion',
                    service: 'result-fusioner',
                    input: ['analysis_result', 'reasoning_result', 'synthesis_result'],
                    output: 'fused_result'
                }
            ],
            output: 'fused_result',
            metadata: {
                version: '1.0',
                complexity: 'very-high'
            }
        };
        
        this.workflows.set(simpleChatWorkflow.id, simpleChatWorkflow);
        this.workflows.set(debateWorkflow.id, debateWorkflow);
        this.workflows.set(multiAgentWorkflow.id, multiAgentWorkflow);
        
        // Initialize metrics for built-in workflows
        for (const workflow of [simpleChatWorkflow, debateWorkflow, multiAgentWorkflow]) {
            this.workflowMetrics.set(workflow.id, {
                executionCount: 0,
                successCount: 0,
                failureCount: 0,
                averageExecutionTime: 0,
                lastExecuted: null
            });
        }
    }

    /**
     * Validate workflow definition
     */
    validateWorkflow(workflow) {
        const required = ['id', 'name', 'steps'];
        
        for (const field of required) {
            if (!workflow[field]) {
                throw new Error(`Workflow missing required field: ${field}`);
            }
        }
        
        if (!Array.isArray(workflow.steps) || workflow.steps.length === 0) {
            throw new Error('Workflow must have at least one step');
        }
        
        // Validate steps
        for (const step of workflow.steps) {
            if (!step.id || !step.service) {
                throw new Error('Workflow step must have id and service');
            }
        }
    }

    /**
     * Select the best workflow for a task
     */
    async selectWorkflow(task, context) {
        // 1. Try exact match first
        if (task.workflowId) {
            const workflow = this.workflows.get(task.workflowId);
            if (workflow) {
                this.eventBus.emitWorkflowEvent(workflow.id, 'selected', { 
                    reason: 'explicit',
                    taskId: context.taskId 
                });
                return workflow;
            }
            console.warn(`Explicit workflow ${task.workflowId} not found, falling back to selection`);
        }

        // 2. Smart workflow selection based on scoring
        const candidates = [];
        
        for (const [id, workflow] of this.workflows) {
            const score = this.calculateWorkflowScore(task, workflow, context);
            if (score > 0) {
                candidates.push({ workflow, score });
            }
        }

        if (candidates.length === 0) {
            // 3. Generate dynamic workflow if enabled
            if (this.config.enableDynamicGeneration) {
                const dynamicWorkflow = this.generateDynamicWorkflow(task, context);
                this.eventBus.emitWorkflowEvent(dynamicWorkflow.id, 'generated', { 
                    taskId: context.taskId 
                });
                return dynamicWorkflow;
            }
            
            throw new Error('No suitable workflow found for task');
        }

        // Sort by score and select best match
        candidates.sort((a, b) => b.score - a.score);
        const selectedWorkflow = candidates[0].workflow;
        
        this.eventBus.emitWorkflowEvent(selectedWorkflow.id, 'selected', { 
            reason: 'scored',
            score: candidates[0].score,
            candidates: candidates.length,
            taskId: context.taskId 
        });
        
        return selectedWorkflow;
    }

    /**
     * Calculate workflow compatibility score
     */
    calculateWorkflowScore(task, workflow, context) {
        let score = 0;
        
        // Task type matching
        if (workflow.triggers?.taskTypes?.includes(task.type)) {
            score += 50;
        }
        
        // Content pattern matching
        if (workflow.triggers?.patterns) {
            for (const pattern of workflow.triggers.patterns) {
                if (task.content?.match(new RegExp(pattern, 'i'))) {
                    score += 20;
                    break; // Only count first match
                }
            }
        }
        
        // Context matching
        if (workflow.triggers?.context) {
            for (const [key, value] of Object.entries(workflow.triggers.context)) {
                if (context[key] === value || task.context?.[key] === value) {
                    score += 10;
                }
            }
        }
        
        // Service availability check
        let serviceAvailability = 1.0;
        for (const step of workflow.steps) {
            if (step.service) {
                try {
                    this.serviceRegistry.getService(step.service);
                } catch (error) {
                    if (!step.optional) {
                        serviceAvailability *= 0.5; // Penalize missing required services
                    }
                }
            }
        }
        
        score *= serviceAvailability;
        
        // Complexity penalty for simple tasks
        const complexity = workflow.metadata?.complexity || 'medium';
        if (task.type === 'chat' || task.type === 'simple') {
            if (complexity === 'high' || complexity === 'very-high') {
                score *= 0.7; // Prefer simpler workflows for simple tasks
            }
        }
        
        // Performance bonus based on historical success
        const metrics = this.workflowMetrics.get(workflow.id);
        if (metrics && metrics.executionCount > 0) {
            const successRate = metrics.successCount / metrics.executionCount;
            score *= (0.8 + (successRate * 0.4)); // Boost successful workflows
        }
        
        return score;
    }

    /**
     * Generate dynamic workflow for task
     */
    generateDynamicWorkflow(task, context) {
        const services = this.serviceRegistry.selectServices(task, [], { strategy: 'best-match', count: 3 });
        
        if (services.length === 0) {
            throw new Error('No suitable services found for dynamic workflow generation');
        }
        
        const workflowId = `dynamic_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        if (services.length === 1) {
            return this.createSimpleWorkflow(workflowId, services[0], task);
        } else {
            return this.createMultiServiceWorkflow(workflowId, services, task, context);
        }
    }

    /**
     * Create simple single-service workflow
     */
    createSimpleWorkflow(workflowId, service, task) {
        return {
            id: workflowId,
            name: `Dynamic Simple Workflow (${service.name})`,
            description: `Auto-generated workflow using ${service.name}`,
            dynamic: true,
            steps: [
                {
                    id: 'execute',
                    service: service.id,
                    input: 'task',
                    output: 'result'
                }
            ],
            output: 'result',
            metadata: {
                version: '1.0',
                complexity: 'low',
                generated: true,
                serviceCount: 1
            }
        };
    }

    /**
     * Create multi-service workflow
     */
    createMultiServiceWorkflow(workflowId, services, task, context) {
        const steps = [];
        
        // If we have CoD protocol service, use it for coordination
        const codService = services.find(s => s.getCapabilities().includes('debate'));
        if (codService) {
            steps.push({
                id: 'debate_coordination',
                service: codService.id,
                input: 'task',
                output: 'coordinated_result',
                config: {
                    participants: services.filter(s => s !== codService).map(s => s.id).slice(0, 3)
                }
            });
        } else {
            // Sequential execution of services
            services.forEach((service, index) => {
                steps.push({
                    id: `step_${index + 1}`,
                    service: service.id,
                    input: index === 0 ? 'task' : `step_${index}_result`,
                    output: `step_${index + 1}_result`
                });
            });
        }
        
        return {
            id: workflowId,
            name: `Dynamic Multi-Service Workflow`,
            description: `Auto-generated workflow using ${services.length} services`,
            dynamic: true,
            steps,
            output: steps[steps.length - 1].output,
            metadata: {
                version: '1.0',
                complexity: services.length > 2 ? 'high' : 'medium',
                generated: true,
                serviceCount: services.length
            }
        };
    }

    /**
     * Execute a workflow
     */
    async execute(workflow, task, context) {
        if (this.activeWorkflows.size >= this.config.maxConcurrentWorkflows) {
            throw new Error('Maximum concurrent workflows limit reached');
        }

        const executionId = generateExecutionId();
        const execution = new WorkflowExecution(executionId, workflow, task, context);
        
        this.activeWorkflows.set(executionId, execution);
        
        try {
            this.eventBus.emitWorkflowEvent(workflow.id, 'started', { 
                executionId,
                taskId: context.taskId
            });
            
            const startTime = Date.now();
            
            const result = await withTimeout(
                execution.run(this.serviceRegistry, this.eventBus),
                this.config.defaultTimeout,
                `Workflow ${workflow.id} execution timed out`
            );
            
            const executionTime = Date.now() - startTime;
            this.updateWorkflowMetrics(workflow.id, true, executionTime);
            
            this.eventBus.emitWorkflowEvent(workflow.id, 'completed', { 
                executionId,
                taskId: context.taskId,
                executionTime,
                result: this.serializeResult(result)
            });
            
            return result;
            
        } catch (error) {
            const executionTime = Date.now() - (execution.startTime || Date.now());
            this.updateWorkflowMetrics(workflow.id, false, executionTime);
            
            this.eventBus.emitWorkflowEvent(workflow.id, 'failed', { 
                executionId,
                taskId: context.taskId,
                error: error.message,
                executionTime
            });
            
            throw error;
            
        } finally {
            this.activeWorkflows.delete(executionId);
        }
    }

    /**
     * Update workflow execution metrics
     */
    updateWorkflowMetrics(workflowId, success, executionTime) {
        const metrics = this.workflowMetrics.get(workflowId);
        if (!metrics) return;
        
        metrics.executionCount++;
        metrics.lastExecuted = new Date().toISOString();
        
        if (success) {
            metrics.successCount++;
        } else {
            metrics.failureCount++;
        }
        
        // Update average execution time
        const totalExecutions = metrics.executionCount;
        const currentAvg = metrics.averageExecutionTime;
        metrics.averageExecutionTime = ((currentAvg * (totalExecutions - 1)) + executionTime) / totalExecutions;
    }

    /**
     * Serialize result for event emission (avoid circular references)
     */
    serializeResult(result) {
        try {
            return JSON.parse(JSON.stringify(result));
        } catch (error) {
            return { error: 'Result serialization failed', message: error.message };
        }
    }

    /**
     * Register a new workflow
     */
    registerWorkflow(workflow) {
        this.validateWorkflow(workflow);
        this.workflows.set(workflow.id, workflow);
        
        this.workflowMetrics.set(workflow.id, {
            executionCount: 0,
            successCount: 0,
            failureCount: 0,
            averageExecutionTime: 0,
            lastExecuted: null
        });
        
        this.eventBus.emitSystemEvent('workflow.registered', { workflowId: workflow.id });
    }

    /**
     * Unregister a workflow
     */
    unregisterWorkflow(workflowId) {
        const workflow = this.workflows.get(workflowId);
        if (!workflow) return false;
        
        this.workflows.delete(workflowId);
        this.workflowMetrics.delete(workflowId);
        
        this.eventBus.emitSystemEvent('workflow.unregistered', { workflowId });
        return true;
    }

    /**
     * Get workflow count
     */
    getWorkflowCount() {
        return this.workflows.size;
    }

    /**
     * Get active workflow count
     */
    getActiveWorkflowCount() {
        return this.activeWorkflows.size;
    }

    /**
     * Get all workflows
     */
    getAllWorkflows() {
        const workflows = [];
        for (const [id, workflow] of this.workflows) {
            workflows.push({
                id,
                name: workflow.name,
                description: workflow.description,
                complexity: workflow.metadata?.complexity || 'medium',
                dynamic: workflow.dynamic || false,
                metrics: this.workflowMetrics.get(id)
            });
        }
        return workflows;
    }

    /**
     * Get active workflow executions
     */
    getActiveWorkflows() {
        const activeWorkflows = [];
        for (const [executionId, execution] of this.activeWorkflows) {
            activeWorkflows.push({
                executionId,
                workflowId: execution.workflow.id,
                workflowName: execution.workflow.name,
                taskId: execution.context.taskId,
                startTime: execution.startTime,
                currentStep: execution.currentStep,
                totalSteps: execution.workflow.steps.length
            });
        }
        return activeWorkflows;
    }

    /**
     * Cancel a workflow execution
     */
    async cancelWorkflow(executionId) {
        const execution = this.activeWorkflows.get(executionId);
        if (!execution) {
            throw new Error(`Workflow execution ${executionId} not found`);
        }
        
        execution.cancel();
        this.activeWorkflows.delete(executionId);
        
        this.eventBus.emitWorkflowEvent(execution.workflow.id, 'cancelled', { 
            executionId,
            reason: 'manual_cancellation'
        });
        
        return { executionId, status: 'cancelled' };
    }
}

/**
 * Workflow Execution class
 */
class WorkflowExecution {
    constructor(id, workflow, task, context) {
        this.id = id;
        this.workflow = workflow;
        this.task = task;
        this.context = context;
        this.state = {};
        this.currentStep = 0;
        this.startTime = Date.now();
        this.cancelled = false;
        this.stepResults = [];
    }

    /**
     * Run the workflow execution
     */
    async run(serviceRegistry, eventBus) {
        try {
            for (let i = 0; i < this.workflow.steps.length; i++) {
                if (this.cancelled) {
                    throw new Error('Workflow execution was cancelled');
                }
                
                const step = this.workflow.steps[i];
                this.currentStep = i;
                
                eventBus.emit('workflow.step.started', {
                    executionId: this.id,
                    workflowId: this.workflow.id,
                    step: step.id,
                    stepIndex: i
                });

                try {
                    const result = await this.executeStep(step, serviceRegistry, eventBus);
                    this.state[step.output || step.id] = result;
                    this.stepResults.push({
                        stepId: step.id,
                        success: true,
                        result: this.serializeStepResult(result),
                        timestamp: new Date().toISOString()
                    });

                    eventBus.emit('workflow.step.completed', {
                        executionId: this.id,
                        workflowId: this.workflow.id,
                        step: step.id,
                        stepIndex: i,
                        result: this.serializeStepResult(result)
                    });

                } catch (error) {
                    this.stepResults.push({
                        stepId: step.id,
                        success: false,
                        error: error.message,
                        timestamp: new Date().toISOString()
                    });

                    eventBus.emit('workflow.step.failed', {
                        executionId: this.id,
                        workflowId: this.workflow.id,
                        step: step.id,
                        stepIndex: i,
                        error: error.message
                    });

                    if (!step.optional) {
                        throw error;
                    }
                    
                    console.warn(`Optional step ${step.id} failed: ${error.message}`);
                }
            }

            return this.buildFinalResult();
            
        } catch (error) {
            throw new Error(`Workflow execution failed at step ${this.currentStep}: ${error.message}`);
        }
    }

    /**
     * Execute a single workflow step
     */
    async executeStep(step, serviceRegistry, eventBus) {
        if (step.type === 'parallel') {
            return await this.executeParallelSteps(step.steps, serviceRegistry, eventBus);
        }
        
        const service = await serviceRegistry.getService(step.service);
        const input = this.prepareStepInput(step);
        
        // Add step configuration to context
        const stepContext = {
            ...this.context,
            stepId: step.id,
            stepConfig: step.config || {},
            workflowId: this.workflow.id,
            executionId: this.id
        };
        
        return await service.execute(input, stepContext);
    }

    /**
     * Execute parallel steps
     */
    async executeParallelSteps(steps, serviceRegistry, eventBus) {
        const promises = steps.map(step => this.executeStep(step, serviceRegistry, eventBus));
        const results = await Promise.allSettled(promises);
        
        const parallelResults = {};
        const errors = [];
        
        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            const result = results[i];
            
            if (result.status === 'fulfilled') {
                parallelResults[step.output || step.id] = result.value;
            } else if (!step.optional) {
                errors.push(`Step ${step.id}: ${result.reason.message}`);
            }
        }
        
        if (errors.length > 0) {
            throw new Error(`Parallel execution failed: ${errors.join(', ')}`);
        }
        
        return parallelResults;
    }

    /**
     * Prepare input for a step
     */
    prepareStepInput(step) {
        if (!step.input) {
            return this.task;
        }
        
        if (step.input === 'task') {
            return this.task;
        }
        
        if (Array.isArray(step.input)) {
            // Multiple inputs - combine them
            const combinedInput = {};
            for (const inputKey of step.input) {
                if (this.state[inputKey] !== undefined) {
                    combinedInput[inputKey] = this.state[inputKey];
                }
            }
            return combinedInput;
        }
        
        // Single input from previous step
        if (step.input.includes('.')) {
            // Nested property access (e.g., 'subtasks.analysis')
            const [baseKey, ...propertyPath] = step.input.split('.');
            let value = this.state[baseKey];
            
            for (const prop of propertyPath) {
                if (value && typeof value === 'object') {
                    value = value[prop];
                } else {
                    value = undefined;
                    break;
                }
            }
            
            return value !== undefined ? value : this.task;
        }
        
        return this.state[step.input] !== undefined ? this.state[step.input] : this.task;
    }

    /**
     * Build final result from workflow state
     */
    buildFinalResult() {
        const outputKey = this.workflow.output || 'result';
        
        if (outputKey === 'state') {
            return this.state;
        }
        
        if (this.state[outputKey] !== undefined) {
            return this.state[outputKey];
        }
        
        // If output key not found, return the last step result
        const lastStep = this.workflow.steps[this.workflow.steps.length - 1];
        const lastStepOutput = lastStep.output || lastStep.id;
        
        return this.state[lastStepOutput] || this.state;
    }

    /**
     * Serialize step result for storage/events
     */
    serializeStepResult(result) {
        try {
            return JSON.parse(JSON.stringify(result));
        } catch (error) {
            return { serialization_error: error.message };
        }
    }

    /**
     * Cancel workflow execution
     */
    cancel() {
        this.cancelled = true;
    }
}

module.exports = WorkflowEngine;
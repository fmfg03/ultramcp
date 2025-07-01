/**
 * A2A Validation Schemas - Joi schemas for A2A API validation
 * Provides comprehensive validation for Agent-to-Agent communication
 */

const Joi = require('joi');

/**
 * Base A2A task request schema
 */
const validateA2ARequest = Joi.object({
    task_type: Joi.string()
        .valid(
            'mcp_orchestration',
            'multi_agent_workflow', 
            'agent_discovery',
            'resource_allocation',
            'health_check',
            'collaborative_analysis',
            'multi_step_research',
            'autonomous_execution',
            'semantic_search',
            'store_memory',
            'context_retrieval',
            'knowledge_sharing',
            'general'
        )
        .required()
        .messages({
            'any.required': 'Task type is required',
            'any.only': 'Invalid task type provided'
        }),
        
    payload: Joi.object().required()
        .messages({
            'any.required': 'Payload is required'
        }),
        
    requester_id: Joi.string().optional(),
    
    priority: Joi.number()
        .min(1)
        .max(10)
        .default(5)
        .messages({
            'number.min': 'Priority must be between 1 and 10',
            'number.max': 'Priority must be between 1 and 10'
        }),
        
    timeout: Joi.number()
        .positive()
        .max(600000) // 10 minutes max
        .default(300000) // 5 minutes default
        .messages({
            'number.positive': 'Timeout must be a positive number',
            'number.max': 'Timeout cannot exceed 10 minutes'
        }),
        
    metadata: Joi.object({
        session_id: Joi.string().optional(),
        trace_id: Joi.string().optional(),
        source: Joi.string().optional(),
        context: Joi.object().optional()
    }).optional()
});

/**
 * A2A task delegation schema
 */
const validateDelegationRequest = Joi.object({
    target_capabilities: Joi.array()
        .items(Joi.string())
        .min(1)
        .required()
        .messages({
            'array.min': 'At least one target capability is required',
            'any.required': 'Target capabilities are required'
        }),
        
    task_data: Joi.object({
        task_type: Joi.string().required(),
        payload: Joi.object().optional(),
        message: Joi.string().optional(),
        query: Joi.string().optional(),
        context: Joi.object().optional()
    }).required(),
    
    options: Joi.object({
        priority: Joi.number().min(1).max(10).default(5),
        timeout: Joi.number().positive().max(600000).default(300000),
        retry_count: Joi.number().min(0).max(5).default(3),
        fallback_to_mcp: Joi.boolean().default(true),
        require_confirmation: Joi.boolean().default(false)
    }).optional()
});

/**
 * MCP orchestration payload schema
 */
const validateMCPOrchestrationPayload = Joi.object({
    message: Joi.string().required()
        .messages({
            'any.required': 'Message is required for MCP orchestration'
        }),
        
    session_id: Joi.string()
        .pattern(/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/)
        .optional()
        .messages({
            'string.pattern.base': 'Session ID must be a valid UUID'
        }),
        
    context: Joi.object({
        previous_results: Joi.array().optional(),
        user_preferences: Joi.object().optional(),
        workflow_state: Joi.object().optional(),
        memory_context: Joi.string().optional()
    }).optional(),
    
    orchestration_options: Joi.object({
        enable_reasoning: Joi.boolean().default(true),
        enable_contradiction: Joi.boolean().default(true),
        enable_memory: Joi.boolean().default(true),
        max_iterations: Joi.number().min(1).max(10).default(3),
        quality_threshold: Joi.number().min(0).max(1).default(0.7)
    }).optional()
});

/**
 * Multi-agent workflow schema
 */
const validateMultiAgentWorkflow = Joi.object({
    workflow_steps: Joi.array().items(
        Joi.object({
            id: Joi.string().optional(),
            type: Joi.string().required(),
            data: Joi.object().required(),
            capabilities: Joi.array().items(Joi.string()).optional(),
            delegate: Joi.boolean().default(false),
            required_capabilities: Joi.array().items(Joi.string()).optional(),
            dependencies: Joi.array().items(Joi.string()).optional(),
            timeout: Joi.number().positive().optional(),
            retry_on_failure: Joi.boolean().default(true)
        })
    ).required(),
    
    coordination_type: Joi.string()
        .valid('sequential', 'parallel', 'conditional', 'pipeline')
        .default('sequential'),
        
    failure_strategy: Joi.string()
        .valid('fail_fast', 'continue_on_error', 'retry_failed', 'rollback')
        .default('continue_on_error'),
        
    max_parallel_tasks: Joi.number().min(1).max(20).default(5),
    
    completion_criteria: Joi.object({
        require_all_success: Joi.boolean().default(false),
        minimum_success_rate: Joi.number().min(0).max(1).default(0.8),
        critical_steps: Joi.array().items(Joi.string()).optional()
    }).optional()
});

/**
 * Agent discovery schema
 */
const validateAgentDiscovery = Joi.object({
    capabilities: Joi.array()
        .items(Joi.string())
        .optional(),
        
    include_load_info: Joi.boolean().default(true),
    
    filter_criteria: Joi.object({
        status: Joi.array().items(
            Joi.string().valid('healthy', 'busy', 'unavailable', 'unknown')
        ).optional(),
        max_load: Joi.number().min(0).max(1).optional(),
        min_capacity: Joi.number().min(0).optional(),
        protocols: Joi.array().items(Joi.string()).optional(),
        regions: Joi.array().items(Joi.string()).optional()
    }).optional(),
    
    sort_by: Joi.string()
        .valid('load', 'capacity', 'response_time', 'capability_match', 'random')
        .default('load'),
        
    limit: Joi.number().min(1).max(100).default(20)
});

/**
 * Resource allocation schema
 */
const validateResourceAllocation = Joi.object({
    resource_type: Joi.string()
        .valid('computational', 'memory', 'network', 'storage', 'agent_time')
        .required(),
        
    allocation_strategy: Joi.string()
        .valid('load_balanced', 'capability_based', 'priority_based', 'cost_optimized', 'latency_optimized')
        .default('load_balanced'),
        
    constraints: Joi.object({
        max_agents: Joi.number().min(1).max(50).optional(),
        required_capabilities: Joi.array().items(Joi.string()).optional(),
        budget_limit: Joi.number().positive().optional(),
        latency_requirement: Joi.number().positive().optional(),
        geographic_constraints: Joi.array().items(Joi.string()).optional(),
        exclude_agents: Joi.array().items(Joi.string()).optional()
    }).optional(),
    
    priority: Joi.number().min(1).max(10).default(5),
    
    duration: Joi.number().positive().optional() // Duration in seconds
});

/**
 * Semantic search schema (for Memory agents)
 */
const validateSemanticSearch = Joi.object({
    query: Joi.string().required()
        .min(1)
        .max(1000)
        .messages({
            'string.min': 'Query cannot be empty',
            'string.max': 'Query cannot exceed 1000 characters'
        }),
        
    top_k: Joi.number().min(1).max(100).default(5),
    
    similarity_threshold: Joi.number().min(0).max(1).default(0.7),
    
    filters: Joi.object({
        date_range: Joi.object({
            start: Joi.date().optional(),
            end: Joi.date().optional()
        }).optional(),
        source_types: Joi.array().items(Joi.string()).optional(),
        metadata_filters: Joi.object().optional()
    }).optional(),
    
    enrich_with_web: Joi.boolean().default(false),
    
    return_metadata: Joi.boolean().default(true)
});

/**
 * Memory storage schema
 */
const validateMemoryStorage = Joi.object({
    content: Joi.string().required()
        .min(1)
        .max(10000)
        .messages({
            'string.min': 'Content cannot be empty',
            'string.max': 'Content cannot exceed 10000 characters'
        }),
        
    metadata: Joi.object({
        title: Joi.string().optional(),
        source: Joi.string().optional(),
        content_type: Joi.string().optional(),
        tags: Joi.array().items(Joi.string()).optional(),
        importance: Joi.number().min(0).max(1).optional(),
        expiry_date: Joi.date().optional(),
        access_permissions: Joi.array().items(Joi.string()).optional()
    }).optional(),
    
    source_agent: Joi.string().optional(),
    
    embedding_options: Joi.object({
        model: Joi.string().optional(),
        chunk_size: Joi.number().positive().optional(),
        overlap_size: Joi.number().min(0).optional()
    }).optional()
});

/**
 * Complex validation for specific A2A task types
 */
const validateTaskByType = (taskType) => {
    const schemas = {
        'mcp_orchestration': validateMCPOrchestrationPayload,
        'multi_agent_workflow': validateMultiAgentWorkflow,
        'agent_discovery': validateAgentDiscovery,
        'resource_allocation': validateResourceAllocation,
        'semantic_search': validateSemanticSearch,
        'store_memory': validateMemoryStorage
    };
    
    return schemas[taskType] || Joi.object(); // Default to any object for unknown types
};

/**
 * Middleware function for comprehensive A2A validation
 */
const validateA2ATaskComplete = (req, res, next) => {
    const { error: baseError } = validateA2ARequest.validate(req.body);
    if (baseError) {
        return res.status(400).json({
            success: false,
            error: 'Base validation failed',
            details: baseError.details[0].message
        });
    }
    
    // Validate payload based on task type
    const { task_type, payload } = req.body;
    const payloadSchema = validateTaskByType(task_type);
    
    if (payloadSchema) {
        const { error: payloadError } = payloadSchema.validate(payload);
        if (payloadError) {
            return res.status(400).json({
                success: false,
                error: 'Payload validation failed',
                task_type,
                details: payloadError.details[0].message
            });
        }
    }
    
    next();
};

/**
 * Health check validation
 */
const validateHealthCheck = Joi.object({
    include_agent_details: Joi.boolean().default(true),
    include_metrics: Joi.boolean().default(true),
    timeout: Joi.number().positive().max(30000).default(10000)
});

module.exports = {
    validateA2ARequest,
    validateDelegationRequest,
    validateMCPOrchestrationPayload,
    validateMultiAgentWorkflow,
    validateAgentDiscovery,
    validateResourceAllocation,
    validateSemanticSearch,
    validateMemoryStorage,
    validateHealthCheck,
    validateTaskByType,
    validateA2ATaskComplete
};
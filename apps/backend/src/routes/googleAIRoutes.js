/**
 * Google AI Routes - REST API routes for Google AI/Gemini integration
 * Provides comprehensive routing for Google AI services
 */

const express = require('express');
const router = express.Router();
const googleAIController = require('../controllers/googleAIController');
const validationMiddleware = require('../middleware/validationMiddleware');
const authMiddleware = require('../middleware/authMiddleware');
const Joi = require('joi');

// Apply authentication middleware to all Google AI routes
router.use(authMiddleware.protectRoute);

/**
 * POST /api/google-ai/chat
 * Chat completion with Google AI models
 */
router.post('/chat',
    validationMiddleware(validateChatRequest),
    googleAIController.chatCompletion.bind(googleAIController)
);

/**
 * POST /api/google-ai/vision
 * Vision analysis with Google AI
 */
router.post('/vision',
    validationMiddleware(validateVisionRequest),
    googleAIController.analyzeImages.bind(googleAIController)
);

/**
 * POST /api/google-ai/embeddings
 * Generate embeddings with Google AI
 */
router.post('/embeddings',
    validationMiddleware(validateEmbeddingRequest),
    googleAIController.generateEmbeddings.bind(googleAIController)
);

/**
 * POST /api/google-ai/function-calling
 * Function calling with Google AI
 */
router.post('/function-calling',
    validationMiddleware(validateFunctionCallingRequest),
    googleAIController.functionCalling.bind(googleAIController)
);

/**
 * POST /api/google-ai/code
 * Code generation with Google AI
 */
router.post('/code',
    validationMiddleware(validateCodeGenerationRequest),
    googleAIController.generateCode.bind(googleAIController)
);

/**
 * GET /api/google-ai/statistics
 * Get comprehensive service statistics
 */
router.get('/statistics',
    googleAIController.getStatistics.bind(googleAIController)
);

/**
 * GET /api/google-ai/model-comparison
 * Get model performance comparison
 */
router.get('/model-comparison',
    googleAIController.getModelComparison.bind(googleAIController)
);

/**
 * GET /api/google-ai/cost-analysis
 * Get cost analysis and projections
 */
router.get('/cost-analysis',
    googleAIController.getCostAnalysis.bind(googleAIController)
);

/**
 * GET /api/google-ai/safety-analysis
 * Get safety analysis and violations
 */
router.get('/safety-analysis',
    googleAIController.getSafetyAnalysis.bind(googleAIController)
);

/**
 * GET /api/google-ai/health
 * Service health check
 */
router.get('/health',
    googleAIController.healthCheck.bind(googleAIController)
);

/**
 * GET /api/google-ai/models
 * Get available models and capabilities
 */
router.get('/models',
    googleAIController.getModels.bind(googleAIController)
);

/**
 * POST /api/google-ai/recommend
 * Get model recommendations for a task
 */
router.post('/recommend',
    validationMiddleware(validateRecommendationRequest),
    googleAIController.getModelRecommendations.bind(googleAIController)
);

/**
 * POST /api/google-ai/reset-metrics
 * Reset monitoring metrics (admin only)
 */
router.post('/reset-metrics',
    // authMiddleware.requireRole('admin'), // Uncomment when role-based auth is implemented
    googleAIController.resetMetrics.bind(googleAIController)
);

// Validation schemas

function validateChatRequest(req, res, next) {
    const schema = Joi.object({
        messages: Joi.array().items(
            Joi.object({
                role: Joi.string().valid('user', 'assistant', 'system').required(),
                content: Joi.string().required()
            })
        ).min(1).required(),
        
        model: Joi.string().valid(
            'gemini-1.5-pro-latest',
            'gemini-1.5-flash-latest',
            'gemini-1.0-pro'
        ).optional(),
        
        temperature: Joi.number().min(0).max(2).optional(),
        max_tokens: Joi.number().positive().max(100000).optional(),
        system_instruction: Joi.string().optional(),
        
        task_type: Joi.string().valid(
            'general',
            'complex_reasoning',
            'creative_writing',
            'analysis',
            'summarization',
            'translation',
            'question_answering'
        ).default('general'),
        
        auto_select_model: Joi.boolean().default(true),
        priority: Joi.string().valid('speed', 'cost', 'quality', 'balanced').default('balanced'),
        complexity: Joi.string().valid('low', 'medium', 'high').default('medium')
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

function validateVisionRequest(req, res, next) {
    const schema = Joi.object({
        images: Joi.array().items(Joi.string()).min(1).max(10).required(),
        prompt: Joi.string().min(1).max(5000).required(),
        
        model: Joi.string().valid(
            'gemini-1.5-pro-latest',
            'gemini-1.5-flash-latest'
        ).optional(),
        
        detail_level: Joi.string().valid('low', 'high').default('high'),
        
        analysis_type: Joi.string().valid(
            'general',
            'object_detection',
            'text_extraction',
            'scene_description',
            'technical_analysis',
            'accessibility'
        ).default('general'),
        
        auto_enhance_prompt: Joi.boolean().default(true)
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

function validateEmbeddingRequest(req, res, next) {
    const schema = Joi.object({
        texts: Joi.array().items(Joi.string().max(8192)).min(1).max(500).required(),
        
        task_type: Joi.string().valid(
            'RETRIEVAL_QUERY',
            'RETRIEVAL_DOCUMENT',
            'SEMANTIC_SIMILARITY',
            'CLASSIFICATION',
            'CLUSTERING'
        ).default('SEMANTIC_SIMILARITY'),
        
        title: Joi.string().max(100).optional(),
        batch_size: Joi.number().min(1).max(100).default(50),
        normalize: Joi.boolean().default(true)
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

function validateFunctionCallingRequest(req, res, next) {
    const schema = Joi.object({
        messages: Joi.array().items(
            Joi.object({
                role: Joi.string().valid('user', 'assistant').required(),
                content: Joi.string().required(),
                functionCalls: Joi.array().optional()
            })
        ).min(1).required(),
        
        functions: Joi.array().items(
            Joi.object({
                name: Joi.string().required(),
                description: Joi.string().required(),
                parameters: Joi.object().optional()
            })
        ).min(1).required(),
        
        model: Joi.string().valid(
            'gemini-1.5-pro-latest',
            'gemini-1.5-flash-latest',
            'gemini-1.0-pro'
        ).optional(),
        
        function_call_mode: Joi.string().valid('auto', 'any', 'none').default('auto'),
        max_iterations: Joi.number().min(1).max(10).default(5),
        auto_execute: Joi.boolean().default(false)
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

function validateCodeGenerationRequest(req, res, next) {
    const schema = Joi.object({
        task: Joi.string().valid(
            'generate',
            'explain',
            'debug',
            'optimize',
            'translate'
        ).required(),
        
        language: Joi.string().optional(),
        prompt: Joi.string().min(1).max(10000).required(),
        code: Joi.string().max(50000).optional(),
        
        template: Joi.string().valid(
            'clean_architecture',
            'microservice',
            'api_endpoint',
            'data_processing',
            'testing'
        ).optional(),
        
        style_guide: Joi.string().max(1000).optional(),
        include_tests: Joi.boolean().default(false),
        include_docs: Joi.boolean().default(false)
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

function validateRecommendationRequest(req, res, next) {
    const schema = Joi.object({
        task_type: Joi.string().required(),
        
        context: Joi.object({
            complexity: Joi.string().valid('low', 'medium', 'high').optional(),
            speed_priority: Joi.boolean().optional(),
            cost_priority: Joi.boolean().optional(),
            multimodal: Joi.boolean().optional(),
            long_context: Joi.boolean().optional(),
            function_calling: Joi.boolean().optional(),
            hasImages: Joi.boolean().optional(),
            longContext: Joi.boolean().optional(),
            costSensitive: Joi.boolean().optional()
        }).optional()
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
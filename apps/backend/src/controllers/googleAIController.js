/**
 * Google AI Controller - REST API endpoints for Google AI/Gemini integration
 * Provides comprehensive interface for Google AI services
 */

const GoogleAIService = require('../services/googleAIService');
const { googleAIMonitoring } = require('../middleware/googleAIMonitoring');
const logger = require('../utils/logger');
const { AppError } = require('../utils/AppError');

class GoogleAIController {
    constructor() {
        this.googleAIService = new GoogleAIService();
        this.isInitialized = false;
        this._initialize();
    }
    
    async _initialize() {
        try {
            await this.googleAIService.initialize();
            this.isInitialized = true;
            logger.info('Google AI Controller initialized successfully');
        } catch (error) {
            logger.error('Failed to initialize Google AI Controller', { error: error.message });
        }
    }
    
    /**
     * Chat completion with Google AI models
     * POST /api/google-ai/chat
     */
    async chatCompletion(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Google AI service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                messages,
                model,
                temperature,
                max_tokens,
                system_instruction,
                task_type = 'general',
                auto_select_model = true,
                priority = 'balanced'
            } = req.body;
            
            if (!messages || !Array.isArray(messages) || messages.length === 0) {
                throw new AppError('Messages array is required', 400, 'MISSING_MESSAGES');
            }
            
            // Track request start
            const requestId = googleAIMonitoring.trackRequestStart({
                model: model || 'auto-selected',
                taskType: task_type,
                input: messages
            });
            
            const options = {
                messages,
                model,
                temperature,
                max_tokens,
                system_instruction,
                task_type,
                auto_select_model,
                requirements: {
                    complexity: req.body.complexity || 'medium',
                    speed_priority: priority === 'speed',
                    cost_priority: priority === 'cost'
                }
            };
            
            const result = await this.googleAIService.chatCompletion(options);
            
            // Track completion
            googleAIMonitoring.trackRequestComplete(requestId, result);
            
            res.json({
                success: true,
                ...result,
                requestId
            });
            
        } catch (error) {
            logger.error('Google AI chat completion failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Vision analysis with Google AI
     * POST /api/google-ai/vision
     */
    async analyzeImages(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Google AI service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                images,
                prompt,
                model,
                detail_level = 'high',
                analysis_type = 'general',
                auto_enhance_prompt = true
            } = req.body;
            
            if (!images || !Array.isArray(images) || images.length === 0) {
                throw new AppError('Images array is required', 400, 'MISSING_IMAGES');
            }
            
            if (!prompt) {
                throw new AppError('Prompt is required', 400, 'MISSING_PROMPT');
            }
            
            // Track request start
            const requestId = googleAIMonitoring.trackRequestStart({
                model: model || 'auto-selected',
                taskType: 'vision_analysis',
                input: prompt,
                images: images
            });
            
            const options = {
                images,
                prompt,
                model,
                detail_level,
                analysis_type,
                auto_enhance_prompt
            };
            
            const result = await this.googleAIService.analyzeImages(options);
            
            // Track completion
            googleAIMonitoring.trackRequestComplete(requestId, result);
            
            res.json({
                success: true,
                ...result,
                requestId
            });
            
        } catch (error) {
            logger.error('Google AI vision analysis failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Generate embeddings with Google AI
     * POST /api/google-ai/embeddings
     */
    async generateEmbeddings(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Google AI service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                texts,
                task_type = 'SEMANTIC_SIMILARITY',
                title,
                batch_size = 50,
                normalize = true
            } = req.body;
            
            if (!texts || !Array.isArray(texts) || texts.length === 0) {
                throw new AppError('Texts array is required', 400, 'MISSING_TEXTS');
            }
            
            // Track request start
            const requestId = googleAIMonitoring.trackRequestStart({
                model: 'text-embedding-004',
                taskType: 'embedding_generation',
                input: texts
            });
            
            const options = {
                texts,
                task_type,
                title,
                batch_size,
                normalize
            };
            
            const result = await this.googleAIService.generateEmbeddings(options);
            
            // Track completion
            googleAIMonitoring.trackRequestComplete(requestId, result);
            
            res.json({
                success: true,
                ...result,
                requestId
            });
            
        } catch (error) {
            logger.error('Google AI embedding generation failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Function calling with Google AI
     * POST /api/google-ai/function-calling
     */
    async functionCalling(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Google AI service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                messages,
                functions,
                model,
                function_call_mode = 'auto',
                max_iterations = 5,
                auto_execute = false
            } = req.body;
            
            if (!messages || !Array.isArray(messages) || messages.length === 0) {
                throw new AppError('Messages array is required', 400, 'MISSING_MESSAGES');
            }
            
            if (!functions || !Array.isArray(functions) || functions.length === 0) {
                throw new AppError('Functions array is required', 400, 'MISSING_FUNCTIONS');
            }
            
            // Track request start
            const requestId = googleAIMonitoring.trackRequestStart({
                model: model || 'auto-selected',
                taskType: 'function_calling',
                input: messages,
                functions: functions
            });
            
            const options = {
                messages,
                functions,
                model,
                function_call_mode,
                max_iterations,
                auto_execute
            };
            
            const result = await this.googleAIService.functionCalling(options);
            
            // Track completion
            googleAIMonitoring.trackRequestComplete(requestId, result);
            
            res.json({
                success: true,
                ...result,
                requestId
            });
            
        } catch (error) {
            logger.error('Google AI function calling failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Code generation with Google AI
     * POST /api/google-ai/code
     */
    async generateCode(req, res, next) {
        try {
            if (!this.isInitialized) {
                throw new AppError('Google AI service not initialized', 503, 'SERVICE_NOT_INITIALIZED');
            }
            
            const {
                task,
                language,
                prompt,
                code,
                template,
                style_guide,
                include_tests = false,
                include_docs = false
            } = req.body;
            
            if (!task) {
                throw new AppError('Task is required', 400, 'MISSING_TASK');
            }
            
            if (!prompt) {
                throw new AppError('Prompt is required', 400, 'MISSING_PROMPT');
            }
            
            // Track request start
            const requestId = googleAIMonitoring.trackRequestStart({
                model: 'gemini-1.5-pro-latest',
                taskType: 'code_generation',
                input: prompt
            });
            
            const options = {
                task,
                language,
                prompt,
                code,
                template,
                style_guide,
                include_tests,
                include_docs
            };
            
            const result = await this.googleAIService.generateCode(options);
            
            // Track completion
            googleAIMonitoring.trackRequestComplete(requestId, result);
            
            res.json({
                success: true,
                ...result,
                requestId
            });
            
        } catch (error) {
            logger.error('Google AI code generation failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get Google AI service statistics
     * GET /api/google-ai/statistics
     */
    async getStatistics(req, res, next) {
        try {
            const serviceStats = this.googleAIService.getStatistics();
            const monitoringStats = googleAIMonitoring.getStatistics();
            
            res.json({
                success: true,
                statistics: {
                    service: serviceStats,
                    monitoring: monitoringStats,
                    timestamp: new Date().toISOString()
                }
            });
            
        } catch (error) {
            logger.error('Failed to get Google AI statistics', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get model performance comparison
     * GET /api/google-ai/model-comparison
     */
    async getModelComparison(req, res, next) {
        try {
            const comparison = googleAIMonitoring.getModelComparison();
            
            res.json({
                success: true,
                modelComparison: comparison,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get model comparison', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get cost analysis
     * GET /api/google-ai/cost-analysis
     */
    async getCostAnalysis(req, res, next) {
        try {
            const costAnalysis = googleAIMonitoring.getCostAnalysis();
            
            res.json({
                success: true,
                costAnalysis,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get cost analysis', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get safety analysis
     * GET /api/google-ai/safety-analysis
     */
    async getSafetyAnalysis(req, res, next) {
        try {
            const safetyAnalysis = googleAIMonitoring.getSafetyAnalysis();
            
            res.json({
                success: true,
                safetyAnalysis,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get safety analysis', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get service health check
     * GET /api/google-ai/health
     */
    async healthCheck(req, res, next) {
        try {
            const serviceHealth = await this.googleAIService.healthCheck();
            
            res.json({
                success: true,
                health: serviceHealth,
                initialized: this.isInitialized,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Google AI health check failed', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get available models
     * GET /api/google-ai/models
     */
    async getModels(req, res, next) {
        try {
            const adapterInfo = this.googleAIService.adapter.getAdapterInfo();
            
            res.json({
                success: true,
                models: adapterInfo.models,
                capabilities: adapterInfo.capabilities,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get Google AI models', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Reset monitoring metrics
     * POST /api/google-ai/reset-metrics
     */
    async resetMetrics(req, res, next) {
        try {
            googleAIMonitoring.resetMetrics();
            
            res.json({
                success: true,
                message: 'Google AI monitoring metrics reset successfully',
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to reset Google AI metrics', { error: error.message });
            next(error);
        }
    }
    
    /**
     * Get model recommendations for a task
     * POST /api/google-ai/recommend
     */
    async getModelRecommendations(req, res, next) {
        try {
            const { task_type, context = {} } = req.body;
            
            if (!task_type) {
                throw new AppError('Task type is required', 400, 'MISSING_TASK_TYPE');
            }
            
            // Get recommendations from both service and model router
            const serviceRecommendation = this.googleAIService.selectOptimalModel(task_type, context);
            
            res.json({
                success: true,
                recommendations: {
                    primaryModel: serviceRecommendation,
                    context,
                    reasoning: 'Selected based on task requirements and context'
                },
                availableModels: this.googleAIService.adapter.getAdapterInfo().models,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            logger.error('Failed to get model recommendations', { error: error.message });
            next(error);
        }
    }
}

module.exports = new GoogleAIController();
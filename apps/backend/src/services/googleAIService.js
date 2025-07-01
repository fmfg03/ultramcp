/**
 * Google AI Service - Enhanced service layer for Google AI integration
 * Provides high-level abstractions and intelligent routing for Google AI models
 */

const GoogleAIAdapter = require('../adapters/googleAIAdapter');
const logger = require('../utils/logger');
const { AppError } = require('../utils/AppError');
const { retryOperation } = require('../utils/retryUtils');

class GoogleAIService {
    constructor() {
        this.adapter = new GoogleAIAdapter();
        this.requestCounter = 0;
        this.costTracker = {
            totalCost: 0,
            requestCosts: [],
            modelUsage: new Map()
        };
        this.performanceMetrics = {
            averageResponseTime: 0,
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0
        };
    }
    
    /**
     * Initialize the service
     */
    async initialize() {
        try {
            await this.adapter._initialize();
            logger.info('Google AI Service initialized successfully');
            return true;
        } catch (error) {
            logger.error('Failed to initialize Google AI Service', { error: error.message });
            throw error;
        }
    }
    
    /**
     * Intelligent model selection based on task requirements
     */
    selectOptimalModel(taskType, requirements = {}) {
        const {
            complexity = 'medium',
            speed_priority = false,
            cost_priority = false,
            multimodal = false,
            long_context = false,
            function_calling = false
        } = requirements;
        
        // Model selection logic
        if (multimodal && (taskType === 'vision' || taskType === 'image_analysis')) {
            return speed_priority ? 'gemini-1.5-flash-latest' : 'gemini-1.5-pro-latest';
        }
        
        if (long_context || (taskType === 'document_analysis' && requirements.context_length > 50000)) {
            return cost_priority ? 'gemini-1.5-flash-latest' : 'gemini-1.5-pro-latest';
        }
        
        if (cost_priority && complexity === 'low') {
            return 'gemini-1.0-pro';
        }
        
        if (speed_priority) {
            return 'gemini-1.5-flash-latest';
        }
        
        if (complexity === 'high' || taskType === 'complex_reasoning') {
            return 'gemini-1.5-pro-latest';
        }
        
        if (function_calling || taskType === 'function_calling') {
            return 'gemini-1.5-pro-latest';
        }
        
        // Default balanced choice
        return 'gemini-1.5-flash-latest';
    }
    
    /**
     * Enhanced chat completion with intelligent features
     */
    async chatCompletion(options) {
        const requestId = `gai-${++this.requestCounter}`;
        const startTime = Date.now();
        
        try {
            const {
                messages,
                model: requestedModel,
                temperature = 0.7,
                max_tokens,
                system_instruction,
                task_type = 'general',
                auto_select_model = true,
                requirements = {}
            } = options;
            
            // Select optimal model if not specified or auto-selection enabled
            let model = requestedModel;
            if (!model || auto_select_model) {
                model = this.selectOptimalModel(task_type, requirements);
                logger.info('Auto-selected Google AI model', {
                    requestId,
                    selectedModel: model,
                    taskType: task_type,
                    requirements
                });
            }
            
            const result = await this.adapter.executeAction('google_ai_chat', {
                model,
                messages,
                temperature,
                maxOutputTokens: max_tokens,
                systemInstruction: system_instruction
            });
            
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, model, responseTime, result.result.usage, true);
            
            return {
                ...result,
                metadata: {
                    ...result.metadata,
                    responseTime,
                    autoSelectedModel: !requestedModel || auto_select_model,
                    taskType: task_type
                }
            };
            
        } catch (error) {
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, options.model || 'unknown', responseTime, null, false);
            
            logger.error('Google AI chat completion failed', {
                requestId,
                error: error.message,
                responseTime
            });
            
            throw error;
        }
    }
    
    /**
     * Enhanced vision analysis with preprocessing
     */
    async analyzeImages(options) {
        const requestId = `gai-vision-${++this.requestCounter}`;
        const startTime = Date.now();
        
        try {
            const {
                images,
                prompt,
                model: requestedModel,
                detail_level = 'high',
                analysis_type = 'general',
                auto_enhance_prompt = true
            } = options;
            
            // Select optimal vision model
            const model = requestedModel || this.selectOptimalModel('vision', {
                multimodal: true,
                speed_priority: detail_level === 'low'
            });
            
            // Enhance prompt based on analysis type
            let enhancedPrompt = prompt;
            if (auto_enhance_prompt) {
                enhancedPrompt = this._enhanceVisionPrompt(prompt, analysis_type);
            }
            
            const result = await this.adapter.executeAction('google_ai_vision', {
                model,
                images,
                prompt: enhancedPrompt,
                detail_level
            });
            
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, model, responseTime, result.result.usage, true);
            
            return {
                ...result,
                metadata: {
                    ...result.metadata,
                    responseTime,
                    analysisType: analysis_type,
                    promptEnhanced: auto_enhance_prompt
                }
            };
            
        } catch (error) {
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, options.model || 'unknown', responseTime, null, false);
            
            logger.error('Google AI vision analysis failed', {
                requestId,
                error: error.message,
                responseTime
            });
            
            throw error;
        }
    }
    
    /**
     * Batch embedding generation with optimization
     */
    async generateEmbeddings(options) {
        const requestId = `gai-embed-${++this.requestCounter}`;
        const startTime = Date.now();
        
        try {
            const {
                texts,
                task_type = 'SEMANTIC_SIMILARITY',
                title,
                batch_size = 50,
                normalize = true
            } = options;
            
            // Process in batches for large text arrays
            const batches = this._createBatches(texts, batch_size);
            const allEmbeddings = [];
            
            for (const batch of batches) {
                const result = await this.adapter.executeAction('google_ai_embedding', {
                    texts: batch,
                    task_type,
                    title
                });
                
                allEmbeddings.push(...result.result.embeddings);
            }
            
            // Normalize embeddings if requested
            if (normalize) {
                allEmbeddings.forEach(embedding => {
                    embedding.embedding = this._normalizeVector(embedding.embedding);
                });
            }
            
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, 'text-embedding-004', responseTime, null, true);
            
            logger.info('Batch embeddings generated', {
                requestId,
                totalTexts: texts.length,
                batches: batches.length,
                responseTime
            });
            
            return {
                success: true,
                result: {
                    embeddings: allEmbeddings,
                    model: 'text-embedding-004',
                    task_type,
                    total_texts: texts.length,
                    dimensions: allEmbeddings[0]?.dimensions || 0,
                    normalized: normalize
                },
                metadata: {
                    requestId,
                    provider: 'google_ai',
                    model: 'text-embedding-004',
                    responseTime,
                    batchCount: batches.length,
                    timestamp: new Date().toISOString()
                }
            };
            
        } catch (error) {
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, 'text-embedding-004', responseTime, null, false);
            
            logger.error('Google AI embedding generation failed', {
                requestId,
                error: error.message,
                responseTime
            });
            
            throw error;
        }
    }
    
    /**
     * Advanced function calling with retry logic
     */
    async functionCalling(options) {
        const requestId = `gai-func-${++this.requestCounter}`;
        const startTime = Date.now();
        
        try {
            const {
                messages,
                functions,
                model: requestedModel,
                function_call_mode = 'auto',
                max_iterations = 5,
                auto_execute = false
            } = options;
            
            const model = requestedModel || this.selectOptimalModel('function_calling', {
                function_calling: true
            });
            
            let currentMessages = [...messages];
            const executionHistory = [];
            
            for (let iteration = 0; iteration < max_iterations; iteration++) {
                const result = await this.adapter.executeAction('google_ai_function_calling', {
                    model,
                    messages: currentMessages,
                    functions,
                    function_call_mode
                });
                
                const functionCalls = result.result.functionCalls;
                
                if (functionCalls.length === 0) {
                    // No more function calls needed
                    const responseTime = Date.now() - startTime;
                    this._recordMetrics(requestId, model, responseTime, result.result.usage, true);
                    
                    return {
                        ...result,
                        metadata: {
                            ...result.metadata,
                            responseTime,
                            iterations: iteration + 1,
                            executionHistory
                        }
                    };
                }
                
                // Record function calls
                executionHistory.push({
                    iteration: iteration + 1,
                    functionCalls: functionCalls,
                    response: result.result.content
                });
                
                if (auto_execute) {
                    // Execute functions and add results to conversation
                    const functionResults = [];
                    
                    for (const call of functionCalls) {
                        try {
                            const functionResult = await this._executeFunctionCall(call, functions);
                            functionResults.push({
                                name: call.name,
                                result: functionResult
                            });
                        } catch (error) {
                            functionResults.push({
                                name: call.name,
                                error: error.message
                            });
                        }
                    }
                    
                    // Add function results to conversation
                    currentMessages.push({
                        role: 'assistant',
                        content: result.result.content,
                        functionCalls: functionCalls
                    });
                    
                    currentMessages.push({
                        role: 'user',
                        content: `Function execution results: ${JSON.stringify(functionResults, null, 2)}`
                    });
                } else {
                    // Return function calls for external execution
                    const responseTime = Date.now() - startTime;
                    this._recordMetrics(requestId, model, responseTime, result.result.usage, true);
                    
                    return {
                        ...result,
                        metadata: {
                            ...result.metadata,
                            responseTime,
                            iterations: iteration + 1,
                            executionHistory,
                            requiresExecution: true
                        }
                    };
                }
            }
            
            throw new AppError('Maximum function calling iterations reached', 400, 'MAX_ITERATIONS_REACHED');
            
        } catch (error) {
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, options.model || 'unknown', responseTime, null, false);
            
            logger.error('Google AI function calling failed', {
                requestId,
                error: error.message,
                responseTime
            });
            
            throw error;
        }
    }
    
    /**
     * Specialized code generation with templates
     */
    async generateCode(options) {
        const requestId = `gai-code-${++this.requestCounter}`;
        const startTime = Date.now();
        
        try {
            const {
                task,
                language,
                prompt,
                code,
                template,
                style_guide,
                include_tests = false,
                include_docs = false
            } = options;
            
            let enhancedPrompt = prompt;
            
            // Apply template if provided
            if (template) {
                enhancedPrompt = this._applyCodeTemplate(prompt, template, language);
            }
            
            // Add style guide requirements
            if (style_guide) {
                enhancedPrompt += `\n\nFollow these style guidelines: ${style_guide}`;
            }
            
            // Add test generation requirement
            if (include_tests) {
                enhancedPrompt += `\n\nInclude comprehensive unit tests for the generated code.`;
            }
            
            // Add documentation requirement
            if (include_docs) {
                enhancedPrompt += `\n\nInclude detailed documentation and comments explaining the code.`;
            }
            
            const model = this.selectOptimalModel('code_generation', {
                complexity: 'high',
                function_calling: false
            });
            
            const result = await this.adapter.executeAction('google_ai_code_generation', {
                model,
                task,
                language,
                code,
                prompt: enhancedPrompt
            });
            
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, model, responseTime, result.result.usage, true);
            
            // Parse code blocks from response if possible
            const parsedCode = this._parseCodeBlocks(result.result.content);
            
            return {
                ...result,
                result: {
                    ...result.result,
                    parsedCode,
                    includesTests: include_tests,
                    includesDocs: include_docs
                },
                metadata: {
                    ...result.metadata,
                    responseTime,
                    language,
                    task,
                    templateUsed: !!template
                }
            };
            
        } catch (error) {
            const responseTime = Date.now() - startTime;
            this._recordMetrics(requestId, 'unknown', responseTime, null, false);
            
            logger.error('Google AI code generation failed', {
                requestId,
                error: error.message,
                responseTime
            });
            
            throw error;
        }
    }
    
    /**
     * Get comprehensive service statistics
     */
    getStatistics() {
        const adapterStats = this.adapter.getStatistics();
        
        return {
            service: {
                requestCounter: this.requestCounter,
                performance: this.performanceMetrics,
                costTracking: {
                    totalCost: this.costTracker.totalCost,
                    averageCostPerRequest: this.costTracker.totalCost / Math.max(this.requestCounter, 1),
                    requestCount: this.costTracker.requestCosts.length,
                    modelUsage: Object.fromEntries(this.costTracker.modelUsage)
                }
            },
            adapter: adapterStats,
            models: adapterStats.modelConfigs
        };
    }
    
    /**
     * Health check for the service
     */
    async healthCheck() {
        try {
            const adapterHealth = await this.adapter.healthCheck();
            
            return {
                service: 'healthy',
                adapter: adapterHealth,
                statistics: {
                    totalRequests: this.performanceMetrics.totalRequests,
                    successRate: this.performanceMetrics.totalRequests > 0 
                        ? (this.performanceMetrics.successfulRequests / this.performanceMetrics.totalRequests * 100)
                        : 0,
                    averageResponseTime: this.performanceMetrics.averageResponseTime
                }
            };
            
        } catch (error) {
            return {
                service: 'unhealthy',
                error: error.message,
                adapter: { status: 'unknown' }
            };
        }
    }
    
    // Private helper methods
    
    _recordMetrics(requestId, model, responseTime, usage, success) {
        this.performanceMetrics.totalRequests++;
        
        if (success) {
            this.performanceMetrics.successfulRequests++;
        } else {
            this.performanceMetrics.failedRequests++;
        }
        
        // Update average response time
        const totalRequests = this.performanceMetrics.totalRequests;
        const currentAverage = this.performanceMetrics.averageResponseTime;
        this.performanceMetrics.averageResponseTime = 
            ((currentAverage * (totalRequests - 1)) + responseTime) / totalRequests;
        
        // Track model usage
        if (!this.costTracker.modelUsage.has(model)) {
            this.costTracker.modelUsage.set(model, { requests: 0, totalTokens: 0, totalCost: 0 });
        }
        
        const modelStats = this.costTracker.modelUsage.get(model);
        modelStats.requests++;
        
        if (usage) {
            modelStats.totalTokens += usage.totalTokens;
            const cost = this.adapter.calculateCost(model, usage);
            modelStats.totalCost += cost;
            this.costTracker.totalCost += cost;
            
            this.costTracker.requestCosts.push({
                requestId,
                model,
                cost,
                usage,
                timestamp: new Date().toISOString()
            });
            
            // Keep only last 1000 request costs
            if (this.costTracker.requestCosts.length > 1000) {
                this.costTracker.requestCosts = this.costTracker.requestCosts.slice(-1000);
            }
        }
    }
    
    _enhanceVisionPrompt(prompt, analysisType) {
        const enhancements = {
            'object_detection': 'Identify and locate all objects in the image. Provide bounding box descriptions if possible.',
            'text_extraction': 'Extract all text visible in the image, including any handwritten text.',
            'scene_description': 'Provide a detailed description of the scene, including setting, activities, and context.',
            'technical_analysis': 'Perform a technical analysis focusing on composition, lighting, quality, and technical aspects.',
            'accessibility': 'Describe the image for accessibility purposes, including all visual elements that would be important for someone who cannot see the image.'
        };
        
        const enhancement = enhancements[analysisType];
        return enhancement ? `${enhancement}\n\n${prompt}` : prompt;
    }
    
    _createBatches(array, batchSize) {
        const batches = [];
        for (let i = 0; i < array.length; i += batchSize) {
            batches.push(array.slice(i, i + batchSize));
        }
        return batches;
    }
    
    _normalizeVector(vector) {
        const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
        return magnitude > 0 ? vector.map(val => val / magnitude) : vector;
    }
    
    async _executeFunctionCall(call, functions) {
        // This would integrate with the actual function execution system
        // For now, return a placeholder
        return `Function ${call.name} would be executed with args: ${JSON.stringify(call.args)}`;
    }
    
    _applyCodeTemplate(prompt, template, language) {
        const templates = {
            'clean_architecture': `Generate clean, well-structured ${language} code following clean architecture principles. ${prompt}`,
            'microservice': `Create a ${language} microservice implementation. ${prompt}`,
            'api_endpoint': `Implement a RESTful API endpoint in ${language}. ${prompt}`,
            'data_processing': `Create efficient data processing code in ${language}. ${prompt}`,
            'testing': `Generate comprehensive test code in ${language}. ${prompt}`
        };
        
        return templates[template] || prompt;
    }
    
    _parseCodeBlocks(content) {
        const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
        const codeBlocks = [];
        let match;
        
        while ((match = codeBlockRegex.exec(content)) !== null) {
            codeBlocks.push({
                language: match[1] || 'unknown',
                code: match[2].trim()
            });
        }
        
        return codeBlocks;
    }
}

module.exports = GoogleAIService;
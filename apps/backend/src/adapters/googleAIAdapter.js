/**
 * Google AI (Gemini) Adapter for SUPERmcp
 * Comprehensive integration with Google's Gemini models including Pro, Flash, and specialized models
 * 
 * Features:
 * - Multi-modal support (text, vision, code)
 * - Embedding generation
 * - Function calling
 * - Long context handling
 * - Cost optimization
 * - Error handling and retries
 */

const { GoogleGenerativeAI, HarmCategory, HarmBlockThreshold } = require('@google/generative-ai');
const logger = require('../utils/logger');
const { retryOperation } = require('../utils/retryUtils');
const { AppError } = require('../utils/AppError');

class GoogleAIAdapter {
    constructor() {
        this.apiKey = process.env.GOOGLE_API_KEY;
        this.genAI = null;
        this.models = new Map();
        this.requestCounter = 0;
        this.isInitialized = false;
        
        // Model configurations
        this.modelConfigs = {
            'gemini-1.5-pro-latest': {
                name: 'Gemini 1.5 Pro',
                maxTokens: 1000000,
                features: ['chat', 'vision', 'function_calling', 'long_context'],
                pricing: { input: 3.50, output: 10.50 },
                description: 'Most capable multimodal model with long context'
            },
            'gemini-1.5-flash-latest': {
                name: 'Gemini 1.5 Flash',
                maxTokens: 1000000,
                features: ['chat', 'vision', 'function_calling', 'fast_response'],
                pricing: { input: 0.35, output: 0.70 },
                description: 'Fast and cost-effective multimodal model'
            },
            'gemini-1.0-pro': {
                name: 'Gemini 1.0 Pro',
                maxTokens: 32768,
                features: ['chat', 'function_calling'],
                pricing: { input: 0.50, output: 1.50 },
                description: 'Balanced performance and cost model'
            },
            'text-embedding-004': {
                name: 'Text Embedding 004',
                maxTokens: 8192,
                features: ['embedding'],
                pricing: { input: 0.20, output: null },
                description: 'Latest text embedding model'
            }
        };
        
        // Safety settings
        this.safetySettings = [
            {
                category: HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            {
                category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            {
                category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            {
                category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
        ];
        
        this._initialize();
    }
    
    /**
     * Initialize the Google AI adapter
     */
    async _initialize() {
        try {
            if (!this.apiKey) {
                logger.warn('Google AI API key not found. Set GOOGLE_API_KEY environment variable.');
                return;
            }
            
            this.genAI = new GoogleGenerativeAI(this.apiKey);
            
            // Initialize model instances
            for (const [modelId, config] of Object.entries(this.modelConfigs)) {
                if (config.features.includes('chat') || config.features.includes('embedding')) {
                    const model = this.genAI.getGenerativeModel({ 
                        model: modelId,
                        safetySettings: this.safetySettings
                    });
                    this.models.set(modelId, model);
                }
            }
            
            this.isInitialized = true;
            logger.info('Google AI adapter initialized successfully', {
                availableModels: Array.from(this.models.keys())
            });
            
        } catch (error) {
            logger.error('Failed to initialize Google AI adapter', { error: error.message });
            throw new AppError('Google AI initialization failed', 500, 'GOOGLE_AI_INIT_ERROR');
        }
    }
    
    /**
     * Get adapter information
     */
    getAdapterInfo() {
        return {
            name: 'Google AI (Gemini)',
            version: '1.0.0',
            description: 'Comprehensive Google AI integration with Gemini models',
            capabilities: [
                'text_generation',
                'multimodal_processing',
                'function_calling',
                'long_context_handling',
                'embedding_generation',
                'vision_analysis',
                'code_generation'
            ],
            models: Object.keys(this.modelConfigs),
            isInitialized: this.isInitialized,
            requiresAuth: true
        };
    }
    
    /**
     * Get available tools/functions for MCP
     */
    getTools() {
        return [
            {
                name: 'google_ai_chat',
                description: 'Generate text using Google AI Gemini models',
                inputSchema: {
                    type: 'object',
                    properties: {
                        model: {
                            type: 'string',
                            enum: ['gemini-1.5-pro-latest', 'gemini-1.5-flash-latest', 'gemini-1.0-pro'],
                            description: 'Gemini model to use'
                        },
                        messages: {
                            type: 'array',
                            description: 'Array of message objects with role and content'
                        },
                        temperature: {
                            type: 'number',
                            minimum: 0,
                            maximum: 2,
                            description: 'Sampling temperature'
                        },
                        maxOutputTokens: {
                            type: 'number',
                            description: 'Maximum tokens to generate'
                        },
                        systemInstruction: {
                            type: 'string',
                            description: 'System instruction for the model'
                        }
                    },
                    required: ['model', 'messages']
                }
            },
            {
                name: 'google_ai_vision',
                description: 'Analyze images using Google AI vision capabilities',
                inputSchema: {
                    type: 'object',
                    properties: {
                        model: {
                            type: 'string',
                            enum: ['gemini-1.5-pro-latest', 'gemini-1.5-flash-latest'],
                            description: 'Vision-capable Gemini model'
                        },
                        images: {
                            type: 'array',
                            description: 'Array of image data (base64 or URLs)'
                        },
                        prompt: {
                            type: 'string',
                            description: 'Text prompt for image analysis'
                        },
                        detail_level: {
                            type: 'string',
                            enum: ['low', 'high'],
                            description: 'Level of detail for analysis'
                        }
                    },
                    required: ['model', 'images', 'prompt']
                }
            },
            {
                name: 'google_ai_embedding',
                description: 'Generate text embeddings using Google AI',
                inputSchema: {
                    type: 'object',
                    properties: {
                        texts: {
                            type: 'array',
                            items: { type: 'string' },
                            description: 'Array of texts to embed'
                        },
                        task_type: {
                            type: 'string',
                            enum: ['RETRIEVAL_QUERY', 'RETRIEVAL_DOCUMENT', 'SEMANTIC_SIMILARITY', 'CLASSIFICATION', 'CLUSTERING'],
                            description: 'Type of embedding task'
                        },
                        title: {
                            type: 'string',
                            description: 'Optional title for the text'
                        }
                    },
                    required: ['texts']
                }
            },
            {
                name: 'google_ai_function_calling',
                description: 'Use Google AI with function calling capabilities',
                inputSchema: {
                    type: 'object',
                    properties: {
                        model: {
                            type: 'string',
                            enum: ['gemini-1.5-pro-latest', 'gemini-1.5-flash-latest', 'gemini-1.0-pro'],
                            description: 'Function-calling capable model'
                        },
                        messages: {
                            type: 'array',
                            description: 'Conversation messages'
                        },
                        functions: {
                            type: 'array',
                            description: 'Available functions for the model'
                        },
                        function_call_mode: {
                            type: 'string',
                            enum: ['auto', 'any', 'none'],
                            description: 'Function calling mode'
                        }
                    },
                    required: ['model', 'messages', 'functions']
                }
            },
            {
                name: 'google_ai_code_generation',
                description: 'Generate and analyze code using Google AI',
                inputSchema: {
                    type: 'object',
                    properties: {
                        model: {
                            type: 'string',
                            enum: ['gemini-1.5-pro-latest', 'gemini-1.5-flash-latest'],
                            description: 'Code-capable Gemini model'
                        },
                        task: {
                            type: 'string',
                            enum: ['generate', 'explain', 'debug', 'optimize', 'translate'],
                            description: 'Code-related task to perform'
                        },
                        language: {
                            type: 'string',
                            description: 'Programming language'
                        },
                        code: {
                            type: 'string',
                            description: 'Existing code (for explain/debug/optimize tasks)'
                        },
                        prompt: {
                            type: 'string',
                            description: 'Description of what to generate or do'
                        }
                    },
                    required: ['model', 'task', 'prompt']
                }
            }
        ];
    }
    
    /**
     * Execute a tool/function
     */
    async executeAction(actionName, parameters) {
        if (!this.isInitialized) {
            throw new AppError('Google AI adapter not initialized', 500, 'ADAPTER_NOT_INITIALIZED');
        }
        
        this.requestCounter++;
        const requestId = `google-ai-${this.requestCounter}`;
        
        logger.info('Executing Google AI action', {
            requestId,
            actionName,
            model: parameters.model,
            hasImages: !!parameters.images?.length
        });
        
        try {
            switch (actionName) {
                case 'google_ai_chat':
                    return await this._handleChatCompletion(parameters, requestId);
                case 'google_ai_vision':
                    return await this._handleVisionAnalysis(parameters, requestId);
                case 'google_ai_embedding':
                    return await this._handleEmbedding(parameters, requestId);
                case 'google_ai_function_calling':
                    return await this._handleFunctionCalling(parameters, requestId);
                case 'google_ai_code_generation':
                    return await this._handleCodeGeneration(parameters, requestId);
                default:
                    throw new AppError(`Unknown action: ${actionName}`, 400, 'UNKNOWN_ACTION');
            }
        } catch (error) {
            logger.error('Google AI action failed', {
                requestId,
                actionName,
                error: error.message,
                model: parameters.model
            });
            throw error;
        }
    }
    
    /**
     * Handle chat completion
     */
    async _handleChatCompletion(parameters, requestId) {
        const { model, messages, temperature = 0.7, maxOutputTokens, systemInstruction } = parameters;
        
        const modelInstance = this.models.get(model);
        if (!modelInstance) {
            throw new AppError(`Model ${model} not available`, 400, 'MODEL_NOT_AVAILABLE');
        }
        
        return await retryOperation(async () => {
            const generationConfig = {
                temperature,
                maxOutputTokens: maxOutputTokens || 8192
            };
            
            // Configure model with system instruction if provided
            let workingModel = modelInstance;
            if (systemInstruction) {
                workingModel = this.genAI.getGenerativeModel({
                    model,
                    systemInstruction,
                    safetySettings: this.safetySettings
                });
            }
            
            // Convert messages to Gemini format
            const history = this._convertMessagesToGeminiFormat(messages.slice(0, -1));
            const lastMessage = messages[messages.length - 1];
            
            const chat = workingModel.startChat({
                history,
                generationConfig
            });
            
            const result = await chat.sendMessage(lastMessage.content);
            const response = await result.response;
            
            const usage = {
                promptTokens: response.usageMetadata?.promptTokenCount || 0,
                completionTokens: response.usageMetadata?.candidatesTokenCount || 0,
                totalTokens: response.usageMetadata?.totalTokenCount || 0
            };
            
            logger.info('Google AI chat completion successful', {
                requestId,
                model,
                usage,
                responseLength: response.text().length
            });
            
            return {
                success: true,
                result: {
                    content: response.text(),
                    model,
                    usage,
                    finishReason: response.candidates?.[0]?.finishReason || 'stop',
                    safetyRatings: response.candidates?.[0]?.safetyRatings || []
                },
                metadata: {
                    requestId,
                    provider: 'google_ai',
                    model,
                    timestamp: new Date().toISOString()
                }
            };
        }, 3);
    }
    
    /**
     * Handle vision analysis
     */
    async _handleVisionAnalysis(parameters, requestId) {
        const { model, images, prompt, detail_level = 'high' } = parameters;
        
        const modelInstance = this.models.get(model);
        if (!modelInstance) {
            throw new AppError(`Model ${model} not available`, 400, 'MODEL_NOT_AVAILABLE');
        }
        
        if (!this.modelConfigs[model].features.includes('vision')) {
            throw new AppError(`Model ${model} does not support vision`, 400, 'VISION_NOT_SUPPORTED');
        }
        
        return await retryOperation(async () => {
            const imageParts = await this._processImages(images);
            
            const parts = [
                { text: prompt },
                ...imageParts
            ];
            
            const result = await modelInstance.generateContent(parts);
            const response = await result.response;
            
            const usage = {
                promptTokens: response.usageMetadata?.promptTokenCount || 0,
                completionTokens: response.usageMetadata?.candidatesTokenCount || 0,
                totalTokens: response.usageMetadata?.totalTokenCount || 0
            };
            
            logger.info('Google AI vision analysis successful', {
                requestId,
                model,
                imageCount: images.length,
                usage
            });
            
            return {
                success: true,
                result: {
                    analysis: response.text(),
                    model,
                    usage,
                    imageCount: images.length,
                    detailLevel: detail_level,
                    safetyRatings: response.candidates?.[0]?.safetyRatings || []
                },
                metadata: {
                    requestId,
                    provider: 'google_ai',
                    model,
                    timestamp: new Date().toISOString()
                }
            };
        }, 3);
    }
    
    /**
     * Handle embedding generation
     */
    async _handleEmbedding(parameters, requestId) {
        const { texts, task_type = 'SEMANTIC_SIMILARITY', title } = parameters;
        
        const model = this.genAI.getGenerativeModel({ model: 'text-embedding-004' });
        
        return await retryOperation(async () => {
            const embeddings = [];
            
            for (const text of texts) {
                const embeddingParams = {
                    content: text,
                    taskType: task_type
                };
                
                if (title) {
                    embeddingParams.title = title;
                }
                
                const result = await model.embedContent(embeddingParams);
                embeddings.push({
                    text,
                    embedding: result.embedding.values,
                    dimensions: result.embedding.values.length
                });
            }
            
            logger.info('Google AI embeddings generated', {
                requestId,
                textCount: texts.length,
                dimensions: embeddings[0]?.dimensions,
                taskType: task_type
            });
            
            return {
                success: true,
                result: {
                    embeddings,
                    model: 'text-embedding-004',
                    task_type,
                    total_texts: texts.length,
                    dimensions: embeddings[0]?.dimensions || 0
                },
                metadata: {
                    requestId,
                    provider: 'google_ai',
                    model: 'text-embedding-004',
                    timestamp: new Date().toISOString()
                }
            };
        }, 3);
    }
    
    /**
     * Handle function calling
     */
    async _handleFunctionCalling(parameters, requestId) {
        const { model, messages, functions, function_call_mode = 'auto' } = parameters;
        
        const modelInstance = this.models.get(model);
        if (!modelInstance) {
            throw new AppError(`Model ${model} not available`, 400, 'MODEL_NOT_AVAILABLE');
        }
        
        return await retryOperation(async () => {
            // Convert functions to Gemini format
            const tools = [{
                functionDeclarations: functions.map(func => ({
                    name: func.name,
                    description: func.description,
                    parameters: func.parameters || {}
                }))
            }];
            
            const workingModel = this.genAI.getGenerativeModel({
                model,
                tools,
                safetySettings: this.safetySettings
            });
            
            const history = this._convertMessagesToGeminiFormat(messages.slice(0, -1));
            const lastMessage = messages[messages.length - 1];
            
            const chat = workingModel.startChat({ history });
            const result = await chat.sendMessage(lastMessage.content);
            const response = await result.response;
            
            const functionCalls = response.functionCalls() || [];
            
            logger.info('Google AI function calling completed', {
                requestId,
                model,
                functionCallsCount: functionCalls.length,
                responseText: response.text()
            });
            
            return {
                success: true,
                result: {
                    content: response.text(),
                    functionCalls: functionCalls.map(call => ({
                        name: call.name,
                        args: call.args
                    })),
                    model,
                    usage: {
                        promptTokens: response.usageMetadata?.promptTokenCount || 0,
                        completionTokens: response.usageMetadata?.candidatesTokenCount || 0,
                        totalTokens: response.usageMetadata?.totalTokenCount || 0
                    }
                },
                metadata: {
                    requestId,
                    provider: 'google_ai',
                    model,
                    timestamp: new Date().toISOString()
                }
            };
        }, 3);
    }
    
    /**
     * Handle code generation
     */
    async _handleCodeGeneration(parameters, requestId) {
        const { model, task, language, code, prompt } = parameters;
        
        let systemPrompt = '';
        let userPrompt = prompt;
        
        switch (task) {
            case 'generate':
                systemPrompt = `You are an expert ${language || 'programming'} developer. Generate clean, efficient, and well-commented code.`;
                break;
            case 'explain':
                systemPrompt = `You are a code analysis expert. Explain the provided code clearly and comprehensively.`;
                userPrompt = `Please explain this ${language || ''} code:\n\n${code}\n\nExplanation: ${prompt}`;
                break;
            case 'debug':
                systemPrompt = `You are a debugging expert. Identify and fix issues in the provided code.`;
                userPrompt = `Debug this ${language || ''} code:\n\n${code}\n\nIssue description: ${prompt}`;
                break;
            case 'optimize':
                systemPrompt = `You are a code optimization expert. Improve the performance and efficiency of the provided code.`;
                userPrompt = `Optimize this ${language || ''} code:\n\n${code}\n\nOptimization goals: ${prompt}`;
                break;
            case 'translate':
                systemPrompt = `You are a code translation expert. Convert code between programming languages while maintaining functionality.`;
                userPrompt = `Translate this code to ${language}:\n\n${code}\n\nAdditional requirements: ${prompt}`;
                break;
        }
        
        const messages = [
            { role: 'user', content: userPrompt }
        ];
        
        return await this._handleChatCompletion({
            model,
            messages,
            systemInstruction: systemPrompt,
            temperature: 0.3 // Lower temperature for code tasks
        }, requestId);
    }
    
    /**
     * Convert messages to Gemini format
     */
    _convertMessagesToGeminiFormat(messages) {
        return messages.map(msg => ({
            role: msg.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: msg.content }]
        }));
    }
    
    /**
     * Process images for vision analysis
     */
    async _processImages(images) {
        const imageParts = [];
        
        for (const image of images) {
            if (typeof image === 'string') {
                if (image.startsWith('data:')) {
                    // Base64 encoded image
                    const [mimeType, data] = image.split(',');
                    imageParts.push({
                        inlineData: {
                            data: data,
                            mimeType: mimeType.split(';')[0].split(':')[1]
                        }
                    });
                } else if (image.startsWith('http')) {
                    // URL - would need to fetch and convert
                    throw new AppError('URL images not yet supported', 400, 'URL_IMAGES_NOT_SUPPORTED');
                } else {
                    // Assume it's base64 without prefix
                    imageParts.push({
                        inlineData: {
                            data: image,
                            mimeType: 'image/jpeg' // Default assumption
                        }
                    });
                }
            }
        }
        
        return imageParts;
    }
    
    /**
     * Get model pricing information
     */
    getModelPricing(model) {
        return this.modelConfigs[model]?.pricing || null;
    }
    
    /**
     * Calculate cost for a request
     */
    calculateCost(model, usage) {
        const pricing = this.getModelPricing(model);
        if (!pricing || !usage) return 0;
        
        const inputCost = (usage.promptTokens / 1000000) * pricing.input;
        const outputCost = pricing.output ? (usage.completionTokens / 1000000) * pricing.output : 0;
        
        return inputCost + outputCost;
    }
    
    /**
     * Get adapter statistics
     */
    getStatistics() {
        return {
            requestCounter: this.requestCounter,
            isInitialized: this.isInitialized,
            availableModels: Array.from(this.models.keys()),
            modelConfigs: this.modelConfigs
        };
    }
    
    /**
     * Health check
     */
    async healthCheck() {
        if (!this.isInitialized) {
            return {
                status: 'unhealthy',
                reason: 'Adapter not initialized'
            };
        }
        
        try {
            // Simple test with the fastest model
            const testModel = this.models.get('gemini-1.5-flash-latest');
            if (testModel) {
                const result = await testModel.generateContent('Hello');
                const response = await result.response;
                
                return {
                    status: 'healthy',
                    responseTime: Date.now(),
                    modelsAvailable: this.models.size,
                    testResponse: response.text().length > 0
                };
            }
            
            return {
                status: 'degraded',
                reason: 'No models available for testing'
            };
            
        } catch (error) {
            return {
                status: 'unhealthy',
                reason: error.message
            };
        }
    }
}

module.exports = GoogleAIAdapter;
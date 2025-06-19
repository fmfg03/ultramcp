/**
 * @file modelRouterService.js
 * @description Service for dynamically selecting the optimal LLM based on task requirements.
 */

const DEFAULT_TEMPERATURE = 0.7;

class ModelRouterService {
    /**
     * @constructor
     * Initializes the ModelRouterService with a predefined set of models and their capabilities.
     */
    constructor() {
        this.models = {
            // Claude Models
            "claude-3-opus-20240229": {
                name: "Claude 3 Opus",
                provider: "anthropic",
                model_id_provider: "claude-3-opus-20240229",
                context_window_tokens: 200000,
                input_cost_per_mtok: 15.00,
                output_cost_per_mtok: 75.00,
                supports_tools: true,
                supports_json: true,
                supports_vision: true,
                strengths: ["complex_reasoning", "research", "long_form_content"],
                latency_profile: "moderate",
                description: "Most powerful model, for complex analysis, research, and long-form content generation.",
                notes: "Requires ANTHROPIC_API_KEY"
            },
            "claude-3-5-sonnet-20240620": {
                name: "Claude 3.5 Sonnet",
                provider: "anthropic",
                model_id_provider: "claude-3-5-sonnet-20240620",
                context_window_tokens: 200000,
                input_cost_per_mtok: 3.00,
                output_cost_per_mtok: 15.00,
                supports_tools: true,
                supports_json: true,
                supports_vision: true,
                strengths: ["enterprise_workloads", "scaled_ai", "web_search_tasks", "coding", "vision"],
                latency_profile: "moderate",
                description: "Balanced performance and speed, ideal for enterprise workloads, scaled AI deployments, and tasks like web search.",
                notes: "Requires ANTHROPIC_API_KEY"
            },
            "claude-3-sonnet-20240229": {
                name: "Claude 3 Sonnet",
                provider: "anthropic",
                model_id_provider: "claude-3-sonnet-20240229",
                context_window_tokens: 200000,
                input_cost_per_mtok: 3.00,
                output_cost_per_mtok: 15.00,
                supports_tools: true,
                supports_json: true,
                supports_vision: true,
                strengths: ["enterprise_workloads", "scaled_ai"],
                latency_profile: "moderate",
                description: "Balanced performance and speed, ideal for enterprise workloads and scaled AI deployments.",
                notes: "Requires ANTHROPIC_API_KEY"
            },
            "claude-3-haiku-20240307": {
                name: "Claude 3 Haiku",
                provider: "anthropic",
                model_id_provider: "claude-3-haiku-20240307",
                context_window_tokens: 200000,
                input_cost_per_mtok: 0.25,
                output_cost_per_mtok: 1.25,
                supports_tools: true,
                supports_json: true,
                supports_vision: true,
                strengths: ["quick_response", "simple_tasks", "summarization"],
                latency_profile: "fast",
                description: "Fastest and most compact model, for near real-time interactions and simple tasks.",
                notes: "Requires ANTHROPIC_API_KEY"
            },
            // OpenAI Models
            "gpt-4-turbo": {
                name: "GPT-4 Turbo",
                provider: "openai",
                model_id_provider: "gpt-4-turbo",
                context_window_tokens: 128000,
                input_cost_per_mtok: 10.00,
                output_cost_per_mtok: 30.00,
                supports_tools: true,
                supports_json: true,
                supports_vision: true,
                strengths: ["complex_reasoning", "code_generation", "creative_content"],
                latency_profile: "moderate",
                description: "OpenAI's most capable model with broad general knowledge and advanced reasoning.",
                notes: "Requires OPENAI_API_KEY"
            },
            "gpt-3.5-turbo": {
                name: "GPT-3.5 Turbo",
                provider: "openai",
                model_id_provider: "gpt-3.5-turbo",
                context_window_tokens: 16385,
                input_cost_per_mtok: 0.50,
                output_cost_per_mtok: 1.50,
                supports_tools: true,
                supports_json: true,
                supports_vision: false,
                strengths: ["general_purpose", "dialogue", "quick_response"],
                latency_profile: "fast",
                description: "Fast and cost-effective model for a wide range of tasks.",
                notes: "Requires OPENAI_API_KEY"
            },
            // Gemini Models (Google AI)
            "gemini-1.5-pro-latest": {
                name: "Gemini 1.5 Pro",
                provider: "google_genai",
                model_id_provider: "gemini-1.5-pro-latest",
                context_window_tokens: 1000000,
                input_cost_per_mtok: 3.50, 
                output_cost_per_mtok: 10.50, 
                supports_tools: true, 
                supports_json: true, 
                supports_vision: true,
                strengths: ["multimodal", "long_context", "complex_reasoning", "code_generation"],
                latency_profile: "moderate",
                description: "Google's most capable multimodal model with a long context window.",
                notes: "Requires GOOGLE_API_KEY. Pricing tiers for context >128K tokens."
            },
            "gemini-1.5-flash-latest": {
                name: "Gemini 1.5 Flash",
                provider: "google_genai",
                model_id_provider: "gemini-1.5-flash-latest",
                context_window_tokens: 1000000,
                input_cost_per_mtok: 0.35, 
                output_cost_per_mtok: 0.70, 
                supports_tools: true,
                supports_json: true,
                supports_vision: true,
                strengths: ["multimodal", "long_context", "fast_response", "cost_effective_large_scale"],
                latency_profile: "fast",
                description: "Fast and versatile multimodal model, optimized for speed and cost at scale.",
                notes: "Requires GOOGLE_API_KEY. Pricing tiers for context >128K tokens."
            },
            "gemini-1.0-pro": { 
                name: "Gemini 1.0 Pro",
                provider: "google_genai",
                model_id_provider: "gemini-1.0-pro",
                context_window_tokens: 32768,
                input_cost_per_mtok: 0.50,
                output_cost_per_mtok: 1.50,
                supports_tools: true,
                supports_json: true,
                supports_vision: true,
                strengths: ["general_purpose_llm", "balanced_performance"],
                latency_profile: "moderate",
                description: "Google's capable model for a balance of performance and cost.",
                notes: "Requires GOOGLE_API_KEY"
            },
            "text-embedding-004": {
                name: "Text Embedding 004",
                provider: "google_genai",
                model_id_provider: "text-embedding-004",
                context_window_tokens: 8192,
                input_cost_per_mtok: 0.20,
                output_cost_per_mtok: null,
                supports_tools: false,
                supports_json: false,
                supports_vision: false,
                strengths: ["text_embedding"],
                latency_profile: "fast",
                description: "Google's latest text embedding model.",
                notes: "Requires GOOGLE_API_KEY. Used for generating embeddings, not chat."
            },
            // DeepSeek Models
            "deepseek-chat": {
                name: "DeepSeek V2 (Chat)",
                provider: "deepseek",
                model_id_provider: "deepseek-chat",
                context_window_tokens: 64000, 
                input_cost_per_mtok: 0.27, 
                output_cost_per_mtok: 1.10, 
                supports_tools: false, 
                supports_json: true, 
                supports_vision: false,
                strengths: ["coding", "reasoning", "cost_effective_chat", "multilingual"],
                latency_profile: "moderate", 
                description: "DeepSeek's V2 model, strong in coding and reasoning, cost-effective for chat applications.",
                notes: "Requires DEEPSEEK_API_KEY. Off-peak pricing discounts available."
            },
            "deepseek-reasoner": {
                name: "DeepSeek R1 (Reasoner)",
                provider: "deepseek",
                model_id_provider: "deepseek-reasoner",
                context_window_tokens: 64000, 
                input_cost_per_mtok: 0.55, 
                output_cost_per_mtok: 2.19, 
                supports_tools: false, 
                supports_json: true, 
                supports_vision: false,
                strengths: ["advanced_reasoning", "complex_problem_solving", "chain_of_thought"],
                latency_profile: "moderate-to-slow", 
                description: "DeepSeek's R1 model, specialized in complex reasoning and chain-of-thought processes.",
                notes: "Requires DEEPSEEK_API_KEY. Off-peak pricing discounts available. Output includes CoT."
            },
            // Mistral AI Models
            "mistral-large-latest": {
                name: "Mistral Large",
                provider: "mistralai",
                model_id_provider: "mistral-large-latest",
                context_window_tokens: 128000,
                input_cost_per_mtok: 4.00,
                output_cost_per_mtok: 12.00,
                supports_tools: true,
                supports_json: true,
                supports_vision: false,
                strengths: ["top_tier_reasoning", "multilingual", "complex_instruction_following"],
                latency_profile: "moderate",
                description: "Mistral AI's flagship model, offering top-tier reasoning and multilingual capabilities.",
                notes: "Requires MISTRAL_API_KEY. Check API for latest model versions."
            },
            "open-mixtral-8x7b": {
                name: "Open Mixtral 8x7B",
                provider: "mistralai",
                model_id_provider: "open-mixtral-8x7b",
                context_window_tokens: 32000,
                input_cost_per_mtok: 0.70,
                output_cost_per_mtok: 0.70,
                supports_tools: true,
                supports_json: true,
                supports_vision: false,
                strengths: ["strong_performance_open_model", "cost_effective_high_throughput"],
                latency_profile: "moderate",
                description: "High-quality sparse mixture-of-experts model, open weights.",
                notes: "Requires MISTRAL_API_KEY if using Mistral's API. Can be self-hosted."
            },
            "mistral-small-latest": {
                name: "Mistral Small",
                provider: "mistralai",
                model_id_provider: "mistral-small-latest",
                context_window_tokens: 32000,
                input_cost_per_mtok: 1.00,
                output_cost_per_mtok: 3.00,
                supports_tools: true,
                supports_json: true,
                supports_vision: false,
                strengths: ["cost_effective", "low_latency", "simple_tasks"],
                latency_profile: "fast",
                description: "Cost-effective model for simple tasks requiring low latency.",
                notes: "Requires MISTRAL_API_KEY. Check API for latest model versions."
            },
            "mistral-embed": {
                name: "Mistral Embed",
                provider: "mistralai",
                model_id_provider: "mistral-embed",
                context_window_tokens: 8192,
                input_cost_per_mtok: 0.10,
                output_cost_per_mtok: null,
                supports_tools: false,
                supports_json: false,
                supports_vision: false,
                strengths: ["text_embedding"],
                latency_profile: "fast",
                description: "Mistral AI's embedding model.",
                notes: "Requires MISTRAL_API_KEY. Used for generating embeddings."
            },
            // Hugging Face Models
            "huggingface-endpoint-generic": {
                name: "Generic Hugging Face Inference Endpoint",
                provider: "huggingface_endpoint",
                model_id_provider: "<YOUR_ENDPOINT_URL_HERE>",
                context_window_tokens: null, 
                input_cost_per_mtok: null, 
                output_cost_per_mtok: null,
                supports_tools: null, 
                supports_json: null,
                supports_vision: null,
                strengths: ["custom_model_deployment", "fine_tuned_models"],
                latency_profile: "variable",
                description: "Placeholder for a user-configured Hugging Face Inference Endpoint. Capabilities and costs vary.",
                notes: "Requires HUGGINGFACEHUB_API_TOKEN. Endpoint URL must be set. Cost is per hour for the instance."
            },
            "huggingface-hub-mistral-7b-instruct": {
                name: "Mistral-7B Instruct (via HF Hub/Local)",
                provider: "huggingface_hub",
                model_id_provider: "mistralai/Mistral-7B-Instruct-v0.2",
                context_window_tokens: 32768,
                input_cost_per_mtok: null, 
                output_cost_per_mtok: null,
                supports_tools: false, 
                supports_json: true, 
                supports_vision: false,
                strengths: ["open_source", "self_hostable", "specific_task_fine_tuning"],
                latency_profile: "variable", 
                description: "Example of using a specific open-source model from Hugging Face Hub.",
                notes: "Requires HUGGINGFACEHUB_API_TOKEN. LangChain's HuggingFaceHub or HuggingFacePipeline integration."
            }
        };
        this.enableLogging = process.env.DEBUG_MODEL_ROUTER_LOGGING === "true";
    }

    getModelConfig(modelId) {
        return this.models[modelId] || null;
    }

    getAllModelConfigs() {
        return this.models;
    }

    routeLLM({ taskType, payloadSize = 0, latencyTolerance, costBudget, userOverride }) {
        if (this.enableLogging) {
            console.log(`ModelRouterService: Routing LLM with params - taskType: ${taskType}, payloadSize: ${payloadSize}, latencyTolerance: ${latencyTolerance}, costBudget: ${costBudget}, userOverride: ${JSON.stringify(userOverride)}`);
        }

        if (userOverride && userOverride.provider && userOverride.model) {
            let overriddenModelKey = Object.keys(this.models).find(key => 
                this.models[key].provider === userOverride.provider && 
                this.models[key].model_id_provider && 
                (this.models[key].model_id_provider.toLowerCase() === userOverride.model.toLowerCase() || 
                 (this.models[key].provider === "huggingface_endpoint" && userOverride.model.startsWith("http") && this.models[key].model_id_provider === "<YOUR_ENDPOINT_URL_HERE>") // Allow matching endpoint URL if generic placeholder
                )
            );
            if (!overriddenModelKey) {
                 overriddenModelKey = Object.keys(this.models).find(key => 
                    this.models[key].provider === userOverride.provider && 
                    this.models[key].name.toLowerCase().includes(userOverride.model.toLowerCase())
                );
            }

            if (overriddenModelKey) {
                const overriddenModelConfig = this.models[overriddenModelKey];
                if (this.enableLogging) console.log(`ModelRouterService: User override applied. Selected: ${overriddenModelConfig.name}`);
                // If overriding to a generic HF endpoint, the model_id_provider becomes the user-provided URL
                const modelIdForProvider = overriddenModelConfig.provider === "huggingface_endpoint" && userOverride.model.startsWith("http") 
                                           ? userOverride.model 
                                           : overriddenModelKey;
                return {
                    provider: overriddenModelConfig.provider,
                    model: modelIdForProvider, 
                    temperature: userOverride.temperature || DEFAULT_TEMPERATURE,
                    tools_enabled: overriddenModelConfig.supports_tools === null ? false : overriddenModelConfig.supports_tools
                };
            }
        }

        let candidateModels = Object.entries(this.models).map(([id, config]) => ({ id, ...config }));

        if (taskType === 'embedding_generation') {
            candidateModels = candidateModels.filter(model => model.strengths && model.strengths.includes('text_embedding'));
        } else {
            candidateModels = candidateModels.filter(model => {
                if (model.strengths && model.strengths.includes('text_embedding')) return false;
                if (payloadSize > 0 && model.context_window_tokens && payloadSize > model.context_window_tokens) {
                    if (this.enableLogging) console.log(`ModelRouterService: Filtering out ${model.id} due to payloadSize ${payloadSize} > context_window ${model.context_window_tokens}`);
                    return false;
                }
                return true;
            });
        }

        if (candidateModels.length === 0) {
            if (this.enableLogging) console.warn(`ModelRouterService: No models left after initial filtering. Falling back to default.`);
            const fallbackId = taskType === 'embedding_generation' ? "text-embedding-004" : "claude-3-haiku-20240307";
            const defaultConfig = this.models[fallbackId] || this.models["claude-3-haiku-20240307"];
            return { provider: defaultConfig.provider, model: fallbackId, temperature: DEFAULT_TEMPERATURE, tools_enabled: defaultConfig.supports_tools === null ? false : defaultConfig.supports_tools };
        }

        const scoredModels = candidateModels.map(model => {
            let score = 0;
            const avgCost = (model.input_cost_per_mtok !== null && model.output_cost_per_mtok !== null) 
                            ? (model.input_cost_per_mtok + model.output_cost_per_mtok) / 2 
                            : (model.input_cost_per_mtok !== null ? model.input_cost_per_mtok : Infinity) ; // Handle embedding models with only input cost
            if (avgCost === Infinity && model.input_cost_per_mtok === null && taskType !== 'embedding_generation') score -=50; // Penalize unknown cost heavily for non-embedding unless it's free (null cost)

            if (costBudget === "lowCost") {
                if (avgCost < 0.5) score += 30;
                else if (avgCost < 1.5) score += 20;
                else if (avgCost < 5.0) score += 10;
                else if (avgCost !== Infinity) score -= (avgCost / 5); // Penalize proportionally
            } else if (costBudget === "balanced") {
                if (avgCost < 1.0) score += 20;
                else if (avgCost < 5.0) score += 15;
                else if (avgCost < 15.0) score += 5;
            } else { // performance_first
                if (avgCost < 5.0) score += 10; 
                else if (avgCost < 15.0) score += 5;
            }

            if (latencyTolerance === "fast" || latencyTolerance === "real-time") {
                if (model.latency_profile === "fast") score += 30;
                else if (model.latency_profile === "moderate") score += 5;
                else if (model.latency_profile !== "variable") score -= 20; 
            } else if (latencyTolerance === "moderate") {
                if (model.latency_profile === "fast") score += 15;
                else if (model.latency_profile === "moderate") score += 10;
                else if (model.latency_profile === "moderate-to-slow") score += 0;
                else if (model.latency_profile !== "variable") score -= 10; 
            }

            const taskStrengthsMap = {
                "complex_reasoning": ["complex_reasoning", "advanced_reasoning"],
                "research": ["research", "long_form_content"],
                "code_generation": ["code_generation", "coding"],
                "summarization": ["summarization", "quick_response"],
                "general_purpose": ["general_purpose", "enterprise_workloads", "balanced_performance"],
                "quick_response": ["quick_response", "fast_response"],
                "long_form_content": ["long_form_content"],
                "creative_content": ["creative_content"],
                "web_search_tasks": ["web_search_tasks", "search"],
                "vision_tasks": ["multimodal", "vision"],
                "tool_use_required": ["supports_tools"], // Special case, check supports_tools directly
                "long_context_tasks": ["long_context"]
            };

            if (taskStrengthsMap[taskType] && model.strengths) {
                if (taskStrengthsMap[taskType].some(strength => model.strengths.includes(strength))) {
                    score += 25;
                }
            }
            if (model.strengths && model.strengths.includes(taskType)) score += 15;
            if (taskType === "tool_use_required") {
                if (model.supports_tools) score += 20;
                else score -= 50; // Heavy penalty if tools are required but not supported
            }
            if (taskType === "vision_tasks") {
                if (model.supports_vision) score += 20;
                else score -= 50; 
            }

            if ((payloadSize > 100000 && model.context_window_tokens && model.context_window_tokens > payloadSize) || taskType === "long_context_tasks") {
                if (model.context_window_tokens && model.context_window_tokens >= 200000) score += 15;
                if (model.context_window_tokens && model.context_window_tokens >= 1000000) score += 10;
            }
            
            if (model.id === "deepseek-reasoner" && taskType === "complex_reasoning") score += 10;
            if (model.id === "huggingface-endpoint-generic" && model.model_id_provider === "<YOUR_ENDPOINT_URL_HERE>") score -= 200; // Very heavy penalty if not configured
            if (model.provider === "huggingface_hub" && costBudget !== "lowCost") score -=10; // If not lowcost, HF hub might be slow/unpredictable unless specific model is good.

            model.score = score;
            return model;
        });

        scoredModels.sort((a, b) => b.score - a.score);

        if (this.enableLogging) {
            console.log("ModelRouterService: Scored Models (Top 5):", scoredModels.slice(0, 5).map(m => ({id: m.id, name:m.name, score: m.score, provider: m.provider, cost: (m.input_cost_per_mtok !== null && m.output_cost_per_mtok !== null) ? (m.input_cost_per_mtok + m.output_cost_per_mtok) / 2 : m.input_cost_per_mtok, latency: m.latency_profile, strengths: m.strengths ? m.strengths.join(', ') : '' })) );
        }

        let selectedModelEntry;
        if (scoredModels.length > 0) {
            selectedModelEntry = scoredModels[0];
        } else {
            if (this.enableLogging) console.warn(`ModelRouterService: No models available after scoring. Falling back to default.`);
            const fallbackId = taskType === 'embedding_generation' ? "text-embedding-004" : "claude-3-haiku-20240307";
            selectedModelEntry = { id: fallbackId, ...this.models[fallbackId] };
        }
        
        const finalModelConfig = this.models[selectedModelEntry.id];
        if (this.enableLogging) console.log(`ModelRouterService: Routing decision - Selected Model: ${finalModelConfig.name} (ID: ${selectedModelEntry.id}) for task: ${taskType} with score: ${selectedModelEntry.score}`);

        return {
            provider: finalModelConfig.provider,
            model: selectedModelEntry.id, 
            temperature: DEFAULT_TEMPERATURE,
            tools_enabled: finalModelConfig.supports_tools === null ? false : finalModelConfig.supports_tools
        };
    }
}

module.exports = ModelRouterService;


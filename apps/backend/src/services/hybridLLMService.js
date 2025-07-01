/**
 * Hybrid LLM Service
 * Intelligent load balancing between local and external LLM providers
 */

const OllamaService = require('./ollamaService');
const PerplexityApiService = require('./research/perplexityApiService');
const { logToSupabase } = require('../config/supabase');

class HybridLLMService {
  constructor() {
    this.ollama = new OllamaService();
    this.perplexity = new PerplexityApiService();
    
    // Provider configurations
    this.providers = {
      local: {
        name: 'Ollama Local',
        cost: 0, // Free
        latency: 'low',
        privacy: 'high',
        available: false
      },
      openai: {
        name: 'OpenAI GPT',
        cost: 'medium',
        latency: 'medium', 
        privacy: 'medium',
        available: export TERM=xterm-256colorprocess.env.OPENAI_API_KEY
      },
      anthropic: {
        name: 'Anthropic Claude',
        cost: 'medium',
        latency: 'medium',
        privacy: 'medium', 
        available: export TERM=xterm-256colorprocess.env.ANTHROPIC_API_KEY
      },
      perplexity: {
        name: 'Perplexity Research',
        cost: 'low',
        latency: 'medium',
        privacy: 'medium',
        available: export TERM=xterm-256colorprocess.env.PERPLEXITY_API_KEY
      }
    };

    // Load balancing strategies
    this.strategies = {
      cost_optimized: 'Prefer free local models, fallback to external',
      performance_optimized: 'Prefer fastest response time',
      privacy_optimized: 'Prefer local models for sensitive data',
      quality_optimized: 'Prefer highest quality models',
      balanced: 'Balance cost, performance, and quality'
    };

    this.defaultStrategy = 'balanced';
    this.fallbackChain = ['local', 'openai', 'anthropic', 'perplexity'];
  }

  /**
   * Initialize service and check provider availability
   */
  async initialize() {
    // Check local Ollama availability
    this.providers.local.available = await this.ollama.isAvailable();
    
    console.log('Hybrid LLM Service initialized:');
    Object.entries(this.providers).forEach(([key, provider]) => {
      console.log();
    });
  }

  /**
   * Select optimal provider based on strategy and task requirements
   */
  selectProvider(taskType, strategy = this.defaultStrategy, requirements = {}) {
    const {
      maxLatency = 30000,
      requiresPrivacy = false,
      maxCost = 'high',
      preferredQuality = 'medium'
    } = requirements;

    // Privacy-first selection
    if (requiresPrivacy && this.providers.local.available) {
      return 'local';
    }

    // Strategy-based selection
    switch (strategy) {
      case 'cost_optimized':
        if (this.providers.local.available) return 'local';
        if (this.providers.perplexity.available) return 'perplexity';
        break;

      case 'performance_optimized':
        if (this.providers.local.available) return 'local';
        if (this.providers.openai.available) return 'openai';
        break;

      case 'privacy_optimized':
        if (this.providers.local.available) return 'local';
        break;

      case 'quality_optimized':
        if (taskType === 'research' && this.providers.perplexity.available) return 'perplexity';
        if (this.providers.anthropic.available) return 'anthropic';
        if (this.providers.openai.available) return 'openai';
        break;

      case 'balanced':
      default:
        // Task-specific routing
        if (taskType === 'coding' && this.providers.local.available) return 'local';
        if (taskType === 'research' && this.providers.perplexity.available) return 'perplexity';
        if (this.providers.local.available) return 'local';
        if (this.providers.anthropic.available) return 'anthropic';
        break;
    }

    // Fallback chain
    for (const provider of this.fallbackChain) {
      if (this.providers[provider].available) {
        return provider;
      }
    }

    throw new Error('No available LLM providers');
  }

  /**
   * Generate response using optimal provider
   */
  async generate(prompt, options = {}) {
    const {
      taskType = 'general',
      strategy = this.defaultStrategy,
      requirements = {},
      fallback = true,
      ...providerOptions
    } = options;

    let selectedProvider = this.selectProvider(taskType, strategy, requirements);
    let attempts = 0;
    const maxAttempts = fallback ? this.fallbackChain.length : 1;

    while (attempts < maxAttempts) {
      try {
        console.log();
        
        const startTime = Date.now();
        let result;

        switch (selectedProvider) {
          case 'local':
            const model = this.ollama.getModelForTask(taskType);
            result = await this.ollama.generate(prompt, { 
              ...providerOptions, 
              model 
            });
            break;

          case 'perplexity':
            result = await this.perplexity.research(prompt, providerOptions);
            // Normalize response format
            result = {
              model: result.model,
              response: result.answer,
              usage: result.usage,
              timing: { duration_ms: Date.now() - startTime },
              finish_reason: result.finishReason,
              provider: 'perplexity'
            };
            break;

          case 'openai':
            result = await this.generateWithOpenAI(prompt, providerOptions);
            break;

          case 'anthropic':
            result = await this.generateWithAnthropic(prompt, providerOptions);
            break;

          default:
            throw new Error();
        }

        // Add provider metadata
        result.provider = selectedProvider;
        result.strategy = strategy;
        result.taskType = taskType;

        // Log successful generation
        await logToSupabase('info', 'Hybrid LLM generation completed', {
          provider: selectedProvider,
          strategy,
          taskType,
          duration_ms: result.timing?.duration_ms,
          tokens_used: result.usage?.total_tokens || 0
        });

        return result;

      } catch (error) {
        console.error(, error.message);
        
        await logToSupabase('warning', 'LLM provider failed, trying fallback', {
          provider: selectedProvider,
          error: error.message,
          attempt: attempts + 1
        });

        attempts++;
        
        if (attempts < maxAttempts && fallback) {
          // Try next provider in fallback chain
          const currentIndex = this.fallbackChain.indexOf(selectedProvider);
          const nextIndex = (currentIndex + 1) % this.fallbackChain.length;
          selectedProvider = this.fallbackChain[nextIndex];
          
          // Skip unavailable providers
            attempts++;
            const nextIndex = (this.fallbackChain.indexOf(selectedProvider) + 1) % this.fallbackChain.length;
            selectedProvider = this.fallbackChain[nextIndex];
          }
        } else {
          throw new Error();
        }
      }
    }
  }

  /**
   * Generate with OpenAI (placeholder - implement with actual OpenAI SDK)
   */
  async generateWithOpenAI(prompt, options = {}) {
    // This would use the OpenAI SDK
    throw new Error('OpenAI integration not yet implemented');
  }

  /**
   * Generate with Anthropic (placeholder - implement with actual Anthropic SDK)
   */
  async generateWithAnthropic(prompt, options = {}) {
    // This would use the Anthropic SDK
    throw new Error('Anthropic integration not yet implemented');
  }

  /**
   * Batch generate with load balancing
   */
  async batchGenerate(prompts, options = {}) {
    const results = [];
    
    for (const prompt of prompts) {
      try {
        const result = await this.generate(prompt, options);
        results.push({
          prompt,
          result,
          success: true
        });
      } catch (error) {
        results.push({
          prompt,
          error: error.message,
          success: false
        });
      }
    }
    
    return results;
  }

  /**
   * Get service status and provider health
   */
  async getStatus() {
    const status = {
      providers: {},
      strategies: this.strategies,
      defaultStrategy: this.defaultStrategy,
      fallbackChain: this.fallbackChain
    };

    // Check each provider status
    for (const [key, provider] of Object.entries(this.providers)) {
      status.providers[key] = {
        ...provider,
        status: provider.available ? 'online' : 'offline'
      };
    }

    // Get local models status if available
    if (this.providers.local.available) {
      status.localModels = await this.ollama.getStatus();
    }

    return status;
  }

  /**
   * Warm up all available providers
   */
  async warmUp() {
    console.log('Warming up hybrid LLM service...');
    
    if (this.providers.local.available) {
      await this.ollama.warmUpModels();
    }
    
    // Test other providers with simple requests
    const testPrompt = 'Hello';
    
    for (const provider of ['openai', 'anthropic', 'perplexity']) {
      if (this.providers[provider].available) {
        try {
          await this.generate(testPrompt, { 
            strategy: 'performance_optimized',
            maxTokens: 10,
            fallback: false 
          });
          console.log();
        } catch (error) {
          console.error(, error.message);
        }
      }
    }
  }

  /**
   * Get cost estimate for a request
   */
  estimateCost(prompt, provider, options = {}) {
    const tokenCount = Math.ceil(prompt.length / 4); // Rough estimate
    
    const costPerToken = {
      local: 0,
      openai: 0.00002, // Rough GPT-4 pricing
      anthropic: 0.000015, // Rough Claude pricing
      perplexity: 0.000005 // Rough Perplexity pricing
    };

    return {
      provider,
      estimatedTokens: tokenCount,
      estimatedCost: tokenCount * (costPerToken[provider] || 0),
      currency: 'USD'
    };
  }
}

module.exports = HybridLLMService;

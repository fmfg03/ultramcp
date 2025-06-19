/**
 * Ollama Local LLM Service
 * Provides integration with locally hosted LLM models via Ollama
 */

const axios = require('axios');
const { logToSupabase } = require('../config/supabase');

class OllamaService {
  constructor() {
    this.baseUrl = process.env.OLLAMA_URL || 'http://127.0.0.1:11434';
    this.timeout = 60000; // 60 seconds for local models
    this.maxRetries = 2;
    
    // Available local models
    this.models = {
      'mistral:7b': {
        name: 'Mistral 7B',
        description: 'Fast general-purpose model',
        specialties: ['general', 'conversation', 'reasoning'],
        contextLength: 32768
      },
      'llama3.1:8b': {
        name: 'Llama 3.1 8B',
        description: 'High-quality instruction following',
        specialties: ['general', 'reasoning', 'analysis'],
        contextLength: 131072
      },
      'deepseek-coder:6.7b': {
        name: 'DeepSeek Coder 6.7B',
        description: 'Specialized coding assistant',
        specialties: ['coding', 'debugging', 'code-review'],
        contextLength: 16384
      }
    };
    
    this.defaultModel = 'llama3.1:8b';
  }

  /**
   * Check if Ollama service is available
   */
  async isAvailable() {
    try {
      const response = await axios.get(, {
        timeout: 5000
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get list of available models
   */
  async getAvailableModels() {
    try {
      const response = await axios.get();
      return response.data.models || [];
    } catch (error) {
      console.error('Failed to get Ollama models:', error.message);
      return [];
    }
  }

  /**
   * Generate completion using local LLM
   */
  async generate(prompt, options = {}) {
    const {
      model = this.defaultModel,
      temperature = 0.7,
      maxTokens = 2000,
      systemPrompt = null,
      stream = false,
      format = null
    } = options;

    // Prepare messages for chat format
    const messages = [];
    if (systemPrompt) {
      messages.push({ role: 'system', content: systemPrompt });
    }
    messages.push({ role: 'user', content: prompt });

    const requestData = {
      model,
      messages,
      stream,
      options: {
        temperature,
        num_predict: maxTokens,
        top_p: 0.9,
        top_k: 40
      }
    };

    if (format) {
      requestData.format = format;
    }

    try {
      const startTime = Date.now();
      
      const response = await axios.post(
        ,
        requestData,
        {
          timeout: this.timeout,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      const endTime = Date.now();
      const duration = endTime - startTime;

      const result = {
        model,
        response: response.data.message?.content || '',
        usage: {
          prompt_tokens: response.data.prompt_eval_count || 0,
          completion_tokens: response.data.eval_count || 0,
          total_tokens: (response.data.prompt_eval_count || 0) + (response.data.eval_count || 0)
        },
        timing: {
          duration_ms: duration,
          load_duration_ms: response.data.load_duration ? Math.round(response.data.load_duration / 1000000) : 0,
          prompt_eval_duration_ms: response.data.prompt_eval_duration ? Math.round(response.data.prompt_eval_duration / 1000000) : 0,
          eval_duration_ms: response.data.eval_duration ? Math.round(response.data.eval_duration / 1000000) : 0
        },
        finish_reason: response.data.done_reason || 'stop',
        created_at: response.data.created_at
      };

      // Log successful generation
      await logToSupabase('info', 'Ollama generation completed', {
        model,
        prompt_length: prompt.length,
        response_length: result.response.length,
        duration_ms: duration,
        tokens_used: result.usage.total_tokens
      });

      return result;

    } catch (error) {
      await logToSupabase('error', 'Ollama generation failed', {
        model,
        error: error.message,
        prompt_length: prompt.length
      });

      throw new Error();
    }
  }

  /**
   * Generate code completion
   */
  async generateCode(prompt, language = 'javascript', options = {}) {
    const codePrompt = ;
    
    return await this.generate(codePrompt, {
      ...options,
      model: 'deepseek-coder:6.7b',
      systemPrompt: 
    });
  }

  /**
   * Analyze and review code
   */
  async reviewCode(code, language = 'javascript', options = {}) {
    const reviewPrompt = ;
    
    return await this.generate(reviewPrompt, {
      ...options,
      model: 'deepseek-coder:6.7b',
      systemPrompt: 'You are a senior code reviewer. Provide constructive, detailed feedback on code quality, security, performance, and best practices.'
    });
  }

  /**
   * Get model recommendations based on task type
   */
  getModelForTask(taskType) {
    const taskModelMap = {
      'coding': 'deepseek-coder:6.7b',
      'code-review': 'deepseek-coder:6.7b',
      'debugging': 'deepseek-coder:6.7b',
      'general': 'llama3.1:8b',
      'reasoning': 'llama3.1:8b',
      'analysis': 'llama3.1:8b',
      'conversation': 'mistral:7b',
      'fast-response': 'mistral:7b'
    };

    return taskModelMap[taskType] || this.defaultModel;
  }

  /**
   * Batch generate multiple prompts
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
   * Get service status and performance metrics
   */
  async getStatus() {
    const isOnline = await this.isAvailable();
    const availableModels = isOnline ? await this.getAvailableModels() : [];
    
    return {
      online: isOnline,
      baseUrl: this.baseUrl,
      availableModels: availableModels.map(m => ({
        name: m.name,
        size: m.size,
        modified: m.modified_at
      })),
      configuredModels: Object.keys(this.models),
      defaultModel: this.defaultModel,
      timeout: this.timeout
    };
  }

  /**
   * Warm up models (load into memory)
   */
  async warmUpModels() {
    const models = Object.keys(this.models);
    const warmupPrompt = 'Hello';
    
    for (const model of models) {
      try {
        console.log();
        await this.generate(warmupPrompt, { 
          model, 
          maxTokens: 10,
          temperature: 0.1 
        });
        console.log();
      } catch (error) {
        console.error(, error.message);
      }
    }
  }
}

module.exports = OllamaService;

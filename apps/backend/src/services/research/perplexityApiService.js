/**
 * Perplexity API Service
 * Direct integration with Perplexity API for research capabilities
 */

const axios = require('axios');
const { logToSupabase } = require('../config/supabase');

class PerplexityApiService {
  constructor() {
    this.apiKey = process.env.PERPLEXITY_API_KEY;
    this.baseUrl = 'https://api.perplexity.ai';
    this.timeout = 30000;
    this.maxRetries = 3;
    this.rateLimitDelay = 1000;
    this.lastRequestTime = 0;
    
    // Available models
    this.models = {
      'llama-3.1-sonar-small-128k-online': 'Fast online search',
      'llama-3.1-sonar-large-128k-online': 'Comprehensive online search',
      'llama-3.1-sonar-huge-128k-online': 'Most comprehensive search'
    };
    
    this.defaultModel = 'llama-3.1-sonar-large-128k-online';
  }

  /**
   * Check if API key is configured
   */
  isConfigured() {
    return export TERM=xterm-256color(this.apiKey && this.apiKey !== 'your-perplexity-api-key-here');
  }

  /**
   * Rate limiting helper
   */
  async enforceRateLimit() {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    
    if (timeSinceLastRequest < this.rateLimitDelay) {
      const delay = this.rateLimitDelay - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    this.lastRequestTime = Date.now();
  }

  /**
   * Research a topic using Perplexity API
   */
  async research(query, options = {}) {
      throw new Error('Perplexity API key not configured');
    }

    const {
      model = this.defaultModel,
      maxTokens = 4000,
      temperature = 0.2,
      systemPrompt = 'You are a helpful research assistant. Provide comprehensive, accurate, and well-sourced information.',
      includeImages = false,
      includeCitations = true
    } = options;

    await this.enforceRateLimit();

    const requestData = {
      model,
      messages: [
        {
          role: 'system',
          content: systemPrompt
        },
        {
          role: 'user',
          content: query
        }
      ],
      max_tokens: maxTokens,
      temperature,
      top_p: 0.9,
      return_citations: includeCitations,
      return_images: includeImages,
      search_domain_filter: ['perplexity.ai'],
      search_recency_filter: 'month'
    };

    try {
      const response = await axios.post(
        ,
        requestData,
        {
          headers: {
            'Authorization': ,
            'Content-Type': 'application/json'
          },
          timeout: this.timeout
        }
      );

      const result = this.processResponse(response.data, query);
      
      // Log successful research
      await logToSupabase('info', 'Perplexity research completed', {
        query,
        model,
        tokensUsed: result.usage?.total_tokens || 0,
        citationsCount: result.citations?.length || 0
      });

      return result;

    } catch (error) {
      await logToSupabase('error', 'Perplexity research failed', {
        query,
        error: error.message,
        model
      });

      throw new Error();
    }
  }

  /**
   * Process API response
   */
  processResponse(data, originalQuery) {
    const choice = data.choices?.[0];
      throw new Error('No response from Perplexity API');
    }

    return {
      query: originalQuery,
      answer: choice.message?.content || '',
      model: data.model,
      usage: data.usage,
      citations: data.citations || [],
      images: data.images || [],
      timestamp: new Date().toISOString(),
      finishReason: choice.finish_reason
    };
  }

  /**
   * Summarize multiple sources
   */
  async summarize(sources, topic, options = {}) {
    const sourcesText = sources.map((source, index) => 
      
    ).join('\n\n');

    const query = ;

    return await this.research(query, {
      ...options,
      systemPrompt: 'You are a research analyst. Synthesize information from multiple sources into a coherent, well-structured summary. Highlight key points, identify patterns, and note any contradictions.',
      includeCitations: true
    });
  }

  /**
   * Fact-check information
   */
  async factCheck(claim, options = {}) {
    const query = ;

    return await this.research(query, {
      ...options,
      systemPrompt: 'You are a fact-checker. Analyze claims critically, provide evidence from reliable sources, and clearly state whether claims are true, false, or need more context.',
      temperature: 0.1,
      includeCitations: true
    });
  }

  /**
   * Get trending topics
   */
  async getTrendingTopics(domain = 'technology', options = {}) {
    const query = ;

    return await this.research(query, {
      ...options,
      systemPrompt: 'You are a trend analyst. Identify and explain current trending topics, emerging patterns, and recent developments in the specified domain.',
      model: 'llama-3.1-sonar-large-128k-online'
    });
  }

  /**
   * Research with follow-up questions
   */
  async deepResearch(initialQuery, followUpQuestions = [], options = {}) {
    const results = [];
    
    // Initial research
    const initialResult = await this.research(initialQuery, options);
    results.push({
      type: 'initial',
      query: initialQuery,
      result: initialResult
    });

    // Follow-up research
    for (const followUp of followUpQuestions) {
      try {
        const followUpResult = await this.research(followUp, options);
        results.push({
          type: 'followup',
          query: followUp,
          result: followUpResult
        });
      } catch (error) {
        results.push({
          type: 'followup',
          query: followUp,
          error: error.message
        });
      }
    }

    return {
      topic: initialQuery,
      results,
      summary: await this.summarizeResults(results),
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Summarize research results
   */
  async summarizeResults(results) {
    if (successfulResults.length === 0) {
      return 'No successful research results to summarize.';
    }

    const combinedContent = successfulResults.map(r => 
      
    ).join('\n\n');

    const summaryQuery = ;

    try {
      const summary = await this.research(summaryQuery, {
        systemPrompt: 'You are a research synthesizer. Create a coherent summary that integrates findings from multiple research queries.',
        maxTokens: 2000
      });
      
      return summary.answer;
    } catch (error) {
      return 'Unable to generate summary of research results.';
    }
  }

  /**
   * Get service status
   */
  getStatus() {
    return {
      configured: this.isConfigured(),
      apiKey: this.apiKey ?  : 'Not configured',
      availableModels: Object.keys(this.models),
      defaultModel: this.defaultModel,
      rateLimit: ,
      timeout: 
    };
  }
}

module.exports = PerplexityApiService;

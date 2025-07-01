/**
 * Perplexity Research Service
 * Provides research capabilities with multiple fallback strategies
 */

const puppeteer = require('puppeteer');
const axios = require('axios');
const cheerio = require('cheerio');
const { logger } = require('../utils/logger');

class PerplexityService {
  constructor() {
    this.strategies = ['headless_browser', 'api_fallback', 'serper_deepseek', 'arxiv_search'];
    this.currentStrategy = 'headless_browser';
    this.timeout = 30000; // 30 seconds
    this.maxRetries = 3;
    this.rateLimitDelay = 2000; // 2 seconds between requests
    this.lastRequestTime = 0;
    
    // Cache for recent searches
    this.searchCache = new Map();
    this.cacheTimeout = 300000; // 5 minutes
    
    // Browser instance for reuse
    this.browser = null;
    this.browserReady = false;
  }

  /**
   * Main search method with automatic fallback
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @returns {Object} Search result with answer and citations
   */
  async searchWithCitations(query, options = {}) {
    const startTime = Date.now();
    logger.info(`Starting research query: "${query.substring(0, 100)}..."`);

    try {
      // Check cache first
      const cacheKey = this._generateCacheKey(query, options);
      const cachedResult = this._getFromCache(cacheKey);
      if (cachedResult) {
        logger.info('Returning cached research result');
        return cachedResult;
      }

      // Rate limiting
      await this._enforceRateLimit();

      // Try strategies in order
      let lastError = null;
      for (const strategy of this.strategies) {
        try {
          logger.info(`Attempting research with strategy: ${strategy}`);
          const result = await this._executeStrategy(strategy, query, options);
          
          if (result && result.answer) {
            // Cache successful result
            this._addToCache(cacheKey, result);
            
            // Add metadata
            result.metadata = {
              strategy: strategy,
              duration: Date.now() - startTime,
              timestamp: new Date().toISOString(),
              cached: false
            };
            
            logger.info(`Research completed successfully with ${strategy} in ${result.metadata.duration}ms`);
            return result;
          }
        } catch (error) {
          logger.warn(`Strategy ${strategy} failed: ${error.message}`);
          lastError = error;
          continue;
        }
      }

      // All strategies failed
      throw new Error(`All research strategies failed. Last error: ${lastError?.message}`);

    } catch (error) {
      logger.error(`Research failed for query "${query}": ${error.message}`);
      throw error;
    }
  }

  /**
   * Execute specific research strategy
   * @param {string} strategy - Strategy name
   * @param {string} query - Search query
   * @param {Object} options - Options
   * @returns {Object} Research result
   */
  async _executeStrategy(strategy, query, options) {
    switch (strategy) {
      case 'headless_browser':
        return await this._perplexityHeadlessBrowser(query, options);
      case 'api_fallback':
        return await this._perplexityAPIFallback(query, options);
      case 'serper_deepseek':
        return await this._serperDeepSeekStrategy(query, options);
      case 'arxiv_search':
        return await this._arxivSearchStrategy(query, options);
      default:
        throw new Error(`Unknown strategy: ${strategy}`);
    }
  }

  /**
   * Perplexity headless browser strategy
   * @param {string} query - Search query
   * @param {Object} options - Options
   * @returns {Object} Research result
   */
  async _perplexityHeadlessBrowser(query, options) {
    let page = null;
    
    try {
      // Initialize browser if needed
      if (!this.browser || !this.browserReady) {
        await this._initializeBrowser();
      }

      page = await this.browser.newPage();
      
      // Set user agent and viewport
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
      await page.setViewport({ width: 1920, height: 1080 });
      
      // Navigate to Perplexity
      await page.goto('https://www.perplexity.ai/', { 
        waitUntil: 'networkidle2',
        timeout: this.timeout 
      });

      // Wait for search input
      await page.waitForSelector('textarea[placeholder*="Ask"], input[placeholder*="Ask"]', { timeout: 10000 });

      // Enter query
      const searchSelector = 'textarea[placeholder*="Ask"], input[placeholder*="Ask"]';
      await page.type(searchSelector, query);
      
      // Submit search
      await page.keyboard.press('Enter');

      // Wait for results
      await page.waitForSelector('[data-testid="answer"], .prose, .answer-content', { timeout: 20000 });

      // Extract answer and citations
      const result = await page.evaluate(() => {
        // Extract main answer
        const answerSelectors = [
          '[data-testid="answer"]',
          '.prose',
          '.answer-content',
          '.copilot-answer',
          '.md\\:prose'
        ];
        
        let answer = '';
        for (const selector of answerSelectors) {
          const element = document.querySelector(selector);
          if (element) {
            answer = element.innerText || element.textContent;
            break;
          }
        }

        // Extract citations/sources
        const citations = [];
        const citationSelectors = [
          'a[href*="http"]',
          '.citation',
          '.source',
          '[data-testid="citation"]'
        ];

        const citationElements = document.querySelectorAll(citationSelectors.join(', '));
        const seenUrls = new Set();

        citationElements.forEach((element, index) => {
          const url = element.href;
          const title = element.textContent?.trim() || element.title || `Source ${index + 1}`;
          
          if (url && url.startsWith('http') && !seenUrls.has(url)) {
            seenUrls.add(url);
            citations.push({
              title: title.substring(0, 200),
              url: url,
              index: citations.length + 1
            });
          }
        });

        return { answer: answer.trim(), citations };
      });

      if (!result.answer) {
        throw new Error('No answer found in Perplexity response');
      }

      return {
        answer: result.answer,
        citations: result.citations,
        confidence: this._calculateConfidence(result),
        source: 'perplexity_browser'
      };

    } catch (error) {
      logger.error(`Perplexity browser strategy failed: ${error.message}`);
      throw error;
    } finally {
      if (page) {
        await page.close();
      }
    }
  }

  /**
   * Perplexity API fallback (when official API becomes available)
   * @param {string} query - Search query
   * @param {Object} options - Options
   * @returns {Object} Research result
   */
  async _perplexityAPIFallback(query, options) {
    // Placeholder for official Perplexity API when available
    throw new Error('Perplexity API not yet available');
  }

  /**
   * Serper + DeepSeek strategy
   * @param {string} query - Search query
   * @param {Object} options - Options
   * @returns {Object} Research result
   */
  async _serperDeepSeekStrategy(query, options) {
    try {
      // Use Serper for search results
      const searchResults = await this._serperSearch(query);
      
      // Use DeepSeek to synthesize answer
      const synthesizedAnswer = await this._synthesizeWithDeepSeek(query, searchResults);
      
      return {
        answer: synthesizedAnswer.answer,
        citations: searchResults.slice(0, 5).map((result, index) => ({
          title: result.title,
          url: result.link,
          snippet: result.snippet,
          index: index + 1
        })),
        confidence: 0.8,
        source: 'serper_deepseek'
      };

    } catch (error) {
      logger.error(`Serper + DeepSeek strategy failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * ArXiv search strategy for academic queries
   * @param {string} query - Search query
   * @param {Object} options - Options
   * @returns {Object} Research result
   */
  async _arxivSearchStrategy(query, options) {
    try {
      // Check if query seems academic
      const academicKeywords = ['research', 'study', 'paper', 'analysis', 'algorithm', 'model', 'theory'];
      const isAcademic = academicKeywords.some(keyword => 
        query.toLowerCase().includes(keyword)
      );

      if (!isAcademic) {
        throw new Error('Query does not appear to be academic');
      }

      // Search ArXiv
      const arxivResults = await this._searchArxiv(query);
      
      if (arxivResults.length === 0) {
        throw new Error('No ArXiv results found');
      }

      // Synthesize answer from top papers
      const topPapers = arxivResults.slice(0, 3);
      const answer = this._synthesizeFromPapers(query, topPapers);

      return {
        answer: answer,
        citations: topPapers.map((paper, index) => ({
          title: paper.title,
          url: paper.link,
          authors: paper.authors,
          published: paper.published,
          index: index + 1
        })),
        confidence: 0.9,
        source: 'arxiv'
      };

    } catch (error) {
      logger.error(`ArXiv strategy failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Search using Serper API
   * @param {string} query - Search query
   * @returns {Array} Search results
   */
  async _serperSearch(query) {
    const response = await axios.post('https://google.serper.dev/search', {
      q: query,
      num: 10
    }, {
      headers: {
        'X-API-KEY': process.env.SERPER_API_KEY,
        'Content-Type': 'application/json'
      },
      timeout: this.timeout
    });

    return response.data.organic || [];
  }

  /**
   * Synthesize answer using DeepSeek
   * @param {string} query - Original query
   * @param {Array} searchResults - Search results
   * @returns {Object} Synthesized answer
   */
  async _synthesizeWithDeepSeek(query, searchResults) {
    const context = searchResults.map(result => 
      `Title: ${result.title}\nSnippet: ${result.snippet}\nURL: ${result.link}`
    ).join('\n\n');

    const prompt = `Based on the following search results, provide a comprehensive answer to the question: "${query}"

Search Results:
${context}

Please provide a well-structured answer that:
1. Directly addresses the question
2. Synthesizes information from multiple sources
3. Is factual and objective
4. Includes relevant details and context

Answer:`;

    // Call DeepSeek API (placeholder - would use actual API)
    const response = await axios.post('https://api.deepseek.com/v1/chat/completions', {
      model: 'deepseek-chat',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 1000,
      temperature: 0.3
    }, {
      headers: {
        'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
        'Content-Type': 'application/json'
      },
      timeout: this.timeout
    });

    return {
      answer: response.data.choices[0].message.content
    };
  }

  /**
   * Search ArXiv for academic papers
   * @param {string} query - Search query
   * @returns {Array} ArXiv results
   */
  async _searchArxiv(query) {
    const searchUrl = `http://export.arxiv.org/api/query?search_query=all:${encodeURIComponent(query)}&start=0&max_results=10`;
    
    const response = await axios.get(searchUrl, { timeout: this.timeout });
    const $ = cheerio.load(response.data, { xmlMode: true });
    
    const papers = [];
    $('entry').each((index, element) => {
      const $entry = $(element);
      papers.push({
        title: $entry.find('title').text().trim(),
        authors: $entry.find('author name').map((i, el) => $(el).text()).get(),
        summary: $entry.find('summary').text().trim(),
        link: $entry.find('id').text().trim(),
        published: $entry.find('published').text().trim()
      });
    });

    return papers;
  }

  /**
   * Synthesize answer from academic papers
   * @param {string} query - Original query
   * @param {Array} papers - Academic papers
   * @returns {string} Synthesized answer
   */
  _synthesizeFromPapers(query, papers) {
    const summaries = papers.map(paper => 
      `${paper.title}: ${paper.summary.substring(0, 300)}...`
    ).join('\n\n');

    return `Based on recent academic research, here's what the literature says about "${query}":\n\n${summaries}\n\nThese papers provide current academic perspectives on the topic.`;
  }

  /**
   * Initialize browser instance
   */
  async _initializeBrowser() {
    try {
      if (this.browser) {
        await this.browser.close();
      }

      this.browser = await puppeteer.launch({
        headless: 'new',
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu'
        ]
      });

      this.browserReady = true;
      logger.info('Browser initialized successfully');
    } catch (error) {
      logger.error(`Failed to initialize browser: ${error.message}`);
      this.browserReady = false;
      throw error;
    }
  }

  /**
   * Calculate confidence score for result
   * @param {Object} result - Research result
   * @returns {number} Confidence score
   */
  _calculateConfidence(result) {
    let confidence = 0.5; // Base confidence

    // Increase confidence based on answer length
    if (result.answer && result.answer.length > 100) {
      confidence += 0.2;
    }

    // Increase confidence based on number of citations
    if (result.citations && result.citations.length > 0) {
      confidence += Math.min(result.citations.length * 0.1, 0.3);
    }

    return Math.min(confidence, 1.0);
  }

  /**
   * Enforce rate limiting
   */
  async _enforceRateLimit() {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    
    if (timeSinceLastRequest < this.rateLimitDelay) {
      const waitTime = this.rateLimitDelay - timeSinceLastRequest;
      logger.info(`Rate limiting: waiting ${waitTime}ms`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    this.lastRequestTime = Date.now();
  }

  /**
   * Generate cache key
   * @param {string} query - Search query
   * @param {Object} options - Options
   * @returns {string} Cache key
   */
  _generateCacheKey(query, options) {
    return `research:${Buffer.from(query + JSON.stringify(options)).toString('base64')}`;
  }

  /**
   * Get result from cache
   * @param {string} key - Cache key
   * @returns {Object|null} Cached result
   */
  _getFromCache(key) {
    const cached = this.searchCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      cached.result.metadata = { ...cached.result.metadata, cached: true };
      return cached.result;
    }
    return null;
  }

  /**
   * Add result to cache
   * @param {string} key - Cache key
   * @param {Object} result - Result to cache
   */
  _addToCache(key, result) {
    this.searchCache.set(key, {
      result: { ...result },
      timestamp: Date.now()
    });

    // Clean old cache entries
    if (this.searchCache.size > 100) {
      const oldestKey = this.searchCache.keys().next().value;
      this.searchCache.delete(oldestKey);
    }
  }

  /**
   * Clean up resources
   */
  async cleanup() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.browserReady = false;
    }
    this.searchCache.clear();
    logger.info('Perplexity service cleaned up');
  }

  /**
   * Health check
   * @returns {Object} Health status
   */
  async healthCheck() {
    try {
      // Test with simple query
      const testResult = await this.searchWithCitations('test query health check', { timeout: 5000 });
      return {
        status: 'healthy',
        strategies: this.strategies,
        currentStrategy: this.currentStrategy,
        browserReady: this.browserReady,
        cacheSize: this.searchCache.size
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        browserReady: this.browserReady
      };
    }
  }
}

// Export singleton instance
const perplexityService = new PerplexityService();

// Graceful shutdown
process.on('SIGTERM', async () => {
  await perplexityService.cleanup();
});

process.on('SIGINT', async () => {
  await perplexityService.cleanup();
});

module.exports = perplexityService;


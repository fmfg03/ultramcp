const BaseMCPAdapter = require("./baseMCPAdapter.js");
const { Anthropic } = require("@anthropic-ai/sdk");
require("dotenv").config({ path: "../../../.env" }); // Corrected path to project root .env

const CLAUDE_API_KEY_ENV = process.env.CLAUDE_API_KEY;

class ClaudeWebSearchAdapter extends BaseMCPAdapter {
  constructor() {
    super();
    this.anthropic = null;
    this.credentialsService = null;
    this._initializeCredentialsService(); // Fire-and-forget async initialization
    if (!CLAUDE_API_KEY_ENV) {
      console.warn("ClaudeWebSearchAdapter: CLAUDE_API_KEY not found in environment variables. Will attempt to use credentialsService.");
    }
  }

  async _initializeCredentialsService() {
    try {
      // Corrected path from backend/src/adapters to project/src/services
      const credentialsServiceModule = require("../../../src/services/credentialsService.js");
      this.credentialsService = credentialsServiceModule.default || credentialsServiceModule;
      console.log("ClaudeWebSearchAdapter: credentialsService loaded successfully.");
    } catch (e) {
      console.error("ClaudeWebSearchAdapter: Failed to dynamically import credentialsService:", e);
    }
  }

  async _getApiKey() {
    if (CLAUDE_API_KEY_ENV) {
      return CLAUDE_API_KEY_ENV;
    }
    if (this.credentialsService && this.credentialsService.getCredential) {
      try {
        console.log("ClaudeWebSearchAdapter: Attempting to fetch API key from credentialsService...");
        const apiKey = await this.credentialsService.getCredential("claude", "apiKey");
        if (apiKey) {
          console.log("ClaudeWebSearchAdapter: API key fetched successfully from credentialsService.");
          return apiKey;
        }
      } catch (error) {
        console.error("ClaudeWebSearchAdapter: Error fetching API key from credentialsService:", error);
      }
    }
    console.error("ClaudeWebSearchAdapter: Claude API Key not available through environment or credentialsService.");
    return null;
  }

  async _initializeAnthropic() {
    if (this.anthropic) return true;
    const apiKey = await this._getApiKey();
    if (apiKey) {
      this.anthropic = new Anthropic({ apiKey });
      console.log("ClaudeWebSearchAdapter: Anthropic client initialized successfully.");
      return true;
    } else {
      console.error("ClaudeWebSearchAdapter: Anthropic client could not be initialized due to missing API key.");
      return false;
    }
  }

  getId() {
    return "claudeWebSearch";
  }

  getTools() {
    return [
      {
        id: "claudeWebSearch/webSearch",
        name: "Claude Web Search",
        description: "Queries Claude with web search enabled to answer questions or find information.",
        parameters: {
          type: "object",
          properties: {
            query: { type: "string", description: "The search query or question for Claude." },
            max_uses: { type: "number", description: "(Note: This parameter is logged but not directly used by Claude's anthropic-search tool for multi-hop control in a single call. Multi-hop typically requires agentic looping.) Maximum number of conceptual search iterations.", default: 3 },
            allow_domains: { type: "array", items: { type: "string" }, description: "(Note: Domain filtering is not directly supported by anthropic-search tool; filtering would be post-response if needed.) Optional list of domains to prioritize.", default: [] },
            block_domains: { type: "array", items: { type: "string" }, description: "(Note: Domain filtering is not directly supported by anthropic-search tool; filtering would be post-response if needed.) Optional list of domains to block.", default: [] }
          },
          required: ["query"]
        }
      }
    ];
  }

  async executeAction(toolId, params) {
    const toolName = toolId.split("/")[1];
    const logs = [`ClaudeWebSearchAdapter: Received action for toolId: ${toolId}`];

    if (toolName === "webSearch") {
      const initialized = await this._initializeAnthropic();
      if (!initialized || !this.anthropic) {
        logs.push("ClaudeWebSearchAdapter: Anthropic client not initialized.");
        return { status: "error", message: "ClaudeWebSearchAdapter: Anthropic client not initialized.", logs };
      }

      const { query, max_uses = 3, allow_domains = [], block_domains = [] } = params;
      logs.push(`ClaudeWebSearchAdapter: Executing webSearch for query: "${query}". Max uses (logged): ${max_uses}, Allow domains (logged): ${allow_domains.join(", ")}, Block domains (logged): ${block_domains.join(", ")}`);

      try {
        const messages = [{ role: "user", content: query }];
        // anthropic-search is a tool Claude can use internally when listed.
        const claudeTools = [{ name: "anthropic-search" }];

        logs.push(`ClaudeWebSearchAdapter: Calling Claude Messages API with query and enabling anthropic-search tool.`);
        const response = await this.anthropic.messages.create({
          model: "claude-3-5-sonnet-20240620", 
          max_tokens: 4096,
          messages: messages,
          tools: claudeTools,
          // tool_choice: { type: "auto" } // Default behavior when tools are provided, lets Claude decide.
        });
        logs.push(`ClaudeWebSearchAdapter: Received response from Claude. Stop reason: ${response.stop_reason}`);

        let rawAnswer = "";
        if (response.content && response.content.length > 0) {
          response.content.forEach(block => {
            if (block.type === "text") {
              rawAnswer += block.text;
            }
          });
        }
        logs.push(`ClaudeWebSearchAdapter: Raw answer from Claude: ${rawAnswer.substring(0, 200)}...`);

        // Parse citations and sources (example format: [1], [2] ... then list at end)
        const sources = [];
        const sourceListRegex = /^\[(\d+)\] Source: (.*?) (\((https?:\/\/[^\s)]+)\))?$/gm; // Matches lines like [1] Source: Title (URL) or [1] Source: Title
        const citationRegex = /\[(\d+)\]/g;
        let cleanedAnswer = rawAnswer;
        let match;
        const sourceMap = new Map();

        while ((match = sourceListRegex.exec(rawAnswer)) !== null) {
            const id = match[1];
            const titleWithPossibleUrl = match[2].trim();
            const url = match[4]; // Group 4 is the URL if present
            sourceMap.set(id, { 
                url: url || "N/A", 
                title: url ? titleWithPossibleUrl.replace(`(${url})`, "").trim() : titleWithPossibleUrl, 
                snippet: titleWithPossibleUrl 
            });
        }
        
        // Remove source list from the answer if it was appended in this format
        if(sourceMap.size > 0) {
            cleanedAnswer = rawAnswer.replace(sourceListRegex, "").trim();
            sourceMap.forEach((src, id) => sources.push(src));
            logs.push(`ClaudeWebSearchAdapter: Parsed ${sources.length} structured sources.`);
        } else {
            // Fallback: basic URL extraction if no structured sources found
            const urlRegex = /https?:\/\/[^\s()]+/g;
            const extractedUrls = new Set();
            let urlMatch;
            while ((urlMatch = urlRegex.exec(rawAnswer)) !== null) {
              extractedUrls.add(urlMatch[0]);
            }
            extractedUrls.forEach(url => {
                sources.push({ url: url, title: "Extracted URL", snippet: "N/A" });
            });
            if (sources.length > 0) logs.push(`ClaudeWebSearchAdapter: Extracted ${sources.length} URLs as fallback sources.`);
        }
        
        // Ensure citations in text are just numbers if we list sources separately
        cleanedAnswer = cleanedAnswer.replace(citationRegex, (match, p1) => `[${p1}]`);

        if (!cleanedAnswer.trim() && sources.length === 0) {
            cleanedAnswer = "No textual answer or sources received from Claude after web search.";
            logs.push("ClaudeWebSearchAdapter: Empty answer and no sources from Claude.");
        }

        return {
          status: "success",
          data: {
            answer: cleanedAnswer.trim(),
            sources: sources
          },
          logs: logs
        };

      } catch (error) {
        console.error(`ClaudeWebSearchAdapter: Error during Claude API call for webSearch:`, error);
        logs.push(`ClaudeWebSearchAdapter: API Error - ${error.message}`);
        return {
          status: "error",
          message: `ClaudeWebSearchAdapter: Error during Claude API call: ${error.message}`,
          logs: logs
        };
      }
    }
    
    logs.push(`ClaudeWebSearchAdapter: Unknown toolId: ${toolId}`);
    console.error(`ClaudeWebSearchAdapter: Unknown toolId: ${toolId}`);
    return { status: "error", message: `ClaudeWebSearchAdapter: Unknown tool: ${toolId}`, logs };
  }
}

module.exports = ClaudeWebSearchAdapter;


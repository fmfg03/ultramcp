const { TavilySearchResults } = require("@langchain/community/tools/tavily_search");
const { DynamicTool } = require("langchain/tools");
const { credentialsService } = require("../../src/services/credentialsService"); // Path to credentials service
const { EmbeddingSearchAdapter } = require("../adapters/EmbeddingSearchAdapter"); // Assuming this is the path
const { mcpBrokerService } = require("../services/mcpBrokerService");

/**
 * @file search_tool.js
 * @description LangChain Tools for Web Search and Document Retrieval.
 */

class SearchLangChainToolsFactory {
    constructor() {
        this.tavilyTool = null;
        this.documentRetrieverTool = null;
    }

    async #initializeTavilyTool() {
        if (this.tavilyTool) return;
        try {
            const tavilyApiKey = await credentialsService.getCredential("tavily", "api_key");
            if (!tavilyApiKey) {
                console.warn("[SearchLangChainToolsFactory] Tavily API key not found in credentialsService. Tavily search tool will not be available.");
                return;
            }
            this.tavilyTool = new TavilySearchResults({ apiKey: tavilyApiKey, maxResults: 5 });
            this.tavilyTool.name = "langchain_tavily_web_search"; // Standardize name
            console.log("[SearchLangChainToolsFactory] Tavily Search Tool initialized.");
        } catch (error) {
            console.error("[SearchLangChainToolsFactory] Failed to initialize Tavily Search Tool:", error.message);
        }
    }

    #initializeDocumentRetrieverTool() {
        if (this.documentRetrieverTool) return;
        // This tool will wrap our existing EmbeddingSearchAdapter
        // The EmbeddingSearchAdapter needs to be instantiated and its search_documents method called.
        // For simplicity, we assume EmbeddingSearchAdapter is already part of mcpBrokerService or can be called directly.
        
        this.documentRetrieverTool = new DynamicTool({
            name: "langchain_internal_document_retriever",
            description: "Searches and retrieves relevant documents from the internal knowledge base. Input should be a search query string.",
            func: async (query) => {
                if (typeof query !== 'string') {
                    return JSON.stringify({ error: "Input must be a string query." });
                }
                try {
                    console.log(`[SearchLangChainToolsFactory] Internal Document Retriever executing query: ${query}`);
                    // Assuming EmbeddingSearchAdapter is registered with mcpBrokerService
                    // or we have a direct way to call it.
                    // This is a conceptual call to how it might be invoked.
                    // The actual implementation would depend on how EmbeddingSearchAdapter is exposed.
                    if (mcpBrokerService && mcpBrokerService.executeTool) {
                        const result = await mcpBrokerService.executeTool("embedding_search/search_documents", { query });
                        console.log(`[SearchLangChainToolsFactory] Internal Document Retriever result:`, result);
                        // Format result for LLM consumption (e.g., string of concatenated snippets)
                        if (result && result.results && Array.isArray(result.results)) {
                            return result.results.map(doc => `Source: ${doc.metadata.source}\nContent: ${doc.page_content}`).join("\n\n---\n\n");
                        }
                        return JSON.stringify(result); // Fallback
                    } else {
                        console.error("[SearchLangChainToolsFactory] mcpBrokerService or EmbeddingSearchAdapter not available for document retrieval.");
                        return JSON.stringify({ error: "Internal document retrieval service not available." });
                    }
                } catch (error) {
                    console.error(`[SearchLangChainToolsFactory] Error in Internal Document Retriever: ${error.message}`);
                    return JSON.stringify({ error: `Internal document retrieval failed: ${error.message}` });
                }
            },
        });
        console.log("[SearchLangChainToolsFactory] Internal Document Retriever Tool initialized.");
    }

    async getTools() {
        await this.#initializeTavilyTool();
        this.#initializeDocumentRetrieverTool();

        const tools = [];
        if (this.tavilyTool) {
            tools.push({
                name: this.tavilyTool.name, // langchain_tavily_web_search
                description: this.tavilyTool.description,
                execute: async (params) => {
                    try {
                        // TavilySearchResults expects a string input
                        const inputString = (typeof params === 'string') ? params : (params && params.query ? params.query : '');
                        if (!inputString) throw new Error("Query string is required for Tavily search.");
                        console.log(`[SearchLangChainToolsFactory] Executing ${this.tavilyTool.name} with query: ${inputString}`);
                        const result = await this.tavilyTool.call(inputString);
                        console.log(`[SearchLangChainToolsFactory] Result for ${this.tavilyTool.name}:`, result);
                        return result;
                    } catch (error) {
                        console.error(`[SearchLangChainToolsFactory] Error executing ${this.tavilyTool.name}: ${error.message}`);
                        return JSON.stringify({ error: `Execution failed: ${error.message}`, details: error.stack });
                    }
                },
                getToolSchema: () => ({
                    name: this.tavilyTool.name,
                    description: this.tavilyTool.description,
                    input_schema: {
                        type: "object",
                        properties: { query: { type: "string", description: "The search query for web search." } },
                        required: ["query"]
                    }
                })
            });
        }

        if (this.documentRetrieverTool) {
            tools.push({
                name: this.documentRetrieverTool.name, // langchain_internal_document_retriever
                description: this.documentRetrieverTool.description,
                execute: async (params) => {
                     // DynamicTool's func handles the execution
                    const inputString = (typeof params === 'string') ? params : (params && params.query ? params.query : '');
                    if (!inputString) return JSON.stringify({ error: "Query string is required for internal document retrieval." });
                    return this.documentRetrieverTool.call(inputString); 
                },
                getToolSchema: () => ({
                    name: this.documentRetrieverTool.name,
                    description: this.documentRetrieverTool.description,
                    input_schema: {
                        type: "object",
                        properties: { query: { type: "string", description: "The search query for internal document retrieval." } },
                        required: ["query"]
                    }
                })
            });
        }
        return tools;
    }
}

// Conceptual registration
/*
async function registerSearchTools() {
    try {
        const searchToolFactory = new SearchLangChainToolsFactory();
        const searchTools = await searchToolFactory.getTools();
        
        searchTools.forEach(tool => {
            if (mcpBrokerService) {
                mcpBrokerService.registerTool(tool.name, {
                    execute: tool.execute,
                    getSchema: tool.getToolSchema,
                    isLangChainTool: true
                });
                console.log(`[SearchLangChainToolsFactory] ${tool.name} registered with mcpBrokerService.`);
            }
        });
    } catch (error) {
        console.error("[SearchLangChainToolsFactory] Failed to initialize or register search tools:", error.message);
    }
}
// registerSearchTools();
*/

module.exports = { SearchLangChainToolsFactory };


const { GithubToolkit } = require("langchain/agents/toolkits/github");
const { DynamicTool } = require("langchain/tools");
const { getJson } = require("serpapi"); // Example for a search tool, can be replaced
const { credentialsService } = require("../../src/services/credentialsService"); // Path to credentials service

/**
 * @file github_tool.js
 * @description LangChain Tool for GitHub interactions.
 * This tool wraps LangChain's GithubToolkit to allow various GitHub operations.
 */

class GitHubLangChainToolFactory {
    constructor(githubToken) {
        if (!githubToken) {
            console.warn("[GitHubLangChainToolFactory] GitHub token not provided directly, will attempt to fetch from credentialsService.");
        }
        this.githubToken = githubToken;
        this.toolkit = null; // Initialize later
    }

    async #initializeToolkit() {
        if (this.toolkit) return;

        let token = this.githubToken;
        if (!token) {
            try {
                token = await credentialsService.getCredential("github", "pat");
                if (!token) {
                    throw new Error("GitHub PAT not found in credentialsService.");
                }
            } catch (error) {
                console.error("[GitHubLangChainToolFactory] Failed to fetch GitHub PAT from credentialsService:", error.message);
                throw new Error(`GitHub PAT is required but not found or fetchable: ${error.message}`);
            }
        }
        // Langchain's GithubToolkit expects the token to be set as an environment variable
        // or passed directly. For robust integration, we should ensure it's available.
        // For now, we assume if a token is fetched/provided, the toolkit can use it.
        // The GithubToolkit itself might handle the token internally if `process.env.GITHUB_PERSONAL_ACCESS_TOKEN` is set.
        // If direct passing is needed, the toolkit instantiation might need adjustment based on LangChain version.
        process.env.GITHUB_PERSONAL_ACCESS_TOKEN = token; // Temporarily set for toolkit initialization
        this.toolkit = new GithubToolkit();
        // It's good practice to unset it if it was only for initialization and the toolkit stores it internally
        // delete process.env.GITHUB_PERSONAL_ACCESS_TOKEN; 
        // However, some LangChain tools might rely on it being present in env throughout their lifecycle.
        // For this example, we'll leave it set, assuming the toolkit might need it.
    }

    async getTools() {
        await this.#initializeToolkit();
        if (!this.toolkit) {
            console.error("[GitHubLangChainToolFactory] Toolkit not initialized, cannot get tools.");
            return [];
        }
        // The GithubToolkit instance has a `tools` property which is an array of tools.
        // We might want to wrap them or provide them as is.
        // For simplicity, returning them directly or wrapping them with our schema.
        return this.toolkit.tools.map(tool => ({
            name: `langchain_github_${tool.name.replace(/ /g, "_").toLowerCase()}`,
            description: tool.description,
            execute: async (params) => {
                try {
                    // Ensure the toolkit is initialized before execution
                    await this.#initializeToolkit(); 
                    console.log(`[GitHubLangChainTool] Executing ${tool.name} with params:`, params);
                    const result = await tool.call(params); // LangChain tools use .call()
                    console.log(`[GitHubLangChainTool] Result for ${tool.name}:`, result);
                    return result;
                } catch (error) {
                    console.error(`[GitHubLangChainTool] Error executing ${tool.name}: ${error.message}`);
                    return JSON.stringify({ error: `Execution failed: ${error.message}`, details: error.stack });
                }
            },
            // Schema generation would depend on how each specific tool in the toolkit defines its input.
            // For now, a generic schema or a schema derived from tool.inputKeys if available.
            getToolSchema: () => ({
                name: `langchain_github_${tool.name.replace(/ /g, "_").toLowerCase()}`,
                description: tool.description,
                input_schema: { 
                    type: "object", 
                    properties: { 
                        // This is a placeholder. Specific tools like ReadFile will have different args.
                        // Example: repo, path for ReadFile. query for SearchIssues.
                        // LangChain tools often expect a single string input or a specific object structure.
                        // We might need to inspect tool.inputKeys or tool.argsSchema
                        input: { type: "string", description: "Input for the GitHub tool. Structure depends on the specific tool." }
                    },
                    required: ["input"]
                 }
            })
        }));
    }
}


// Conceptual registration (similar to code_interpreter.js)
/*
async function registerGitHubTools() {
    try {
        const ghToolFactory = new GitHubLangChainToolFactory();
        const githubTools = await ghToolFactory.getTools();
        
        githubTools.forEach(tool => {
            if (mcpBrokerService) {
                mcpBrokerService.registerTool(tool.name, {
                    execute: tool.execute,
                    getSchema: tool.getToolSchema,
                    isLangChainTool: true
                });
                console.log(`[GitHubLangChainTool] ${tool.name} registered with mcpBrokerService.`);
            }
        });
    } catch (error) {
        console.error("[GitHubLangChainTool] Failed to initialize or register GitHub tools:", error.message);
    }
}

// registerGitHubTools(); // Call this during system initialization
*/

module.exports = { GitHubLangChainToolFactory };


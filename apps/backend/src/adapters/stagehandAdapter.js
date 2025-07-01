const BaseMCPAdapter = require("./baseMCPAdapter");
const { Stagehand } = require("@browserbasehq/stagehand");
const { z } = require("zod"); // Stagehand uses Zod for schemas, might be useful

// Load Browserbase credentials from environment variables
const BROWSERBASE_API_KEY = process.env.BROWSERBASE_API_KEY;
const BROWSERBASE_PROJECT_ID = process.env.BROWSERBASE_PROJECT_ID;

class StagehandAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    if (!BROWSERBASE_API_KEY || !BROWSERBASE_PROJECT_ID) {
      console.warn("StagehandAdapter: BROWSERBASE_API_KEY or BROWSERBASE_PROJECT_ID is not set. Adapter will not function.");
      this.stagehand = null;
    } else {
      try {
        // Initialize Stagehand with Browserbase credentials
        this.stagehand = new Stagehand({
          browserbase: {
            apiKey: BROWSERBASE_API_KEY,
            projectId: BROWSERBASE_PROJECT_ID,
          },
          // Add OpenAI/Anthropic keys if needed for specific features, load from env
          // openai: { apiKey: process.env.OPENAI_API_KEY },
          // anthropic: { apiKey: process.env.ANTHROPIC_API_KEY },
        });
        console.log("StagehandAdapter: Initialized with Browserbase credentials.");
      } catch (error) {
        console.error("StagehandAdapter: Failed to initialize client:", error);
        this.stagehand = null;
      }
    }
  }

  getId() {
    return "stagehand";
  }

  async getTools() {
    // Refined tools based on Stagehand SDK capabilities
    return [
      {
        id: `${this.getId()}/goto`,
        name: "Navigate Browser (Stagehand)",
        description: "Navigates the browser to a specified URL.",
        parameters: {
          type: "object",
          properties: {
            url: { type: "string", description: "The URL to navigate to." },
            // sessionId: { type: "string", description: "Optional session ID to reuse a browser session." }
          },
          required: ["url"]
        },
      },
      {
        id: `${this.getId()}/act`,
        name: "Perform Action (Stagehand)",
        description: "Performs an action on the current browser page based on a natural language instruction.",
        parameters: {
          type: "object",
          properties: {
            instruction: { type: "string", description: "Natural language instruction for the action (e.g., \"Click the search button\")." },
            // sessionId: { type: "string", description: "Optional session ID to reuse a browser session." }
          },
          required: ["instruction"]
        },
      },
      {
        id: `${this.getId()}/extract`,
        name: "Extract Data (Stagehand)",
        description: "Extracts structured data from the current browser page based on an instruction.",
        parameters: {
          type: "object",
          properties: {
            instruction: { type: "string", description: "Natural language instruction for what data to extract." },
            schema: { type: "object", description: "Optional Zod schema definition (as JSON) for the desired data structure. If omitted, LLM infers structure." },
            // sessionId: { type: "string", description: "Optional session ID to reuse a browser session." }
          },
          required: ["instruction"]
        },
      },
    ];
  }

  // Helper to get a page object (potentially managing sessions in the future)
  async _getPage(sessionId) {
    if (!this.stagehand) {
      throw new Error("Stagehand client is not initialized.");
    }
    // For now, each call gets a new page context. Session management could be added.
    // If sessionId was provided, we might try to connect to an existing session.
    return this.stagehand.page; 
  }

  // Updated signature: removed 'action' parameter
  async executeAction(toolId, params) { 
    // Check params directly
    if (!params) {
        throw new Error("Missing parameters for Stagehand action.");
    }
    
    const page = await this._getPage(params.sessionId); // Assuming sessionId might be added later
    const toolName = toolId.split("/")[1];
    console.log(`StagehandAdapter executing: ${toolId} with params:`, params);

    try {
      let response;
      switch (toolName) {
        case "goto":
          const { url } = params;
          if (!url) throw new Error("Missing required parameter: url");
          response = await page.goto(url);
          // goto usually returns null or response object, maybe just confirm success
          return { success: true, message: `Navigated to ${url}` };

        case "act":
          const { instruction: actInstruction } = params;
          if (!actInstruction) throw new Error("Missing required parameter: instruction");
          // The act method performs the action
          response = await page.act(actInstruction);
          // act might return details about the action taken, or just confirm success
          return { success: true, message: `Action performed: ${actInstruction}`, result: response };

        case "extract":
          const { instruction: extractInstruction, schema: jsonSchema } = params;
          if (!extractInstruction) throw new Error("Missing required parameter: instruction");
          
          let zodSchema = undefined;
          if (jsonSchema) {
            // Basic attempt to parse JSON schema into Zod. 
            // This is complex and might need a more robust implementation 
            // or rely on Stagehand's internal handling if schema is passed differently.
            try {
              // This is a placeholder - converting JSON schema to Zod dynamically is non-trivial.
              // For now, we'll pass the instruction and let the LLM infer if schema is complex.
              // If the schema is simple (e.g., { text: "string" }), we might parse it.
              // A safer approach might be to require schema in Zod format string directly.
              console.warn("StagehandAdapter: Dynamic Zod schema generation from JSON is complex. Passing instruction only for now.");
            } catch (e) {
              console.error("Failed to parse schema for Stagehand extract:", e);
              throw new Error("Invalid schema format provided for extract tool.");
            }
          }

          // Use the extract method
          response = await page.extract({
            instruction: extractInstruction,
            // schema: zodSchema, // Pass schema if successfully parsed/defined
          });
          return { success: true, message: `Data extracted based on: ${extractInstruction}`, data: response };

        default:
          throw new Error(`Unknown tool/action: ${toolId}`);
      }
    } catch (error) {
      console.error(`StagehandAdapter Error executing ${toolId}:`, error.message);
      throw new Error(`Failed to execute Stagehand action ${toolId}: ${error.message}`);
    }
  }
}

module.exports = StagehandAdapter;


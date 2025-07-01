const axios = require("axios");
const BaseMCPAdapter = require("./baseMCPAdapter");
const config = require("../config/env"); // Assuming API keys might be stored here

const GETZEP_API_URL = process.env.GETZEP_API_URL || "https://api.getzep.com"; // Example URL
const GETZEP_API_KEY = process.env.GETZEP_API_KEY; // Load from env

class GetzepAdapter extends BaseMCPAdapter {
  constructor() {
    super(config); // Pass config if needed
    if (!GETZEP_API_KEY) {
      console.warn("GetzepAdapter: GETZEP_API_KEY is not set. Adapter might not function correctly.");
    }
    this.client = axios.create({
      baseURL: GETZEP_API_URL,
      headers: { Authorization: `Bearer ${GETZEP_API_KEY}` },
    });
  }

  getId() {
    return "getzep";
  }

  async getTools() {
    // Define tools based on Getzep's capabilities (memory management)
    // This is a hypothetical example
    return [
      {
        id: `${this.getId()}/addMemory`,
        name: "Add Memory",
        description: "Adds a message or interaction to a session's memory.",
        parameters: {
          type: "object",
          properties: {
            sessionId: { type: "string", description: "The unique ID of the session." },
            role: { type: "string", description: "Role of the message sender (e.g., 'user', 'ai')." },
            content: { type: "string", description: "The content of the message." },
          },
          required: ["sessionId", "role", "content"],
        },
      },
      {
        id: `${this.getId()}/getMemory`,
        name: "Get Memory",
        description: "Retrieves the recent memory for a given session.",
        parameters: {
          type: "object",
          properties: {
            sessionId: { type: "string", description: "The unique ID of the session." },
            limit: { type: "integer", description: "Optional limit on the number of messages to retrieve." },
          },
          required: ["sessionId"],
        },
      },
      {
        id: `${this.getId()}/searchMemory`,
        name: "Search Memory",
        description: "Searches the memory of a session for relevant information.",
        parameters: {
          type: "object",
          properties: {
            sessionId: { type: "string", description: "The unique ID of the session." },
            query: { type: "string", description: "The search query." },
          },
          required: ["sessionId", "query"],
        },
      },
    ];
  }

  // Updated signature: removed 'action' parameter
  async executeAction(toolId, params) { 
    if (!GETZEP_API_KEY) {
      throw new Error("Getzep API Key is not configured.");
    }

    // Check params directly
    if (!params) {
        throw new Error("Missing parameters for Getzep action.");
    }

    const toolName = toolId.split("/")[1]; // Extract tool name like 'addMemory'
    console.log(`GetzepAdapter executing: ${toolId} with params:`, params);

    try {
      let response;
      switch (toolName) {
        case "addMemory":
          if (!params.sessionId || !params.role || !params.content) {
            throw new Error("Missing required parameters for addMemory: sessionId, role, content");
          }
          // Example: POST /sessions/{sessionId}/memory
          response = await this.client.post(`/sessions/${params.sessionId}/memory`, {
            messages: [{ role: params.role, content: params.content }],
          });
          return { success: true, ...response.data }; // Adjust based on actual API response
        case "getMemory":
          if (!params.sessionId) {
            throw new Error("Missing required parameter for getMemory: sessionId");
          }
          // Example: GET /sessions/{sessionId}/memory
          response = await this.client.get(`/sessions/${params.sessionId}/memory`, {
            params: { limit: params.limit }, // limit might be undefined, handled by API
          });
          return { success: true, ...response.data }; // Adjust based on actual API response
        case "searchMemory":
          if (!params.sessionId || !params.query) {
            throw new Error("Missing required parameters for searchMemory: sessionId, query");
          }
          // Example: POST /sessions/{sessionId}/search
          response = await this.client.post(`/sessions/${params.sessionId}/search`, {
            query: params.query,
          });
          return { success: true, ...response.data }; // Adjust based on actual API response
        default:
          throw new Error(`Unknown tool/action: ${toolId}`);
      }
    } catch (error) {
      console.error(`GetzepAdapter Error executing ${toolId}:`, error.response?.data || error.message);
      const errorMessage = error.response?.data?.message || error.message || "Unknown error";
      throw new Error(`Failed to execute Getzep action ${toolId}: ${errorMessage}`);
    }
  }
}

module.exports = GetzepAdapter;


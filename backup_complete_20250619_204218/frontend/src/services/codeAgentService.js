// Service to interact with the backend MCP Broker API

const API_BASE_URL = ""; // Use relative path for Vite proxy

/**
 * Fetches the list of available MCP tools from the backend.
 * @returns {Promise<Array<object>>} A promise that resolves to an array of tool objects.
 */
const getTools = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tools`); // Request goes to /api/tools
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const tools = await response.json();
    return tools;
  } catch (error) {
    console.error("Error fetching tools:", error);
    throw error; // Re-throw the error to be handled by the caller
  }
};

/**
 * Executes a specific MCP tool action via the backend API.
 * @param {string} toolId The ID of the tool to execute.
 * @param {string} action The action to perform (currently likely just implied).
 * @param {object} params The parameters for the action.
 * @returns {Promise<object>} A promise that resolves to the result of the action.
 */
const executeTool = async (toolId, action, params) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tools/execute`, { // Request goes to /api/tools/execute
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ toolId, action, params }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || "Unknown error"}`);
    }
    const result = await response.json();
    return result;
  } catch (error) {
    console.error(`Error executing tool ${toolId}:`, error);
    throw error; // Re-throw the error to be handled by the caller
  }
};

const codeAgentService = {
  getTools,
  executeTool,
};

export default codeAgentService;


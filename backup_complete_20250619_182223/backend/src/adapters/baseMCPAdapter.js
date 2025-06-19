// Base class/interface for all MCP Adapters

class BaseMCPAdapter {
  constructor(config = {}) { // Added default for config
    this.config = config;
  }

  /**
   * Returns a unique identifier for this adapter.
   * @returns {string} The adapter ID.
   */
  getId() {
    throw new Error("Method 'getId()' must be implemented by subclasses.");
  }

  /**
   * Returns a list of tools provided by this adapter.
   * Each tool object should conform to the MCP tool specification.
   * @returns {Promise<Array<object>>} A promise that resolves to an array of tool objects.
   */
  async getTools() {
    throw new Error("Method 'getTools()' must be implemented by subclasses.");
  }

  /**
   * Executes a specific action for a tool managed by this adapter.
   * @param {string} toolName The name of the tool to execute (e.g., "scrapeUrl", not "adapterId/scrapeUrl").
   * @param {object} params The parameters for the action.
   * @returns {Promise<object>} A promise that resolves to the result of the action.
   */
  async executeAction(toolName, params) {
    throw new Error("Method 'executeAction(toolName, params)' must be implemented by subclasses.");
  }

  // Logging methods
  logInfo(message, details = null) {
    const adapterId = typeof this.getId === 'function' ? this.getId() : 'BaseAdapter';
    console.log(`[INFO][${adapterId}] ${message}`);
    if (details) {
      console.log(`[INFO][${adapterId}] Details:`, details);
    }
  }

  logWarn(message, details = null) {
    const adapterId = typeof this.getId === 'function' ? this.getId() : 'BaseAdapter';
    console.warn(`[WARN][${adapterId}] ${message}`);
    if (details) {
      console.warn(`[WARN][${adapterId}] Details:`, details);
    }
  }

  logError(message, error = null) {
    const adapterId = typeof this.getId === 'function' ? this.getId() : 'BaseAdapter';
    console.error(`[ERROR][${adapterId}] ${message}`);
    if (error) {
      console.error(`[ERROR][${adapterId}] Error Details:`, error.message || error, error.stack || '');
    }
  }
}

module.exports = BaseMCPAdapter;


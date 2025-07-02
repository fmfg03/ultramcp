const BaseMCPAdapter = require("./baseMCPAdapter");
const { spawn } = require("child_process");
const WebSocket = require("ws");

/**
 * Playwright-MCP Adapter for UltraMCP
 * Integrates Playwright-MCP server as an MCP adapter in the UltraMCP ecosystem
 * 
 * Features:
 * - Dynamic connection to Playwright-MCP server
 * - Tool discovery and execution routing
 * - Session management and error handling
 * - Integration with UltraMCP monitoring and logging
 */
class PlaywrightMCPAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    
    // Configuration
    this.serverCommand = config.serverCommand || ["npx", "playwright-mcp"];
    this.timeout = config.timeout || 30000;
    this.headless = config.headless !== false; // Default to headless
    this.maxRetries = config.maxRetries || 3;
    
    // State management
    this.serverProcess = null;
    this.mcpConnection = null;
    this.isConnected = false;
    this.availableTools = [];
    this.sessionId = null;
    
    // Initialize connection
    this.initializeConnection();
  }

  getId() {
    return "playwright-mcp";
  }

  /**
   * Initialize connection to Playwright-MCP server
   */
  async initializeConnection() {
    try {
      this.logInfo("Initializing Playwright-MCP connection");
      
      // Start Playwright-MCP server process
      await this.startMCPServer();
      
      // Establish WebSocket connection
      await this.connectToMCPServer();
      
      // Discover available tools
      await this.discoverTools();
      
      this.logInfo("Playwright-MCP adapter initialized successfully");
    } catch (error) {
      this.logError("Failed to initialize Playwright-MCP adapter", error);
      throw error;
    }
  }

  /**
   * Start the Playwright-MCP server process
   */
  async startMCPServer() {
    return new Promise((resolve, reject) => {
      try {
        this.logInfo("Starting Playwright-MCP server", { command: this.serverCommand });
        
        this.serverProcess = spawn(this.serverCommand[0], this.serverCommand.slice(1), {
          stdio: ["pipe", "pipe", "pipe"],
          env: {
            ...process.env,
            PLAYWRIGHT_HEADLESS: this.headless.toString(),
            MCP_LOG_LEVEL: "info"
          }
        });

        // Handle server output
        this.serverProcess.stdout.on("data", (data) => {
          const output = data.toString();
          this.logInfo("Playwright-MCP server output", { output: output.trim() });
          
          // Check if server is ready (you may need to adjust this based on actual output)
          if (output.includes("Server listening") || output.includes("MCP server started")) {
            resolve();
          }
        });

        this.serverProcess.stderr.on("data", (data) => {
          const error = data.toString();
          this.logWarn("Playwright-MCP server stderr", { error: error.trim() });
        });

        this.serverProcess.on("error", (error) => {
          this.logError("Playwright-MCP server process error", error);
          reject(error);
        });

        this.serverProcess.on("exit", (code) => {
          this.logWarn("Playwright-MCP server exited", { code });
          this.isConnected = false;
        });

        // Timeout fallback
        setTimeout(() => {
          if (!this.isConnected) {
            this.logInfo("Server startup timeout reached, proceeding with connection attempt");
            resolve();
          }
        }, 5000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Connect to the MCP server via WebSocket or stdio
   */
  async connectToMCPServer() {
    try {
      // For now, we'll communicate via stdio with the spawned process
      // In a full implementation, you might use WebSocket or other protocols
      
      this.mcpConnection = {
        send: (message) => {
          if (this.serverProcess && this.serverProcess.stdin.writable) {
            this.serverProcess.stdin.write(JSON.stringify(message) + "\n");
          }
        },
        onMessage: null,
        onError: null
      };

      // Set up message handling
      this.setupMessageHandling();
      
      this.isConnected = true;
      this.logInfo("Connected to Playwright-MCP server");
      
    } catch (error) {
      this.logError("Failed to connect to MCP server", error);
      throw error;
    }
  }

  /**
   * Set up message handling for MCP communication
   */
  setupMessageHandling() {
    if (this.serverProcess && this.serverProcess.stdout) {
      this.serverProcess.stdout.on("data", (data) => {
        try {
          const lines = data.toString().split("\n").filter(line => line.trim());
          
          for (const line of lines) {
            try {
              const message = JSON.parse(line);
              this.handleMCPMessage(message);
            } catch (parseError) {
              // Ignore non-JSON output (likely logs)
              continue;
            }
          }
        } catch (error) {
          this.logError("Error processing MCP messages", error);
        }
      });
    }
  }

  /**
   * Handle incoming MCP messages
   */
  handleMCPMessage(message) {
    this.logInfo("Received MCP message", { message });
    
    // Handle different MCP message types
    switch (message.method) {
      case "tools/list":
        this.handleToolsList(message);
        break;
      case "tools/call":
        this.handleToolCallResponse(message);
        break;
      default:
        this.logInfo("Unhandled MCP message type", { method: message.method });
    }
  }

  /**
   * Discover available tools from Playwright-MCP server
   */
  async discoverTools() {
    try {
      this.logInfo("Discovering Playwright-MCP tools");
      
      // Send tools list request to MCP server
      const request = {
        jsonrpc: "2.0",
        id: this.generateRequestId(),
        method: "tools/list",
        params: {}
      };
      
      if (this.mcpConnection) {
        this.mcpConnection.send(request);
      }
      
      // For now, define expected tools based on typical Playwright-MCP capabilities
      this.availableTools = [
        {
          id: `${this.getId()}/navigate`,
          name: "Navigate to URL",
          description: "Navigate to a specific URL and wait for page load",
          parameters: {
            type: "object",
            properties: {
              url: {
                type: "string",
                description: "The URL to navigate to"
              },
              waitFor: {
                type: "string",
                description: "What to wait for after navigation (load, networkidle, etc.)",
                default: "load"
              }
            },
            required: ["url"]
          }
        },
        {
          id: `${this.getId()}/click`,
          name: "Click Element",
          description: "Click on an element specified by selector",
          parameters: {
            type: "object",
            properties: {
              selector: {
                type: "string",
                description: "CSS selector or text content to click"
              },
              options: {
                type: "object",
                description: "Click options (timeout, force, etc.)"
              }
            },
            required: ["selector"]
          }
        },
        {
          id: `${this.getId()}/type`,
          name: "Type Text",
          description: "Type text into an input field",
          parameters: {
            type: "object",
            properties: {
              selector: {
                type: "string",
                description: "CSS selector for the input field"
              },
              text: {
                type: "string",
                description: "Text to type"
              },
              clear: {
                type: "boolean",
                description: "Clear the field before typing",
                default: true
              }
            },
            required: ["selector", "text"]
          }
        },
        {
          id: `${this.getId()}/screenshot`,
          name: "Take Screenshot",
          description: "Take a screenshot of the current page or specific element",
          parameters: {
            type: "object",
            properties: {
              selector: {
                type: "string",
                description: "CSS selector for element screenshot (optional)"
              },
              fullPage: {
                type: "boolean",
                description: "Take full page screenshot",
                default: false
              },
              quality: {
                type: "number",
                description: "Screenshot quality (0-100)",
                default: 90
              }
            }
          }
        },
        {
          id: `${this.getId()}/extract`,
          name: "Extract Data",
          description: "Extract structured data from the page",
          parameters: {
            type: "object",
            properties: {
              schema: {
                type: "object",
                description: "JSON schema describing the data to extract"
              },
              selector: {
                type: "string",
                description: "CSS selector to limit extraction scope (optional)"
              }
            },
            required: ["schema"]
          }
        },
        {
          id: `${this.getId()}/wait_for`,
          name: "Wait for Element",
          description: "Wait for an element to appear or disappear",
          parameters: {
            type: "object",
            properties: {
              selector: {
                type: "string",
                description: "CSS selector to wait for"
              },
              state: {
                type: "string",
                description: "Element state to wait for (visible, hidden, attached, detached)",
                default: "visible"
              },
              timeout: {
                type: "number",
                description: "Timeout in milliseconds",
                default: 30000
              }
            },
            required: ["selector"]
          }
        }
      ];
      
      this.logInfo(`Discovered ${this.availableTools.length} Playwright-MCP tools`);
      
    } catch (error) {
      this.logError("Failed to discover tools", error);
      throw error;
    }
  }

  /**
   * Get available tools
   */
  async getTools() {
    return this.availableTools;
  }

  /**
   * Execute a tool action
   */
  async executeAction(toolId, params) {
    try {
      const toolName = toolId.split("/")[1];
      this.logInfo(`Executing Playwright-MCP action: ${toolName}`, { params });
      
      // Validate connection
      if (!this.isConnected || !this.mcpConnection) {
        throw new Error("Playwright-MCP connection not established");
      }
      
      // Create MCP tool call request
      const request = {
        jsonrpc: "2.0",
        id: this.generateRequestId(),
        method: "tools/call",
        params: {
          name: toolName,
          arguments: params
        }
      };
      
      // Send request to MCP server
      const result = await this.sendMCPRequest(request);
      
      this.logInfo(`Playwright-MCP action completed: ${toolName}`, { result });
      return result;
      
    } catch (error) {
      this.logError(`Failed to execute Playwright-MCP action: ${toolId}`, error);
      throw error;
    }
  }

  /**
   * Send MCP request and wait for response
   */
  async sendMCPRequest(request) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`MCP request timeout: ${request.method}`));
      }, this.timeout);
      
      // Store the resolve/reject for this request ID
      if (!this.pendingRequests) {
        this.pendingRequests = new Map();
      }
      
      this.pendingRequests.set(request.id, { resolve, reject, timeout });
      
      // Send the request
      this.mcpConnection.send(request);
    });
  }

  /**
   * Handle tool call response
   */
  handleToolCallResponse(message) {
    if (this.pendingRequests && this.pendingRequests.has(message.id)) {
      const { resolve, reject, timeout } = this.pendingRequests.get(message.id);
      clearTimeout(timeout);
      this.pendingRequests.delete(message.id);
      
      if (message.error) {
        reject(new Error(message.error.message || "MCP tool call failed"));
      } else {
        resolve(message.result);
      }
    }
  }

  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `playwright-mcp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Handle tools list response
   */
  handleToolsList(message) {
    if (message.result && message.result.tools) {
      this.logInfo("Received tools list from Playwright-MCP", { 
        count: message.result.tools.length 
      });
      
      // Update available tools with server response
      this.availableTools = message.result.tools.map(tool => ({
        id: `${this.getId()}/${tool.name}`,
        name: tool.displayName || tool.name,
        description: tool.description,
        parameters: tool.inputSchema || {}
      }));
    }
  }

  /**
   * Clean up resources
   */
  async cleanup() {
    try {
      this.logInfo("Cleaning up Playwright-MCP adapter");
      
      this.isConnected = false;
      
      if (this.serverProcess) {
        this.serverProcess.kill("SIGTERM");
        
        // Force kill after timeout
        setTimeout(() => {
          if (this.serverProcess && !this.serverProcess.killed) {
            this.serverProcess.kill("SIGKILL");
          }
        }, 5000);
      }
      
      if (this.pendingRequests) {
        // Reject all pending requests
        for (const [id, { reject, timeout }] of this.pendingRequests) {
          clearTimeout(timeout);
          reject(new Error("Adapter cleanup - request cancelled"));
        }
        this.pendingRequests.clear();
      }
      
      this.logInfo("Playwright-MCP adapter cleanup completed");
      
    } catch (error) {
      this.logError("Error during Playwright-MCP adapter cleanup", error);
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      if (!this.isConnected || !this.serverProcess) {
        return { healthy: false, reason: "Not connected" };
      }
      
      // Simple ping test
      const pingRequest = {
        jsonrpc: "2.0",
        id: this.generateRequestId(),
        method: "ping",
        params: {}
      };
      
      await this.sendMCPRequest(pingRequest);
      
      return { 
        healthy: true, 
        tools: this.availableTools.length,
        connected: this.isConnected
      };
      
    } catch (error) {
      return { 
        healthy: false, 
        reason: error.message,
        connected: this.isConnected
      };
    }
  }
}

module.exports = PlaywrightMCPAdapter;
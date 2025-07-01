const BaseMCPAdapter = require("./baseMCPAdapter");
const { executeInContainer, checkDockerAvailability } = require("../utils/dockerService.js");
const AppError = require("../utils/AppError.js");

// Define a default Docker image for CLI commands. This should ideally be configurable
// and a minimal image with only necessary tools.
const DEFAULT_CLI_DOCKER_IMAGE = "alpine/git"; // alpine/git includes common shell tools and git.

class CliAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    this.dockerImage = config.dockerImage || DEFAULT_CLI_DOCKER_IMAGE;
    console.log(`CliAdapter: Initialized. Shell commands will be executed in Docker image: ${this.dockerImage}`);
    // Check Docker availability on startup (optional, can be done on first use)
    checkDockerAvailability().then(available => {
      if (!available) {
        console.warn("CliAdapter Warning: Docker does not seem to be available. CLI execution will fail.");
      }
    });
  }

  getId() {
    return "cli";
  }

  async getTools() {
    return [
      {
        id: `${this.getId()}/execute_command`,
        name: "Execute Shell Command (Sandboxed CLI)",
        description: `Executes a shell command in a sandboxed Docker container (${this.dockerImage}).`,
        parameters: {
          type: "object",
          properties: {
            command: { type: "string", description: "The shell command to execute (e.g., \"ls -la\")." },
            args: { type: "array", items: { type: "string" }, description: "Optional arguments for the command.", default: [] },
            workingDir: { type: "string", description: "Optional working directory inside the container (e.g., /mnt/data)." },
            envVars: { type: "object", additionalProperties: { type: "string" }, description: "Optional environment variables for the command (e.g., {\"MY_VAR\": \"value\"})." },
            // volumeBinds: { type: "array", items: { type: "string" }, description: "Optional volume binds (e.g., [\"/host/path:/container/path:ro\"]). Use with extreme caution." }
          },
          required: ["command"]
        },
      }
    ];
  }

  async executeAction(toolId, params) {
    console.log(`CliAdapter executing (sandboxed): ${toolId} with params:`, params);
    if (toolId === `${this.getId()}/execute_command`) {
      if (!params || !params.command) {
        throw new AppError("Missing required parameter: command", 400, "CLI_MISSING_COMMAND");
      }

      const commandParts = [params.command, ...(params.args || [])];
      
      const dockerOptions = {
        workingDir: params.workingDir, // Will default to "/" in dockerService if undefined
        // Binds should be carefully controlled and validated if exposed.
        // For now, not directly exposing arbitrary binds from user input for security.
        // binds: params.volumeBinds || [], 
        env: params.envVars || {},
        timeout: this.config.timeout || 60000, // Adapter-specific timeout or global default
        resourceLimits: this.config.resourceLimits || { Memory: 128 * 1024 * 1024 } // Example: 128MB RAM limit
      };

      try {
        console.log(`Executing in Docker (${this.dockerImage}):`, commandParts.join(" "), "Options:", dockerOptions);
        const result = await executeInContainer(this.dockerImage, commandParts, dockerOptions);
        
        if (result.exitCode === 0) {
          return { success: true, stdout: result.stdout, stderr: result.stderr, exitCode: result.exitCode };
        } else {
          console.warn(`CLI execution in Docker failed for command: ${commandParts.join(" ")}, Exit Code: ${result.exitCode}`);
          // For non-zero exit codes, it's often useful to return stderr as part of the error or main output
          return { 
            success: false, 
            error: `Command execution failed with exit code ${result.exitCode}.`, 
            stdout: result.stdout, 
            stderr: result.stderr, 
            exitCode: result.exitCode 
          };
        }
      } catch (error) {
        // AppError from dockerService will be caught here, or other unexpected errors
        console.error(`CLI Docker execution failed for command: ${commandParts.join(" ")}`, error);
        throw error; // Re-throw the AppError or a new one wrapping it
      }
    }
    throw new AppError(`Tool ${toolId} not supported by CliAdapter.`, 404, "TOOL_NOT_FOUND");
  }
}

module.exports = CliAdapter;


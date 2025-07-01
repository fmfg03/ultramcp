const BaseMCPAdapter = require("./baseMCPAdapter");
const { executeInContainer, checkDockerAvailability } = require("../utils/dockerService.js");
const AppError = require("../utils/AppError.js");

// Define a default Docker image for GitHub CLI commands.
// This image should have gh CLI installed.
// For example, a custom image or one like "actions/gh-cli" or a derivative.
// Using "alpine/git" for now, assuming gh might be available or installed in a derived image.
// A more robust solution would be a dedicated image with gh.
const DEFAULT_GITHUB_DOCKER_IMAGE = "alpine/git"; // Placeholder, ideally an image with gh pre-installed

class GithubAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    this.token = process.env.GITHUB_TOKEN || config.token;
    this.dockerImage = config.dockerImage || DEFAULT_GITHUB_DOCKER_IMAGE;

    if (!this.token) {
      console.warn("GithubAdapter: GITHUB_TOKEN is not set. gh CLI might not be authenticated.");
    }
    console.log(`GithubAdapter: Initialized. gh CLI commands will be executed in Docker image: ${this.dockerImage}`);
    
    checkDockerAvailability().then(available => {
      if (!available) {
        console.warn("GithubAdapter Warning: Docker does not seem to be available. gh CLI execution will fail.");
      } else {
        // Optionally, check if gh is available in the specified Docker image on startup
        // This is more complex and might be better handled on first actual use or with a dedicated health check.
      }
    });
  }

  getId() {
    return "github";
  }

  async getTools() {
    return [
      {
        id: `${this.getId()}/get_repo_content`,
        name: "Get Repository Content (GitHub, Sandboxed)",
        description: `Retrieves the content of a file within a GitHub repository using gh CLI in a sandboxed Docker container (${this.dockerImage}).`,
        parameters: {
          type: "object",
          properties: {
            owner: { type: "string", description: "Repository owner (user or organization)." },
            repo: { type: "string", description: "Repository name." },
            path: { type: "string", description: "Path to the file within the repository." },
            ref: { type: "string", description: "Optional branch, tag, or commit SHA (defaults to default branch)." }
          },
          required: ["owner", "repo", "path"]
        },
      },
      // Future tools: list_branches, create_commit, etc.
    ];
  }

  async executeAction(toolId, params) {
    console.log(`GithubAdapter executing (sandboxed): ${toolId} with params:`, params);

    if (!params) {
      throw new AppError("Missing parameters for GitHub action.", 400, "GITHUB_MISSING_PARAMS");
    }

    if (toolId === `${this.getId()}/get_repo_content`) {
      const { owner, repo, path, ref } = params;
      if (!owner || !repo || !path) {
        throw new AppError("Missing required parameters: owner, repo, path", 400, "GITHUB_MISSING_REPO_INFO");
      }

      // Construct the gh command parts
      const ghCommand = "gh";
      const ghArgs = ["api", `/repos/${owner}/${repo}/contents/${path}`];
      if (ref) {
        ghArgs.push(`--jq`, `.?ref=${ref}`); // Using --jq for query params with gh api, or construct URL string for ?ref=
        // Simpler: construct the full path with ref for gh api
        // ghArgs[1] = `/repos/${owner}/${repo}/contents/${path}?ref=${ref}`; // This is more direct for gh api
      }
      // Corrected approach for ref with gh api:
      let apiPath = `/repos/${owner}/${repo}/contents/${path}`;
      if (ref) {
        apiPath += `?ref=${ref}`;
      }
      const commandToExecute = [ghCommand, "api", apiPath];

      const dockerOptions = {
        env: { GITHUB_TOKEN: this.token }, // Pass GITHUB_TOKEN to the container
        timeout: this.config.timeout || 60000, 
        resourceLimits: this.config.resourceLimits || { Memory: 128 * 1024 * 1024 }
      };

      try {
        console.log(`Executing in Docker (${this.dockerImage}):`, commandToExecute.join(" "));
        const result = await executeInContainer(this.dockerImage, commandToExecute, dockerOptions);

        if (result.stderr && result.exitCode !== 0) {
            // If gh CLI itself errors (e.g., not found in image, auth failure before API call)
            console.error(`GithubAdapter gh Docker execution stderr for ${toolId}:`, result.stderr);
            throw new AppError(`gh command execution in Docker failed: ${result.stderr}`, 500, "GITHUB_DOCKER_EXEC_STDERR", true, result);
        }
        
        // gh api commands often output JSON to stdout. stderr might contain progress or warnings.
        if (result.stderr){
            console.warn(`GithubAdapter gh Docker execution stderr (non-fatal or warning): ${result.stderr}`);
        }

        if (result.exitCode !== 0) {
            throw new AppError(`gh command failed with exit code ${result.exitCode}. Stdout: ${result.stdout}, Stderr: ${result.stderr}`, 500, "GITHUB_GH_COMMAND_FAILED", true, result);
        }

        const responseData = JSON.parse(result.stdout);
        let decoded_content = null;
        if (responseData.content && responseData.encoding === "base64") {
          decoded_content = Buffer.from(responseData.content, "base64").toString("utf-8");
        }

        return {
          success: true,
          message: `Successfully retrieved content for ${path} in ${owner}/${repo}`,
          data: { ...responseData, decoded_content }
        };

      } catch (error) {
        // Handle AppErrors from executeInContainer or JSON.parse errors
        console.error(`GithubAdapter Docker execution or processing failed for ${toolId}:`, error);
        if (error instanceof AppError) throw error;
        throw new AppError(`Failed to execute or process gh command for ${toolId}: ${error.message}`, 500, "GITHUB_ACTION_FAILED", true, error);
      }
    }
    throw new AppError(`Tool ${toolId} not supported by GithubAdapter.`, 404, "TOOL_NOT_FOUND");
  }
}

module.exports = GithubAdapter;


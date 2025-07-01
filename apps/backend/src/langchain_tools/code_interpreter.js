const { executeInContainer, checkDockerAvailability } = require("../utils/dockerService.js");
const AppError = require("../utils/AppError.js");

// Define a default Docker image for Python code execution.
// This should be a minimal Python image.
const DEFAULT_PYTHON_DOCKER_IMAGE = "python:3.11-alpine";

/**
 * @file code_interpreter.js
 * @description LangChain Tool for Python Code Interpretation, sandboxed with Docker.
 */
class CodeInterpreterLangChainTool {
    constructor(config = {}) {
        this.name = "langchain_code_interpreter";
        this.description = `Executes Python code snippets in a sandboxed Docker container (${config.dockerImage || DEFAULT_PYTHON_DOCKER_IMAGE}) and returns the result. Input should be a string of valid Python code.`;
        this.dockerImage = config.dockerImage || DEFAULT_PYTHON_DOCKER_IMAGE;
        this.config = config;

        checkDockerAvailability().then(available => {
            if (!available) {
                console.warn(`CodeInterpreterLangChainTool Warning: Docker does not seem to be available. Python execution will fail.`);
            }
        });
    }

    async execute(codeString) {
        if (typeof codeString !== "string") {
            // Return a JSON string as per previous error format, but use AppError for consistency if this were an API endpoint
            return JSON.stringify({ error: "Input must be a string of Python code." });
        }

        const command = ["python", "-c", codeString];
        const dockerOptions = {
            timeout: this.config.timeout || 60000, // 60 seconds default timeout
            resourceLimits: this.config.resourceLimits || { Memory: 256 * 1024 * 1024, CpuShares: 512 }, // Example: 256MB RAM limit
            // No volume binds by default for security
        };

        try {
            console.log(`[CodeInterpreterLangChainTool] Executing code in Docker (${this.dockerImage}): python -c "${codeString.substring(0, 100)}..."`);
            const result = await executeInContainer(this.dockerImage, command, dockerOptions);

            if (result.exitCode === 0) {
                console.log(`[CodeInterpreterLangChainTool] Execution successful. Stdout: ${result.stdout}`);
                // LangChain tools typically expect a string output.
                // Concatenate stdout and stderr if both exist, or just stdout.
                let output = result.stdout;
                if (result.stderr) {
                    // Decide if stderr should be part of the successful output or indicate an issue
                    // For a REPL, stderr might contain warnings or non-fatal errors that are part of the interaction
                    output += `\n--- STDERR ---\n${result.stderr}`;
                }
                return output.trim(); 
            } else {
                console.error(`[CodeInterpreterLangChainTool] Execution failed. Exit Code: ${result.exitCode}. Stderr: ${result.stderr}. Stdout: ${result.stdout}`);
                return JSON.stringify({
                    error: `Python execution failed with exit code ${result.exitCode}.`,
                    stdout: result.stdout,
                    stderr: result.stderr
                });
            }
        } catch (error) {
            console.error(`[CodeInterpreterLangChainTool] Docker execution error: ${error.message}`);
            if (error instanceof AppError) {
                 return JSON.stringify({
                    error: `Docker execution failed: ${error.message}`,
                    details: error.details || error.stack,
                    errorCode: error.errorCode
                });
            }
            return JSON.stringify({ error: `Docker execution failed: ${error.message}`, details: error.stack });
        }
    }

    getToolSchema() {
        return {
            name: this.name,
            description: this.description,
            input_schema: {
                type: "object",
                properties: {
                    codeString: {
                        type: "string",
                        description: "The Python code to execute."
                    }
                },
                required: ["codeString"]
            }
        };
    }
}

module.exports = { CodeInterpreterLangChainTool };


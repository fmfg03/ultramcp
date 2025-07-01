const BaseMCPAdapter = require("./baseMCPAdapter");
const { exec } = require("child_process"); // For simple execution, sandbox needed for safety
const util = require("util");

const execPromise = util.promisify(exec);

class PythonAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    // Configuration might include Python path, linter paths, sandbox settings
    console.log("PythonAdapter: Initialized. Execution environment security is crucial.");
  }

  getId() {
    return "python";
  }

  async getTools() {
    return [
      {
        id: `${this.getId()}/execute_code`,
        name: "Execute Python Code",
        description: "Executes a Python code snippet. Ensure code is safe.",
        parameters: { 
          type: "object",
          properties: {
            code: { type: "string", description: "The Python code snippet to execute." },
            // Potentially add parameters for input, environment variables, etc.
          },
          required: ["code"]
        },
      },
      {
        id: `${this.getId()}/analyze_code`,
        name: "Analyze Python Code",
        description: "Performs static analysis on Python code (e.g., using Pylint/Flake8).",
        parameters: { 
          type: "object",
          properties: {
            code: { type: "string", description: "The Python code snippet to analyze." }
          },
          required: ["code"]
        },
      }
      // Add more tools later: e.g., run_tests, format_code, etc.
    ];
  }

  // Updated signature: removed 'action' parameter
  async executeAction(toolId, params) { 
    console.log(`PythonAdapter executing: ${toolId} with params:`, params);
    
    // Check params directly
    if (!params) {
        throw new Error("Missing parameters for Python action.");
    }

    if (toolId === `${this.getId()}/execute_code`) {
      const { code } = params;
      if (!code) {
        throw new Error("Missing required parameter: code");
      }
      // SECURITY WARNING: Executing arbitrary Python code is highly dangerous.
      // A proper sandbox (e.g., Docker container, restricted environment) is essential in production.
      try {
        // Simple execution example (UNSAFE FOR PRODUCTION)
        // Write code to a temporary file? Or pass via stdin?
        // For simplicity, using exec with python -c (limited complexity)
        // Escape double quotes within the code string for the shell command
        const escapedCode = code.replace(/"/g, '\\"'); 
        const command = `python3 -c "${escapedCode}"`;
        console.log(`Executing command: ${command}`);
        const { stdout, stderr } = await execPromise(command);
        return { success: true, stdout, stderr };
      } catch (error) {
        console.error(`Python execution failed:`, error);
        return { success: false, error: error.message, stdout: error.stdout, stderr: error.stderr };
      }
    }
    if (toolId === `${this.getId()}/analyze_code`) {
      const { code } = params;
      if (!code) {
        throw new Error("Missing required parameter: code");
      }
      // Placeholder: Implement actual static analysis (e.g., run Pylint/Flake8)
      // This would likely involve writing the code to a temp file and running the linter
      console.warn("Python code analysis is currently a placeholder.");
      return { success: true, message: "Placeholder: Python code analysis executed.", analysis_report: {}, params };
    }
    throw new Error(`Tool ${toolId} not supported by PythonAdapter.`);
  }
}

module.exports = PythonAdapter;


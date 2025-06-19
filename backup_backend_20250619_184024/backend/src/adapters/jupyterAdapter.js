const BaseMCPAdapter = require("./baseMCPAdapter");
const axios = require("axios");
const WebSocket = require("ws"); // Kept for now if other tools might use it, or for future kernel interaction
const { v4: uuidv4 } = require("uuid");
const { executeInContainer, checkDockerAvailability } = require("../utils/dockerService.js");
const AppError = require("../utils/AppError.js");

const DEFAULT_JUPYTER_PYTHON_DOCKER_IMAGE = "python:3.11-alpine";

class JupyterAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    this.gatewayUrl = process.env.JUPYTER_GATEWAY_URL || config.gatewayUrl;
    this.token = process.env.JUPYTER_TOKEN || config.token;
    this.kernels = {}; // Store kernel info from gateway
    this.dockerImage = config.dockerImage || DEFAULT_JUPYTER_PYTHON_DOCKER_IMAGE;

    if (!this.gatewayUrl) {
      console.warn("JupyterAdapter: JUPYTER_GATEWAY_URL is not set. Kernel management tools will not function.");
    }
    console.log(`JupyterAdapter: Initialized. Python code execution tool will use Docker image: ${this.dockerImage}. Kernel management tools depend on external Gateway.`);
    
    checkDockerAvailability().then(available => {
      if (!available) {
        console.warn("JupyterAdapter Warning: Docker does not seem to be available. Sandboxed Python code execution will fail.");
      }
    });
  }

  getId() {
    return "jupyter";
  }

  _getHeaders() {
    const headers = { "Content-Type": "application/json" };
    if (this.token) {
      headers.Authorization = `token ${this.token}`;
    }
    return headers;
  }

  async getTools() {
    return [
      {
        id: `${this.getId()}/list_kernels`,
        name: "List Running Kernels (Jupyter Gateway)",
        description: "Lists all currently running Jupyter kernels managed by the external Jupyter Gateway. Security of these kernels depends on Gateway configuration.",
        parameters: { type: "object", properties: {} },
      },
      {
        id: `${this.getId()}/start_kernel`,
        name: "Start Jupyter Kernel (Jupyter Gateway)",
        description: "Requests the external Jupyter Gateway to start a new kernel. Security depends on Gateway configuration.",
        parameters: {
          type: "object",
          properties: {
            name: { type: "string", description: "Optional kernel spec name (e.g., \"python3\")." }
          }
        },
      },
      {
        id: `${this.getId()}/get_kernel_info`,
        name: "Get Kernel Info (Jupyter Gateway)",
        description: "Retrieves information about a specific running Jupyter kernel from the external Gateway.",
        parameters: {
          type: "object",
          properties: {
            kernel_id: { type: "string", description: "ID of the target Jupyter kernel on the Gateway." }
          },
          required: ["kernel_id"]
        },
      },
      {
        id: `${this.getId()}/stop_kernel`,
        name: "Stop Jupyter Kernel (Jupyter Gateway)",
        description: "Requests the external Jupyter Gateway to stop a running kernel.",
        parameters: {
          type: "object",
          properties: {
            kernel_id: { type: "string", description: "ID of the Jupyter kernel on the Gateway to stop." }
          },
          required: ["kernel_id"]
        },
      },
      {
        id: `${this.getId()}/execute_python_code_sandboxed`,
        name: "Execute Python Code (Sandboxed)",
        description: `Executes a Python code snippet in a sandboxed Docker container (${this.dockerImage}). This is stateless and does not use a persistent Jupyter kernel.`,
        parameters: {
          type: "object",
          properties: {
            code: { type: "string", description: "The Python code snippet to execute." }
          },
          required: ["code"]
        },
      },
    ];
  }

  // --- REST API Methods for Kernel Management (interacting with external Gateway) ---
  async _listKernels() {
    if (!this.gatewayUrl) throw new AppError("Jupyter Gateway URL not configured.", 500, "JUPYTER_NO_GATEWAY_URL");
    const url = `${this.gatewayUrl}/api/kernels`;
    const response = await axios.get(url, { headers: this._getHeaders() });
    return response.data;
  }

  async _startKernel(name) {
    if (!this.gatewayUrl) throw new AppError("Jupyter Gateway URL not configured.", 500, "JUPYTER_NO_GATEWAY_URL");
    const url = `${this.gatewayUrl}/api/kernels`;
    const payload = name ? { name } : {};
    const response = await axios.post(url, payload, { headers: this._getHeaders() });
    this.kernels[response.data.id] = { info: response.data }; // Store kernel info
    return response.data;
  }

  async _getKernelInfo(kernelId) {
    if (!this.gatewayUrl) throw new AppError("Jupyter Gateway URL not configured.", 500, "JUPYTER_NO_GATEWAY_URL");
    const url = `${this.gatewayUrl}/api/kernels/${kernelId}`;
    const response = await axios.get(url, { headers: this._getHeaders() });
    return response.data;
  }

  async _stopKernel(kernelId) {
    if (!this.gatewayUrl) throw new AppError("Jupyter Gateway URL not configured.", 500, "JUPYTER_NO_GATEWAY_URL");
    const url = `${this.gatewayUrl}/api/kernels/${kernelId}`;
    await axios.delete(url, { headers: this._getHeaders() });
    delete this.kernels[kernelId];
    return { success: true, message: `Kernel ${kernelId} stopped on Gateway.` };
  }

  // --- Sandboxed Python Execution Method ---
  async _executePythonCodeSandboxed(code) {
    const command = ["python", "-c", code];
    const dockerOptions = {
        timeout: this.config.timeout || 60000, 
        resourceLimits: this.config.resourceLimits || { Memory: 256 * 1024 * 1024, CpuShares: 512 }, 
    };

    try {
        console.log(`[JupyterAdapter] Executing code in Docker (${this.dockerImage}): python -c "${code.substring(0,100)}..."`);
        const result = await executeInContainer(this.dockerImage, command, dockerOptions);

        if (result.exitCode === 0) {
            let output = result.stdout;
            if (result.stderr) {
                output += `\n--- STDERR ---\n${result.stderr}`;
            }
            return { success: true, output: output.trim(), stdout: result.stdout, stderr: result.stderr, exitCode: result.exitCode };
        } else {
            console.warn(`[JupyterAdapter] Sandboxed Python execution failed. Exit Code: ${result.exitCode}. Stderr: ${result.stderr}. Stdout: ${result.stdout}`);
            throw new AppError(
                `Python execution failed with exit code ${result.exitCode}. Stderr: ${result.stderr || '(empty)'}. Stdout: ${result.stdout || '(empty)'}`,
                500, 
                "JUPYTER_PYTHON_EXEC_FAILED", 
                true, 
                result
            );
        }
    } catch (error) {
        console.error(`[JupyterAdapter] Docker execution error for Python code: ${error.message}`);
        if (error instanceof AppError) throw error;
        throw new AppError(`Docker execution failed for Python code: ${error.message}`, 500, "JUPYTER_DOCKER_PYTHON_FAILED", true, error);
    }
  }

  async executeAction(toolId, params) {
    console.log(`JupyterAdapter executing: ${toolId} with params:`, params);
    
    params = params || {}; // Ensure params is an object

    const toolName = toolId.split("/")[1];

    try {
      switch (toolName) {
        case "list_kernels":
          const kernels = await this._listKernels();
          return { success: true, kernels };
        case "start_kernel":
          const newKernel = await this._startKernel(params.name);
          return { success: true, kernel: newKernel };
        case "get_kernel_info":
          if (!params.kernel_id) throw new AppError("Missing required parameter: kernel_id", 400, "JUPYTER_MISSING_KERNEL_ID");
          const kernelInfo = await this._getKernelInfo(params.kernel_id);
          return { success: true, kernel: kernelInfo };
        case "stop_kernel":
          if (!params.kernel_id) throw new AppError("Missing required parameter: kernel_id", 400, "JUPYTER_MISSING_KERNEL_ID");
          return await this._stopKernel(params.kernel_id);
        case "execute_python_code_sandboxed":
          if (!params.code) throw new AppError("Missing required parameter: code", 400, "JUPYTER_MISSING_CODE");
          return await this._executePythonCodeSandboxed(params.code);
        default:
          throw new AppError(`Tool ${toolId} not supported by JupyterAdapter.`, 404, "TOOL_NOT_FOUND");
      }
    } catch (error) {
      console.error(`JupyterAdapter Error executing ${toolId}:`, error.message);
      if (error instanceof AppError) throw error;
      const errorMessage = error.response?.data?.message || error.message;
      throw new AppError(`Failed to execute Jupyter action ${toolId}: ${errorMessage}`, 500, "JUPYTER_ACTION_FAILED", true, error);
    }
  }
}

module.exports = JupyterAdapter;


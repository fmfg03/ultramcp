const Docker = require("dockerode");
const stream = require("stream");
const AppError = require("./AppError"); // Assuming AppError is in the same utils directory or adjust path

// Initialize Docker connection (adjust based on your Docker setup, e.g., socket path)
let docker;
try {
  docker = new Docker(); // Defaults to /var/run/docker.sock or DOCKER_HOST
} catch (error) {
  console.error("Failed to initialize Docker connection:", error);
  // Docker might not be available or configured correctly. 
  // The service will fail gracefully if docker object is not created.
}

/**
 * Executes a command inside a Docker container.
 *
 * @param {string} imageName The name of the Docker image to use.
 * @param {Array<string>} command The command and its arguments to execute (e.g., ["ls", "-la"]).
 * @param {object} [options={}] Docker run options (e.g., binds, workingDir, resourceLimits).
 * @param {string} [options.workingDir="/"] Working directory inside the container.
 * @param {Array<string>} [options.binds=[]] Volume binds (e.g., ["/host/path:/container/path:ro"]).
 * @param {number} [options.timeout=60000] Execution timeout in milliseconds.
 * @param {object} [options.resourceLimits={}] Resource limits (e.g., { Memory: 100 * 1024 * 1024, CpuShares: 512 }).
 * @param {object} [options.env={}] Environment variables for the container.
 * @returns {Promise<{stdout: string, stderr: string, exitCode: number}>} The execution result.
 */
async function executeInContainer(imageName, command, options = {}) {
  if (!docker) {
    throw new AppError("Docker service is not available or not initialized.", 503, "DOCKER_UNAVAILABLE");
  }

  const { 
    workingDir = "/", 
    binds = [], 
    timeout = 60000, // 60 seconds default timeout
    resourceLimits = {}, // e.g., { Memory: 100 * 1024 * 1024 (100MB) }
    env = {}
  } = options;

  let container;
  let stdout = "";
  let stderr = "";
  let exitCode = -1;

  const envArray = Object.entries(env).map(([key, value]) => `${key}=${value}`);

  try {
    // Ensure the image exists locally, pull if not (optional, can be pre-pulled)
    // await docker.pull(imageName);

    container = await docker.createContainer({
      Image: imageName,
      Cmd: command,
      WorkingDir: workingDir,
      AttachStdout: true,
      AttachStderr: true,
      Tty: false, // Important for non-interactive commands
      OpenStdin: false,
      HostConfig: {
        Binds: binds,
        AutoRemove: true, // Remove container after execution
        ...resourceLimits // Apply resource limits like Memory, CpuShares
      },
      Env: envArray,
    });

    const containerStream = await container.attach({ stream: true, stdout: true, stderr: true });

    // Create promise to handle stream completion and timeout
    const streamPromise = new Promise((resolve, reject) => {
      containerStream.on("data", (chunk) => {
        // Docker multiplexes stdout and stderr. The first byte indicates the stream type.
        // 0x01 for stdout, 0x02 for stderr.
        if (chunk[0] === 1) {
          stdout += chunk.slice(8).toString("utf-8"); // Skip 8-byte header
        } else if (chunk[0] === 2) {
          stderr += chunk.slice(8).toString("utf-8"); // Skip 8-byte header
        }
      });
      containerStream.on("end", resolve);
      containerStream.on("error", reject);
    });

    await container.start();

    // Wait for command to finish or timeout
    const waitResultPromise = container.wait({ timeout }); // Dockerode wait timeout is in seconds, convert ms
    
    // Race the stream completion and container wait/timeout
    await Promise.race([
        streamPromise,
        new Promise((_, reject) => setTimeout(() => reject(new Error("Container execution timed out")), timeout))
    ]);
    
    const waitResult = await waitResultPromise;
    exitCode = waitResult.StatusCode;

  } catch (err) {
    console.error(`Error executing command in Docker container ${imageName}:`, err);
    stderr += `Docker execution error: ${err.message}`;
    if (err.message && err.message.includes("timed out")) {
        exitCode = -1; // Indicate timeout specifically if possible
        stderr += " (Timeout)";
    }
    // Ensure container is removed if it exists and an error occurred before AutoRemove
    if (container) {
      try {
        await container.remove({ force: true });
      } catch (removeError) {
        console.error("Failed to remove container after error:", removeError);
      }
    }
    // Re-throw a structured error or return error details
    throw new AppError(`Failed to execute command in Docker: ${err.message}`, 500, "DOCKER_EXEC_FAILED", true, { stdout, stderr, exitCode, originalError: err });
  } finally {
    // AutoRemove should handle this, but as a fallback:
    if (container) {
      try {
        const inspectData = await container.inspect();
        if (inspectData.State.Running) {
            await container.stop().catch(e => console.error("Error stopping container in finally:", e));
        }
        // If AutoRemove is false or failed, this would be needed.
        // await container.remove().catch(e => console.error("Error removing container in finally:", e));
      } catch (inspectError) {
        // Container might have already been removed
      }
    }
  }

  return { stdout, stderr, exitCode };
}

/**
 * Checks if Docker is available and responsive.
 * @returns {Promise<boolean>}
 */
async function checkDockerAvailability() {
  if (!docker) return false;
  try {
    await docker.ping();
    return true;
  } catch (error) {
    console.error("Docker ping failed:", error.message);
    return false;
  }
}

module.exports = {
  executeInContainer,
  checkDockerAvailability,
};

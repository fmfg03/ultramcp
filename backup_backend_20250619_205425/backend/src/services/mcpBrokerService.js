const { getSupabaseClient } = require("../../../src/adapters/supabaseAdapter.js");
const AppError = require("../utils/AppError.js");
const { retryOperation } = require("../utils/retryUtils.js");

const adapters = {};

const persistAdapterRegistration = async (adapter) => {
  const operation = async () => {
    const adapterId = adapter.getId();
    const adapterName = adapter.name || adapterId;
    const adapterClass = adapter.constructor.name;
    const config = typeof adapter.getConfig === "function" ? adapter.getConfig() : (adapter.config || {});

    const supabase = getSupabaseClient(); // This might throw if Supabase is not configured
    const { data, error } = await supabase
      .from("adapter_registrations")
      .upsert({
        adapter_id: adapterId,
        adapter_name: adapterName,
        adapter_class: adapterClass,
        config: config,
        enabled: true,
        updated_at: new Date().toISOString()
      }, { onConflict: "adapter_id" })
      .select();

    if (error) {
      console.error(`[MCPBrokerService] Supabase error persisting adapter ${adapterId}:`, error);
      throw new AppError(`Failed to persist adapter registration for ${adapterId} to Supabase.`, 500, "DB_UPSERT_FAILED", true, error.message);
    }
    console.log(`[MCPBrokerService] Adapter registration persisted/updated for ${adapterId}:`, data ? data[0] : "No data returned");
    return data;
  };

  try {
    // Retry Supabase operation, as it might be a transient network issue
    return await retryOperation(operation, 3, 200); // 3 retries, 200ms initial delay
  } catch (e) {
    // If retryOperation re-throws the AppError or another error
    console.error("[MCPBrokerService] Exception in persistAdapterRegistration after retries:", e.message);
    // Decide if this should be a critical error. For now, log and don't re-throw to allow server to run if DB is temporarily down.
    // However, the caller (registerAdapter) might decide to throw based on its needs.
    // For now, let's re-throw so the caller is aware persistence failed critically.
    if (e instanceof AppError) throw e;
    throw new AppError(`Critical failure persisting adapter ${adapter.getId()} after retries.`, 500, "PERSIST_ADAPTER_CRITICAL", false, e.message);
  }
};

const registerAdapter = async (adapter, persist = true) => {
  if (!adapter || typeof adapter.getId !== "function") {
    throw new AppError("Attempted to register an invalid or ID-less adapter object.", 400, "INVALID_ADAPTER_OBJECT");
  }
  const adapterId = adapter.getId();
  if (!adapterId) {
    throw new AppError("Attempted to register an adapter with no ID.", 400, "ADAPTER_ID_MISSING");
  }
  
  console.log(`[MCPBrokerService] Registering adapter: ${adapterId}`);
  adapters[adapterId] = adapter;

  if (persist) {
    try {
      await persistAdapterRegistration(adapter);
    } catch (error) {
      // Log the error, but the decision to halt or continue depends on how critical persistence is for this registration call.
      // For now, we log and let the adapter be registered in-memory.
      console.error(`[MCPBrokerService] Failed to persist adapter ${adapterId} during registration: ${error.message}. Adapter registered in-memory only.`);
      // Optionally, re-throw if persistence is mandatory for successful registration
      // throw new AppError(`Adapter ${adapterId} registered in-memory, but persistence failed.`, 500, "ADAPTER_PERSIST_FAILED_ON_REGISTER", true, error.details);
    }
  }
  return true;
};

const getAdapter = (adapterId) => {
  if (!adapters[adapterId]) {
    // This is not necessarily an error to be thrown, depends on context. Caller should check for null.
    // console.warn(`[MCPBrokerService] Adapter ${adapterId} not found.`);
    return null;
  }
  return adapters[adapterId];
};

const getAvailableTools = async () => {
  const allTools = [];
  for (const adapterId in adapters) {
    try {
      if (typeof adapters[adapterId].getTools === "function") {
        const adapterTools = await adapters[adapterId].getTools();
        if (Array.isArray(adapterTools)) {
          adapterTools.forEach(tool => {
            if (tool && typeof tool === "object") {
              tool.adapterId = adapterId;
            }
          });
          allTools.push(...adapterTools);
        } else {
          console.warn(`[MCPBrokerService] Adapter ${adapterId} getTools() did not return an array.`);
        }
      } else {
        console.warn(`[MCPBrokerService] Adapter ${adapterId} does not have a getTools method.`);
      }
    } catch (error) {
      // Log error for individual adapter but continue gathering tools from others
      console.error(`[MCPBrokerService] Error getting tools from adapter ${adapterId}:`, error.message);
      // Optionally, could add a placeholder error tool or skip
    }
  }
  return allTools; // Caller (mcpController) will handle if this is empty or needs error reporting
};

const executeToolAction = async (toolId, params) => {
  if (!toolId || typeof toolId !== "string") {
    throw new AppError("Invalid toolId provided to executeToolAction.", 400, "INVALID_TOOL_ID");
  }
  const parts = toolId.split("/");
  const adapterId = parts[0];

  const adapter = adapters[adapterId];

  if (!adapter) {
    throw new AppError(`Adapter ${adapterId} not found for tool ${toolId}.`, 404, "ADAPTER_NOT_FOUND");
  }
  if (typeof adapter.executeAction !== "function") {
    throw new AppError(`Adapter ${adapterId} does not have an executeAction method.`, 501, "ADAPTER_METHOD_NOT_IMPLEMENTED");
  }

  console.log(`[MCPBrokerService] executeToolAction: Executing tool ${toolId} via adapter ${adapterId} with params:`, params);
  try {
    // Retry logic could be more sophisticated here, e.g., based on error type from adapter.executeAction
    // For now, a simple retry for the whole operation if it fails.
    const operation = () => adapter.executeAction(toolId, params);
    // Let's assume most tool executions are not idempotent or retrying them here is too generic.
    // Retries should ideally be handled by the adapter itself if it knows the action is safe to retry,
    // or by a higher-level orchestrator node that understands the context.
    // For now, no automatic retry in executeToolAction itself unless specified by design for all tools.
    const result = await operation(); 
    return result;
  } catch (error) {
    console.error(`[MCPBrokerService] Error executing tool ${toolId} via adapter ${adapterId}:`, error.message);
    if (error instanceof AppError) throw error; // Re-throw if already an AppError (e.g., from adapter)
    throw new AppError(`Execution failed for tool ${toolId} via adapter ${adapterId}.`, 500, "TOOL_EXECUTION_FAILED", true, error.message);
  }
};

const executeTool = async (toolId, params) => {
  return executeToolAction(toolId, params);
};

module.exports = {
  registerAdapter,
  getAdapter,
  getAvailableTools,
  executeToolAction,
  executeTool,
};


const mcpBrokerService = require("../services/mcpBrokerService");
const AppError = require("../utils/AppError");

const getAvailableTools = async (req, res, next) => {
  try {
    const tools = await mcpBrokerService.getAvailableTools();
    res.json(tools);
  } catch (error) {
    // Pass to global error handler
    next(new AppError("Failed to retrieve available tools", 500, "GET_TOOLS_FAILED", true, error.message));
  }
};

const executeToolAction = async (req, res, next) => {
  const { toolId, params } = req.body;
  if (!toolId) {
    return next(new AppError("Missing toolId in request body", 400, "MISSING_TOOL_ID"));
  }

  try {
    const result = await mcpBrokerService.executeTool(toolId, params);
    res.json(result);
  } catch (error) {
    // If error is already an AppError from the service, pass it along
    if (error instanceof AppError) {
        return next(error);
    }
    // Otherwise, wrap it
    next(new AppError(`Failed to execute action for tool ${toolId}`, 500, "EXECUTE_TOOL_FAILED", true, error.message));
  }
};

module.exports = {
  getAvailableTools,
  executeToolAction,
};


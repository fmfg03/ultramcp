const express = require("express");
const mcpController = require("../controllers/mcpController.js");
const validateRequest = require("../middleware/validationMiddleware.js");
const { executeToolSchema, registerAdapterSchema, getAdapterSchema } = require("../validation/mcpSchemas.js");
const { protect } = require("../middleware/authMiddleware.js"); // Protect MCP routes

const router = express.Router();

// Route to get available MCP tools/adapters
// This might be public or protected depending on requirements. Assuming protected for now.
router.get("/tools", protect, mcpController.getAvailableTools);

// Route to execute a single tool action (this was the old /execute route)
// This is a more specific version of the executeTool defined in mcpController
// router.post("/execute", protect, mcpController.executeToolAction); // This seems to be a generic one, let's use the specific one below

// POST /api/mcp/tools/:adapterId/execute/:toolId - Execute a specific tool
router.post("/tools/:adapterId/execute/:toolId", protect, validateRequest(executeToolSchema), mcpController.executeToolById);

// POST /api/mcp/adapters/register - Register a new adapter
// This should likely be an admin-only route in the future with RBAC
router.post("/adapters/register", protect, validateRequest(registerAdapterSchema), mcpController.registerAdapterHandler);

// GET /api/mcp/adapters - Get all registered adapters
router.get("/adapters", protect, mcpController.getRegisteredAdapters);

// GET /api/mcp/adapters/:adapterId - Get a specific adapter
router.get("/adapters/:adapterId", protect, validateRequest(getAdapterSchema), mcpController.getAdapterById);

module.exports = router;

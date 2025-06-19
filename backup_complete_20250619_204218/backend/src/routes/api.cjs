const express = require("express");
const router = express.Router();

// Import the new route handlers
const orchestrateRoutes = require("./orchestrateRoutes.js");
const logRoutes = require("./logRoutes.js");
const mcpRoutes = require("./mcpRoutes.js"); // Assuming mcpController.js is now mcpRoutes.js for general MCP actions

// Mount the new route handlers
router.use("/orchestrate", orchestrateRoutes);
router.use("/logs", logRoutes);
router.use("/mcp", mcpRoutes); // For getAvailableTools, executeToolAction

module.exports = router;


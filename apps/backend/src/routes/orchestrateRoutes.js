const express = require("express");
const router = express.Router();
const orchestrateController = require("../controllers/orchestrateController.js");
const validateRequest = require("../middleware/validationMiddleware.js");
const { handleCommandSchema } = require("../validation/orchestrationSchemas.js");
const { protect } = require("../middleware/authMiddleware.js"); // Orchestration should be protected

// POST /api/orchestrate/
// Assuming file uploads (if any) are handled by a preceding middleware like multer,
// and `req.body` would contain other fields that need validation.
router.post("/", protect, validateRequest(handleCommandSchema), orchestrateController.handleCommand);

module.exports = router;

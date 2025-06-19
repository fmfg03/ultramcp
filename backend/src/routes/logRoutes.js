const express = require("express");
const router = express.Router();
const logController = require("../controllers/logController.js");
const validateRequest = require("../middleware/validationMiddleware.js");
const { saveLogSchema, getLogsSchema } = require("../validation/logSchemas.js");
const { protect } = require("../middleware/authMiddleware.js"); // Assuming logs might be protected

// POST /api/logs/ - Save a new log entry
// Consider if this endpoint should be protected. For now, adding protect middleware.
router.post("/", protect, validateRequest(saveLogSchema), logController.saveLog);

// GET /api/logs/ - Retrieve log entries
// Consider if this endpoint should be protected. For now, adding protect middleware.
router.get("/", protect, validateRequest(getLogsSchema), logController.getLogs);

module.exports = router;

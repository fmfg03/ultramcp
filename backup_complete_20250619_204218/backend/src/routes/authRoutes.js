const express = require("express");
const router = express.Router();
const authController = require("../controllers/authController.js");
const validateRequest = require("../middleware/validationMiddleware.js");
const { registerSchema, loginSchema, refreshTokenSchema } = require("../validation/authSchemas.js");
const { protect } = require("../middleware/authMiddleware.js"); // For logout and potentially refresh if needed

// POST /api/auth/register
router.post("/register", validateRequest(registerSchema), authController.register);

// POST /api/auth/login
router.post("/login", validateRequest(loginSchema), authController.login);

// POST /api/auth/logout
// Logout should be protected to ensure a valid session is being terminated
router.post("/logout", protect, authController.logout);

// POST /api/auth/refresh
router.post("/refresh", validateRequest(refreshTokenSchema), authController.refreshToken);

module.exports = router;

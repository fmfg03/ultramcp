const { z } = require("zod");

const saveLogBodySchema = z.object({
  command: z.string().min(1, "Command cannot be empty"),
  timestamp: z.string().datetime({ message: "Invalid timestamp format" }), // ISO 8601
  response: z.object({}).passthrough().optional(), // Allow any object structure for response
  user_id: z.string().uuid({ message: "Invalid user ID format" }).optional(),
  llm_used: z.string().optional(),
  agent_used: z.string().optional(),
  session_id: z.string().optional(),
  status: z.enum(["success", "error", "pending", "in_progress"]).optional().default("success"),
  error_message: z.string().optional(),
  duration_ms: z.number().int().positive().optional(),
  metadata: z.record(z.any()).optional(), // For any other custom fields
});

const saveLogSchema = z.object({
  body: saveLogBodySchema,
  query: z.object({}).optional(),
  params: z.object({}).optional(),
});

const getLogsQuerySchema = z.object({
  limit: z.string().regex(/^\d+$/).transform(Number).optional(), // Convert string to number
  offset: z.string().regex(/^\d+$/).transform(Number).optional(),
  user_id: z.string().uuid({ message: "Invalid user ID format" }).optional(),
  session_id: z.string().optional(),
  status: z.enum(["success", "error", "pending", "in_progress"]).optional(),
  date_from: z.string().datetime({ message: "Invalid date_from format" }).optional(),
  date_to: z.string().datetime({ message: "Invalid date_to format" }).optional(),
});

const getLogsSchema = z.object({
  body: z.object({}).optional(),
  query: getLogsQuerySchema,
  params: z.object({}).optional(),
});

module.exports = {
  saveLogSchema,
  getLogsSchema,
};

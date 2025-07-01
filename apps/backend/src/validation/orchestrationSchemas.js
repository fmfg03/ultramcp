const { z } = require("zod");

const handleCommandBodySchema = z.object({
  command: z.string().min(1, "Command cannot be empty"),
  userId: z.string().uuid({ message: "Invalid user ID format" }).optional(), // Assuming userId is a UUID if provided
  sessionId: z.string().optional(),
  // metadata can be any object, passthrough allows unknown keys
  metadata: z.record(z.any()).optional(), 
  // Potentially add more specific fields if the command structure is known
  // For example, if 'command' is an object with specific properties:
  // command: z.object({
  //   type: z.string(),
  //   payload: z.any(),
  // }).openapi({example: {type: "greeting", payload: "hello"}}),
});

const handleCommandSchema = z.object({
  body: handleCommandBodySchema,
  query: z.object({}).optional(),
  params: z.object({}).optional(),
});

module.exports = {
  handleCommandSchema,
};

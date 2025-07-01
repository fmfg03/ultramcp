const { z } = require("zod");

// Schema for /api/mcp/tools/:adapterId/execute/:toolId
const executeToolParamsSchema = z.object({
  adapterId: z.string().min(1, "Adapter ID cannot be empty"),
  toolId: z.string().min(1, "Tool ID cannot be empty"),
});

const executeToolBodySchema = z.object({
  params: z.record(z.any()).optional(), // Allow any object structure for tool parameters
});

const executeToolSchema = z.object({
  body: executeToolBodySchema,
  params: executeToolParamsSchema,
  query: z.object({}).optional(),
});

// Schema for /api/mcp/adapters/register
const registerAdapterBodySchema = z.object({
  adapter_id: z.string().min(1, "Adapter ID cannot be empty"),
  name: z.string().min(1, "Adapter name cannot be empty"),
  description: z.string().optional(),
  // config_schema can be complex, allowing any object for now, or define a stricter schema if known
  config_schema: z.record(z.any()).optional(), 
  module_path: z.string().min(1, "Module path cannot be empty"),
  // persist: z.boolean().optional().default(false), // Already handled in service logic
});

const registerAdapterSchema = z.object({
  body: registerAdapterBodySchema,
  query: z.object({}).optional(),
  params: z.object({}).optional(),
});

// Schema for /api/mcp/adapters/:adapterId
const getAdapterParamsSchema = z.object({
  adapterId: z.string().min(1, "Adapter ID cannot be empty"),
});

const getAdapterSchema = z.object({
  body: z.object({}).optional(),
  query: z.object({}).optional(),
  params: getAdapterParamsSchema,
});

module.exports = {
  executeToolSchema,
  registerAdapterSchema,
  getAdapterSchema,
};

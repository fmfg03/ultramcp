const { z } = require("zod");

const registerBodySchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(6, { message: "Password must be at least 6 characters long" }),
  username: z.string().min(3).optional(),
});

const registerSchema = z.object({
  body: registerBodySchema,
  query: z.object({}).optional(),
  params: z.object({}).optional(),
});

const loginBodySchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

const loginSchema = z.object({
  body: loginBodySchema,
  query: z.object({}).optional(),
  params: z.object({}).optional(),
});

const refreshTokenBodySchema = z.object({
    refresh_token: z.string().min(1, {message: "Refresh token cannot be empty"}),
});

const refreshTokenSchema = z.object({
    body: refreshTokenBodySchema,
    query: z.object({}).optional(),
    params: z.object({}).optional(),
});

module.exports = {
  registerSchema,
  loginSchema,
  refreshTokenSchema,
};

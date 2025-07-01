const AppError = require("../utils/AppError");

const validateRequest = (schema) => async (req, res, next) => {
  try {
    const validatedData = await schema.parseAsync({
      body: req.body,
      query: req.query,
      params: req.params,
    });
    // Attach validated data to request object
    req.validatedBody = validatedData.body;
    req.validatedQuery = validatedData.query;
    req.validatedParams = validatedData.params;
    next();
  } catch (error) {
    if (error.errors) { // ZodError
      const errorMessages = error.errors.map(err => ({
        path: err.path.join("."),
        message: err.message,
      }));
      // Log the detailed validation errors for debugging
      console.error("Validation Error Details:", JSON.stringify(errorMessages, null, 2));
      return next(new AppError("Input validation failed. Please check your data.", 400, "VALIDATION_ERROR", true, { errors: errorMessages }));
    }
    // Forward other unexpected errors
    console.error("Unexpected error in validation middleware:", error);
    next(new AppError("An unexpected error occurred during input validation.", 500, "INTERNAL_VALIDATION_ERROR", false, error));
  }
};

module.exports = validateRequest;


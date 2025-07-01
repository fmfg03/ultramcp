const AppError = require("../utils/AppError.js"); // Adjust path as necessary

const handleOperationalError = (err, res) => {
  res.status(err.statusCode).json({
    status: err.status,
    message: err.message,
    errorCode: err.errorCode,
    details: err.details
  });
};

const globalErrorHandler = (err, req, res, next) => {
  err.statusCode = err.statusCode || 500;
  err.status = err.status || "error";

  console.error("[GlobalErrorHandler] An error occurred:", {
    message: err.message,
    statusCode: err.statusCode,
    errorCode: err.errorCode,
    isOperational: err.isOperational,
    details: err.details,
    // Avoid logging full stack in production for non-operational errors if too verbose
    stack: process.env.NODE_ENV === "development" || err.isOperational ? err.stack : "Stack hidden in production for non-operational errors.",
    requestPath: req.path,
    requestMethod: req.method
  });

  if (err.isOperational) {
    return handleOperationalError(err, res);
  } else {
    if (process.env.NODE_ENV === "development") {
      return res.status(500).json({
        status: "error",
        message: "Something went very wrong! (Dev Mode)",
        error: {
            message: err.message,
            stack: err.stack,
            errorCode: err.errorCode,
            details: err.details
        }
      });
    }
    // Production: generic message for non-operational errors
    return res.status(500).json({
      status: "error",
      message: "An internal server error occurred. Please try again later."
    });
  }
};

module.exports = globalErrorHandler;

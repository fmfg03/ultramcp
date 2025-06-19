class AppError extends Error {
  constructor(message, statusCode, errorCode, isOperational = true, details = null) {
    super(message);
    this.statusCode = statusCode; 
    this.errorCode = errorCode;   
    this.isOperational = isOperational; 
    this.details = details;       
    this.status = `${statusCode}`.startsWith("4") ? "fail" : "error"; 

    Error.captureStackTrace(this, this.constructor);
  }
}

module.exports = AppError;

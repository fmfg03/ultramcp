const { getSupabaseClient } = require("../adapters/supabaseAdapter"); // Adjusted path
const AppError = require("../utils/AppError");

const protect = async (req, res, next) => {
  let token;

  if (req.headers.authorization && req.headers.authorization.startsWith("Bearer")) {
    token = req.headers.authorization.split(" ")[1];
  }

  if (!token) {
    return next(new AppError("Not authorized to access this route. No token provided.", 401, "AUTH_NO_TOKEN"));
  }

  const supabase = getSupabaseClient();
  if (!supabase) {
    return next(new AppError("Supabase client not available. Check server configuration.", 503, "SUPABASE_UNAVAILABLE"));
  }

  try {
    const { data: { user }, error } = await supabase.auth.getUser(token);

    if (error) {
        // Map Supabase specific errors or provide a generic one
        let statusCode = 401;
        let errorCode = "AUTH_INVALID_TOKEN";
        if (error.message.toLowerCase().includes("invalid token") || error.message.toLowerCase().includes("jwt expired")) {
            // Keep generic for security, but log specific error
            console.error("Auth Middleware Error:", error.message);
        } else if (error.status) {
            statusCode = error.status;
        }
        return next(new AppError(error.message || "Not authorized. Token verification failed.", statusCode, errorCode, true, error));
    }

    if (!user) {
        return next(new AppError("Not authorized. User not found for this token.", 401, "AUTH_USER_NOT_FOUND"));
    }

    // Attach user to the request object
    req.user = user;
    req.token = token; // Make token available for logout if needed
    next();

  } catch (err) {
    // Catch any other unexpected errors during token verification
    console.error("Auth Middleware Unexpected Error:", err);
    return next(new AppError("Server error during authentication.", 500, "AUTH_SERVER_ERROR_MIDDLEWARE", false, err));
  }
};

// Optional: Middleware for role-based access control (can be expanded later)
const authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user || !req.user.app_metadata || !req.user.app_metadata.roles) {
        return next(new AppError("User roles not found. Cannot authorize.", 403, "AUTH_NO_ROLES"));
    }
    const userRoles = req.user.app_metadata.roles || []; // Assuming roles are in app_metadata.roles
    if (!roles.some(role => userRoles.includes(role))) {
      return next(new AppError(`User role(s) '${userRoles.join(', ')}' not authorized to access this route. Required: ${roles.join(' or ')}.`, 403, "AUTH_INSUFFICIENT_ROLE"));
    }
    next();
  };
};

module.exports = { protect, authorize };

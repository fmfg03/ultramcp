const { getSupabaseClient } = require("../adapters/supabaseAdapter"); // Adjusted path
const AppError = require("../utils/AppError");

// Basic email validation
const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const register = async (req, res, next) => {
  const { email, password, username } = req.body;

  if (!email || !password) {
    return next(new AppError("Email and password are required", 400, "AUTH_MISSING_CREDENTIALS"));
  }
  if (!isValidEmail(email)) {
    return next(new AppError("Invalid email format", 400, "AUTH_INVALID_EMAIL"));
  }
  if (password.length < 6) {
    return next(new AppError("Password must be at least 6 characters long", 400, "AUTH_PASSWORD_TOO_SHORT"));
  }

  const supabase = getSupabaseClient();
  if (!supabase) {
    return next(new AppError("Supabase client not available. Check server configuration.", 503, "SUPABASE_UNAVAILABLE"));
  }

  try {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: {
          username: username || email.split("@")[0], // Optional: store username in metadata
        }
      }
    });

    if (error) {
      // Supabase specific errors can be mapped to AppError
      let statusCode = 500;
      let errorCode = "AUTH_SIGNUP_FAILED";
      if (error.message.includes("User already registered") || error.status === 400 || error.status === 422) {
        statusCode = 409; // Conflict or Bad Request
        errorCode = "AUTH_USER_EXISTS";
      }
      return next(new AppError(error.message, statusCode, errorCode, true, error));
    }

    // data.user contains the user object
    // data.session contains session details including access_token and refresh_token if auto-confirm is on or user is already confirmed
    // If email confirmation is required, data.session might be null initially.
    let responseMessage = "Registration successful.";
    if (data.user && data.user.identities && data.user.identities.length > 0 && !data.session) {
        responseMessage = "Registration successful. Please check your email to confirm your account.";
    }
    
    // Do not send back the full session object or password in the response for security.
    // The client will typically get the session from Supabase client library after successful OAuth or if email confirmation is off.
    // For API-based signup, if a session is returned, it means the user is confirmed and logged in.
    res.status(201).json({
      status: "success",
      message: responseMessage,
      user: {
        id: data.user?.id,
        email: data.user?.email,
        // Include session tokens if available and appropriate for your flow
        // session: data.session // Be cautious about sending session directly, consider what client needs
      }
    });
  } catch (err) {
    return next(new AppError(`Server error during registration: ${err.message}`, 500, "AUTH_SERVER_ERROR", false, err));
  }
};

const login = async (req, res, next) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return next(new AppError("Email and password are required", 400, "AUTH_MISSING_CREDENTIALS"));
  }
  if (!isValidEmail(email)) {
    return next(new AppError("Invalid email format", 400, "AUTH_INVALID_EMAIL"));
  }

  const supabase = getSupabaseClient();
  if (!supabase) {
    return next(new AppError("Supabase client not available. Check server configuration.", 503, "SUPABASE_UNAVAILABLE"));
  }

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });

    if (error) {
      let statusCode = 401;
      let errorCode = "AUTH_INVALID_LOGIN";
      if (error.message.includes("Invalid login credentials")) {
        // Keep it generic for security
      } else if (error.status) {
        statusCode = error.status === 400 ? 400 : 401; // Supabase might return 400 for some auth errors
      }
      return next(new AppError(error.message, statusCode, errorCode, true, error));
    }

    // data.user contains the user object
    // data.session contains session details including access_token and refresh_token
    res.status(200).json({
      status: "success",
      message: "Login successful",
      token: data.session.access_token, // Send the access token
      refreshToken: data.session.refresh_token, // Send the refresh token (client must store securely)
      user: {
        id: data.user.id,
        email: data.user.email,
        // any other non-sensitive user details from data.user
      }
    });
  } catch (err) {
    return next(new AppError(`Server error during login: ${err.message}`, 500, "AUTH_SERVER_ERROR", false, err));
  }
};

const logout = async (req, res, next) => {
    const supabase = getSupabaseClient();
    if (!supabase) {
        return next(new AppError("Supabase client not available.", 503, "SUPABASE_UNAVAILABLE"));
    }
    try {
        // The token to invalidate is usually passed in the Authorization header
        // and handled by Supabase client on the server-side when calling signOut.
        // If you have the token from an auth middleware (req.token), you can pass it.
        const { error } = await supabase.auth.signOut(req.token); // req.token would be set by auth middleware

        if (error) {
            return next(new AppError(error.message, 500, "AUTH_SIGNOUT_FAILED", true, error));
        }
        res.status(200).json({ status: "success", message: "Logout successful" });
    } catch (err) {
        return next(new AppError(`Server error during logout: ${err.message}`, 500, "AUTH_SERVER_ERROR", false, err));
    }
};

const refreshToken = async (req, res, next) => {
    const { refresh_token } = req.body;
    if (!refresh_token) {
        return next(new AppError("Refresh token is required", 400, "AUTH_MISSING_REFRESH_TOKEN"));
    }

    const supabase = getSupabaseClient();
    if (!supabase) {
        return next(new AppError("Supabase client not available.", 503, "SUPABASE_UNAVAILABLE"));
    }

    try {
        const { data, error } = await supabase.auth.refreshSession({ refresh_token });

        if (error) {
            return next(new AppError(error.message, 401, "AUTH_REFRESH_FAILED", true, error));
        }

        res.status(200).json({
            status: "success",
            message: "Token refreshed successfully",
            token: data.session.access_token,
            refreshToken: data.session.refresh_token, // Supabase might issue a new refresh token
            user: {
                id: data.user.id,
                email: data.user.email,
            }
        });
    } catch (err) {
        return next(new AppError(`Server error during token refresh: ${err.message}`, 500, "AUTH_SERVER_ERROR", false, err));
    }
};


module.exports = {
  register,
  login,
  logout,
  refreshToken
};

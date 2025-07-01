const logService = require("../services/logService.cjs");
const AppError = require("../utils/AppError");

class LogController {
  async saveLog(req, res, next) { // Added next parameter
    try {
      const logData = req.body;
      if (!logData.command || !logData.timestamp) {
        return next(new AppError("Missing required fields (command, timestamp) for log entry.", 400, "MISSING_LOG_FIELDS"));
      }
      const result = await logService.cjs.saveLog(logData);
      res.status(201).json({ status: "success", message: "Log saved successfully", data: result });
    } catch (error) {
      // If error is already an AppError from the service, pass it along
      if (error instanceof AppError) {
        return next(error);
      }
      // Otherwise, wrap it
      next(new AppError("Internal server error while saving log.", 500, "SAVE_LOG_FAILED", false, error.message));
    }
  }

  async getLogs(req, res, next) { // Added next parameter
    try {
      const logs = await logService.cjs.getLogs();
      res.status(200).json({ status: "success", logs });
    } catch (error) {
      // If error is already an AppError from the service, pass it along
      if (error instanceof AppError) {
        return next(error);
      }
      // Otherwise, wrap it
      next(new AppError("Internal server error while retrieving logs.", 500, "GET_LOGS_FAILED", false, error.message));
    }
  }
}

module.exports = new LogController();


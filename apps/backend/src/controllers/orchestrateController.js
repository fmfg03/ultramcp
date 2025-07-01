const orchestrationService = require("../services/orchestrationService");
const inputPreprocessorService = require("../services/InputPreprocessorService");
const AppError = require("../utils/AppError");

class OrchestrateController {
  async handleCommand(req, res, next) { // Added next parameter
    try {
      const rawRequestBody = req.body;
      const uploadedFiles = req.files || [];

      if (!rawRequestBody.request && uploadedFiles.length === 0) {
        // Use AppError for client errors, pass to global handler
        return next(new AppError("Missing 'request' text or files in request body", 400, "MISSING_REQUEST_DATA"));
      }

      const filesToProcess = uploadedFiles.map(file => ({
        tempFilePath: file.path,
        originalFilename: file.originalname,
        size: file.size
      }));

      const preprocessedInput = await inputPreprocessorService.process(rawRequestBody.request, filesToProcess);

      const effectiveLLM = rawRequestBody.llm || preprocessedInput.llm_used || "claude-3-sonnet";
      const effectiveAgent = rawRequestBody.agent || "builder-judge";

      const orchestrationPayload = {
        request: preprocessedInput.cleaned_prompt,
        original_input: preprocessedInput.original_input,
        structured_data: preprocessedInput.structured_data,
        files: preprocessedInput.files,
        llm: effectiveLLM,
        agent: effectiveAgent,
      };

      const result = await orchestrationService.processCommand(orchestrationPayload);
      
      // If orchestrationService itself returns an error structure, handle it or ensure it throws AppError
      if (result && result.status === "error") {
        // Convert service-level error to AppError if not already
        return next(new AppError(result.message || "Orchestration failed", result.statusCode || 400, result.errorCode || "ORCHESTRATION_ERROR", true, result.details));
      }
      
      res.status(200).json(result);
    } catch (error) {
      // If error is already an AppError from a service, pass it along
      if (error instanceof AppError) {
        return next(error);
      }
      // Otherwise, wrap it as a generic internal server error
      next(new AppError("Internal server error while processing command.", 500, "ORCHESTRATE_CONTROLLER_ERROR", false, error.message));
    }
  }
}

module.exports = new OrchestrateController();


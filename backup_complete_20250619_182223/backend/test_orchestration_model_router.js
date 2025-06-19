// test_orchestration_model_router.js
const OrchestrationService = require("./src/services/orchestrationService");

async function runTest() {
    console.log("--- Starting ModelRouter Integration Test ---");

    // To get detailed logs from ModelRouterService, ensure DEBUG_MODEL_ROUTER_LOGGING=true is set in your .env file or environment.
    // This script will primarily check if OrchestrationService calls ModelRouterService and attempts to configure LLMs based on its output.

    console.log("Attempting to process a command for Builder/Judge workflow with OrchestrationService...");
    try {
        const result = await OrchestrationService.processCommand("User request: analyze this data and provide a summary.");
        console.log("--- OrchestrationService processCommand (Builder/Judge) Result ---");
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error("--- Error during Builder/Judge test execution ---");
        console.error(error);
    }

    console.log("\nAttempting to process a command for Ideation workflow with OrchestrationService...");
    try {
        const ideationResult = await OrchestrationService.processCommand("Ideate new names for a coffee shop.");
        console.log("--- OrchestrationService processCommand (Ideation) Result ---");
        console.log(JSON.stringify(ideationResult, null, 2));
    } catch (error) {
        console.error("--- Error during Ideation test execution ---");
        console.error(error);
    }

    console.log("--- ModelRouter Integration Test Finished ---");
}

runTest();


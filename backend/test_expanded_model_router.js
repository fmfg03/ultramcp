// Test script for the expanded ModelRouterService
const ModelRouterService = require("./src/services/modelRouterService");

// Enable debug logging in ModelRouterService for detailed output during tests
process.env.DEBUG_MODEL_ROUTER_LOGGING = "true";

const router = new ModelRouterService();

console.log("--- Starting ModelRouterService Test Suite ---");

const testScenarios = [
    // Scenario 1: Low cost, quick response, small payload
    {
        params: { taskType: "quick_response", payloadSize: 100, latencyTolerance: "fast", costBudget: "lowCost" },
        description: "Low cost, quick response, small payload (e.g., simple Q&A)"
    },
    // Scenario 2: Balanced cost/performance, code generation, medium payload
    {
        params: { taskType: "code_generation", payloadSize: 2000, latencyTolerance: "moderate", costBudget: "balanced" },
        description: "Balanced cost/performance, code generation, medium payload"
    },
    // Scenario 3: Performance first, complex reasoning, large payload
    {
        params: { taskType: "complex_reasoning", payloadSize: 150000, latencyTolerance: "high", costBudget: "performance_first" },
        description: "Performance first, complex reasoning, very large payload (should pick a model with large context)"
    },
    // Scenario 4: Low cost, summarization, medium payload, fast latency needed
    {
        params: { taskType: "summarization", payloadSize: 5000, latencyTolerance: "fast", costBudget: "lowCost" },
        description: "Low cost, summarization, medium payload, fast latency"
    },
    // Scenario 5: User override to a specific OpenAI model
    {
        params: { taskType: "general_purpose", payloadSize: 1000, latencyTolerance: "moderate", costBudget: "balanced", userOverride: { provider: "openai", model: "gpt-4-turbo" } },
        description: "User override to GPT-4 Turbo"
    },
    // Scenario 6: User override to a specific Claude model
    {
        params: { taskType: "research", payloadSize: 10000, latencyTolerance: "high", costBudget: "performance_first", userOverride: { provider: "anthropic", model: "claude-3-opus-20240229" } },
        description: "User override to Claude 3 Opus"
    },
    // Scenario 7: Task requiring tool use, balanced budget
    {
        params: { taskType: "tool_use_required", payloadSize: 500, latencyTolerance: "moderate", costBudget: "balanced" },
        description: "Task requiring tool use, balanced budget"
    },
    // Scenario 8: Vision task, performance first
    {
        params: { taskType: "vision_tasks", payloadSize: 1000, latencyTolerance: "moderate", costBudget: "performance_first" },
        description: "Vision task, performance first"
    },
    // Scenario 9: Long context task, performance first
    {
        params: { taskType: "long_context_tasks", payloadSize: 250000, latencyTolerance: "high", costBudget: "performance_first" },
        description: "Long context task (e.g., analyzing a large document)"
    },
    // Scenario 10: Embedding generation task
    {
        params: { taskType: "embedding_generation", payloadSize: 200, latencyTolerance: "fast", costBudget: "lowCost" },
        description: "Embedding generation task"
    },
    // Scenario 11: User override to a Gemini model
    {
        params: { taskType: "general_purpose", payloadSize: 1000, latencyTolerance: "moderate", costBudget: "balanced", userOverride: { provider: "google_genai", model: "gemini-1.5-pro-latest" } },
        description: "User override to Gemini 1.5 Pro"
    },
    // Scenario 12: User override to a DeepSeek model
    {
        params: { taskType: "coding", payloadSize: 1500, latencyTolerance: "moderate", costBudget: "lowCost", userOverride: { provider: "deepseek", model: "deepseek-chat" } },
        description: "User override to DeepSeek Chat"
    },
    // Scenario 13: User override to a Mistral model
    {
        params: { taskType: "complex_instruction_following", payloadSize: 3000, latencyTolerance: "moderate", costBudget: "balanced", userOverride: { provider: "mistralai", model: "mistral-large-latest" } },
        description: "User override to Mistral Large"
    },
    // Scenario 14: User override to a generic Hugging Face endpoint (needs URL)
    {
        params: { taskType: "custom_model_deployment", payloadSize: 1000, latencyTolerance: "variable", costBudget: "balanced", userOverride: { provider: "huggingface_endpoint", model: "http://localhost:8080/custom-model" } },
        description: "User override to a generic Hugging Face endpoint (simulated URL)"
    },
    // Scenario 15: User override to a specific Hugging Face Hub model
    {
        params: { taskType: "general_purpose", payloadSize: 1000, latencyTolerance: "variable", costBudget: "lowCost", userOverride: { provider: "huggingface_hub", model: "mistralai/Mistral-7B-Instruct-v0.2" } },
        description: "User override to a specific Hugging Face Hub model (Mistral-7B Instruct)"
    },
    // Scenario 16: Very low cost, quick response, very small payload
    {
        params: { taskType: "quick_response", payloadSize: 50, latencyTolerance: "fast", costBudget: "lowCost" },
        description: "Very low cost, quick response, very small payload (should favor cheapest fast models)"
    },
    // Scenario 17: Complex reasoning, but strict low cost budget
    {
        params: { taskType: "complex_reasoning", payloadSize: 10000, latencyTolerance: "high", costBudget: "lowCost" },
        description: "Complex reasoning, but strict low cost budget"
    },
    // Scenario 18: Payload size exceeding all known context windows (should fallback or error gracefully - current logic will filter all out and use default)
    {
        params: { taskType: "general_purpose", payloadSize: 2000000, latencyTolerance: "high", costBudget: "balanced" },
        description: "Payload size exceeding all known context windows"
    }
];

let testsPassed = 0;
let testsFailed = 0;

testScenarios.forEach((scenario, index) => {
    console.log(`\n--- Test Scenario ${index + 1}: ${scenario.description} ---`);
    console.log("Input Params:", JSON.stringify(scenario.params, null, 2));
    try {
        const selectedLlm = router.routeLLM(scenario.params);
        console.log("Selected LLM Config:", JSON.stringify(selectedLlm, null, 2));
        
        // Basic validation: check if a model was returned and has provider and model fields
        if (selectedLlm && selectedLlm.provider && selectedLlm.model) {
            console.log(`Scenario ${index + 1} PASSED: Model selected - ${selectedLlm.provider}/${selectedLlm.model}`);
            testsPassed++;
        } else {
            console.error(`Scenario ${index + 1} FAILED: No valid model configuration returned.`);
            testsFailed++;
        }
    } catch (error) {
        console.error(`Scenario ${index + 1} FAILED with error:`, error.message);
        testsFailed++;
    }
});

console.log("\n--- Test Suite Summary ---");
console.log(`Total Scenarios: ${testScenarios.length}`);
console.log(`Passed: ${testsPassed}`);
console.log(`Failed: ${testsFailed}`);

if (testsFailed > 0) {
    console.error("\nSOME TESTS FAILED!");
    // process.exit(1); // Optionally exit with error code if tests fail
} else {
    console.log("\nALL TESTS PASSED SUCCESSFULLY!");
}

console.log("\n--- Testing getModelConfig --- ");
const specificModel = router.getModelConfig("claude-3-opus-20240229");
console.log("Config for claude-3-opus-20240229:", specificModel ? specificModel.name : "Not found");

const nonExistentModel = router.getModelConfig("non-existent-model-123");
console.log("Config for non-existent-model-123:", nonExistentModel ? nonExistentModel.name : "Not found");

console.log("\n--- Testing getAllModelConfigs --- ");
const allModels = router.getAllModelConfigs();
console.log(`Retrieved ${Object.keys(allModels).length} model configurations.`);
if (Object.keys(allModels).length > 10) { // Check if a reasonable number of models are loaded
    console.log("getAllModelConfigs seems to be working.");
} else {
    console.error("getAllModelConfigs might not be returning all models.");
}

console.log("\n--- End of ModelRouterService Test Suite ---");


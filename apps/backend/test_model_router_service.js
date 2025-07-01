const ModelRouterService = require("./src/services/modelRouterService.js");

// Initialize the service
const modelRouter = new ModelRouterService();

// --- Test Cases ---
const testCases = [
    {
        description: "Low cost, quick response, small payload -> Haiku",
        params: { taskType: "quick_response", payloadSize: 500, latencyTolerance: "low", costBudget: "lowCost" },
        expectedModel: "claude-3-haiku-20240307"
    },
    {
        description: "Low cost, summarization, medium payload -> Haiku",
        params: { taskType: "summarization", payloadSize: 5000, latencyTolerance: "medium", costBudget: "lowCost" },
        expectedModel: "claude-3-haiku-20240307"
    },
    {
        description: "Low cost, general purpose -> GPT-3.5 Turbo",
        params: { taskType: "general_purpose", payloadSize: 2000, latencyTolerance: "medium", costBudget: "lowCost" },
        expectedModel: "gpt-3.5-turbo"
    },
    {
        description: "Balanced, code generation -> Claude 3.5 Sonnet",
        params: { taskType: "code_gen", payloadSize: 10000, latencyTolerance: "medium", costBudget: "balanced" },
        expectedModel: "claude-3.5-sonnet-20240620"
    },
    {
        description: "Balanced, complex reasoning, small payload -> Opus",
        params: { taskType: "complex_reasoning", payloadSize: 10000, latencyTolerance: "high", costBudget: "balanced" },
        expectedModel: "claude-3-opus-20240229"
    },
    {
        description: "Balanced, other -> GPT-4 Turbo",
        params: { taskType: "unknown_task", payloadSize: 30000, latencyTolerance: "medium", costBudget: "balanced" },
        expectedModel: "gpt-4-turbo"
    },
    {
        description: "Performance first, complex reasoning -> Opus",
        params: { taskType: "complex_reasoning", payloadSize: 150000, latencyTolerance: "high", costBudget: "performance_first" },
        expectedModel: "claude-3-opus-20240229"
    },
    {
        description: "Performance first, code generation -> GPT-4 Turbo",
        params: { taskType: "code_gen", payloadSize: 20000, latencyTolerance: "medium", costBudget: "performance_first" },
        expectedModel: "gpt-4-turbo"
    },
    {
        description: "Performance first, default -> Claude 3.5 Sonnet",
        params: { taskType: "general_chat", payloadSize: 1000, latencyTolerance: "medium", costBudget: "performance_first" },
        expectedModel: "claude-3.5-sonnet-20240620"
    },
    {
        description: "Real-time latency, moderate model initially chosen -> Haiku (if quick_response)",
        params: { taskType: "quick_response", payloadSize: 500, latencyTolerance: "real-time", costBudget: "balanced" }, // Balanced might pick Sonnet, but latency forces Haiku
        expectedModel: "claude-3-haiku-20240307"
    },
    {
        description: "Real-time latency, moderate model initially chosen -> GPT-3.5 Turbo (if not quick_response)",
        params: { taskType: "general_purpose", payloadSize: 500, latencyTolerance: "real-time", costBudget: "balanced" }, // Balanced might pick Sonnet, but latency forces GPT-3.5
        expectedModel: "gpt-3.5-turbo"
    },
    {
        description: "Search task -> Claude 3.5 Sonnet",
        params: { taskType: "search", payloadSize: 1000, latencyTolerance: "medium", costBudget: "balanced" },
        expectedModel: "claude-3.5-sonnet-20240620"
    },
    {
        description: "User override to GPT-3.5 Turbo",
        params: { taskType: "complex_reasoning", payloadSize: 100000, latencyTolerance: "high", costBudget: "performance_first", userOverride: { provider: "openai", model: "gpt-3.5-turbo" } },
        expectedModel: "gpt-3.5-turbo",
        expectedProvider: "openai"
    },
    {
        description: "User override to Claude Opus (full name)",
        params: { taskType: "quick_response", payloadSize: 100, latencyTolerance: "low", costBudget: "lowCost", userOverride: { provider: "anthropic", model: "Claude 3 Opus" } },
        expectedModel: "claude-3-opus-20240229",
        expectedProvider: "anthropic"
    },
    {
        description: "User override to non-existent model (should default, or handle gracefully - current logic defaults based on other params)",
        params: { taskType: "quick_response", payloadSize: 100, latencyTolerance: "low", costBudget: "lowCost", userOverride: { provider: "anthropic", model: "non-existent-model-123" } },
        expectedModel: "claude-3-haiku-20240307" // Falls back to heuristic as override fails
    }
];

let allTestsPassed = true;

console.log("--- Starting ModelRouterService Tests ---");

// Enable logging in the service for more detailed output during tests
process.env.DEBUG_MODEL_ROUTER_LOGGING = "true";
// Re-initialize to pick up env var (if constructor logic depends on it at init time)
const modelRouterWithLogging = new ModelRouterService(); 

testCases.forEach((tc, index) => {
    console.log(`\n--- Test Case ${index + 1}: ${tc.description} ---`);
    console.log("Input Params:", JSON.stringify(tc.params, null, 2));
    const result = modelRouterWithLogging.routeLLM(tc.params);
    console.log("Routing Result:", JSON.stringify(result, null, 2));

    let testPassed = result.model === tc.expectedModel;
    if (tc.expectedProvider && result.provider !== tc.expectedProvider) {
        testPassed = false;
    }

    if (testPassed) {
        console.log(`Status: PASSED - Expected ${tc.expectedModel}, Got ${result.model}`);
    } else {
        allTestsPassed = false;
        console.error(`Status: FAILED - Expected Model: ${tc.expectedModel}, Got: ${result.model}`);
        if (tc.expectedProvider) {
            console.error(`           Expected Provider: ${tc.expectedProvider}, Got: ${result.provider}`);
        }
    }
});

console.log("\n--- ModelRouterService Tests Summary ---");
if (allTestsPassed) {
    console.log("All tests PASSED!");
} else {
    console.error("Some tests FAILED.");
}

// Test getModelConfig and getAllModelConfigs
console.log("\n--- Testing getModelConfig --- ");
const opusConfig = modelRouter.getModelConfig("claude-3-opus-20240229");
console.log("Config for claude-3-opus-20240229:", opusConfig ? opusConfig.name : "Not found");
const fakeConfig = modelRouter.getModelConfig("fake-model");
console.log("Config for fake-model:", fakeConfig ? fakeConfig.name : "Not found");

console.log("\n--- Testing getAllModelConfigs --- ");
const allConfigs = modelRouter.getAllModelConfigs();
console.log("Total models configured:", Object.keys(allConfigs).length);
// console.log(JSON.stringify(allConfigs, null, 2)); // Uncomment for full config list

process.env.DEBUG_MODEL_ROUTER_LOGGING = "false"; // Reset env var


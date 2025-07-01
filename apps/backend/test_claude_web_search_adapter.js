require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });

// --- Mocking CredentialsService ---
let mockCredentialsService = {
    getCredential: async (service, key) => {
        console.log(`Mock credentialsService: getCredential called for ${service} - ${key}`);
        if (mockCredentialsService._shouldReturnKey) {
            return "mock_api_key_from_service";
        }
        if (mockCredentialsService._shouldThrowError) {
            throw new Error("Mock credentialsService Error");
        }
        return null; // Simulate key not found
    },
    _shouldReturnKey: false,
    _shouldThrowError: false,
    reset: function() {
        this._shouldReturnKey = false;
        this._shouldThrowError = false;
    }
};

// This is a common way to mock a module in Node.js for tests without Jest's full capabilities
const Module = require("module");
const originalRequire = Module.prototype.require;
Module.prototype.require = function(path) {
    if (path.endsWith("src/services/credentialsService.js")) { // Intercept require for credentialsService
        return mockCredentialsService;
    }
    return originalRequire.apply(this, arguments);
};

const ClaudeWebSearchAdapter = require("./src/adapters/ClaudeWebSearchAdapter.js");

// --- Mocking Anthropic SDK ---
let mockAnthropicInstance;
const mockAnthropicMessagesCreate = async (params) => {
    console.log("Mock Anthropic: messages.create called with:", JSON.stringify(params, null, 2));
    if (mockAnthropicInstance._shouldThrowError) {
        throw new Error("Mock Anthropic API Error");
    }
    if (!mockAnthropicInstance._apiKeyValid) {
        throw new Error("Mock Anthropic: Invalid API Key (simulated)");
    }
    return {
        id: "msg_mock123",
        type: "message",
        role: "assistant",
        model: "claude-3-5-sonnet-20240620",
        stop_reason: "tool_use",
        content: [
            { type: "text", text: "The capital of France is Paris. [1]" },
            { type: "tool_use", id: "toolu_mock_search_1", name: "anthropic-search", input: { "query": params.messages[0].content } },
            { type: "text", text: "\n\n[1] Source: Wikipedia - Paris (https://en.wikipedia.org/wiki/Paris)" }
        ],
        usage: { input_tokens: 10, output_tokens: 50 }
    };
};

// Mock the @anthropic-ai/sdk module itself
Module.prototype.require = function(path) {
    if (path === "@anthropic-ai/sdk") {
        return {
            Anthropic: function(options) {
                console.log("Mock Anthropic SDK: Constructor called with options:", options ? { apiKeyExists: !!options.apiKey } : "undefined");
                mockAnthropicInstance = this;
                this._apiKeyValid = !!options.apiKey;
                this._shouldThrowError = false;
                this.messages = { create: mockAnthropicMessagesCreate };
                return this;
            }
        };
    }
    if (path.endsWith("src/services/credentialsService.js")) { 
        return mockCredentialsService;
    }
    return originalRequire.apply(this, arguments);
};


// --- Test Runner ---
async function runTest(testName, testFn) {
    console.log(`\n--- Running Test: ${testName} ---`);
    let originalApiKeyEnv = process.env.CLAUDE_API_KEY;
    mockCredentialsService.reset(); // Reset credentials mock before each test

    try {
        await testFn();
    } catch (error) {
        console.error(`FAIL: ${testName}. Error:`, error.message, error.stack);
        return false;
    } finally {
        if (originalApiKeyEnv === undefined) delete process.env.CLAUDE_API_KEY;
        else process.env.CLAUDE_API_KEY = originalApiKeyEnv;
        if (mockAnthropicInstance) {
            mockAnthropicInstance._shouldThrowError = false;
            mockAnthropicInstance._apiKeyValid = true; 
        }
    }
    return true;
}

async function testClaudeWebSearchAdapter() {
    console.log("Testing ClaudeWebSearchAdapter with enhanced mocking...");
    let allTestsPassed = true;

    // Test Case 1: Successful Web Search (using API Key from ENV)
    allTestsPassed = await runTest("Successful Web Search (ENV KEY)", async () => {
        process.env.CLAUDE_API_KEY = "env_mock_claude_api_key";
        const adapter = new ClaudeWebSearchAdapter();
        await new Promise(resolve => setTimeout(resolve, 150)); // Allow async init

        const params = { query: "What is the capital of France?" };
        const result = await adapter.executeAction("claudeWebSearch/webSearch", params);
        console.log("Successful Search (ENV KEY) Result:", JSON.stringify(result, null, 2));
        if (!(result && result.status === "success" && result.data && result.data.answer.includes("Paris"))) {
            throw new Error("Web search (ENV KEY) failed or returned unexpected data.");
        }
        if (!(result.data.sources && result.data.sources.length > 0 && result.data.sources[0].url.includes("wikipedia"))) {
            throw new Error("Successful search (ENV KEY) but sources are missing or incorrect.");
        }
        console.log("PASS: Successful Web Search (ENV KEY) with sources.");
    }) && allTestsPassed;

    // Test Case 1.2: Successful Web Search (using API Key from CredentialsService)
    allTestsPassed = await runTest("Successful Web Search (CredentialsService KEY)", async () => {
        delete process.env.CLAUDE_API_KEY; // Ensure ENV key is NOT set
        mockCredentialsService._shouldReturnKey = true; // Mock service to return a key
        
        const adapter = new ClaudeWebSearchAdapter();
        await new Promise(resolve => setTimeout(resolve, 150)); 

        const params = { query: "What is the capital of Germany?" };
        const result = await adapter.executeAction("claudeWebSearch/webSearch", params);
        console.log("Successful Search (CredentialsService KEY) Result:", JSON.stringify(result, null, 2));
        if (!(result && result.status === "success" && result.data && result.data.answer.includes("Paris"))) { // Mock still returns Paris
            throw new Error("Web search (CredentialsService KEY) failed or returned unexpected data.");
        }
        console.log("PASS: Successful Web Search (CredentialsService KEY).");
    }) && allTestsPassed;

    // Test Case 2: API Key Missing (ENV and CredentialsService fail)
    allTestsPassed = await runTest("API Key Missing (ENV & Service Fail)", async () => {
        delete process.env.CLAUDE_API_KEY;
        mockCredentialsService._shouldReturnKey = false; // Service returns null (no key)
        
        const adapter = new ClaudeWebSearchAdapter();
        await new Promise(resolve => setTimeout(resolve, 150)); 

        const params = { query: "Query with no API key" };
        const result = await adapter.executeAction("claudeWebSearch/webSearch", params);
        console.log("API Key Missing (ENV & Service Fail) Result:", JSON.stringify(result, null, 2));
        if (!(result && result.status === "error" && result.message.includes("Anthropic client not initialized"))) {
            throw new Error("API Key Missing (ENV & Service Fail) test failed to return the expected error.");
        }
        console.log("PASS: API Key Missing (ENV & Service Fail) test.");
    }) && allTestsPassed;

    // Test Case 2.2: CredentialsService Error during API Key fetch
    allTestsPassed = await runTest("CredentialsService Error on Key Fetch", async () => {
        delete process.env.CLAUDE_API_KEY;
        mockCredentialsService._shouldThrowError = true; // Service throws an error
        
        const adapter = new ClaudeWebSearchAdapter();
        await new Promise(resolve => setTimeout(resolve, 150)); 

        const params = { query: "Query with credentials service error" };
        const result = await adapter.executeAction("claudeWebSearch/webSearch", params);
        console.log("CredentialsService Error Result:", JSON.stringify(result, null, 2));
        // Adapter should still result in "Anthropic client not initialized" as it couldn't get a key
        if (!(result && result.status === "error" && result.message.includes("Anthropic client not initialized"))) {
            throw new Error("CredentialsService Error test failed to return the expected client initialization error.");
        }
        console.log("PASS: CredentialsService Error on Key Fetch test.");
    }) && allTestsPassed;

    // Test Case 3: Claude API Error (Anthropic SDK throws)
    allTestsPassed = await runTest("Claude API Error (SDK Throws)", async () => {
        process.env.CLAUDE_API_KEY = "env_mock_claude_api_key"; // Key is available
        mockCredentialsService._shouldReturnKey = false; // Service not used if ENV is set
        
        const adapter = new ClaudeWebSearchAdapter();
        await new Promise(resolve => setTimeout(resolve, 150));
        
        if (mockAnthropicInstance) mockAnthropicInstance._shouldThrowError = true; // Tell Anthropic mock to throw

        const params = { query: "Query that causes API error" };
        const result = await adapter.executeAction("claudeWebSearch/webSearch", params);
        console.log("Claude API Error (SDK Throws) Result:", JSON.stringify(result, null, 2));
        if (!(result && result.status === "error" && result.message.includes("Mock Anthropic API Error"))) {
            throw new Error("Claude API Error (SDK Throws) test failed to return the expected error.");
        }
        console.log("PASS: Claude API Error (SDK Throws) test.");
    }) && allTestsPassed;
    
    // Test Case 4: Unknown toolId
    allTestsPassed = await runTest("Unknown toolId", async () => {
        process.env.CLAUDE_API_KEY = "env_mock_claude_api_key"; // Key available for adapter init
        const adapter = new ClaudeWebSearchAdapter();
        await new Promise(resolve => setTimeout(resolve, 150));

        const params = { query: "Test query" };
        const result = await adapter.executeAction("claudeWebSearch/unknownTool", params);
        console.log("Unknown toolId Result:", JSON.stringify(result, null, 2));
        if (!(result && result.status === "error" && result.message.includes("Unknown tool"))) {
            throw new Error("Unknown toolId test failed to return the expected error.");
        }
        console.log("PASS: Unknown toolId test.");
    }) && allTestsPassed;

    console.log("\n-----------------------------------------");
    if (allTestsPassed) {
        console.log("All ClaudeWebSearchAdapter tests PASSED!");
    } else {
        console.error("Some ClaudeWebSearchAdapter tests FAILED.");
    }
    console.log("-----------------------------------------");

    // Restore original require
    Module.prototype.require = originalRequire;
}

testClaudeWebSearchAdapter();


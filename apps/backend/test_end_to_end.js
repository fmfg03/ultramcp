const axios = require("axios");
const { spawn } = require("child_process");
const path = require("path");

const SERVER_URL = "http://localhost:3001"; // Assuming port 3001 from .env
const ORCHESTRATE_ENDPOINT = `${SERVER_URL}/orchestrate`;
const SERVER_START_TIMEOUT = 15000; // 15 seconds for server to start
const REQUEST_TIMEOUT = 20000; // 20 seconds for API requests

let serverProcess;

async function startServer() {
    return new Promise((resolve, reject) => {
        console.log("Starting server...");
        const serverPath = path.join(__dirname, "src", "server.cjs");
        serverProcess = spawn("node", [serverPath], { cwd: __dirname });

        let serverReady = false;

        serverProcess.stdout.on("data", (data) => {
            const output = data.toString();
            console.log(`Server STDOUT: ${output}`);
            if (output.includes("Server listening on port 3001") || output.includes("MCP Broker Service initialized")) { // Adjust based on actual server ready message
                if (!serverReady) {
                    serverReady = true;
                    console.log("Server started successfully.");
                    resolve(serverProcess);
                }
            }
        });

        serverProcess.stderr.on("data", (data) => {
            console.error(`Server STDERR: ${data.toString()}`);
            // Don't reject immediately on stderr, some warnings might be normal
        });

        serverProcess.on("error", (err) => {
            console.error("Failed to start server process:", err);
            if (!serverReady) reject(err);
        });

        serverProcess.on("close", (code) => {
            console.log(`Server process exited with code ${code}`);
            if (!serverReady) reject(new Error(`Server process exited prematurely with code ${code}`));
        });

        // Timeout for server start
        setTimeout(() => {
            if (!serverReady) {
                console.error("Server start timed out.");
                if (serverProcess) serverProcess.kill();
                reject(new Error("Server start timed out"));
            }
        }, SERVER_START_TIMEOUT);
    });
}

async function stopServer() {
    return new Promise((resolve) => {
        if (serverProcess && !serverProcess.killed) {
            console.log("Stopping server...");
            serverProcess.kill("SIGINT"); // Graceful shutdown
            const timeout = setTimeout(() => {
                if (serverProcess && !serverProcess.killed) {
                    console.warn("Forcefully killing server process...");
                    serverProcess.kill("SIGKILL");
                }
                resolve();
            }, 5000); // 5 seconds to shut down gracefully
            serverProcess.on("close", () => {
                clearTimeout(timeout);
                console.log("Server stopped.");
                resolve();
            });
        } else {
            resolve();
        }
    });
}

async function runTest(testName, testFn) {
    console.log(`\n--- Running E2E Test: ${testName} ---`);
    let success = false;
    try {
        await testFn();
        success = true;
        console.log(`PASS: ${testName}`);
    } catch (error) {
        console.error(`FAIL: ${testName}. Error:`, error.message, error.response ? error.response.data : error.stack);
    }
    return success;
}

async function main() {
    try {
        await startServer();
    } catch (error) {
        console.error("Failed to start server for E2E tests. Aborting.", error);
        process.exit(1);
    }

    let allTestsPassed = true;

    // Test Case 1: ClaudeWebSearchAdapter - General Knowledge Question
    allTestsPassed = await runTest("ClaudeWebSearchAdapter - General Knowledge", async () => {
        const payload = {
            input: "What is the current weather in London?",
            chat_history: [],
            user_id: "e2e-test-user",
            session_id: "e2e-test-session-claude-web"
        };
        console.log("Sending request to /orchestrate for ClaudeWebSearchAdapter...");
        const response = await axios.post(ORCHESTRATE_ENDPOINT, payload, { timeout: REQUEST_TIMEOUT });
        console.log("Response from /orchestrate (ClaudeWebSearchAdapter):", JSON.stringify(response.data, null, 2));
        if (response.status !== 200) throw new Error(`Expected status 200, got ${response.status}`);
        if (!response.data || !response.data.response) throw new Error("Response data or response.data.response is missing");
        if (!response.data.routing_decision || response.data.routing_decision.adapter_id !== "claude_web_search") {
            throw new Error(`Expected routing to claude_web_search, got ${response.data.routing_decision ? response.data.routing_decision.adapter_id : 'undefined'}`);
        }
        // Further checks on the content of response.data.response.answer would be good here
        if (!response.data.response.answer || response.data.response.answer.length === 0) throw new Error("Answer from ClaudeWebSearchAdapter is empty");
        console.log("ClaudeWebSearchAdapter test seems okay based on routing and non-empty answer.");
    }) && allTestsPassed;

    // Test Case 2: EmbeddingSearchAdapter - Ingest and Search (Simplified)
    // For a true E2E, we might need a separate ingest step or pre-populate data.
    // This test will assume routing and a basic query that might trigger it.
    allTestsPassed = await runTest("EmbeddingSearchAdapter - Semantic Query", async () => {
        const payload = {
            input: "Tell me about the project requirements for MCP system.", // A query likely to hit embeddings
            chat_history: [],
            user_id: "e2e-test-user",
            session_id: "e2e-test-session-embedding"
        };
        // First, ingest a document (if Zep is empty, search will yield nothing relevant)
        // This requires the EmbeddingSearchAdapter to be registered and Zep to be running.
        // We will assume for now that the `ingest_document` tool is available via the orchestrator if routed to embedding_search
        // However, the orchestrator doesn't directly call tools; it calls adapter.executeAction.
        // So, this test relies on the InputPreprocessor routing to embedding_search and then the adapter handling a search.
        // A more complete test would involve a separate call to an ingest endpoint or a more complex orchestration flow.

        console.log("Sending request to /orchestrate for EmbeddingSearchAdapter (semantic query)...");
        const response = await axios.post(ORCHESTRATE_ENDPOINT, payload, { timeout: REQUEST_TIMEOUT });
        console.log("Response from /orchestrate (EmbeddingSearchAdapter):", JSON.stringify(response.data, null, 2));
        if (response.status !== 200) throw new Error(`Expected status 200, got ${response.status}`);
        if (!response.data || !response.data.response) throw new Error("Response data or response.data.response is missing");
        if (!response.data.routing_decision || response.data.routing_decision.adapter_id !== "embedding_search") {
             // It might route to claude_tool_agent if the query is complex enough, let's allow that as a secondary possibility
            if (response.data.routing_decision.adapter_id !== "claude_tool_agent") {
                throw new Error(`Expected routing to embedding_search or claude_tool_agent, got ${response.data.routing_decision ? response.data.routing_decision.adapter_id : 'undefined'}`);
            }
            console.log("Query routed to claude_tool_agent, which is an acceptable alternative for this query.");
        }
        if (!response.data.response.results && !response.data.response.answer) throw new Error("Search results or answer from EmbeddingSearchAdapter/ToolAgent is missing");
        console.log("EmbeddingSearchAdapter/ToolAgent test seems okay based on routing and non-empty response.");
    }) && allTestsPassed;

    // Test Case 3: ClaudeToolAgentAdapter - Complex query (placeholder)
    allTestsPassed = await runTest("ClaudeToolAgentAdapter - Complex Query", async () => {
        const payload = {
            input: "Create a plan to build a website for a bakery, then write the HTML for the homepage.",
            chat_history: [],
            user_id: "e2e-test-user",
            session_id: "e2e-test-session-tool-agent"
        };
        console.log("Sending request to /orchestrate for ClaudeToolAgentAdapter...");
        const response = await axios.post(ORCHESTRATE_ENDPOINT, payload, { timeout: REQUEST_TIMEOUT * 3 }); // Longer timeout for agent
        console.log("Response from /orchestrate (ClaudeToolAgentAdapter):", JSON.stringify(response.data, null, 2));
        if (response.status !== 200) throw new Error(`Expected status 200, got ${response.status}`);
        if (!response.data || !response.data.response) throw new Error("Response data or response.data.response is missing");
        if (!response.data.routing_decision || response.data.routing_decision.adapter_id !== "claude_tool_agent") {
            throw new Error(`Expected routing to claude_tool_agent, got ${response.data.routing_decision ? response.data.routing_decision.adapter_id : 'undefined'}`);
        }
        if (!response.data.response.answer || response.data.response.answer.length === 0) throw new Error("Answer from ClaudeToolAgentAdapter is empty");
        console.log("ClaudeToolAgentAdapter test seems okay based on routing and non-empty answer.");
    }) && allTestsPassed;

    console.log("\n-----------------------------------------");
    if (allTestsPassed) {
        console.log("All E2E tests PASSED!");
    } else {
        console.error("Some E2E tests FAILED.");
    }
    console.log("-----------------------------------------");

    await stopServer();
    process.exit(allTestsPassed ? 0 : 1);
}

main().catch(async (err) => {
    console.error("Unhandled error in E2E test runner:", err);
    await stopServer();
    process.exit(1);
});


require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });
const inputPreprocessorService = require("./src/services/InputPreprocessorService.js");

async function testInputPreprocessorRouting() {
    console.log("Testing InputPreprocessorService Routing Logic...");

    const testCases = [
        {
            description: "Simple query, expect default_llm_service or orchestrator",
            rawData: "Hello there",
            filesToProcess: [],
            expectedAdapter: ["default_llm_service", "orchestration_service"] // Can be either
        },
        {
            description: "Query with 'search for', expect claude_web_search",
            rawData: "search for the latest news on AI",
            filesToProcess: [],
            expectedAdapter: "claude_web_search"
        },
        {
            description: "Query with 'what is', expect claude_web_search",
            rawData: "what is the capital of France?",
            filesToProcess: [],
            expectedAdapter: "claude_web_search"
        },
        {
            description: "Query with files, expect embedding_search",
            rawData: "summarize these documents for me",
            filesToProcess: [{ originalFilename: "test.pdf", tempFilePath: "/tmp/fakefile.pdf", size: 1024 }], // Simulate file info
            expectedAdapter: "embedding_search"
        },
        {
            description: "Query with 'search my documents', expect embedding_search",
            rawData: "search my documents for project alpha details",
            filesToProcess: [],
            expectedAdapter: "embedding_search"
        },
        {
            description: "Query with 'book a', expect claude_tool_agent",
            rawData: "book a flight to New York",
            filesToProcess: [],
            expectedAdapter: "claude_tool_agent"
        },
        {
            description: "Complex query that might be rephrased, then routed to tool agent",
            rawData: "If the weather is good tomorrow, can you find a good picnic spot and then order some sandwiches?",
            filesToProcess: [],
            expectedAdapter: "claude_tool_agent" // Rephrasing might happen first, then routing
        },
        {
            description: "Long query, expect rephrase and then default/orchestrator or specific if keywords match",
            rawData: "This is a very long query that definitely exceeds the threshold for rephrasing, it talks about many things and I want to see how the system handles it and what kind of processing it will apply to it. I am not sure if it contains specific keywords for routing after rephrasing but let us check that out. I need to understand the process flow.",
            filesToProcess: [],
            // Expected adapter depends on keywords after rephrasing, could be default or specific.
            // For this test, we primarily check if rephrasing occurs and routing is attempted.
            // We won't assert a specific adapter here, just that a decision is made.
            expectedAdapter: null // null means we check for decision, not specific adapter
        }
    ];

    let allTestsPassed = true;

    // Create a dummy file for file upload test case
    const dummyFilePath = "/tmp/fakefile.pdf";
    if (!require("fs").existsSync("/tmp")) require("fs").mkdirSync("/tmp");
    require("fs").writeFileSync(dummyFilePath, "dummy content");

    for (const tc of testCases) {
        console.log(`\nRunning test: ${tc.description}`);
        try {
            const result = await inputPreprocessorService.process(tc.rawData, tc.filesToProcess);
            console.log("Processed Output:", JSON.stringify(result, null, 2));

            if (!result.routing_decision || !result.routing_decision.adapter_id) {
                console.error(`FAIL: ${tc.description} - No routing decision made.`);
                allTestsPassed = false;
                continue;
            }

            if (tc.expectedAdapter === null) { // For cases where we only check if a decision is made
                 console.log(`PASS: ${tc.description} - Routing decision made: ${result.routing_decision.adapter_id}`);
            } else if (Array.isArray(tc.expectedAdapter)) {
                if (tc.expectedAdapter.includes(result.routing_decision.adapter_id)) {
                    console.log(`PASS: ${tc.description} - Routed to ${result.routing_decision.adapter_id} (expected one of: ${tc.expectedAdapter.join(", ")})`);
                } else {
                    console.error(`FAIL: ${tc.description} - Expected route to one of ${tc.expectedAdapter.join(", ")}, but got ${result.routing_decision.adapter_id}`);
                    allTestsPassed = false;
                }
            } else {
                if (result.routing_decision.adapter_id === tc.expectedAdapter) {
                    console.log(`PASS: ${tc.description} - Routed to ${result.routing_decision.adapter_id}`);
                } else {
                    console.error(`FAIL: ${tc.description} - Expected route to ${tc.expectedAdapter}, but got ${result.routing_decision.adapter_id}`);
                    allTestsPassed = false;
                }
            }

            // Check if rephrasing occurred for the long query test case
            if (tc.description.startsWith("Long query")) {
                if (result.llm_used_rephrase) {
                    console.log(`INFO: ${tc.description} - Rephrasing occurred as expected (LLM: ${result.llm_used_rephrase}).`);
                } else {
                    console.warn(`WARN: ${tc.description} - Expected rephrasing for long query, but it did not occur.`);
                    // This might not be a hard fail depending on exact rephrase logic and thresholds
                }
            }

        } catch (error) {
            console.error(`ERROR during test "${tc.description}":`, error);
            allTestsPassed = false;
        }
    }

    // Clean up dummy file
    if (require("fs").existsSync(dummyFilePath)) require("fs").unlinkSync(dummyFilePath);

    console.log("\n-----------------------------------------");
    if (allTestsPassed) {
        console.log("All InputPreprocessorService routing tests PASSED!");
    } else {
        console.error("Some InputPreprocessorService routing tests FAILED.");
    }
    console.log("-----------------------------------------");
}

testInputPreprocessorRouting();


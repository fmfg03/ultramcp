// Test script for router-LangGraph bridge in orchestrationService.js
const orchestrationApp = require("./services/orchestrationService.js");
const inputPreprocessor = require("./services/InputPreprocessorService.js");
const mcpBrokerService = require("./services/mcpBrokerService.js"); // To potentially mock or observe tool calls

// Mock mcpBrokerService.getAvailableTools if it causes issues or for consistent testing
const originalGetAvailableTools = mcpBrokerService.getAvailableTools;
mcpBrokerService.getAvailableTools = async () => {
    console.log("[TestRunner] Mocked mcpBrokerService.getAvailableTools() called");
    return [
        { id: "embedding_search/search_documents", description: "Searches documents using embeddings.", adapterId: "embedding_search" },
        { id: "claude_web_search/webSearch", description: "Performs a web search.", adapterId: "claude_web_search" },
        { id: "claude_tool_agent/execute_task_with_tools", description: "Executes a task with a set of tools.", adapterId: "claude_tool_agent" },
        { id: "cli/execute_command", description: "Executes a CLI command.", adapterId: "cli" },
    ];
};

// Mock mcpBrokerService.executeTool to prevent actual execution and observe calls
const originalExecuteTool = mcpBrokerService.executeTool;
mcpBrokerService.executeTool = async (toolId, params) => {
    console.log(`[TestRunner] Mocked mcpBrokerService.executeTool CALLED with toolId: ${toolId}, params:`, params);
    if (toolId === "embedding_search/search_documents") {
        return { search_results: [`Mocked search result for query: ${params.query}`] };
    }
    if (toolId === "claude_web_search/webSearch") {
        return { search_results: [`Mocked web result for query: ${params.query}`] };
    }
    if (toolId === "claude_tool_agent/execute_task_with_tools") {
        return { agent_response: `Mocked agent response for task: ${params.task_description}` };
    }
    if (toolId === "cli/execute_command") {
        return { output: `Mocked CLI output for command: ${params.command}` };
    }
    return { mocked_result: `Result for ${toolId}` };
};


async function runTest(testName, userQuery, mockFiles = []) {
    console.log(`\n--- Starting Test: ${testName} ---`);
    console.log(`User Query: ${userQuery}`);

    const processedInput = await inputPreprocessor.process(userQuery, mockFiles);
    console.log("[TestRunner] InputPreprocessor Output:", JSON.stringify(processedInput, null, 2));

    if (!processedInput.routing_decision) {
        console.error("[TestRunner] ERROR: No routing_decision from InputPreprocessorService.");
        return;
    }

    const initialState = {
        request: processedInput.cleaned_prompt,
        routing_decision: processedInput.routing_decision,
        files: processedInput.files || [],
        // workflowType and other initial states will be set by entryNode or subsequent nodes
    };

    console.log("[TestRunner] Invoking LangGraph with initial state:", JSON.stringify(initialState, null, 2));
    
    try {
        // Simulate a chatId for potential session-based logic, though current graph doesn't use it in invoke config
        const result = await orchestrationApp.invoke(initialState, { configurable: { thread_id: `test-chat-${Date.now()}` } });
        console.log("[TestRunner] LangGraph Final Result:", JSON.stringify(result, null, 2));
        console.log(`--- Test Finished: ${testName} ---`);
    } catch (error) {
        console.error(`[TestRunner] ERROR during LangGraph invocation for test "${testName}":`, error);
        console.log(`--- Test Finished with ERROR: ${testName} ---`);
    }
}

async function main() {
    // Test Case 1: Web Search
    await runTest("Web Search Test", "search for the latest news on AI advancements");

    // Test Case 2: Embedding Search (simulate a file)
    // InputPreprocessorService expects file objects with tempFilePath or content.
    // For simplicity, we are not actually creating files, but rely on the preprocessor's logic.
    // The current preprocessor mock for _handleFileUploads might need adjustment if real file paths are strictly needed by the graph.
    // However, the `files` array in `agentState` is what `semanticSearchNode` uses.
    await runTest("Embedding Search Test", "find information about project X in my documents", 
        [{ originalFilename: "test_doc.txt", tempFilePath: "/tmp/fake_test_doc.txt", size: 100 }] 
        // The preprocessor will try to move this, it might log errors but should still populate `processedInput.files`
        // if the mock/actual file handling logic is robust enough or if we mock it further.
        // For now, we assume `processedInput.files` will contain the path it *would* have saved to.
    );

    // Test Case 3: Tool Agent
    await runTest("Tool Agent Test", "book a flight to London for next week and find a hotel");

    // Test Case 4: Default LLM Planning (fallback in plannerNode)
    await runTest("Default LLM Planning Test", "tell me a very interesting story about a robot");

    // Test Case 5: Ideation Flow
    await runTest("Ideation Flow Test", "brainstorm some cool names for a new coffee shop");
    
    // Test Case 6: Direct tool routing from preprocessor (if preprocessor routes to a specific tool_id)
    // This depends on InputPreprocessorService's _determineIntentAndRoute to potentially return a specific toolId.
    // The current preprocessor routes to adapter_ids, which plannerNode then maps to specific nodes or builder.
    // Let's test a case where preprocessor might suggest 'cli/execute_command' if it were designed to.
    // For now, let's use a query that should hit the planner's LLM or fallback for builderNode.
    await runTest("Simple CLI-like command", "list all files in my current directory please");

    // Restore original mcpBrokerService methods if necessary for other tests, though not critical for this script
    mcpBrokerService.getAvailableTools = originalGetAvailableTools;
    mcpBrokerService.executeTool = originalExecuteTool;
}

main().catch(err => console.error("[TestRunner] Unhandled error in main:", err));



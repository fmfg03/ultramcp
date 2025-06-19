// Test script for OrchestrationService with advanced LangGraph nodes
const orchestrationService = require("./src/services/orchestrationService"); // Use instance directly
const mcpBrokerService = require("./src/services/mcpBrokerService"); // Corrected path

// Mocking mcpBrokerService for controlled testing
// In a real test, you might want to have a more sophisticated mock or a test instance of the broker
let mockToolResponses = {};
mcpBrokerService.getAvailableTools = async () => [
    { id: "langchain_tavily_web_search", description: "Web search via Tavily", schema: { query: "string" } },
    { id: "langchain_code_interpreter", description: "Executes Python code", schema: { code: "string" } },
    { id: "langchain_github_read_file", description: "Reads a file from GitHub", schema: { owner: "string", repo: "string", path: "string" } },
    { id: "cli/execute_command", description: "Executes a shell command", schema: { command: "string" } },
    { id: "embedding_search/search_documents", description: "Semantic search in documents", schema: { query: "string", files: "array" } },
    { id: "claude_tool_agent/execute_task_with_tools", description: "Claude agent for tool use", schema: { task_description: "string" } },
];

mcpBrokerService.executeTool = async (toolId, params) => {
    console.log(`[Mock MCPBroker] executeTool called: ${toolId}, Params:`, params);
    if (mockToolResponses[toolId]) {
        const response = mockToolResponses[toolId](params);
        if (response.error) throw new Error(response.error);
        return response.result;
    }
    if (toolId === "langchain_tavily_web_search") return `Mock search results for: ${params.query}`;
    if (toolId === "langchain_code_interpreter") {
        if (params.code && params.code.includes("error")) throw new Error("Simulated code execution error");
        return `Mock code execution result for: ${params.code}`;
    }
    if (toolId === "cli/execute_command") return `Mock CLI output for: ${params.command}`;
    return `Mock result for ${toolId}`;
};

// Configure environment variables for LLMs (ensure these are set in your actual test environment or CI)
// These are placeholders; actual keys are needed for LLMs to function.
process.env.OPENAI_API_KEY = process.env.OPENAI_API_KEY || "sk-testkey";
process.env.ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "sk-testkey-anthropic";
process.env.GOOGLE_API_KEY = process.env.GOOGLE_API_KEY || "google-testkey";
process.env.TAVILY_API_KEY = process.env.TAVILY_API_KEY || "tvly-testkey"; // For Tavily search tool

// Optional: Set default LLM providers and models if ModelRouterService might not find specific ones
process.env.PLANNER_LLM_PROVIDER = "OpenAI";
process.env.PLANNER_LLM_MODEL = "gpt-3.5-turbo";
process.env.JUDGE_LLM_PROVIDER = "OpenAI";
process.env.JUDGE_LLM_MODEL = "gpt-3.5-turbo";
process.env.BUILDER_LLM_PROVIDER = "OpenAI";
process.env.BUILDER_LLM_MODEL = "gpt-3.5-turbo";
process.env.REFACTOR_LLM_PROVIDER = "OpenAI";
process.env.REFACTOR_LLM_MODEL = "gpt-3.5-turbo";


const runTest = async (testName, userInput, routingDecision = null, files = null, approvalRequired = false) => {
    console.log(`\n--- Running Test: ${testName} ---`);
    console.log(`Input: "${userInput}"`);
    if (routingDecision) console.log("Routing Decision:", routingDecision);
    if (files) console.log("Files:", files);
    if (approvalRequired) console.log("Approval Required: true");

    try {
        const response = await orchestrationService.processCommand(userInput, routingDecision, files, approvalRequired);
        console.log(`[Test Result - ${testName}] Final Response:`, response);
    } catch (error) {
        console.error(`[Test Error - ${testName}] orchestrationservice.processCommand failed:`, error);
    }
    console.log(`--- Test Ended: ${testName} ---\n`);
};

const main = async () => {
    // Test 1: Simple request, should go through Planner -> Builder -> Judge -> Finalizer
    mockToolResponses = {}; // Reset mocks
    await runTest("Simple Web Search Request", "What is LangGraph?");

    // Test 2: Request that might need refactoring (Simulate Judge asking for revision)
    // For this, we need to mock the Judge LLM or have a way to inject its decision.
    // The current Judge LLM prompt is hardcoded, so direct mocking of Judge LLM is complex without changing OrchestrationService.
    // Instead, we can simulate a tool error in builder, then judge might say revise, then refactor.
    mockToolResponses["langchain_code_interpreter"] = (params) => {
        if (params.code === "print(\'hello\')") return { result: "hello_world_output_needs_refactor" }; // Judge might find this needing refactor
        return { result: `Executed: ${params.code}` };
    };
    // To properly test refactor, Judge needs to return {verdict: "revise", feedback: "..."}
    // This requires deeper mocking of the LLM used by Judge or modifying judgeNode to be more deterministic for tests.
    // For now, we assume judge might ask for revision based on some output.
    await runTest("Request potentially needing Refactor", "Write a python script to print hello", { adapter_id: "langchain_code_interpreter", tool_id: "langchain_code_interpreter", params: { code: "print(\'hello\')"}, confidence: 0.9 });

    // Test 3: Request leading to an error in Builder, then Escalation
    mockToolResponses = {}; // Reset mocks
    mockToolResponses["langchain_code_interpreter"] = () => ({ error: "Critical execution failure" });
    // This test relies on the Judge correctly identifying the error and routing to escalate if maxRevisions is hit or error is severe.
    // The current judgeNode routes to escalate if verdict is "error" or max revisions for "revise" is hit.
    await runTest("Request leading to Builder Error and Escalation", "Execute faulty code", { adapter_id: "langchain_code_interpreter", tool_id: "langchain_code_interpreter", params: { code: "import non_existent_module"}, confidence: 0.9 });

    // Test 4: Request requiring Human Approval (Simulated)
    // The approveNode currently auto-approves or sets to pending. True test needs graph interruption.
    await runTest("Request needing Human Approval", "Deploy the critical application to production", null, null, true);

    // Test 5: Direct routing to semanticSearchNode
    mockToolResponses = {};
    mockToolResponses["embedding_search/search_documents"] = (params) => ({ result: `Semantic search for: ${params.query} in files: ${params.files}` });
    await runTest("Direct Semantic Search", "Find relevant documents about AI ethics", { adapter_id: "embedding_search", tool_id: "embedding_search/search_documents", confidence: 0.95 }, ["doc1.pdf", "doc2.txt"]);

    // Test 6: Ideation workflow
    await runTest("Ideation Workflow Test", "Ideate on new names for a coffee shop");
    
    // Test 7: Planner fallback to Tavily search
    mockToolResponses = {}; // Ensure no specific tool mock leads to this
    // Relies on PlannerLLM failing or not providing a valid plan, then falling back.
    // To force this, we could temporarily disable PlannerLLM or make it return invalid JSON.
    // For now, assume a generic query might trigger it if no other routing is matched.
    await runTest("Planner Fallback to Web Search", "Tell me about the weather in Paris tomorrow");

    // Test 8: Max revisions leading to escalation
    // This requires the Judge LLM to consistently return "revise" for a few rounds.
    // This is hard to simulate without direct control over the Judge LLM responses.
    // We can simulate the state for currentRevision >= maxRevisions and judge verdict "revise"
    console.log("--- Test 8: Max Revisions (Conceptual - hard to trigger deterministically without LLM mocking) ---");
    // To test this path: Judge must return {verdict: "revise", feedback: "..."} multiple times.
    // The graph logic is: if (verdict === "revise" && state.currentRevision >= state.maxRevisions) -> "escalateNode"

    // Test 9: Direct routing to claudeToolAgentNode
    mockToolResponses = {};
    mockToolResponses["claude_tool_agent/execute_task_with_tools"] = (params) => ({ result: `Claude agent executed: ${params.task_description}` });
    await runTest("Direct Claude Tool Agent", "Use tools to book a flight to London", { adapter_id: "claude_tool_agent", tool_id: "claude_tool_agent/execute_task_with_tools", confidence: 0.95 });

    console.log("\nAll tests scheduled. Check console for outputs.");
};

main().catch(console.error);


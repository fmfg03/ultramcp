const BaseMCPAdapter = require("./baseMCPAdapter");
const { Anthropic } = require("@anthropic-ai/sdk");
const credentialsService = require("../../../src/services/credentialsService.js");

class ClaudeToolAgentAdapter extends BaseMCPAdapter {
    constructor(config = {}) {
        super(config);
        this.anthropic = null;
        this.apiKey = null;
        this.model = config.model || "claude-3-opus-20240229"; // Or other suitable model
        this.mcpBroker = config.mcpBroker; // To call other tools/adapters
        this._initialize();
    }

    async _initialize() {
        try {
            this.apiKey = process.env.ANTHROPIC_API_KEY || await credentialsService.getCredential("anthropic", "apiKey");
            if (!this.apiKey) {
                console.error("ClaudeToolAgentAdapter: ANTHROPIC_API_KEY not found in environment or credentialsService.");
                this.logError("ANTHROPIC_API_KEY not found. Adapter will not function.");
                return;
            }
            this.anthropic = new Anthropic({ apiKey: this.apiKey });
            this.logInfo("Anthropic client initialized successfully.");
        } catch (error) {
            console.error("ClaudeToolAgentAdapter: Error initializing Anthropic client:", error);
            this.logError(`Error initializing Anthropic client: ${error.message}`);
        }
    }

    getId() {
        return "claude_tool_agent";
    }

    async getTools() { // Made async to match potential future needs, though not strictly necessary for current static return
        return [
            {
                name: "execute_task_with_tools",
                description: "Executes a given task by intelligently using a provided set of tools. The task will be described in natural language. A manifest of available tools must be provided.",
                input_schema: {
                    type: "object",
                    properties: {
                        task_description: {
                            type: "string",
                            description: "The natural language description of the task to be accomplished."
                        },
                        tool_manifest: {
                            type: "array",
                            description: "An array of tool definitions that Claude can use. Each definition should follow the Claude tool format.",
                            items: {
                                type: "object",
                                properties: {
                                    name: { type: "string" },
                                    description: { type: "string" },
                                    input_schema: { type: "object" }
                                },
                                required: ["name", "description", "input_schema"]
                            }
                        },
                        max_iterations: {
                            type: "integer",
                            description: "Maximum number of tool use iterations before returning a direct answer or error.",
                            default: 5
                        }
                    },
                    required: ["task_description", "tool_manifest"]
                }
            }
        ];
    }

    async executeAction(toolName, params) {
        if (!this.anthropic) {
            const errorMsg = "ClaudeToolAgentAdapter: Anthropic client not initialized. Cannot execute action.";
            console.error(errorMsg);
            this.logError(errorMsg);
            return { error: errorMsg };
        }

        if (toolName !== "execute_task_with_tools") {
            const errorMsg = `ClaudeToolAgentAdapter: Tool ${toolName} not supported.`;
            console.error(errorMsg);
            this.logError(errorMsg);
            return { error: errorMsg };
        }

        const { task_description, tool_manifest, max_iterations = 5 } = params;
        let messages = [
            { role: "user", content: task_description }
        ];

        this.logInfo(`Starting task execution: ${task_description} with ${tool_manifest.length} tools. Max iterations: ${max_iterations}`);

        for (let i = 0; i < max_iterations; i++) {
            this.logInfo(`Iteration ${i + 1}/${max_iterations}`);
            try {
                const response = await this.anthropic.messages.create({
                    model: this.model,
                    max_tokens: 4096,
                    messages: messages,
                    tools: tool_manifest
                });

                this.logInfo(`Claude response received. Stop reason: ${response.stop_reason}`);
                
                let hasToolUse = false;
                const currentTurnResponseMessages = []; // Messages to be added for this turn

                if (response.content) {
                    for (const contentBlock of response.content) { // Changed from forEach to for...of
                        if (contentBlock.type === "text") {
                            this.logInfo(`Claude text response: ${contentBlock.text}`);
                            currentTurnResponseMessages.push({ role: "assistant", content: [{type: "text", text: contentBlock.text}] }); // Ensure content is an array of blocks for Claude
                        } else if (contentBlock.type === "tool_use") {
                            hasToolUse = true;
                            const toolNameFromClaude = contentBlock.name;
                            const toolInput = contentBlock.input;
                            const toolUseId = contentBlock.id;
                            this.logInfo(`Claude requests tool: ${toolNameFromClaude} with input: ${JSON.stringify(toolInput)} (ID: ${toolUseId})`);

                            let toolResultContent;
                            let toolExecutionSuccessful = false;

                            if (this.mcpBroker) {
                                try {
                                    this.logInfo(`Attempting to execute tool '${toolNameFromClaude}' via mcpBroker.`);
                                    const toolResult = await this.mcpBroker.executeTool(toolNameFromClaude, toolInput); // await is now valid here
                                    this.logInfo(`Tool '${toolNameFromClaude}' executed via mcpBroker. Result: ${JSON.stringify(toolResult)}`);
                                    toolResultContent = toolResult; 
                                    toolExecutionSuccessful = toolResult && !toolResult.error; // Check for an error property in the result
                                } catch (e) {
                                    this.logError(`Error executing tool '${toolNameFromClaude}' via mcpBroker: ${e.message}`);
                                    toolResultContent = { error: `Error executing tool ${toolNameFromClaude}: ${e.message}` };
                                    toolExecutionSuccessful = false;
                                }
                            } else {
                                this.logWarn(`mcpBroker not available. Simulating tool execution for '${toolNameFromClaude}'.`);
                                toolResultContent = { error: `Tool ${toolNameFromClaude} execution is not implemented in this adapter without mcpBroker.` };
                                toolExecutionSuccessful = false;
                            }
                            
                            // Construct the tool_result message for Claude
                            const toolResultBlock = {
                                type: "tool_result",
                                tool_use_id: toolUseId,
                                content: toolExecutionSuccessful ? JSON.stringify(toolResultContent) : JSON.stringify(toolResultContent), // Claude expects stringified JSON for content
                            };
                            if (!toolExecutionSuccessful) {
                                toolResultBlock.is_error = true;
                            }
                            currentTurnResponseMessages.push({ role: "user", content: [toolResultBlock] });
                        }
                    }
                }
                
                // Add assistant's text messages (if any from this turn) to the main messages array first
                const assistantTextContent = response.content.filter(cb => cb.type === "text").map(cb => ({type: "text", text: cb.text}));
                if(assistantTextContent.length > 0) {
                    messages.push({role: "assistant", content: assistantTextContent});
                }
                // Then add user's tool_result messages
                const toolResultMessagesForClaude = currentTurnResponseMessages.filter(m => m.role === "user" && m.content[0].type === "tool_result");
                messages = messages.concat(toolResultMessagesForClaude);

                if (response.stop_reason === "tool_use") {
                    if (!hasToolUse) {
                        this.logWarn("Claude stop_reason is 'tool_use' but no tool_use content block found. Treating as end_turn.");
                        const finalAnswer = messages.filter(m => m.role === 'assistant' && m.content && m.content[0] && m.content[0].type === 'text').map(m => m.content[0].text).join('\n');
                        return { answer: finalAnswer || "No textual answer from Claude after tool_use stop_reason without tool content.", logs: this.getLogs(), trace: messages };
                    }
                    // Continue loop for next interaction with Claude
                } else if (response.stop_reason === "end_turn" || response.stop_reason === "max_tokens") {
                    this.logInfo("Claude interaction ended (end_turn or max_tokens).");
                    const finalAnswer = messages.filter(m => m.role === 'assistant' && m.content && m.content[0] && m.content[0].type === 'text').map(m => m.content[0].text).join('\n');
                    return { answer: finalAnswer || "No textual answer from Claude.", logs: this.getLogs(), trace: messages };
                } else {
                    this.logWarn(`Unexpected stop_reason: ${response.stop_reason}. Ending interaction.`);
                    const finalAnswer = messages.filter(m => m.role === 'assistant' && m.content && m.content[0] && m.content[0].type === 'text').map(m => m.content[0].text).join('\n');
                    return { answer: finalAnswer || "Interaction ended with unexpected stop reason.", logs: this.getLogs(), trace: messages };
                }

            } catch (error) {
                console.error("ClaudeToolAgentAdapter: Error during Claude API call or processing:", error);
                this.logError(`Error during Claude API call: ${error.message}`);
                return { error: `Claude API call failed: ${error.message}`, logs: this.getLogs(), trace: messages };
            }
        }

        this.logWarn("Max iterations reached. Returning current state.");
        const finalAnswer = messages.filter(m => m.role === 'assistant' && m.content && m.content[0] && m.content[0].type === 'text').map(m => m.content[0].text).join('\n');
        return { error: "Max iterations reached without a final answer.", answer: finalAnswer, logs: this.getLogs(), trace: messages };
    }
}

module.exports = ClaudeToolAgentAdapter;


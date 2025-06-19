const BaseMCPAdapter = require("./baseMCPAdapter.js");
const inputPreprocessorService = require("../services/InputPreprocessorService.js");
const orchestrationService = require("../services/orchestrationService.js");
// TelegramBot will be dynamically imported

class TelegramAdapter extends BaseMCPAdapter {
  constructor(config) {
    super(config);
    this.bot = null;
    this.botToken = null;
    console.log("TelegramAdapter initialized.");
  }

  getId() {
    return "telegram";
  }

  async getTools() {
    return [
      {
        id: `${this.getId()}/sendMessage`,
        name: "Send Telegram Message",
        description: "Sends a message to a specified Telegram chat ID.",
        parameters: {
          type: "object",
          properties: {
            chatId: { type: ["string", "number"], description: "The target chat ID." },
            text: { type: "string", description: "The message text to send." },
          },
          required: ["chatId", "text"],
        },
      },
      {
        id: `${this.getId()}/startPollingUpdates`,
        name: "Start Polling Telegram Updates",
        description: "Starts polling for new messages from Telegram for the configured bot.",
        parameters: {
          type: "object",
          properties: {},
        },
      },
    ];
  }

  async _initializeBot() {
    if (this.bot) return true;

    this.botToken = process.env.TELEGRAM_BOT_TOKEN;

    if (!this.botToken) {
        console.log("TelegramAdapter: TELEGRAM_BOT_TOKEN not found in environment variables. Attempting to retrieve from credentialsService.");
        try {
            const credentialsServiceModule = await import("../../../../src/services/credentialsService.js");
            this.botToken = await credentialsServiceModule.getCredential("telegram", "botToken");
        } catch (e) {
            console.error("TelegramAdapter: Failed to dynamically import or use credentialsService:", e);
        }
    } else {
        console.log("TelegramAdapter: Using TELEGRAM_BOT_TOKEN from environment variable.");
    }

    if (!this.botToken) {
      console.error("TelegramAdapter: Bot token not found from environment or credentialsService. Cannot initialize bot.");
      return false;
    }

    try {
      const TelegramBotImport = await import("node-telegram-bot-api");
      const TelegramBot = TelegramBotImport.default;
      this.bot = new TelegramBot(this.botToken);
      console.log("TelegramAdapter: Bot initialized successfully with token.");
      return true;
    } catch (error) {
      console.error("TelegramAdapter: Failed to initialize Telegram Bot. Is node-telegram-bot-api installed?", error);
      this.bot = null;
      return false;
    }
  }

  async executeAction(toolId, params) {
    console.log(`TelegramAdapter: Executing action ${toolId} with params:`, params);

    const action = toolId.split("/")[1];

    if (!this.bot && !(await this._initializeBot())) {
      return { success: false, error: "Telegram bot could not be initialized. Token might be missing or invalid." };
    }
    if (!this.bot) { 
        return { success: false, error: "Telegram bot is not available after initialization attempt." };
    }

    switch (action) {
      case "sendMessage":
        if (!params.chatId || !params.text) {
          return { success: false, error: "Missing chatId or text for sendMessage." };
        }
        try {
          await this.bot.sendMessage(params.chatId, params.text);
          return { success: true, data: `Message sent to ${params.chatId}.` };
        } catch (error) {
          console.error("TelegramAdapter: Error sending message:", error);
          return { success: false, error: error.message };
        }

      case "startPollingUpdates":
        try {
          if (this.bot.isPolling()) {
            console.log("TelegramAdapter: Polling already active.");
            return { success: true, data: "Polling was already active." };
          }
          this.bot.startPolling({ polling: true }); 
          console.log("TelegramAdapter: Started polling for Telegram updates.");

          this.bot.on("message", async (msg) => {
            console.log("TelegramAdapter: Received message:", msg);
            const chatId = msg.chat.id;
            const inputText = msg.text;

            if (!inputText) {
              console.log("TelegramAdapter: Received message without text, ignoring.");
              return;
            }

            try {
              const preprocessedInput = await inputPreprocessorService.process(inputText, []);
              const orchestrationPayload = {
                request: preprocessedInput.cleaned_prompt,
                original_input: preprocessedInput.original_input,
                structured_data: preprocessedInput.structured_data,
                files: preprocessedInput.files,
                llm: preprocessedInput.llm_used || "claude-3-sonnet", 
                agent: "builder-judge", 
                metadata: { source: "telegram", chatId: chatId, userId: msg.from.id }
              };

              const orchestrationResult = await orchestrationService.processCommand(orchestrationPayload);

              if (orchestrationResult && orchestrationResult.output) {
                await this.bot.sendMessage(chatId, orchestrationResult.output);
              } else {
                await this.bot.sendMessage(chatId, "Sorry, I encountered an issue processing your request.");
              }
            } catch (processingError) {
              console.error("TelegramAdapter: Error processing incoming message through MCP:", processingError);
              await this.bot.sendMessage(chatId, "Sorry, there was an error processing your message.");
            }
          });

          this.bot.on("polling_error", (error) => {
            console.error("TelegramAdapter: Polling error:", error.code, error.message);
          });

          return { success: true, data: "Started polling for Telegram updates." };
        } catch (error) {
          console.error("TelegramAdapter: Error starting polling:", error);
          return { success: false, error: error.message };
        }

      default:
        return { success: false, error: `Unknown action: ${action} for TelegramAdapter.` };
    }
  }
}

module.exports = TelegramAdapter;


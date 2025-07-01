require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");
const serveStatic = require("serve-static");
const mcpRoutes = require("./routes/mcpRoutes");
const mcpBrokerService = require("./services/mcpBrokerService");
const orchestrationService = require("./services/orchestrationService"); // Import orchestrationService

// Import all adapters
const GetzepAdapter = require("./adapters/getzepAdapter");
const FirecrawlAdapter = require("./adapters/firecrawlAdapter");
const StagehandAdapter = require("./adapters/stagehandAdapter");
const ChromaAdapter = require("./adapters/chromaAdapter");
const CliAdapter = require("./adapters/cliAdapter");
const GithubAdapter = require("./adapters/githubAdapter");
const JupyterAdapter = require("./adapters/jupyterAdapter");
const PythonAdapter = require("./adapters/pythonAdapter");
const SchedulerAdapter = require("./adapters/schedulerAdapter");
const EmailAdapter = require("./adapters/emailAdapter");
const NotionAdapter = require("./adapters/notionAdapter"); // Import NotionAdapter

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Initialize and Register adapters on startup
const adaptersToRegister = [
  new GetzepAdapter(),
  new FirecrawlAdapter(),
  new StagehandAdapter(),
  new ChromaAdapter(),
  new CliAdapter(),
  new GithubAdapter(),
  new JupyterAdapter(),
  new PythonAdapter(),
  new SchedulerAdapter(orchestrationService),
  new EmailAdapter(),
  new NotionAdapter() // Add NotionAdapter instance
];

async function initializeAndRegisterAdapters() {
  for (const adapter of adaptersToRegister) {
    try {
      if (typeof adapter.initialize === "function") {
        await adapter.initialize(); // Call initialize if it exists
      }
      mcpBrokerService.registerAdapter(adapter);
    } catch (error) {
      console.error(`Error initializing or registering adapter ${adapter.name || adapter.id}:`, error);
    }
  }
}

initializeAndRegisterAdapters();

// Mount MCP API routes
app.use("/api/mcp", mcpRoutes);

// --- Serve Frontend Static Files using serve-static ---
const frontendBuildPath = path.resolve(__dirname, "../../frontend/dist");

app.use(serveStatic(frontendBuildPath, { index: ["index.html"] }));

// --- End Serve Frontend ---

const server = app.listen(port, () => {
  console.log(`MCP Broker backend listening on port ${port}`);
});

// Graceful shutdown for adapters that need it (like Scheduler)
const gracefulShutdown = async () => {
  console.log("\nGracefully shutting down...");
  for (const adapter of adaptersToRegister) {
    if (typeof adapter.shutdown === "function") {
      try {
        await adapter.shutdown();
      } catch (e) {
        console.error(`Error during shutdown for adapter ${adapter.name || adapter.id}:`, e);
      }
    }
  }
  server.close(() => {
    console.log("Server closed.");
    process.exit(0);
  });

  // Force close server after 5 seconds if it hasn't closed yet
  setTimeout(() => {
    console.error("Could not close connections in time, forcefully shutting down");
    process.exit(1);
  }, 5000);
};

process.on("SIGTERM", gracefulShutdown);
process.on("SIGINT", gracefulShutdown);


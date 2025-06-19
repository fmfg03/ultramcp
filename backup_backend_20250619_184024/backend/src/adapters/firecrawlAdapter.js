const BaseMCPAdapter = require("./baseMCPAdapter");
const { FirecrawlApp } = require("@mendable/firecrawl-js");

const FIRECRAWL_API_KEY = process.env.FIRECRAWL_API_KEY; // Load from env

class FirecrawlAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    if (!FIRECRAWL_API_KEY) {
      console.warn("FirecrawlAdapter: FIRECRAWL_API_KEY is not set. Adapter might not function correctly.");
      this.client = null;
    } else {
      try {
        // Initialize the FirecrawlApp from the SDK
        this.client = new FirecrawlApp({ apiKey: FIRECRAWL_API_KEY });
        console.log("FirecrawlAdapter: Initialized with API Key.");
      } catch (error) {
        console.error("FirecrawlAdapter: Failed to initialize client:", error);
        this.client = null;
      }
    }
  }

  getId() {
    return "firecrawl";
  }

  async getTools() {
    // Updated tool definitions based on SDK/API docs
    return [
      {
        id: `${this.getId()}/scrapeUrl`,
        name: "Scrape URL",
        description: "Scrapes a single URL and returns the content in specified formats (default: markdown).",
        parameters: {
          type: "object",
          properties: {
            url: { type: "string", description: "The URL to scrape." },
            formats: { type: "array", items: { type: "string" }, description: "Desired output formats (e.g., [\"markdown\", \"html\"]).", default: ["markdown"] },
            pageOptions: { type: "object", description: "Options like screenshot, onlyMainContent.", default: {} },
            jsonOptions: { type: "object", description: "Options for LLM extraction (mode, prompt, schema).", default: {} },
            actions: { type: "array", items: { type: "object" }, description: "Actions to perform before scraping (click, wait, etc.).", default: [] }
          },
          required: ["url"],
        },
      },
      {
        id: `${this.getId()}/crawlUrl`,
        name: "Crawl URL",
        description: "Initiates a crawl job for a website starting from a URL. Returns a job ID.",
        parameters: {
          type: "object",
          properties: {
            url: { type: "string", description: "The starting URL to crawl." },
            limit: { type: "integer", description: "Maximum number of pages to crawl.", default: 10 },
            scrapeOptions: { type: "object", description: "Scraping options to apply to each crawled page (e.g., formats).", default: { formats: ["markdown"] } },
            crawlerOptions: { type: "object", description: "Options for the crawler (e.g., excludes, maxDepth).", default: {} }
          },
          required: ["url"],
        },
      },
      // Added tool to check crawl status
      {
        id: `${this.getId()}/checkCrawlStatus`,
        name: "Check Crawl Status",
        description: "Checks the status and retrieves results of a previously submitted crawl job.",
        parameters: {
          type: "object",
          properties: {
            jobId: { type: "string", description: "The ID of the crawl job to check." }
          },
          required: ["jobId"],
        },
      },
    ];
  }

  // Updated signature: removed 'action' parameter
  async executeAction(toolId, params) { 
    if (!this.client) {
      throw new Error("Firecrawl client is not initialized. Check FIRECRAWL_API_KEY.");
    }

    // Check params directly
    if (!params) {
        throw new Error("Missing parameters for Firecrawl action.");
    }

    const toolName = toolId.split("/")[1]; // Extract tool name like 'scrapeUrl'
    console.log(`FirecrawlAdapter executing: ${toolId} with params:`, params);

    try {
      let response;
      switch (toolName) {
        case "scrapeUrl":
          const { url, ...scrapeParams } = params;
          if (!url) throw new Error("Missing required parameter: url");
          // Use the SDK's scrapeUrl method
          response = await this.client.scrapeUrl(url, scrapeParams);
          // The SDK returns the data object directly
          return { success: true, data: response }; 

        case "crawlUrl":
          const { url: crawlUrl, ...crawlParams } = params;
          if (!crawlUrl) throw new Error("Missing required parameter: url");
          // Use the SDK's crawlUrl method
          // Note: SDK might handle async differently, check SDK docs if needed. Assuming it returns job ID directly.
          response = await this.client.crawlUrl(crawlUrl, crawlParams);
          // The SDK returns the job ID object
          return { success: true, ...response }; 

        case "checkCrawlStatus":
          const { jobId } = params;
          if (!jobId) throw new Error("Missing required parameter: jobId");
          // Use the SDK's checkCrawlStatus method
          response = await this.client.checkCrawlStatus(jobId);
          // The SDK returns the status/data object
          return { success: true, ...response };

        default:
          throw new Error(`Unknown tool/action: ${toolId}`);
      }
    } catch (error) {
      console.error(`FirecrawlAdapter Error executing ${toolId}:`, error.response?.data || error.message);
      // Attempt to extract a more specific error message if available
      const errorMessage = error.response?.data?.error || error.message || "Unknown error";
      throw new Error(`Failed to execute Firecrawl action ${toolId}: ${errorMessage}`);
    }
  }
}

module.exports = FirecrawlAdapter;


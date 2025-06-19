const BaseMCPAdapter = require("./baseMCPAdapter");
// const FirecrawlApp = require("@mendable/firecrawl-js").default; // No longer directly used
// const { ZepClient, Document } = require("@getzep/zep-js"); // No longer directly used
require("dotenv").config({ path: "../../.env" });

class EmbeddingSearchAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    this.mcpBroker = config.mcpBroker;
    if (!this.mcpBroker) {
      console.warn("EmbeddingSearchAdapter: mcpBroker not provided. Adapter will not be able to execute sub-tasks (Firecrawl, Zep).");
      this.logError("mcpBroker not provided during initialization.");
    }
    this.logInfo("EmbeddingSearchAdapter initialized.");
  }

  getId() {
    return "embedding_search"; // Corrected ID to match routing logic
  }

  getTools() {
    return [
      {
        name: "ingest_document", // Changed from id to name for consistency with other adapters
        description: "Ingests a document (from URL or text) into the Zep embedding store. Uses Firecrawl for URL scraping.",
        input_schema: {
          type: "object",
          properties: {
            url: { type: "string", description: "URL of the document to ingest." },
            text: { type: "string", description: "Text content to ingest directly." },
            document_id: { type: "string", description: "Optional unique ID for the document." },
            collection_name: {type: "string", description: "Name of the Zep collection to ingest into.", default: "default_collection"}
          },
          // Requires at least one of url or text
        }
      },
      {
        name: "search_documents", // Changed from id to name
        description: "Queries the Zep embedding store for semantically similar documents.",
        input_schema: {
          type: "object",
          properties: {
            query: { type: "string", description: "The search query." },
            collection_name: {type: "string", description: "Name of the Zep collection to query.", default: "default_collection"},
            top_k: { type: "number", description: "Number of results to return.", default: 5 }
          },
          required: ["query"]
        }
      }
    ];
  }

  _chunkText(text, chunkSize = 1000, overlap = 100) {
    const chunks = [];
    let i = 0;
    while (i < text.length) {
      chunks.push(text.substring(i, i + chunkSize));
      i += chunkSize - overlap;
      if (i + overlap >= text.length && i < text.length) {
        chunks.push(text.substring(i));
        break;
      }
    }
    return chunks.filter(chunk => chunk.trim() !== "");
  }

  async executeAction(toolName, params) {
    this.logInfo(`Executing action: ${toolName} with params: ${JSON.stringify(params)}`);
    if (!this.mcpBroker) {
      const errorMsg = "EmbeddingSearchAdapter: mcpBroker not available. Cannot execute action.";
      this.logError(errorMsg);
      return { success: false, error: errorMsg };
    }

    const collection_name = params.collection_name || "default_collection";

    if (toolName === "ingest_document") {
      const { url, text, document_id } = params;
      let contentToProcess = text;
      let source = document_id || (text ? "direct_text_input" : url);

      if (!url && !text) {
        const errorMsg = "Either url or text must be provided for ingestion.";
        this.logError(errorMsg);
        return { success: false, error: errorMsg };
      }

      if (url) {
        try {
          this.logInfo(`Scraping URL via mcpBroker: ${url}`);
          const scrapeResult = await this.mcpBroker.executeTool("firecrawl/scrapeUrl", { url });
          if (scrapeResult && scrapeResult.success && scrapeResult.data && scrapeResult.data.markdown) {
            contentToProcess = scrapeResult.data.markdown;
            source = url;
            this.logInfo(`URL scraped successfully. Content length: ${contentToProcess.length}`);
          } else {
            const errorMsg = `Failed to scrape content from URL: ${url}. Firecrawl result: ${JSON.stringify(scrapeResult)}`;
            this.logError(errorMsg, scrapeResult);
            return { success: false, error: errorMsg, details: scrapeResult };
          }
        } catch (error) {
          const errorMsg = `Error scraping URL ${url} via mcpBroker: ${error.message}`;
          this.logError(errorMsg, error);
          return { success: false, error: errorMsg };
        }
      }

      if (!contentToProcess) {
        const errorMsg = "No content to process for ingestion after attempting scrape/text input.";
        this.logError(errorMsg);
        return { success: false, error: errorMsg };
      }

      try {
        this.logInfo(`Chunking text for collection '${collection_name}'. Source: ${source}`);
        const chunks = this._chunkText(contentToProcess);
        if (chunks.length === 0) {
          this.logInfo("No content to chunk after processing.");
          return { success: true, message: "No content to chunk after processing.", document_id: source };
        }

        const zepDocuments = chunks.map((chunk, index) => ({
          document_id: document_id ? `${document_id}_${index}` : `${source}_chunk_${index}`,
          content: chunk,
          metadata: { source: source, original_document_id: document_id || source }
        }));
        
        this.logInfo(`Adding ${zepDocuments.length} document chunks to Zep collection '${collection_name}' via mcpBroker.`);
        const zepAddResult = await this.mcpBroker.executeTool("zep/add_documents", {
          collectionName: collection_name,
          documents: zepDocuments
        });

        if (zepAddResult && zepAddResult.success) {
          this.logInfo(`Successfully ingested ${zepDocuments.length} chunks into Zep.`);
          return {
            success: true,
            message: `Successfully ingested ${zepDocuments.length} chunks from ${source} into Zep collection '${collection_name}'.`,
            document_id: document_id || source,
            chunks_count: zepDocuments.length,
            zep_response: zepAddResult
          };
        } else {
          const errorMsg = `Failed to add documents to Zep. Result: ${JSON.stringify(zepAddResult)}`;
          this.logError(errorMsg, zepAddResult);
          return { success: false, error: errorMsg, details: zepAddResult };
        }
      } catch (error) {
        const errorMsg = `Error ingesting document into Zep via mcpBroker: ${error.message}`;
        this.logError(errorMsg, error);
        return { success: false, error: errorMsg };
      }
    }

    if (toolName === "search_documents") {
      const { query, top_k = 5 } = params;
      this.logInfo(`Executing Zep search for "${query}" in collection '${collection_name}' (top_k: ${top_k}) via mcpBroker.`);
      try {
        const zepSearchResult = await this.mcpBroker.executeTool("zep/search_documents", {
          collectionName: collection_name,
          query: query,
          limit: top_k
        });

        if (zepSearchResult && zepSearchResult.success) {
          this.logInfo(`Zep search successful. Found ${zepSearchResult.results ? zepSearchResult.results.length : 0} results.`);
          return {
            success: true,
            query: query,
            results: zepSearchResult.results || [],
            zep_response: zepSearchResult
          };
        } else {
          const errorMsg = `Zep search failed. Result: ${JSON.stringify(zepSearchResult)}`;
          this.logError(errorMsg, zepSearchResult);
          return { success: false, error: errorMsg, details: zepSearchResult };
        }
      } catch (error) {
        const errorMsg = `Error querying Zep via mcpBroker: ${error.message}`;
        this.logError(errorMsg, error);
        return { success: false, error: errorMsg };
      }
    }

    const unknownToolMsg = `EmbeddingSearchAdapter: Unknown toolName: ${toolName}`;
    this.logError(unknownToolMsg);
    return { success: false, error: unknownToolMsg };
  }
}

module.exports = EmbeddingSearchAdapter;


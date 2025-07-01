const BaseMCPAdapter = require("./baseMCPAdapter");
const { ChromaClient } = require("chromadb");

class ChromaAdapter extends BaseMCPAdapter {
  constructor(config = {}) {
    super(config);
    this.chromaUrl = process.env.CHROMA_URL || config.chromaUrl;
    if (!this.chromaUrl) {
      console.warn("ChromaAdapter: CHROMA_URL is not set. Adapter will likely fail.");
      this.client = null;
    } else {
      try {
        this.client = new ChromaClient({ path: this.chromaUrl });
        console.log(`ChromaAdapter: Initialized with URL: ${this.chromaUrl}`);
      } catch (error) {
        console.error(`ChromaAdapter: Failed to initialize client with URL ${this.chromaUrl}:`, error);
        this.client = null;
      }
    }
  }

  getId() {
    return "chroma";
  }

  async getTools() {
    // Tool definitions remain the same as before
    return [
      {
        id: `${this.getId()}/add_vector`,
        name: "Add Vector (Chroma)",
        description: "Adds a vector embedding and associated metadata to a Chroma collection.",
        parameters: {
          type: "object",
          properties: {
            collection: { type: "string", description: "The target collection name." },
            // Changed vector to embeddings to match Chroma API, but kept description similar
            embeddings: { type: "array", items: { type: "array", items: { type: "number" } }, description: "The vector embedding(s). Array of arrays." },
            metadatas: { type: "array", items: { type: "object" }, description: "Associated metadata object(s). Array of objects." },
            ids: { type: "array", items: { type: "string" }, description: "Unique ID(s) for the entries. Array of strings." }
          },
          required: ["collection", "embeddings", "metadatas", "ids"]
        },
      },
      {
        id: `${this.getId()}/search_vector`,
        name: "Search Vector (Chroma)",
        description: "Performs a semantic search for similar vectors in a Chroma collection.",
        parameters: {
          type: "object",
          properties: {
            collection: { type: "string", description: "The target collection name." },
            // Changed query_vector to query_embeddings
            query_embeddings: { type: "array", items: { type: "array", items: { type: "number" } }, description: "The query vector embedding(s). Array of arrays." },
            // Changed k to n_results
            n_results: { type: "integer", description: "Number of nearest neighbors to return.", default: 2 },
            where: { type: "object", description: "Optional metadata filter." },
            where_document: { type: "object", description: "Optional document content filter." }
          },
          required: ["collection", "query_embeddings"]
        },
      }
    ];
  }

  // Updated signature: removed 'action' parameter
  async executeAction(toolId, params) { 
    if (!this.client) {
      throw new Error("ChromaAdapter client is not initialized. Check CHROMA_URL.");
    }
    console.log(`ChromaAdapter executing: ${toolId} with params:`, params);

    // Check params directly
    if (!params) {
        throw new Error("Missing parameters for Chroma action.");
    }

    const collectionName = params.collection;
    if (!collectionName) {
      throw new Error("Missing required parameter: collection");
    }

    try {
      // Get or create collection - necessary for both add and query in case it doesn't exist for query
      // Note: getOrCreateCollection might be better for add, getCollection for query, but this simplifies
      const collection = await this.client.getOrCreateCollection({ name: collectionName });

      if (toolId === `${this.getId()}/add_vector`) {
        const { ids, embeddings, metadatas } = params;
        if (!ids || !embeddings || !metadatas) {
          throw new Error("Missing required parameters for add_vector: ids, embeddings, metadatas");
        }
        // Ensure parameters are arrays as expected by Chroma client
        const addParams = {
            ids: Array.isArray(ids) ? ids : [ids],
            embeddings: Array.isArray(embeddings[0]) ? embeddings : [embeddings], // Chroma expects array of embeddings
            metadatas: Array.isArray(metadatas) ? metadatas : [metadatas],
        };
        const result = await collection.add(addParams);
        console.log("Chroma add result:", result); // Chroma add usually returns void or true on success
        return { success: true, message: `Vector(s) added to Chroma collection '${collectionName}'.`, result: result };

      } else if (toolId === `${this.getId()}/search_vector`) {
        const { query_embeddings, n_results = 2, where, where_document } = params;
        if (!query_embeddings) {
          throw new Error("Missing required parameter for search_vector: query_embeddings");
        }
        // Ensure query_embeddings is an array of embeddings
        const queryParams = {
            queryEmbeddings: Array.isArray(query_embeddings[0]) ? query_embeddings : [query_embeddings],
            nResults: n_results,
            ...(where && { where }),
            ...(where_document && { whereDocument: where_document }),
        };

        const results = await collection.query(queryParams);
        return { success: true, message: `Vector search executed in Chroma collection '${collectionName}'.`, results: results };
      }
      
      throw new Error(`Tool ${toolId} not supported by ChromaAdapter.`);

    } catch (error) {
      console.error(`ChromaAdapter error executing ${toolId}:`, error);
      throw new Error(`ChromaAdapter failed to execute ${toolId}: ${error.message}`);
    }
  }
}

module.exports = ChromaAdapter;


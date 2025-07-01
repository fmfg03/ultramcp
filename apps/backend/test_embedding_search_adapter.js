require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });
const EmbeddingSearchAdapter = require("./src/adapters/EmbeddingSearchAdapter.js");
const mcpBrokerService = require("./src/services/mcpBrokerService.js"); // Needed if adapter uses it internally, or for mocking

// Mocking mcpBrokerService for Firecrawl and Zep interactions
const mockMcpBrokerService = {
    executeTool: async (toolName, params) => {
        console.log(`Mock MCPBroker: executeTool called with ${toolName}, params: ${JSON.stringify(params)}`);
        if (toolName === "firecrawl/scrapeUrl") {
            if (!params.url) return { success: false, error: "URL is required for scrapeUrl" };
            return {
                success: true,
                data: {
                    content: `Mocked scraped content for ${params.url}. This is a test document. It contains various keywords like apple, banana, and orange. The quick brown fox jumps over the lazy dog.`,
                    markdown: `# Mocked Scraped Content for ${params.url}\nThis is a test document. It contains various keywords like apple, banana, and orange. The quick brown fox jumps over the lazy dog.`,
                    metadata: { title: `Mock Title for ${params.url}`, sourceURL: params.url }
                },
                logs: [`Mock Firecrawl: Scraped ${params.url}`]
            };
        }
        if (toolName === "zep/add_documents") {
            if (!params.collectionName || !params.documents || params.documents.length === 0) {
                return { success: false, error: "collectionName and documents are required for add_documents" };
            }
            return {
                success: true,
                message: `${params.documents.length} documents added to Zep collection ${params.collectionName} (mocked).`,
                failed_documents: [],
                logs: [`Mock Zep: Added ${params.documents.length} documents to ${params.collectionName}`]
            };
        }
        if (toolName === "zep/search_documents") {
            if (!params.collectionName || !params.query) {
                return { success: false, error: "collectionName and query are required for search_documents" };
            }
            return {
                success: true,
                results: [
                    { document_id: "doc1", content: "Mock search result 1 related to " + params.query, score: 0.9, metadata: { sourceURL: "http://mock.doc/1" } },
                    { document_id: "doc2", content: "Another mock result for " + params.query, score: 0.85, metadata: { sourceURL: "http://mock.doc/2" } }
                ],
                logs: [`Mock Zep: Searched collection ${params.collectionName} for query \"${params.query}\"`]
            };
        }
        return { success: false, error: `Mock MCPBroker: Tool ${toolName} not recognized or mock not implemented` };
    }
};

async function testEmbeddingSearchAdapter() {
    console.log("Testing EmbeddingSearchAdapter...");
    
    const adapter = new EmbeddingSearchAdapter({ mcpBroker: mockMcpBrokerService });
    let allTestsPassed = true;

    // Test Case 1: Ingest Document
    console.log("\n--- Test Case 1: Ingest Document ---");
    const ingestParams = { url: "https://example.com/test-page", collection_name: "test_collection" };
    try {
        const ingestResult = await adapter.executeAction("ingest_document", ingestParams);
        console.log("Ingest Result:", JSON.stringify(ingestResult, null, 2));
        if (ingestResult && ingestResult.success === true && ingestResult.message && ingestResult.message.includes("Successfully ingested")) {
            console.log("PASS: Ingest document test.");
        } else {
            console.error("FAIL: Ingest document test. Unexpected result:", ingestResult);
            allTestsPassed = false;
        }
    } catch (error) {
        console.error("ERROR during ingest document test:", error);
        allTestsPassed = false;
    }

    // Test Case 2: Search Documents
    console.log("\n--- Test Case 2: Search Documents ---");
    const searchParams = { query: "apple banana", collection_name: "test_collection", top_k: 2 };
    try {
        const searchResult = await adapter.executeAction("search_documents", searchParams);
        console.log("Search Result:", JSON.stringify(searchResult, null, 2));
        if (searchResult && searchResult.success === true && searchResult.results && searchResult.results.length > 0) {
            console.log(`PASS: Search documents test. Found ${searchResult.results.length} results.`);
        } else {
            console.error("FAIL: Search documents test. No results or error:", searchResult);
            allTestsPassed = false;
        }
    } catch (error) {
        console.error("ERROR during search documents test:", error);
        allTestsPassed = false;
    }

    // Test Case 3: Ingest Document - Missing URL/Text
    console.log("\n--- Test Case 3: Ingest Document - Missing URL/Text ---");
    const ingestParamsError = { collection_name: "test_collection_error" }; // No url or text
    try {
        const ingestResultError = await adapter.executeAction("ingest_document", ingestParamsError);
        console.log("Ingest Error Result:", JSON.stringify(ingestResultError, null, 2));
        if (ingestResultError && ingestResultError.success === false && ingestResultError.error && ingestResultError.error.includes("Either url or text must be provided")) {
            console.log("PASS: Ingest document missing URL/text error test.");
        } else {
            console.error("FAIL: Ingest document missing URL/text error test. Unexpected result:", ingestResultError);
            allTestsPassed = false;
        }
    } catch (error) {
        console.error("ERROR during ingest document missing URL/text error test:", error);
        allTestsPassed = false;
    }
    
    // Test Case 4: Search Documents - Missing Query
    console.log("\n--- Test Case 4: Search Documents - Missing Query ---");
    const searchParamsError = { collection_name: "test_collection_error" }; // No query
    try {
        const searchResultError = await adapter.executeAction("search_documents", searchParamsError);
        console.log("Search Error Result:", JSON.stringify(searchResultError, null, 2));
        // The error comes from the mock broker in this case
        if (searchResultError && searchResultError.success === false && searchResultError.details && searchResultError.details.error && searchResultError.details.error.includes("query are required")) {
            console.log("PASS: Search documents missing query error test.");
        } else {
            console.error("FAIL: Search documents missing query error test. Unexpected result:", searchResultError);
            allTestsPassed = false;
        }
    } catch (error) {
        console.error("ERROR during search documents missing query error test:", error);
        allTestsPassed = false;
    }

    console.log("\n-----------------------------------------");
    if (allTestsPassed) {
        console.log("All EmbeddingSearchAdapter tests PASSED!");
    } else {
        console.error("Some EmbeddingSearchAdapter tests FAILED.");
    }
    console.log("-----------------------------------------");
}

testEmbeddingSearchAdapter();


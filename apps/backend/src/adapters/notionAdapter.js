const { Client } = require("@notionhq/client");
const BaseMCPAdapter = require("./baseMCPAdapter");

class NotionAdapter extends BaseMCPAdapter {
    constructor() {
        super();
        this.id = "notion";
        this.name = "Notion Adapter";
        this.description = "Interacts with Notion workspaces, pages, and databases.";
        this.tools = [
            {
                id: "notion/get_page_content",
                name: "Get Notion Page Content",
                description: "Retrieves the content (blocks) of a Notion page.",
                params: [
                    { name: "page_id", type: "string", required: true, description: "The ID of the Notion page." }
                ]
            },
            {
                id: "notion/create_page",
                name: "Create Notion Page",
                description: "Creates a new page in Notion.",
                params: [
                    { name: "parent_page_id", type: "string", required: false, description: "The ID of the parent page. If not provided, creates a top-level page in authorized workspace." },
                    { name: "parent_database_id", type: "string", required: false, description: "The ID of the parent database. If provided, parent_page_id is ignored." },
                    { name: "title", type: "string", required: true, description: "The title of the new page." },
                    { name: "properties", type: "object", required: false, description: "Object of page properties (for database pages)." },
                    { name: "children_blocks", type: "array", required: false, description: "Array of Notion block objects for the page content." }
                ]
            },
            {
                id: "notion/append_block_children",
                name: "Append Block Children to Page/Block",
                description: "Appends new block children to a Notion page or an existing block.",
                params: [
                    { name: "block_id", type: "string", required: true, description: "The ID of the block (page or other block) to append children to." },
                    { name: "children_blocks", type: "array", required: true, description: "Array of Notion block objects to append." }
                ]
            },
            {
                id: "notion/query_database",
                name: "Query Notion Database",
                description: "Queries a Notion database based on filter criteria.",
                params: [
                    { name: "database_id", type: "string", required: true, description: "The ID of the Notion database." },
                    { name: "filter", type: "object", required: false, description: "Notion API filter object." },
                    { name: "sorts", type: "array", required: false, description: "Notion API sorts array." }
                ]
            }
        ];

        this.notion = null;
        this.notionApiKey = process.env.NOTION_API_KEY;
    }

    getId() {
        return this.id;
    }

    async initialize() {
        if (this.notionApiKey) {
            this.notion = new Client({ auth: this.notionApiKey });
            console.log("NotionAdapter: Initialized with API key.");
        } else {
            console.warn("NotionAdapter: NOTION_API_KEY is not set. Adapter will not function.");
        }
        return Promise.resolve();
    }

    async executeAction(toolId, params) {
        if (!this.notion) {
            return { success: false, error: "NotionAdapter: Not initialized. NOTION_API_KEY is missing." };
        }

        console.log(`[NotionAdapter] executeAction called with toolId: ${toolId}, params:`, JSON.stringify(params, null, 2));
        const actualToolName = toolId.split("/")[1];

        try {
            switch (actualToolName) {
                case "get_page_content":
                    return await this.getPageContent(params);
                case "create_page":
                    return await this.createPage(params);
                case "append_block_children":
                    return await this.appendBlockChildren(params);
                case "query_database":
                    return await this.queryDatabase(params);
                default:
                    return { success: false, error: `Unsupported tool: ${toolId}` };
            }
        } catch (error) {
            console.error(`[NotionAdapter] Error executing ${toolId}:`, error);
            return { success: false, error: error.message, details: error.code || error.body };
        }
    }

    async getPageContent(params) {
        const { page_id } = params;
        if (!page_id) return { success: false, error: "Missing page_id parameter." };
        
        const response = await this.notion.blocks.children.list({ block_id: page_id });
        return { success: true, data: response };
    }

    async createPage(params) {
        const { parent_page_id, parent_database_id, title, properties, children_blocks } = params;
        if (!title) return { success: false, error: "Missing title parameter." };
        if (!parent_page_id && !parent_database_id) return { success: false, error: "Either parent_page_id or parent_database_id must be provided." };

        const pageArgs = {
            parent: {},
            properties: {
                title: [{ type: "text", text: { content: title } }]
            },
        };

        if (parent_database_id) {
            pageArgs.parent.database_id = parent_database_id;
            // For database pages, title is a property, not a top-level key
            pageArgs.properties = { ...properties, ...{ [Object.keys(properties).find(k => properties[k].type === 'title') || 'title']: { title: [{ type: "text", text: { content: title } }] } } };
        } else {
            pageArgs.parent.page_id = parent_page_id;
        }

        if (children_blocks && Array.isArray(children_blocks)) {
            pageArgs.children = children_blocks;
        }

        const response = await this.notion.pages.create(pageArgs);
        return { success: true, data: response };
    }

    async appendBlockChildren(params) {
        const { block_id, children_blocks } = params;
        if (!block_id || !children_blocks || !Array.isArray(children_blocks)) {
            return { success: false, error: "Missing or invalid block_id or children_blocks parameters." };
        }
        const response = await this.notion.blocks.children.append({
            block_id: block_id,
            children: children_blocks,
        });
        return { success: true, data: response };
    }

    async queryDatabase(params) {
        const { database_id, filter, sorts } = params;
        if (!database_id) return { success: false, error: "Missing database_id parameter." };

        const queryArgs = { database_id: database_id };
        if (filter) queryArgs.filter = filter;
        if (sorts) queryArgs.sorts = sorts;

        const response = await this.notion.databases.query(queryArgs);
        return { success: true, data: response };
    }

    async shutdown() {
        console.log("NotionAdapter: Shutting down.");
        return Promise.resolve();
    }
}

module.exports = NotionAdapter;


# Notion Adapter Design

## 1. Overview

The Notion Adapter will enable the MCP Broker to interact with Notion workspaces. This allows workflows to read from and write to Notion pages and databases, effectively using Notion as an operational data store, task manager, or documentation hub for automated processes.

## 2. Tools Exposed

The adapter will expose the following tools, focusing on common database and page interactions:

*   **`create_database_page`**: Creates a new page (entry) in a specified Notion database.
*   **`update_database_page_properties`**: Updates specific properties of an existing page in a database.
*   **`query_database`**: Retrieves pages from a database based on filters and sorts.
*   **`retrieve_page_content`**: Retrieves the block content of a specific page.
*   **`append_block_children`**: Appends new content blocks to a page or an existing block.
*   **`retrieve_block_children`**: Retrieves the children of a block.

## 3. Tool Parameters and Functionality

### 3.1. `create_database_page`

*   **Description**: Creates a new item (page) in a specified Notion database.
*   **Parameters**:
    *   `database_id` (string, required): The ID of the target Notion database.
    *   `properties` (object, required): An object defining the properties of the new page, conforming to Notion API's property value object structure. Example: `{"Name": {"title": [{"text": {"content": "New Task"}}]}, "Status": {"select": {"name": "To Do"}}}`.
*   **Functionality**:
    1.  Uses the Notion SDK's `client.pages.create()` method.
    2.  The `parent` will be `{ database_id: params.database_id }`.
*   **Returns**: `{ success: true, page_id: "new_page_id", message: "Page created successfully." }` or `{ success: false, error: "Error message" }`.

### 3.2. `update_database_page_properties`

*   **Description**: Updates the properties of an existing page within a database.
*   **Parameters**:
    *   `page_id` (string, required): The ID of the Notion page to update.
    *   `properties` (object, required): An object defining the properties to update, same format as in `create_database_page`.
*   **Functionality**:
    1.  Uses the Notion SDK's `client.pages.update()` method.
*   **Returns**: `{ success: true, page_id: "updated_page_id", message: "Page properties updated successfully." }` or `{ success: false, error: "Error message" }`.

### 3.3. `query_database`

*   **Description**: Queries a Notion database for pages matching specified filters and sorts.
*   **Parameters**:
    *   `database_id` (string, required): The ID of the database to query.
    *   `filter` (object, optional): A Notion API filter object. Example: `{"property": "Status", "select": {"equals": "In Progress"}}`.
    *   `sorts` (array of objects, optional): A Notion API sorts array. Example: `[{"property": "Last Edited", "direction": "descending"}]`.
    *   `page_size` (number, optional, default: 100): Number of results to return.
    *   `start_cursor` (string, optional): For pagination.
*   **Functionality**:
    1.  Uses the Notion SDK's `client.databases.query()` method.
*   **Returns**: `{ success: true, results: [pageObject1, ...], next_cursor: "cursor_string_or_null", has_more: boolean }` or `{ success: false, error: "Error message" }`.

### 3.4. `retrieve_page_content` (Simplified to retrieve block children of a page)

*   **Description**: Retrieves all block children for a given page ID.
*   **Parameters**:
    *   `page_id` (string, required): The ID of the page whose content (blocks) is to be retrieved.
*   **Functionality**:
    1.  This is essentially a wrapper around `retrieve_block_children` where the `block_id` is the `page_id`.
    2.  Uses `client.blocks.children.list({ block_id: params.page_id })`.
*   **Returns**: `{ success: true, blocks: [blockObject1, ...], next_cursor: "cursor_string_or_null", has_more: boolean }` or `{ success: false, error: "Error message" }`.

### 3.5. `append_block_children`

*   **Description**: Appends new content blocks to a specified parent block (which can be a page ID).
*   **Parameters**:
    *   `block_id` (string, required): The ID of the parent block (or page) to append to.
    *   `children` (array of objects, required): An array of Notion block objects to append. Example: `[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "This is a new paragraph."}}]}}]`.
*   **Functionality**:
    1.  Uses the Notion SDK's `client.blocks.children.append()` method.
*   **Returns**: `{ success: true, results: [appendedBlockObject1, ...], message: "Blocks appended successfully." }` or `{ success: false, error: "Error message" }`.

### 3.6. `retrieve_block_children`

*   **Description**: Retrieves the children of a specific block.
*   **Parameters**:
    *   `block_id` (string, required): The ID of the block whose children are to be retrieved.
    *   `page_size` (number, optional, default: 100): Number of results to return.
    *   `start_cursor` (string, optional): For pagination.
*   **Functionality**:
    1.  Uses the Notion SDK's `client.blocks.children.list()` method.
*   **Returns**: `{ success: true, results: [blockObject1, ...], next_cursor: "cursor_string_or_null", has_more: boolean }` or `{ success: false, error: "Error message" }`.

## 4. Configuration (Environment Variables)

*   `NOTION_API_KEY` (string, required): The Notion integration token (Internal Integration Token).
*   (Optional) `NOTION_DEFAULT_DATABASE_ID_TASKS` (string): A default database ID for common task logging, could be used by orchestration logic if no specific DB ID is provided for certain high-level actions.
*   (Optional) `NOTION_DEFAULT_DATABASE_ID_LOGS` (string): A default database ID for general logging.

## 5. Libraries

*   `@notionhq/client`: The official JavaScript SDK for the Notion API.

## 6. Security Considerations

*   **API Key Protection**: The `NOTION_API_KEY` is sensitive and must be stored securely as an environment variable.
*   **Permissions**: The Notion integration token will have specific permissions granted to it within the Notion workspace (e.g., access to certain pages/databases). Ensure the token has the minimum necessary permissions for the adapter's intended operations.
*   **Data Privacy**: Be mindful of the data being read from or written to Notion, especially if it contains PII or sensitive business information. The MCP Broker's access and logging should respect data privacy principles.
*   **Input Validation**: While the Notion API handles its own validation, the adapter should ensure that parameters like `database_id` and `page_id` are in the correct format if possible before making API calls to provide clearer error messages.

## 7. Adapter Structure (Conceptual)

```javascript
// notionAdapter.js
const { Client } = require("@notionhq/client");
const BaseMCPAdapter = require("./baseMCPAdapter");

class NotionAdapter extends BaseMCPAdapter {
    constructor() {
        super();
        this.id = "notion";
        this.name = "Notion";
        this.description = "Interacts with Notion pages and databases.";
        this.tools = [
            // Tool definitions as per section 3
        ];
        this.notion = null;
    }

    async initialize() {
        if (process.env.NOTION_API_KEY) {
            this.notion = new Client({ auth: process.env.NOTION_API_KEY });
            console.log("NotionAdapter: Initialized with API key.");
        } else {
            console.warn("NotionAdapter: NOTION_API_KEY not set. Adapter will not function.");
        }
    }

    async executeAction(toolId, action, params) {
        if (!this.notion) {
            throw new Error("NotionAdapter not initialized. Check NOTION_API_KEY.");
        }
        const actualToolName = toolId.split("/")[1];

        switch (actualToolName) {
            case "create_database_page":
                return this.createDatabasePage(params);
            case "update_database_page_properties":
                return this.updateDatabasePageProperties(params);
            case "query_database":
                return this.queryDatabase(params);
            case "retrieve_page_content": // essentially retrieve_block_children for a page
                return this.retrieveBlockChildren({ block_id: params.page_id, page_size: params.page_size, start_cursor: params.start_cursor });
            case "append_block_children":
                return this.appendBlockChildren(params);
            case "retrieve_block_children":
                return this.retrieveBlockChildren(params);
            default:
                throw new Error(`Unsupported tool: ${toolId}`);
        }
    }

    async createDatabasePage(params) { /* ... use this.notion.pages.create ... */ }
    async updateDatabasePageProperties(params) { /* ... use this.notion.pages.update ... */ }
    async queryDatabase(params) { /* ... use this.notion.databases.query ... */ }
    async appendBlockChildren(params) { /* ... use this.notion.blocks.children.append ... */ }
    async retrieveBlockChildren(params) { /* ... use this.notion.blocks.children.list ... */ }
}

module.exports = NotionAdapter;
```

## 8. Dependencies

*   `@notionhq/client`

This design provides a comprehensive set of tools for interacting with Notion. The use cases like "Log today’s execution results" would typically use `create_database_page` to add an entry to a log database. "Update my Focus Mode" could involve updating a page property in a personal task database using `update_database_page_properties` or appending a block to a journal page using `append_block_children`.

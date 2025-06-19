# Changelog

## [0.3.0] - 2025-05-09

### Added
- **Real Tool Orchestration in `orchestrationService.js`:**
  - Refactored `orchestrationService.js` to call `mcpBrokerService.executeTool(toolId, params)` for actual tool execution, replacing placeholder logic.
  - Integrated `firecrawlAdapter.js` as the first example of a real tool being orchestrated for the `builder-judge` agent workflow.
  - Implemented dynamic import of `credentialsService.js` within `orchestrationService.js` to handle mixed CommonJS and ES Module environments.
- **Credential Injection:**
  - `orchestrationService.js` now attempts to fetch credentials (e.g., `firecrawl/apiKey`) using `credentialsService.getCredential(service, key)` before tool execution.
  - Logs a warning if a required credential is not found.
- **Debug Logging for Adapters:**
  - Introduced `DEBUG_MCP_ADAPTER_LOGGING` environment variable (in `.env` and `.env.example`).
  - When `DEBUG_MCP_ADAPTER_LOGGING=true`, `orchestrationService.js` provides more verbose logging within the `trace` field of the API response, aiding in adapter development and troubleshooting.
- **Adapter Registration in `server.cjs`:**
  - Modified `server.cjs` to explicitly import and register tool adapters (e.g., `FirecrawlAdapter`) with the `mcpBrokerService` instance upon server startup.

### Changed
- **`orchestrationService.js`:**
  - Major refactor to support real tool calls, credential injection, and enhanced trace logging.
  - Updated to use dynamic `import()` for `credentialsService.js`.
- **`.env.example`:** Added `DEBUG_MCP_ADAPTER_LOGGING` variable.
- **`server.cjs`:** Added adapter registration logic for `mcpBrokerService`.

### Fixed
- **Credential Service Import Path:** Corrected the dynamic import path for `credentialsService.js` in `orchestrationService.js`.
- **Adapter Registration:** Ensured `FirecrawlAdapter` (and potentially others from the unzipped files) is correctly registered with `mcpBrokerService` in `server.cjs`, resolving "Adapter not found" errors.
- **Supabase Initialization:** Updated `.env` with actual Supabase credentials provided by the user, resolving "Invalid URL" errors during server startup.
- **Server Startup Script:** Consistently used `server.cjs` (instead of `server.js`) when starting the backend server.
- **`logController.js` Syntax Error:** Corrected an invalid `const` declaration.

## [0.2.0] - 2025-05-09

### Added
- **Frontend Command Console:**
  - Implemented a React-based Command Console UI (`/frontend`) with TailwindCSS and Lucide-React icons.
  - Features include a command input area, response display section, and a command history panel.
  - Integrated frontend with backend API endpoints for sending commands and fetching/displaying history.
  - Added loading states and basic error display for API interactions.
- **Backend API & Services:**
  - Developed an Express.js backend server (`/backend/src/server.cjs`).
  - Created API endpoint `POST /api/orchestrate` to receive commands, process them via `orchestrationService.js` (with placeholder logic for `builder-judge` and `ideators` agent types), and return JSON responses.
  - Created API endpoints `POST /api/logs` and `GET /api/logs` for saving and retrieving command history.
  - Implemented `orchestrateController.js` and `logController.js` to handle API request logic.
  - Implemented `logService.cjs` to interact with Supabase for storing and fetching command logs.
- **Supabase Integration for Logging:**
  - Defined schema for `command_logs` table in Supabase to store command, response, timestamp, user, LLM, and agent details.
  - Created SQL script (`/backend/src/database/create_command_logs_table.sql`) for table creation.
  - Developed a Node.js script (`/backend/src/database/setup_database.js`) to execute the SQL schema (requires a manual `execute_sql_statement` helper function in Supabase).
  - Updated `supabaseClient.cjs` for Supabase connection.
- **Documentation:**
  - Significantly updated `README.md` with details on new features, setup instructions, usage guide (including secure credential management, workflow scheduling, log viewing/debugging, workflow type differences), "MCP Ready" badge, and known limitations/TODOs.

### Changed
- **Backend Module System:**
  - Refactored multiple backend JavaScript files (e.g., `server.js`, `api.js`, `supabaseClient.js`, `logService.js`, controller files) to use the `.cjs` extension and CommonJS module syntax (`require`/`module.exports`) to resolve ES Module compatibility issues with the project's `type: "module"` setting in `package.json`.
  - Updated all internal `require` paths in the backend to correctly point to the renamed `.cjs` files.
- **README.md:** Overhauled to reflect the new command console system and incorporate user-requested documentation points.

### Fixed
- **Backend Server Startup:**
  - Resolved `ReferenceError: require is not defined` by converting backend files to CommonJS (`.cjs`).
  - Fixed `Error: Cannot find module` issues by installing missing dependencies (`express`, `cors`) in the backend project.
  - Corrected import paths after renaming files to `.cjs`.
- **Supabase Client Usage:** Ensured all services correctly import and use the `supabaseClient.cjs` module.

## [0.1.0] - (Previous Version Date from original file if available, otherwise estimate)

### Added
- Implemented Supabase adapter (`src/adapters/supabaseAdapter.js`) with singleton client, table setup (credentials, scheduled_jobs), and CRUD operations (createRecord, getRecord, updateRecord, deleteRecord, listRecords).
- Implemented Credentials Service (`src/services/credentialsService.js`) for secure storage and retrieval of encrypted credentials using AES encryption and Supabase backend.
- Added JSDoc comments to all functions in `supabaseAdapter.js`.
- Developed unit tests for `supabaseAdapter.js` and `credentialsService.js` using Jest, mocking dependencies like `@supabase/supabase-js` and `crypto-js`.
- Created `.env.example` file with required environment variables: `SUPABASE_URL`, `SUPABASE_KEY`, `CRED_ENCRYPTION_KEY`.
- Configured `package.json` and `babel.config.js` for ES Module support with Jest testing.
- Created comprehensive `README.md` detailing features, setup, usage examples, and testing for both the Supabase adapter and Credentials Service.

### Changed
- Refactored `supabaseAdapter.js` to use a singleton pattern for the Supabase client (`getSupabaseClient()`) to improve testability and ensure a single client instance.
- Updated `credentialsService.js` to use `getSupabaseClient()` from the adapter.
- Corrected mocking strategies in test files (`tests/supabaseAdapter.test.js`, `tests/credentialsService.test.js`) to accurately reflect the adapter and service implementations, ensuring all tests pass.

### Fixed
- Resolved various Jest testing issues related to ES Modules, mock implementations, and environment variable handling.
- Fixed an issue in `supabaseAdapter.test.js` where a template literal for an error message was not correctly formatted.


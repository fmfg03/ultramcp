# Scheduler Adapter Design (Native with node-cron)

## 1. Overview

The Scheduler Adapter will provide native scheduling capabilities within the MCP Broker backend. It will allow users to schedule workflows (which are processed by the `orchestrationService.js`) to run at specific times or intervals using cron expressions. This adapter will use the `node-cron` library for managing and executing scheduled jobs.

## 2. Tools Exposed

The adapter will expose the following tools:

*   **`schedule_workflow`**: Schedules a new workflow execution.
*   **`list_scheduled_jobs`**: Lists all currently scheduled jobs.
*   **`unschedule_job`**: Removes a previously scheduled job.
*   **`get_job_details`**: Retrieves details for a specific scheduled job.

## 3. Tool Parameters and Functionality

### 3.1. `schedule_workflow`

*   **Description**: Schedules a workflow to be executed based on a cron expression.
*   **Parameters**:
    *   `job_id` (string, required): A unique identifier for the job. Users can provide this, or the system can generate one if not provided. Must be unique.
    *   `cron_string` (string, required): A valid cron expression (e.g., "0 9 * * *" for 9 AM daily).
    *   `workflow_request` (object, required): The request object to be sent to the `/api/mcp/orchestrate` endpoint. This typically includes a `request` field with the natural language instruction for the workflow (e.g., `{"request": "Send me a daily summary via email"}`).
    *   `description` (string, optional): A human-readable description for the scheduled job.
*   **Functionality**:
    1.  Validate the `cron_string`.
    2.  Ensure `job_id` is unique if provided, or generate a unique ID.
    3.  Store the job details (job_id, cron_string, workflow_request, description).
    4.  Use `node-cron` to schedule a task. The task, when triggered, will:
        *   Log the job execution start.
        *   Call the `orchestrationService.runOrchestration(workflow_request)`.
        *   Log the result (success or failure) of the orchestration.
        *   (Future) Potentially send a notification or log to a persistent store about the execution status.
*   **Returns**: `{ success: true, job_id: "generated_or_provided_id", message: "Workflow scheduled successfully." }` or `{ success: false, error: "Error message" }`.

### 3.2. `list_scheduled_jobs`

*   **Description**: Lists all currently active scheduled jobs.
*   **Parameters**: None.
*   **Functionality**: Retrieve and return a list of all stored job details (job_id, cron_string, workflow_request description, next_run_time (if available from cron instance)).
*   **Returns**: `{ success: true, jobs: [{ job_id, cron_string, workflow_request, description, next_run_time }, ...] }` or `{ success: false, error: "Error message" }`.

### 3.3. `unschedule_job`

*   **Description**: Stops and removes a scheduled job.
*   **Parameters**:
    *   `job_id` (string, required): The ID of the job to unschedule.
*   **Functionality**:
    1.  Find the job by `job_id`.
    2.  Stop the `node-cron` task associated with the job.
    3.  Remove the job details from storage.
*   **Returns**: `{ success: true, message: "Job unscheduled successfully." }` or `{ success: false, error: "Job not found or error unscheduling." }`.

### 3.4. `get_job_details`

*   **Description**: Retrieves details for a specific scheduled job.
*   **Parameters**:
    *   `job_id` (string, required): The ID of the job.
*   **Functionality**: Retrieve and return the details of the specified job.
*   **Returns**: `{ success: true, job: { job_id, cron_string, workflow_request, description, next_run_time } }` or `{ success: false, error: "Job not found." }`.

## 4. Job Management and Persistence

*   **In-Memory Storage (Initial)**: Initially, scheduled jobs and their `node-cron` instances will be managed in memory within the adapter. This means jobs will be lost if the backend server restarts.
    *   A simple object or Map can store job definitions: `{[job_id]: { cron_string, workflow_request, description, cron_task_instance }}`.
*   **Job IDs**: Must be unique. The adapter should enforce this.
*   **`node-cron` Integration**: The `node-cron` library will be used. Each scheduled job will have a corresponding `cron.ScheduledTask` instance. The `schedule_workflow` tool will create these, and `unschedule_job` will call their `stop()` method and remove them.
*   **Error Handling**: The adapter should handle errors gracefully, such as invalid cron strings or issues with starting/stopping jobs.
*   **Execution Context**: When a scheduled job triggers, it will execute the `orchestrationService.runOrchestration` function. The adapter needs access to this service.

## 5. Future Considerations (Out of Scope for Initial Design)

*   **Persistent Job Storage**: For jobs to survive server restarts, they would need to be stored persistently (e.g., in a JSON file, a simple database like SQLite, or a more robust DB). On server startup, the adapter would need to read these jobs and reschedule them with `node-cron`.
*   **Job Execution History/Logs**: Storing a history of job executions (start time, end time, status, output/error) would be valuable for monitoring and debugging.
*   **Concurrency Management**: If workflows can be long-running, consider how to manage concurrent executions if a job is scheduled to run very frequently.
*   **Security**: Ensure that the `workflow_request` payload is handled securely, as it dictates what the orchestration service will attempt to do.

## 6. Adapter Structure (Conceptual)

```javascript
// schedulerAdapter.js
const cron = require("node-cron");
const { v4: uuidv4 } = require("uuid");
const BaseMCPAdapter = require("./baseMCPAdapter");
// Presumed access to orchestrationService, potentially via dependency injection or a global/service locator pattern
// const orchestrationService = require("../services/orchestrationService");

class SchedulerAdapter extends BaseMCPAdapter {
    constructor(orchestrationService) {
        super();
        this.id = "scheduler";
        this.name = "Scheduler";
        this.description = "Schedules and manages workflow executions.";
        this.tools = [
            // Tool definitions as per section 3
        ];
        this.scheduledJobs = new Map(); // In-memory store: job_id -> { cron_string, workflow_request, description, cron_task_instance }
        this.orchestrationService = orchestrationService; // Passed in constructor
    }

    async initialize() {
        console.log("SchedulerAdapter: Initialized. Native scheduling enabled.");
        // If implementing persistence, load and reschedule jobs here
    }

    async executeAction(toolId, action, params) { // Adapting to current mcpBrokerService structure
        // Current mcpBrokerService calls executeAction(toolId, action, params)
        // but for this adapter, action is implied by toolId (e.g. scheduler/schedule_workflow)
        // So, we can map toolId directly to methods.
        const actualToolName = toolId.split('/')[1];

        switch (actualToolName) {
            case "schedule_workflow":
                return this.scheduleWorkflow(params);
            case "list_scheduled_jobs":
                return this.listScheduledJobs(params);
            case "unschedule_job":
                return this.unscheduleJob(params);
            case "get_job_details":
                return this.getJobDetails(params);
            default:
                throw new Error(`Unsupported tool: ${toolId}`);
        }
    }

    async scheduleWorkflow(params) { /* ... */ }
    async listScheduledJobs(params) { /* ... */ }
    async unscheduleJob(params) { /* ... */ }
    async getJobDetails(params) { /* ... */ }

    // Helper to stop all jobs on shutdown (if needed)
    async shutdown() {
        this.scheduledJobs.forEach(job => job.cron_task_instance.stop());
        console.log("SchedulerAdapter: All scheduled jobs stopped.");
    }
}

module.exports = SchedulerAdapter;
```

## 7. Dependencies

*   `node-cron`: For cron job scheduling.
*   `uuid`: For generating unique job IDs if not provided by the user.

This design provides a foundation for the native Scheduler Adapter. The next step would be to implement this logic.

const cron = require("node-cron");
const { v4: uuidv4 } = require("uuid");
const fs = require("fs");
const path = require("path");
const BaseMCPAdapter = require("./baseMCPAdapter");

const JOBS_FILE_PATH = path.join(__dirname, "..", "..", "scheduled_jobs.json"); // Store in backend root

class SchedulerAdapter extends BaseMCPAdapter {
    constructor(orchestrationService) {
        super();
        this.id = "scheduler";
        this.name = "Scheduler";
        this.description = "Schedules and manages workflow executions using node-cron with persistence.";
        this.tools = [
            {
                id: "scheduler/schedule_workflow",
                name: "Schedule Workflow",
                description: "Schedules a workflow to be executed based on a cron expression.",
                params: [
                    { name: "name", type: "string", required: true, description: "A unique name for the job (will be used as job_id)." },
                    { name: "cron", type: "string", required: true, description: "A valid cron expression (e.g., \"0 9 * * *\")." },
                    { name: "workflow", type: "string", required: true, description: "Type of workflow for orchestration (e.g., 'orchestrate', 'builderJudge', 'ideation'). Passed as hint to orchestrator." },
                    { name: "params", type: "object", required: true, description: "Parameters/details for the task to be executed by the orchestrator." },
                    { name: "description", type: "string", required: false, description: "A human-readable description for the job." }
                ]
            },
            {
                id: "scheduler/list_scheduled_jobs",
                name: "List Scheduled Jobs",
                description: "Lists all currently active scheduled jobs.",
                params: []
            },
            {
                id: "scheduler/unschedule_job",
                name: "Unschedule Job",
                description: "Stops and removes a scheduled job.",
                params: [
                    { name: "job_id", type: "string", required: true, description: "The ID (name) of the job to unschedule." }
                ]
            },
            {
                id: "scheduler/get_job_details",
                name: "Get Job Details",
                description: "Retrieves details for a specific scheduled job.",
                params: [
                    { name: "job_id", type: "string", required: true, description: "The ID (name) of the job." }
                ]
            }
        ];
        this.scheduledJobs = new Map(); 
        if (!orchestrationService) {
            console.warn("SchedulerAdapter: OrchestrationService not provided! Scheduled jobs will not be able to execute workflows.");
        }
        this.orchestrationService = orchestrationService;
    }

    getId() {
        return this.id;
    }

    async initialize() {
        console.log("SchedulerAdapter: Initializing with persistence...");
        this._loadJobsFromFile();
        return Promise.resolve();
    }

    _saveJobsToFile() {
        const jobsToSave = [];
        for (const jobData of this.scheduledJobs.values()) {
            const { cronTaskInstance, ...serializableJobData } = jobData;
            jobsToSave.push(serializableJobData);
        }
        try {
            fs.writeFileSync(JOBS_FILE_PATH, JSON.stringify(jobsToSave, null, 2));
            console.log(`SchedulerAdapter: ${jobsToSave.length} jobs saved to ${JOBS_FILE_PATH}`);
        } catch (error) {
            console.error("SchedulerAdapter: Error saving jobs to file:", error);
        }
    }

    _loadJobsFromFile() {
        try {
            if (fs.existsSync(JOBS_FILE_PATH)) {
                const data = fs.readFileSync(JOBS_FILE_PATH, "utf8");
                const loadedJobs = JSON.parse(data);
                let reScheduledCount = 0;
                for (const job of loadedJobs) {
                    if (job.jobId && job.cronString && job.workflowRequestDetails) {
                        this._rescheduleJob(job.jobId, job.cronString, job.workflowRequestDetails, job.description, false);
                        reScheduledCount++;
                    }
                }
                console.log(`SchedulerAdapter: Loaded and re-scheduled ${reScheduledCount} jobs from ${JOBS_FILE_PATH}`);
            } else {
                console.log(`SchedulerAdapter: No jobs file found at ${JOBS_FILE_PATH}. Starting with an empty schedule.`);
            }
        } catch (error) {
            console.error("SchedulerAdapter: Error loading jobs from file:", error);
        }
    }

    _rescheduleJob(job_id, cron_string, workflow_request_details, description, saveToFile = true) {
         if (!this.orchestrationService) {
            console.warn(`SchedulerAdapter: OrchestrationService not available. Cannot reschedule job ${job_id}.`);
            return { success: false, error: "OrchestrationService not available. Cannot reschedule job." };
        }
        // Validation is now implicitly handled by cron.schedule() throwing an error for invalid patterns

        try {
            const task = cron.schedule(cron_string, async () => {
                console.log(`SchedulerAdapter: Executing job '${job_id}': ${description || 'No description'}`);
                
                const taskDefinitionObj = workflow_request_details.task_definition;
                const workflowTypeHintStr = workflow_request_details.workflow_type_hint;

                let requestString = `Execute scheduled task '${description || job_id}'.`;
                if (taskDefinitionObj && Object.keys(taskDefinitionObj).length > 0) {
                    requestString += ` Details: ${JSON.stringify(taskDefinitionObj)}`;
                }
                console.log(`SchedulerAdapter: Triggering workflow with request string: "${requestString}", hint: "${workflowTypeHintStr}"`);

                try {
                    const result = await this.orchestrationService.runOrchestration(requestString, workflowTypeHintStr);
                    console.log(`SchedulerAdapter: Job '${job_id}' workflow execution result:`, result);
                } catch (e) {
                    console.error(`SchedulerAdapter: Error executing workflow for job '${job_id}':`, e);
                }
            });

            const jobData = {
                jobId: job_id,
                cronString: cron_string,
                workflowRequestDetails: workflow_request_details,
                description: description || '',
                cronTaskInstance: task,
            };
            this.scheduledJobs.set(job_id, jobData);
            console.log(`SchedulerAdapter: Job '${job_id}' re-scheduled: ${description || 'No description'}`);
            if (saveToFile) {
                this._saveJobsToFile();
            }
            return { success: true, job_id: job_id };
        } catch (error) {
            // This catch block will now handle invalid cron strings from cron.schedule()
            console.error(`SchedulerAdapter: Error re-scheduling job '${job_id}':`, error);
            return { success: false, error: `Failed to re-schedule job: ${error.message}` }; // error.message will contain cron pattern error
        }
    }

    async executeAction(toolId, receivedParams) {
        console.log(`[SchedulerAdapter] executeAction called with toolId: ${toolId}, receivedParams:`, JSON.stringify(receivedParams, null, 2));
        const actualToolName = toolId.split("/")[1];

        if (!this.orchestrationService && actualToolName === "schedule_workflow") {
             return { success: false, error: "OrchestrationService not available. Cannot schedule workflows." };
        }

        switch (actualToolName) {
            case "schedule_workflow":
                return this.scheduleWorkflow(receivedParams);
            case "list_scheduled_jobs":
                return this.listScheduledJobs();
            case "unschedule_job":
                return this.unscheduleJob(receivedParams);
            case "get_job_details":
                return this.getJobDetails(receivedParams);
            default:
                return { success: false, error: `Unsupported tool: ${toolId}` };
        }
    }

    async scheduleWorkflow(externalParams) {
        console.log("[SchedulerAdapter] scheduleWorkflow called with externalParams:", JSON.stringify(externalParams, null, 2));
        if (!externalParams) return { success: false, error: "Parameters object is undefined in scheduleWorkflow." };

        const { name, cron, workflow, params, description } = externalParams;
        
        const job_id_to_use = name;
        const cron_string_to_use = cron;
        const description_to_use = description;
        const stored_workflow_config = { 
            task_definition: params,
            workflow_type_hint: workflow
        };

        if (!job_id_to_use) {
            return { success: false, error: "Missing 'name' (job_id) parameter." };
        }
        // Removed explicit cron.validate check here, as _rescheduleJob's try-catch will handle it.
        if (!cron_string_to_use) {
             return { success: false, error: "Missing 'cron' string parameter." };
        }
        if (typeof stored_workflow_config.task_definition !== 'object' || stored_workflow_config.task_definition === null) {
            return { success: false, error: "Invalid 'params' format. It must be an object." };
        }
        if (typeof stored_workflow_config.workflow_type_hint !== 'string') {
            return { success: false, error: "Invalid 'workflow' format. It must be a string." };
        }

        if (this.scheduledJobs.has(job_id_to_use)) {
            return { success: false, error: `Job with ID (name) '${job_id_to_use}' already exists.` };
        }
        
        const result = this._rescheduleJob(job_id_to_use, cron_string_to_use, stored_workflow_config, description_to_use, true);
        if (result.success) {
            return { success: true, job_id: job_id_to_use, message: "Workflow scheduled successfully." };
        } else {
            return result; 
        }
    }

    async listScheduledJobs() {
        const jobsList = [];
        for (const [jobId, jobData] of this.scheduledJobs.entries()) {
            let nextRunTime = 'N/A';
            try {
                if (jobData.cronTaskInstance && typeof jobData.cronTaskInstance.nextDates === 'function') {
                    const nextDates = jobData.cronTaskInstance.nextDates(1);
                    if (nextDates.length > 0) nextRunTime = nextDates[0].toString();
                } else if (jobData.cronTaskInstance && typeof jobData.cronTaskInstance.nextDate === 'function') {
                     nextRunTime = jobData.cronTaskInstance.nextDate().toString();
                }
            } catch (e) { console.warn(`SchedulerAdapter: Could not retrieve next run time for job ${jobId}`, e.message); }
            jobsList.push({
                job_id: jobId,
                cron_string: jobData.cronString,
                workflow_request_details: jobData.workflowRequestDetails,
                description: jobData.description,
                next_run_time: nextRunTime
            });
        }
        return { success: true, jobs: jobsList };
    }

    async unscheduleJob(params) {
        console.log("[SchedulerAdapter] unscheduleJob called with params:", JSON.stringify(params, null, 2));
        const { job_id } = params;
        if (!job_id) return { success: false, error: "job_id (name) is required." };
        const jobData = this.scheduledJobs.get(job_id);
        if (!jobData) return { success: false, error: `Job with ID (name) '${job_id}' not found.` };

        try {
            jobData.cronTaskInstance.stop();
            this.scheduledJobs.delete(job_id);
            this._saveJobsToFile(); 
            console.log(`SchedulerAdapter: Job '${job_id}' unscheduled and stopped.`);
            return { success: true, message: "Job unscheduled successfully." };
        } catch (error) {
            console.error(`SchedulerAdapter: Error unscheduling job '${job_id}':`, error);
            return { success: false, error: `Failed to unschedule job: ${error.message}` };
        }
    }

    async getJobDetails(params) {
        console.log("[SchedulerAdapter] getJobDetails called with params:", JSON.stringify(params, null, 2));
        const { job_id } = params;
        if (!job_id) return { success: false, error: "job_id (name) is required." };
        const jobData = this.scheduledJobs.get(job_id);
        if (!jobData) return { success: false, error: `Job with ID (name) '${job_id}' not found.` };
        let nextRunTime = 'N/A';
         try {
            if (jobData.cronTaskInstance && typeof jobData.cronTaskInstance.nextDates === 'function') {
                const nextDates = jobData.cronTaskInstance.nextDates(1);
                if (nextDates.length > 0) nextRunTime = nextDates[0].toString();
            } else if (jobData.cronTaskInstance && typeof jobData.cronTaskInstance.nextDate === 'function') {
                    nextRunTime = jobData.cronTaskInstance.nextDate().toString();
            }
        } catch (e) { console.warn(`SchedulerAdapter: Could not retrieve next run time for job ${job_id}`, e.message); }

        return {
            success: true,
            job: {
                job_id: jobData.jobId,
                cron_string: jobData.cronString,
                workflow_request_details: jobData.workflowRequestDetails,
                description: jobData.description,
                next_run_time: nextRunTime
            }
        };
    }

    async shutdown() {
        console.log("SchedulerAdapter: Shutting down. Stopping all scheduled jobs...");
        for (const [jobId, jobData] of this.scheduledJobs.entries()) {
            try {
                jobData.cronTaskInstance.stop();
                console.log(`SchedulerAdapter: Job '${jobId}' stopped.`);
            } catch (e) {
                console.error(`SchedulerAdapter: Error stopping job '${jobId}' during shutdown:`, e);
            }
        }
        this.scheduledJobs.clear();
        console.log("SchedulerAdapter: All jobs stopped and cleared from memory.");
    }
}

module.exports = SchedulerAdapter;


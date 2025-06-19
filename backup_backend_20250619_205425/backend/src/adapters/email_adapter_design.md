# Email Adapter Design (Send + Parse)

## 1. Overview

The Email Adapter will provide capabilities to send emails and, where feasible, parse incoming emails to trigger or inform workflows within the MCP Broker backend. It aims to integrate email as a key input/output channel for automated operations.

## 2. Tools Exposed

The adapter will expose the following tools:

*   **`send_email`**: Sends an email.
*   **`setup_email_webhook`** (Conceptual for receiving/parsing): Configures a webhook endpoint for an external email service to forward parsed email data. (Actual implementation depends on chosen service and may require manual setup by user outside the adapter initially).
*   **`process_incoming_email`** (Internal, triggered by webhook): Processes data from an email received via a webhook.

**Note on Parsing/Receiving Emails:**
Directly accessing user mailboxes (via IMAP/POP3 or Gmail API) for parsing presents significant security and configuration challenges (OAuth2, credential management). A more robust and secure approach for applications to "receive" emails is via webhook integrations with services like Mailgun, SendGrid, or Postmark, which handle the email reception and initial parsing, then forward structured data to a pre-defined HTTP endpoint.

This design will focus on `nodemailer` for sending and outline the webhook approach for receiving/parsing, acknowledging that the receiving part might be more of a guideline for integration rather than a fully automated setup within the adapter itself initially.

## 3. Tool Parameters and Functionality

### 3.1. `send_email`

*   **Description**: Sends an email using a configured email transport (e.g., SMTP, Mailgun API).
*   **Parameters**:
    *   `to` (string or array of strings, required): Email address(es) of the recipient(s).
    *   `subject` (string, required): Subject line of the email.
    *   `text_body` (string, optional): Plain text content of the email.
    *   `html_body` (string, optional): HTML content of the email. (If both text and HTML are provided, most clients will prefer HTML).
    *   `cc` (string or array of strings, optional): CC recipient(s).
    *   `bcc` (string or array of strings, optional): BCC recipient(s).
    *   `reply_to` (string, optional): Reply-to email address.
    *   `attachments` (array of objects, optional): Files to attach.
        *   Each object: `{ filename: "name.txt", content: "base64_encoded_content_or_path_to_file", contentType: "text/plain" }` (Path to file might be restricted for security).
*   **Functionality**:
    1.  Validate required parameters.
    2.  Construct the email object compatible with `nodemailer`.
    3.  Use the configured `nodemailer` transporter to send the email.
    4.  Log the success or failure of the email sending attempt.
*   **Returns**: `{ success: true, message_id: "provider_message_id", message: "Email sent successfully." }` or `{ success: false, error: "Error message" }`.

### 3.2. `setup_email_webhook` (Conceptual / Informational Tool)

*   **Description**: Provides information and potentially a target URL for configuring an external email service (like Mailgun, SendGrid) to forward incoming emails to the MCP Broker. This tool might not perform direct actions but guide the user.
*   **Parameters**: None, or perhaps a `service_provider` (e.g., "mailgun") to get specific instructions.
*   **Functionality**:
    1.  Explain that for receiving emails, the user needs to configure their email service (e.g., Mailgun) to forward emails for a specific address/domain to a webhook URL provided by this MCP Broker instance.
    2.  The MCP Broker backend will need a dedicated HTTP endpoint (e.g., `/api/mcp/adapters/email/webhook`) to receive these POST requests.
    3.  This tool would return the expected webhook URL: `https://<your_mcp_broker_domain>/api/mcp/adapters/email/webhook`.
*   **Returns**: `{ success: true, webhook_url: "<generated_url>", instructions: "Configure your email provider (e.g., Mailgun) to POST incoming email data to this URL..." }`.

### 3.3. `process_incoming_email` (Internal - Not directly exposed as a user tool)

*   **Description**: This is an internal handler for the webhook. When an external service POSTs email data, this function is triggered.
*   **Triggered by**: HTTP POST request to `/api/mcp/adapters/email/webhook`.
*   **Input**: The structured JSON payload sent by the email service (e.g., Mailgun's parsed email format, which includes sender, recipient, subject, body-plain, body-html, attachments, etc.).
*   **Functionality**:
    1.  Validate the incoming request (e.g., using a secret key shared with the email provider for security).
    2.  Extract relevant information from the payload (sender, subject, body, attachments).
    3.  **Crucially, decide what to do with this parsed email.** This is where the "parse replies to trigger workflows" use case comes in. The adapter itself might not contain complex parsing logic. Instead, it could:
        *   Log the received email data.
        *   Emit an event that other services (like the `orchestrationService`) can listen to.
        *   Potentially, if a specific `workflow_trigger_keyword` is found in the subject or body, it could directly invoke `orchestrationService.runOrchestration` with a predefined request based on the email content.
*   **Returns**: HTTP 200 OK to the email service if processed successfully, or an error code.

## 4. Configuration (Environment Variables)

*   `EMAIL_ADAPTER_PROVIDER` (string, e.g., "smtp", "mailgun", "sendgrid"): Specifies the email sending service.
*   **For SMTP:**
    *   `SMTP_HOST` (string)
    *   `SMTP_PORT` (number)
    *   `SMTP_SECURE` (boolean, true for SSL/TLS)
    *   `SMTP_USER` (string)
    *   `SMTP_PASS` (string)
    *   `EMAIL_FROM_ADDRESS` (string, default sender)
*   **For Mailgun/SendGrid (Sending):**
    *   `MAILGUN_API_KEY` (string) / `SENDGRID_API_KEY` (string)
    *   `MAILGUN_DOMAIN` (string) (if using Mailgun)
    *   `EMAIL_FROM_ADDRESS` (string, default sender)
*   **For Webhook (Receiving):**
    *   `EMAIL_WEBHOOK_SECRET` (string): A secret key to verify incoming webhook requests from the email provider.

## 5. Libraries

*   `nodemailer`: For sending emails. Versatile and supports various transports.
*   Potentially specific SDKs if using API-based sending (e.g., `@mailgun.js`, `@sendgrid/mail`).

## 6. Security Considerations

*   **Credential Protection**: API keys and SMTP credentials must be stored securely (environment variables are a good start).
*   **Input Sanitization (Sending)**: Sanitize `to`, `subject`, and body content if constructed from user inputs to prevent email header injection or other attacks. However, since LLMs might generate these, the primary risk is the LLM generating malicious content.
*   **Webhook Security**: The webhook endpoint for receiving emails must be secured (e.g., using a shared secret, IP whitelisting if possible) to prevent unauthorized POST requests.
*   **Attachment Handling (Sending & Receiving)**: Be cautious with file paths for attachments when sending. For received attachments, scan for malware if they are processed automatically. Ensure content types are handled correctly.
*   **Data Privacy (Receiving)**: Emails can contain sensitive information. Ensure compliance with privacy regulations if storing or processing email content.

## 7. Adapter Structure (Conceptual)

```javascript
// emailAdapter.js
const nodemailer = require("nodemailer");
const BaseMCPAdapter = require("./baseMCPAdapter");

class EmailAdapter extends BaseMCPAdapter {
    constructor() {
        super();
        this.id = "email";
        this.name = "Email";
        this.description = "Sends emails and provides a webhook for receiving/parsing emails.";
        this.tools = [
            { id: "email/send_email", name: "Send Email", description: "...", params: [...] },
            { id: "email/setup_email_webhook", name: "Setup Email Webhook Info", description: "...", params: [] }
        ];
        this.transporter = null; // nodemailer transporter
    }

    async initialize() {
        // Configure nodemailer transporter based on ENV variables
        // (SMTP_HOST, MAILGUN_API_KEY, etc.)
        // Example for SMTP:
        // this.transporter = nodemailer.createTransport({ host, port, secure, auth: { user, pass } });
        console.log("EmailAdapter: Initialized.");
    }

    async executeAction(toolId, action, params) {
        const actualToolName = toolId.split("/")[1];
        switch (actualToolName) {
            case "send_email":
                return this.sendEmail(params);
            case "setup_email_webhook":
                return this.setupEmailWebhookInfo(params);
            default:
                throw new Error(`Unsupported tool: ${toolId}`);
        }
    }

    async sendEmail(params) { /* ... nodemailer logic ... */ }
    async setupEmailWebhookInfo(params) {
        const webhookUrl = `YOUR_MCP_BROKER_PUBLIC_URL/api/mcp/adapters/email/webhook`; // URL needs to be dynamic
        return {
            success: true,
            webhook_url: webhookUrl,
            instructions: `Configure your email provider (e.g., Mailgun, SendGrid) to forward incoming email data via POST to this URL. Ensure to secure the webhook with the EMAIL_WEBHOOK_SECRET if applicable.`
        };
    }

    // This method would be called by an Express route handler for the webhook
    async handleIncomingWebhook(requestBody) {
        // 1. Verify request (e.g., using EMAIL_WEBHOOK_SECRET)
        // 2. Process requestBody (parsed email data)
        // 3. Log, emit event, or trigger orchestrationService.runOrchestration
        console.log("Received email via webhook:", requestBody);
        // Example: Trigger workflow if subject contains [TODO]
        if (requestBody.subject && requestBody.subject.includes("[TODO]")) {
            // const workflowReq = { request: `Process TODO item from email: ${requestBody.subject}` };
            // this.orchestrationService.runOrchestration(workflowReq); // Needs access to orchestrationService
        }
        return { success: true };
    }
}

module.exports = EmailAdapter;
```

## 8. Dependencies

*   `nodemailer`
*   (Optional) SDKs for specific email providers like Mailgun or SendGrid if not using SMTP directly for sending.

This design focuses on a practical approach for sending and a robust (webhook-based) strategy for receiving emails, minimizing direct security burdens on the MCP Broker for email parsing.

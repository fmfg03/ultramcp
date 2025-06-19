const nodemailer = require("nodemailer");
const BaseMCPAdapter = require("./baseMCPAdapter");

class EmailAdapter extends BaseMCPAdapter {
    constructor() {
        super();
        this.id = "email";
        this.name = "Email Adapter";
        this.description = "Handles sending emails and potentially parsing incoming emails.";
        this.tools = [
            {
                id: "email/send_email",
                name: "Send Email",
                description: "Sends an email using a pre-configured SMTP transport.",
                params: [
                    { name: "to", type: "string", required: true, description: "Recipient email address(es), comma-separated for multiple." },
                    { name: "subject", type: "string", required: true, description: "Subject of the email." },
                    { name: "text", type: "string", required: false, description: "Plain text body of the email." },
                    { name: "html", type: "string", required: false, description: "HTML body of the email. If text is also provided, this is preferred by most clients." },
                    { name: "attachments", type: "array", required: false, description: "Array of attachment objects (see nodemailer documentation for format). e.g., [{ filename: \"report.pdf\", path: \"/path/to/report.pdf\" }]" }
                ]
            },
            // Future: email/setup_inbound_webhook (for parsing, more complex)
        ];

        // Transporter configuration should be done via environment variables
        // Example: EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USER, EMAIL_SMTP_PASS, EMAIL_SMTP_SECURE (true/false)
        // EMAIL_FROM_ADDRESS
        this.transporter = null;
        this.fromAddress = process.env.EMAIL_FROM_ADDRESS || "noreply@example.com";
    }

    getId() {
        return this.id;
    }

    async initialize() {
        const host = process.env.EMAIL_SMTP_HOST;
        const port = parseInt(process.env.EMAIL_SMTP_PORT, 10);
        const secure = process.env.EMAIL_SMTP_SECURE === "true"; // true for 465, false for other ports
        const user = process.env.EMAIL_SMTP_USER;
        const pass = process.env.EMAIL_SMTP_PASS;

        if (host && port && user && pass) {
            this.transporter = nodemailer.createTransport({
                host: host,
                port: port,
                secure: secure, 
                auth: {
                    user: user,
                    pass: pass,
                },
            });
            try {
                await this.transporter.verify();
                console.log("EmailAdapter: SMTP transporter configured and verified successfully.");
            } catch (error) {
                console.error("EmailAdapter: SMTP transporter verification failed:", error);
                this.transporter = null; // Disable if verification fails
            }
        } else {
            console.warn("EmailAdapter: SMTP configuration missing (EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USER, EMAIL_SMTP_PASS). Email sending will be disabled.");
        }
        return Promise.resolve();
    }

    async executeAction(toolId, params) {
        console.log(`[EmailAdapter] executeAction called with toolId: ${toolId}, params:`, JSON.stringify(params, null, 2));
        const actualToolName = toolId.split("/")[1];

        switch (actualToolName) {
            case "send_email":
                return this.sendEmail(params);
            default:
                return { success: false, error: `Unsupported tool: ${toolId}` };
        }
    }

    async sendEmail(params) {
        if (!this.transporter) {
            return { success: false, error: "EmailAdapter: SMTP transporter is not configured or failed to initialize. Cannot send email." };
        }

        const { to, subject, text, html, attachments } = params;

        if (!to || !subject || (!text && !html)) {
            return { success: false, error: "Missing required parameters for sending email (to, subject, and text or html body)." };
        }

        const mailOptions = {
            from: this.fromAddress, // sender address
            to: to, // list of receivers
            subject: subject, // Subject line
            text: text, // plain text body
            html: html, // html body
            attachments: attachments // array of attachment objects
        };

        try {
            const info = await this.transporter.sendMail(mailOptions);
            console.log("EmailAdapter: Message sent: %s", info.messageId);
            return { success: true, messageId: info.messageId, response: info.response, message: "Email sent successfully." };
        } catch (error) {
            console.error("EmailAdapter: Error sending email:", error);
            return { success: false, error: `Failed to send email: ${error.message}` };
        }
    }

    async shutdown() {
        console.log("EmailAdapter: Shutting down.");
        if (this.transporter) {
            // Nodemailer transporters don't typically need explicit closing unless using pooled connections in a specific way.
            // For simple SMTP, there's often no explicit close method or it's handled internally.
        }
        return Promise.resolve();
    }
}

module.exports = EmailAdapter;


"""
Email Adapter - Handles email notifications and communications
"""

import asyncio
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class EmailAdapter:
    """Adapter for email notifications and communications"""
    
    def __init__(self):
        self.is_initialized = False
        self.smtp_config = {}
        self.email_templates = {}
        self.sent_emails = []
        
    async def initialize(self):
        """Initialize email adapter"""
        try:
            await self._load_smtp_config()
            await self._load_email_templates()
            await self._test_smtp_connection()
            self.is_initialized = True
            logger.info("✅ Email adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize email adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("EmailAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock email adapter")
    
    async def _load_smtp_config(self):
        """Load SMTP configuration"""
        self.smtp_config = {
            "host": os.getenv("SMTP_HOST", "localhost"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() == "true",
            "from_email": os.getenv("SMTP_FROM_EMAIL", "noreply@ultramcp.com"),
            "from_name": os.getenv("SMTP_FROM_NAME", "UltraMCP Actions Service")
        }
    
    async def _load_email_templates(self):
        """Load email templates"""
        self.email_templates = {
            "default": {
                "subject": "{subject}",
                "html": """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{subject}</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .header { background-color: #f4f4f4; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
                        .button { display: inline-block; padding: 10px 20px; background-color: #007cba; color: white; text-decoration: none; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>UltraMCP Actions Service</h2>
                    </div>
                    <div class="content">
                        <p>{message}</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message from UltraMCP Actions Service</p>
                        <p>Sent at: {timestamp}</p>
                    </div>
                </body>
                </html>
                """,
                "text": """
                UltraMCP Actions Service
                ========================
                
                {message}
                
                ---
                This is an automated message from UltraMCP Actions Service
                Sent at: {timestamp}
                """
            },
            "escalation": {
                "subject": "{urgency_indicator} {subject}",
                "html": """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{subject}</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .header { background-color: #ff4444; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .urgency-high { border-left: 5px solid #ff4444; padding-left: 15px; }
                        .urgency-critical { border-left: 5px solid #cc0000; padding-left: 15px; background-color: #fff5f5; }
                        .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
                        .action-button { display: inline-block; padding: 12px 24px; background-color: #ff4444; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>🚨 ESCALATION REQUIRED</h2>
                    </div>
                    <div class="content">
                        <div class="urgency-{urgency}">
                            <h3>Context: {context}</h3>
                            <p><strong>Urgency:</strong> {urgency}</p>
                            <p><strong>Escalated by:</strong> {escalated_by}</p>
                            <p><strong>Time:</strong> {timestamp}</p>
                            
                            {additional_details}
                            
                            <p style="margin-top: 20px;">
                                <a href="{tracking_url}" class="action-button">View Escalation Details</a>
                            </p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>This escalation requires immediate attention</p>
                        <p>UltraMCP Actions Service</p>
                    </div>
                </body>
                </html>
                """
            },
            "approval": {
                "subject": "📋 Approval Required: {action_description}",
                "html": """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Approval Required</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .header { background-color: #007cba; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .approval-box { border: 2px solid #007cba; padding: 15px; margin: 15px 0; border-radius: 5px; }
                        .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
                        .approve-button { display: inline-block; padding: 12px 24px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin-right: 10px; }
                        .reject-button { display: inline-block; padding: 12px 24px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>📋 Approval Request</h2>
                    </div>
                    <div class="content">
                        <div class="approval-box">
                            <h3>Action: {action_description}</h3>
                            <p><strong>Requested by:</strong> {requester}</p>
                            <p><strong>Justification:</strong> {justification}</p>
                            <p><strong>Impact Assessment:</strong> {impact_assessment}</p>
                            <p><strong>Deadline:</strong> {deadline}</p>
                            <p><strong>Expires:</strong> {expires_at}</p>
                            
                            <div style="margin-top: 20px;">
                                <a href="{approval_url}&action=approve" class="approve-button">✅ Approve</a>
                                <a href="{approval_url}&action=reject" class="reject-button">❌ Reject</a>
                            </div>
                            
                            <p style="margin-top: 15px;">
                                <small><a href="{approval_url}">View full details and provide comments</a></small>
                            </p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>This approval request expires at: {expires_at}</p>
                        <p>UltraMCP Actions Service</p>
                    </div>
                </body>
                </html>
                """
            },
            "notification": {
                "subject": "{subject}",
                "html": """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{subject}</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .header { background-color: #28a745; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .notification-box { border-left: 5px solid #28a745; padding-left: 15px; margin: 15px 0; }
                        .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>📢 Notification</h2>
                    </div>
                    <div class="content">
                        <div class="notification-box">
                            {message}
                        </div>
                    </div>
                    <div class="footer">
                        <p>UltraMCP Actions Service</p>
                        <p>Sent at: {timestamp}</p>
                    </div>
                </body>
                </html>
                """
            }
        }
    
    async def _test_smtp_connection(self):
        """Test SMTP connection"""
        if not self.smtp_config["username"]:
            logger.info("ℹ️ No SMTP credentials configured, skipping connection test")
            return
        
        try:
            # Test connection without sending email
            if self.smtp_config["use_ssl"]:
                server = smtplib.SMTP_SSL(self.smtp_config["host"], self.smtp_config["port"])
            else:
                server = smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"])
                if self.smtp_config["use_tls"]:
                    server.starttls()
            
            if self.smtp_config["username"]:
                server.login(self.smtp_config["username"], self.smtp_config["password"])
            
            server.quit()
            logger.info("✅ SMTP connection test successful")
            
        except Exception as e:
            logger.warning(f"⚠️ SMTP connection test failed: {e}")
            raise
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "send_email":
            return await self._send_email(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _send_email(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification"""
        
        # Extract email parameters
        recipients = input_data.get("recipients", [])
        subject = input_data.get("subject", "")
        template = input_data.get("template", "default")
        data = input_data.get("data", {})
        priority = input_data.get("priority", "normal")
        attachments = input_data.get("attachments", [])
        cc = input_data.get("cc", [])
        bcc = input_data.get("bcc", [])
        
        # Validate recipients
        if not recipients:
            raise ValueError("At least one recipient must be specified")
        
        if not subject:
            raise ValueError("Subject is required")
        
        # Generate message ID
        message_id = f"MSG-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # Prepare template data
        template_data = {
            "subject": subject,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id,
            **data
        }
        
        # Get email template
        email_template = self.email_templates.get(template, self.email_templates["default"])
        
        # Render email content
        rendered_subject = email_template["subject"].format(**template_data)
        rendered_html = email_template["html"].format(**template_data)
        rendered_text = email_template.get("text", "").format(**template_data)
        
        # Send emails
        delivery_status = {}
        failed_recipients = []
        
        for recipient in recipients:
            try:
                await self._send_single_email(
                    recipient=recipient,
                    subject=rendered_subject,
                    html_content=rendered_html,
                    text_content=rendered_text,
                    attachments=attachments,
                    cc=cc,
                    bcc=bcc,
                    priority=priority
                )
                delivery_status[recipient] = "delivered"
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Failed to send email to {recipient}: {e}")
                delivery_status[recipient] = f"failed: {str(e)}"
                failed_recipients.append(recipient)
        
        # Record sent email
        email_record = {
            "message_id": message_id,
            "subject": rendered_subject,
            "recipients": recipients,
            "cc": cc,
            "bcc": bcc,
            "template": template,
            "priority": priority,
            "delivery_status": delivery_status,
            "sent_at": datetime.utcnow(),
            "failed_recipients": failed_recipients
        }
        
        self.sent_emails.append(email_record)
        
        # Keep only last 1000 sent emails in memory
        if len(self.sent_emails) > 1000:
            self.sent_emails = self.sent_emails[-1000:]
        
        return {
            "message_id": message_id,
            "status": "sent" if not failed_recipients else "partial_failure",
            "delivery_status": delivery_status,
            "successful_recipients": len([r for r in recipients if delivery_status[r] == "delivered"]),
            "failed_recipients": len(failed_recipients),
            "sent_at": email_record["sent_at"].isoformat()
        }
    
    async def _send_single_email(self, recipient: str, subject: str, html_content: str, 
                                text_content: str, attachments: List[str], cc: List[str], 
                                bcc: List[str], priority: str):
        """Send single email"""
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add CC and BCC
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Set priority
            if priority == "high":
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            elif priority == "low":
                msg['X-Priority'] = '5'
                msg['X-MSMail-Priority'] = 'Low'
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
            
            # Add attachments
            for attachment_path in attachments:
                try:
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to attach file {attachment_path}: {e}")
            
            # Send email
            if self.smtp_config["username"]:
                # Use configured SMTP server
                await self._send_via_smtp(msg, [recipient] + cc + bcc)
            else:
                # Log email instead of sending (development mode)
                logger.info(f"📧 EMAIL (dev mode): To: {recipient}, Subject: {subject}")
                
        except Exception as e:
            logger.error(f"❌ Error creating/sending email to {recipient}: {e}")
            raise
    
    async def _send_via_smtp(self, msg: MIMEMultipart, all_recipients: List[str]):
        """Send email via SMTP server"""
        
        # Run SMTP sending in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, msg, all_recipients)
    
    def _smtp_send(self, msg: MIMEMultipart, all_recipients: List[str]):
        """Send email using SMTP (synchronous)"""
        
        try:
            # Connect to SMTP server
            if self.smtp_config["use_ssl"]:
                server = smtplib.SMTP_SSL(self.smtp_config["host"], self.smtp_config["port"])
            else:
                server = smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"])
                if self.smtp_config["use_tls"]:
                    server.starttls()
            
            # Authenticate
            if self.smtp_config["username"]:
                server.login(self.smtp_config["username"], self.smtp_config["password"])
            
            # Send email
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()
            
        except Exception as e:
            logger.error(f"❌ SMTP send failed: {e}")
            raise
    
    async def get_email_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get status of sent email"""
        
        for email in self.sent_emails:
            if email["message_id"] == message_id:
                return {
                    "message_id": message_id,
                    "status": "sent" if not email["failed_recipients"] else "partial_failure",
                    "subject": email["subject"],
                    "recipients": email["recipients"],
                    "delivery_status": email["delivery_status"],
                    "sent_at": email["sent_at"].isoformat()
                }
        
        return None
    
    async def get_email_statistics(self) -> Dict[str, Any]:
        """Get email sending statistics"""
        
        total_emails = len(self.sent_emails)
        if total_emails == 0:
            return {"total_emails": 0}
        
        successful_emails = len([e for e in self.sent_emails if not e["failed_recipients"]])
        total_recipients = sum(len(e["recipients"]) for e in self.sent_emails)
        failed_deliveries = sum(len(e["failed_recipients"]) for e in self.sent_emails)
        
        # Template usage
        template_usage = {}
        for email in self.sent_emails:
            template = email.get("template", "default")
            template_usage[template] = template_usage.get(template, 0) + 1
        
        return {
            "total_emails": total_emails,
            "successful_emails": successful_emails,
            "total_recipients": total_recipients,
            "failed_deliveries": failed_deliveries,
            "success_rate": (successful_emails / total_emails * 100) if total_emails > 0 else 0,
            "template_usage": template_usage,
            "smtp_configured": bool(self.smtp_config.get("username"))
        }
    
    async def cleanup(self):
        """Cleanup email adapter"""
        
        # Save email logs before cleanup
        if self.sent_emails:
            logger.info(f"📧 Email adapter sent {len(self.sent_emails)} emails during session")
        
        self.sent_emails.clear()
        self.is_initialized = False
        logger.info("✅ Email adapter cleaned up")
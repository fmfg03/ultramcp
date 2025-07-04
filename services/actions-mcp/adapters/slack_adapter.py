"""
Slack Adapter - Handles Slack messaging and notifications
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import aiohttp

from .mock_adapter import MockAdapter

logger = logging.getLogger(__name__)

class SlackAdapter:
    """Adapter for Slack messaging and notifications"""
    
    def __init__(self):
        self.is_initialized = False
        self.slack_config = {}
        self.message_templates = {}
        self.sent_messages = []
        self.channel_cache = {}
        
    async def initialize(self):
        """Initialize Slack adapter"""
        try:
            await self._load_slack_config()
            await self._load_message_templates()
            await self._test_slack_connection()
            self.is_initialized = True
            logger.info("✅ Slack adapter initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Slack adapter: {e}")
            # Fall back to mock adapter
            self.mock_adapter = MockAdapter("SlackAdapter")
            await self.mock_adapter.initialize()
            logger.info("✅ Using mock Slack adapter")
    
    async def _load_slack_config(self):
        """Load Slack configuration"""
        self.slack_config = {
            "bot_token": os.getenv("SLACK_BOT_TOKEN", ""),
            "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
            "app_token": os.getenv("SLACK_APP_TOKEN", ""),
            "signing_secret": os.getenv("SLACK_SIGNING_SECRET", ""),
            "default_channel": os.getenv("SLACK_DEFAULT_CHANNEL", "#general"),
            "bot_name": os.getenv("SLACK_BOT_NAME", "UltraMCP Actions"),
            "bot_emoji": os.getenv("SLACK_BOT_EMOJI", ":robot_face:"),
            "api_base_url": "https://slack.com/api"
        }
        
        if not self.slack_config["bot_token"] and not self.slack_config["webhook_url"]:
            raise ValueError("Either SLACK_BOT_TOKEN or SLACK_WEBHOOK_URL must be configured")
    
    async def _load_message_templates(self):
        """Load Slack message templates"""
        self.message_templates = {
            "default": {
                "text": "{message}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "{message}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "_Sent by UltraMCP Actions Service at {timestamp}_"
                            }
                        ]
                    }
                ]
            },
            "escalation": {
                "text": "🚨 ESCALATION: {context}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🚨 *ESCALATION REQUIRED*\n\n*Context:* {context}\n*Urgency:* {urgency}\n*Escalated by:* {escalated_by}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Details"
                                },
                                "style": "danger",
                                "url": "{tracking_url}"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"⏰ Escalated at {{timestamp}} | 🆔 {{escalation_id}}"
                            }
                        ]
                    }
                ]
            },
            "approval": {
                "text": "📋 Approval Required: {action_description}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📋 *Approval Required*\n\n*Action:* {action_description}\n*Requested by:* {requester}\n*Justification:* {justification}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "✅ Approve"
                                },
                                "style": "primary",
                                "url": "{approval_url}&action=approve"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "❌ Reject"
                                },
                                "style": "danger",
                                "url": "{approval_url}&action=reject"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "📋 Details"
                                },
                                "url": "{approval_url}"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"⏰ Expires: {{expires_at}} | 🆔 {{approval_id}}"
                            }
                        ]
                    }
                ]
            },
            "notification": {
                "text": "📢 {subject}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📢 *{subject}*\n\n{message}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "_UltraMCP Actions Service notification at {timestamp}_"
                            }
                        ]
                    }
                ]
            },
            "workflow": {
                "text": "⚙️ Workflow {status}: {workflow_type}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "⚙️ *Workflow {status}*\n\n*Type:* {workflow_type}\n*Environment:* {environment}\n*Status:* {status}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Monitor Progress"
                                },
                                "url": "{monitoring_url}"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"🆔 {{workflow_id}} | ⏰ {{timestamp}}"
                            }
                        ]
                    }
                ]
            }
        }
    
    async def _test_slack_connection(self):
        """Test Slack connection"""
        if self.slack_config["bot_token"]:
            try:
                await self._api_call("auth.test")
                logger.info("✅ Slack Bot API connection test successful")
            except Exception as e:
                logger.warning(f"⚠️ Slack Bot API test failed: {e}")
                if not self.slack_config["webhook_url"]:
                    raise
        
        if self.slack_config["webhook_url"]:
            try:
                test_payload = {
                    "text": "UltraMCP Actions Service connection test",
                    "username": self.slack_config["bot_name"],
                    "icon_emoji": self.slack_config["bot_emoji"]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.slack_config["webhook_url"],
                        json=test_payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            logger.info("✅ Slack Webhook connection test successful")
                        else:
                            raise Exception(f"Webhook returned status {response.status}")
                            
            except Exception as e:
                logger.warning(f"⚠️ Slack Webhook test failed: {e}")
                if not self.slack_config["bot_token"]:
                    raise
    
    async def execute(self, action_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Slack action"""
        
        if not self.is_initialized and hasattr(self, 'mock_adapter'):
            return await self.mock_adapter.execute(action_name, input_data)
        
        if action_name == "send_slack_message":
            return await self._send_slack_message(input_data)
        else:
            raise ValueError(f"Unsupported action: {action_name}")
    
    async def _send_slack_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack message"""
        
        # Extract message parameters
        channel = input_data.get("channel", self.slack_config["default_channel"])
        message = input_data.get("message", "")
        template = input_data.get("template", "default")
        data = input_data.get("data", {})
        thread_ts = input_data.get("thread_ts")
        blocks = input_data.get("blocks")
        
        # Validate parameters
        if not channel:
            raise ValueError("Channel is required")
        
        if not message and not blocks:
            raise ValueError("Either message or blocks must be provided")
        
        # Generate message timestamp
        message_ts = str(int(datetime.utcnow().timestamp() * 1000000))
        
        # Prepare template data
        template_data = {
            "message": message,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "channel": channel,
            **data
        }
        
        # Get message template and render content
        if template in self.message_templates:
            msg_template = self.message_templates[template]
            rendered_text = msg_template["text"].format(**template_data)
            
            # Render blocks if template has them
            if "blocks" in msg_template and not blocks:
                blocks = self._render_blocks(msg_template["blocks"], template_data)
        else:
            rendered_text = message
        
        # Prepare Slack payload
        payload = {
            "channel": channel,
            "text": rendered_text,
            "username": self.slack_config["bot_name"],
            "icon_emoji": self.slack_config["bot_emoji"]
        }
        
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        if blocks:
            payload["blocks"] = blocks
        
        try:
            # Send message via Bot API or Webhook
            if self.slack_config["bot_token"]:
                result = await self._send_via_bot_api(payload)
            else:
                result = await self._send_via_webhook(payload)
            
            # Record sent message
            message_record = {
                "message_ts": result.get("ts", message_ts),
                "channel": channel,
                "text": rendered_text,
                "template": template,
                "thread_ts": thread_ts,
                "sent_at": datetime.utcnow(),
                "delivery_status": "sent"
            }
            
            self.sent_messages.append(message_record)
            
            # Keep only last 1000 sent messages
            if len(self.sent_messages) > 1000:
                self.sent_messages = self.sent_messages[-1000:]
            
            return {
                "message_ts": message_record["message_ts"],
                "channel": channel,
                "status": "sent",
                "template_used": template,
                "sent_at": message_record["sent_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send Slack message: {e}")
            raise
    
    def _render_blocks(self, blocks: List[Dict], data: Dict[str, Any]) -> List[Dict]:
        """Render Slack blocks with template data"""
        
        rendered_blocks = []
        
        for block in blocks:
            # Deep copy block to avoid modifying template
            rendered_block = json.loads(json.dumps(block))
            
            # Recursively render all text fields
            self._render_block_texts(rendered_block, data)
            rendered_blocks.append(rendered_block)
        
        return rendered_blocks
    
    def _render_block_texts(self, obj: Any, data: Dict[str, Any]):
        """Recursively render text fields in Slack blocks"""
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and "{" in value:
                    try:
                        obj[key] = value.format(**data)
                    except KeyError:
                        # Keep original text if template variable not found
                        pass
                else:
                    self._render_block_texts(value, data)
        elif isinstance(obj, list):
            for item in obj:
                self._render_block_texts(item, data)
    
    async def _send_via_bot_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via Slack Bot API"""
        
        headers = {
            "Authorization": f"Bearer {self.slack_config['bot_token']}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.slack_config['api_base_url']}/chat.postMessage"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    error = result.get("error", "Unknown error")
                    raise Exception(f"Slack API error: {error}")
                
                return result
    
    async def _send_via_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via Slack Webhook"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.slack_config["webhook_url"],
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Webhook error {response.status}: {error_text}")
                
                # Webhooks don't return message timestamp
                return {"ts": str(int(datetime.utcnow().timestamp()))}
    
    async def _api_call(self, method: str, **kwargs) -> Dict[str, Any]:
        """Make Slack API call"""
        
        headers = {
            "Authorization": f"Bearer {self.slack_config['bot_token']}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.slack_config['api_base_url']}/{method}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=kwargs,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    error = result.get("error", "Unknown error")
                    raise Exception(f"Slack API error: {error}")
                
                return result
    
    async def get_channel_info(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get information about Slack channel"""
        
        # Check cache first
        if channel in self.channel_cache:
            return self.channel_cache[channel]
        
        try:
            if self.slack_config["bot_token"]:
                # Try to get channel info via API
                if channel.startswith("#"):
                    # Convert channel name to ID
                    channels_result = await self._api_call("conversations.list", types="public_channel,private_channel")
                    for ch in channels_result.get("channels", []):
                        if ch["name"] == channel[1:]:  # Remove #
                            channel_id = ch["id"]
                            break
                    else:
                        return None
                else:
                    channel_id = channel
                
                info_result = await self._api_call("conversations.info", channel=channel_id)
                channel_info = info_result.get("channel", {})
                
                # Cache result
                self.channel_cache[channel] = channel_info
                return channel_info
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get channel info for {channel}: {e}")
        
        return None
    
    async def get_message_status(self, message_ts: str, channel: str) -> Optional[Dict[str, Any]]:
        """Get status of sent message"""
        
        for message in self.sent_messages:
            if message["message_ts"] == message_ts and message["channel"] == channel:
                return {
                    "message_ts": message_ts,
                    "channel": channel,
                    "status": message["delivery_status"],
                    "sent_at": message["sent_at"].isoformat(),
                    "template": message["template"]
                }
        
        return None
    
    async def get_slack_statistics(self) -> Dict[str, Any]:
        """Get Slack messaging statistics"""
        
        total_messages = len(self.sent_messages)
        if total_messages == 0:
            return {"total_messages": 0}
        
        # Channel usage
        channel_usage = {}
        for message in self.sent_messages:
            channel = message["channel"]
            channel_usage[channel] = channel_usage.get(channel, 0) + 1
        
        # Template usage
        template_usage = {}
        for message in self.sent_messages:
            template = message.get("template", "default")
            template_usage[template] = template_usage.get(template, 0) + 1
        
        # Thread usage
        thread_messages = len([m for m in self.sent_messages if m.get("thread_ts")])
        
        return {
            "total_messages": total_messages,
            "channel_usage": channel_usage,
            "template_usage": template_usage,
            "thread_messages": thread_messages,
            "api_method": "bot_api" if self.slack_config["bot_token"] else "webhook",
            "bot_configured": bool(self.slack_config["bot_token"]),
            "webhook_configured": bool(self.slack_config["webhook_url"])
        }
    
    async def cleanup(self):
        """Cleanup Slack adapter"""
        
        if self.sent_messages:
            logger.info(f"💬 Slack adapter sent {len(self.sent_messages)} messages during session")
        
        self.sent_messages.clear()
        self.channel_cache.clear()
        self.is_initialized = False
        logger.info("✅ Slack adapter cleaned up")
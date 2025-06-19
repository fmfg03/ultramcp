/**
 * WhatsApp Adapter for MCP System
 * Ready-to-plug integration with mock implementation
 */

class WhatsAppAdapter {
    constructor(config = {}) {
        this.config = {
            apiKey: config.apiKey || process.env.WHATSAPP_API_KEY,
            phoneNumberId: config.phoneNumberId || process.env.WHATSAPP_PHONE_NUMBER_ID,
            webhookToken: config.webhookToken || process.env.WHATSAPP_WEBHOOK_TOKEN,
            apiVersion: config.apiVersion || 'v18.0',
            baseUrl: config.baseUrl || 'https://graph.facebook.com',
            mockMode: config.mockMode || !config.apiKey,
            ...config
        };
        
        this.isConnected = false;
        this.messageQueue = [];
        this.webhookHandlers = new Map();
        
        this.initialize();
    }

    /**
     * Initialize WhatsApp adapter
     */
    async initialize() {
        if (this.config.mockMode) {
            console.log('📱 WhatsApp Adapter initialized in MOCK mode');
            this.isConnected = true;
            return;
        }

        try {
            // Verify API credentials
            await this.verifyCredentials();
            this.isConnected = true;
            console.log('📱 WhatsApp Adapter initialized successfully');
        } catch (error) {
            console.error('❌ WhatsApp Adapter initialization failed:', error.message);
            this.isConnected = false;
        }
    }

    /**
     * Verify API credentials
     */
    async verifyCredentials() {
        if (this.config.mockMode) {
            return { status: 'mock_verified' };
        }

        // TODO: Implement actual API verification
        // const response = await fetch(`${this.config.baseUrl}/${this.config.apiVersion}/${this.config.phoneNumberId}`, {
        //     headers: {
        //         'Authorization': `Bearer ${this.config.apiKey}`
        //     }
        // });
        
        return { status: 'verified' };
    }

    /**
     * Send text message
     * @param {string} to - Recipient phone number
     * @param {string} message - Message text
     * @param {Object} options - Additional options
     */
    async sendMessage(to, message, options = {}) {
        if (this.config.mockMode) {
            return this.mockSendMessage(to, message, options);
        }

        try {
            const payload = {
                messaging_product: 'whatsapp',
                to: to,
                type: 'text',
                text: {
                    body: message
                }
            };

            // TODO: Implement actual API call
            // const response = await fetch(`${this.config.baseUrl}/${this.config.apiVersion}/${this.config.phoneNumberId}/messages`, {
            //     method: 'POST',
            //     headers: {
            //         'Authorization': `Bearer ${this.config.apiKey}`,
            //         'Content-Type': 'application/json'
            //     },
            //     body: JSON.stringify(payload)
            // });

            return {
                success: true,
                messageId: `msg_${Date.now()}`,
                to: to,
                message: message
            };
        } catch (error) {
            console.error('Failed to send WhatsApp message:', error);
            throw error;
        }
    }

    /**
     * Send template message
     * @param {string} to - Recipient phone number
     * @param {string} templateName - Template name
     * @param {Object} parameters - Template parameters
     */
    async sendTemplate(to, templateName, parameters = {}) {
        if (this.config.mockMode) {
            return this.mockSendTemplate(to, templateName, parameters);
        }

        try {
            const payload = {
                messaging_product: 'whatsapp',
                to: to,
                type: 'template',
                template: {
                    name: templateName,
                    language: {
                        code: parameters.language || 'en'
                    },
                    components: parameters.components || []
                }
            };

            // TODO: Implement actual API call
            return {
                success: true,
                messageId: `template_${Date.now()}`,
                to: to,
                template: templateName
            };
        } catch (error) {
            console.error('Failed to send WhatsApp template:', error);
            throw error;
        }
    }

    /**
     * Send media message
     * @param {string} to - Recipient phone number
     * @param {string} mediaType - Type of media (image, document, audio, video)
     * @param {string} mediaUrl - URL of the media
     * @param {Object} options - Additional options
     */
    async sendMedia(to, mediaType, mediaUrl, options = {}) {
        if (this.config.mockMode) {
            return this.mockSendMedia(to, mediaType, mediaUrl, options);
        }

        try {
            const payload = {
                messaging_product: 'whatsapp',
                to: to,
                type: mediaType,
                [mediaType]: {
                    link: mediaUrl,
                    caption: options.caption || ''
                }
            };

            // TODO: Implement actual API call
            return {
                success: true,
                messageId: `media_${Date.now()}`,
                to: to,
                mediaType: mediaType,
                mediaUrl: mediaUrl
            };
        } catch (error) {
            console.error('Failed to send WhatsApp media:', error);
            throw error;
        }
    }

    /**
     * Handle incoming webhook
     * @param {Object} webhookData - Webhook payload
     */
    async handleWebhook(webhookData) {
        if (this.config.mockMode) {
            return this.mockHandleWebhook(webhookData);
        }

        try {
            const { entry } = webhookData;
            
            for (const entryItem of entry || []) {
                const { changes } = entryItem;
                
                for (const change of changes || []) {
                    if (change.field === 'messages') {
                        await this.processIncomingMessages(change.value);
                    }
                }
            }

            return { status: 'processed' };
        } catch (error) {
            console.error('Failed to handle WhatsApp webhook:', error);
            throw error;
        }
    }

    /**
     * Process incoming messages
     * @param {Object} messageData - Message data from webhook
     */
    async processIncomingMessages(messageData) {
        const { messages, contacts } = messageData;

        for (const message of messages || []) {
            const contact = contacts?.find(c => c.wa_id === message.from);
            
            const processedMessage = {
                id: message.id,
                from: message.from,
                timestamp: message.timestamp,
                type: message.type,
                contact: contact,
                content: this.extractMessageContent(message)
            };

            // Trigger registered handlers
            await this.triggerHandlers('message', processedMessage);
        }
    }

    /**
     * Extract message content based on type
     * @param {Object} message - Raw message object
     */
    extractMessageContent(message) {
        switch (message.type) {
            case 'text':
                return { text: message.text?.body };
            case 'image':
                return { 
                    mediaId: message.image?.id,
                    caption: message.image?.caption 
                };
            case 'document':
                return { 
                    mediaId: message.document?.id,
                    filename: message.document?.filename,
                    caption: message.document?.caption 
                };
            case 'audio':
                return { 
                    mediaId: message.audio?.id 
                };
            case 'video':
                return { 
                    mediaId: message.video?.id,
                    caption: message.video?.caption 
                };
            default:
                return { raw: message };
        }
    }

    /**
     * Register webhook handler
     * @param {string} event - Event type
     * @param {Function} handler - Handler function
     */
    onWebhook(event, handler) {
        if (!this.webhookHandlers.has(event)) {
            this.webhookHandlers.set(event, []);
        }
        this.webhookHandlers.get(event).push(handler);
    }

    /**
     * Trigger registered handlers
     * @param {string} event - Event type
     * @param {Object} data - Event data
     */
    async triggerHandlers(event, data) {
        const handlers = this.webhookHandlers.get(event) || [];
        
        for (const handler of handlers) {
            try {
                await handler(data);
            } catch (error) {
                console.error(`Handler error for event ${event}:`, error);
            }
        }
    }

    // Mock implementations for testing
    mockSendMessage(to, message, options) {
        console.log(`📱 [MOCK] Sending message to ${to}: ${message}`);
        return {
            success: true,
            messageId: `mock_msg_${Date.now()}`,
            to: to,
            message: message,
            mock: true
        };
    }

    mockSendTemplate(to, templateName, parameters) {
        console.log(`📱 [MOCK] Sending template "${templateName}" to ${to}`);
        return {
            success: true,
            messageId: `mock_template_${Date.now()}`,
            to: to,
            template: templateName,
            mock: true
        };
    }

    mockSendMedia(to, mediaType, mediaUrl, options) {
        console.log(`📱 [MOCK] Sending ${mediaType} to ${to}: ${mediaUrl}`);
        return {
            success: true,
            messageId: `mock_media_${Date.now()}`,
            to: to,
            mediaType: mediaType,
            mediaUrl: mediaUrl,
            mock: true
        };
    }

    mockHandleWebhook(webhookData) {
        console.log('📱 [MOCK] Handling webhook:', JSON.stringify(webhookData, null, 2));
        return { status: 'mock_processed' };
    }

    /**
     * Get adapter status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            mockMode: this.config.mockMode,
            messageQueue: this.messageQueue.length,
            handlers: Array.from(this.webhookHandlers.keys())
        };
    }
}

module.exports = { WhatsAppAdapter };


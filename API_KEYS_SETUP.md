# 🔑 UltraMCP API Keys Setup Guide

This guide will help you configure all the required API keys for UltraMCP to function properly.

## 🚀 Required API Keys (Replace placeholders in .env)

### 1. OpenAI API Key (REQUIRED)
```bash
OPENAI_API_KEY=sk-your-real-openai-api-key-here
```
- **Get it from**: https://platform.openai.com/api-keys
- **Used for**: LLM orchestration, voice processing, embeddings
- **Current placeholder**: `sk-dev-placeholder-replace-with-real-key`

### 2. Anthropic Claude API Key (REQUIRED)
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-real-claude-key-here
```
- **Get it from**: https://console.anthropic.com/
- **Used for**: Multi-LLM debates, reasoning tasks
- **Current placeholder**: `sk-ant-api03-dev-placeholder-claude-key`

## 📊 Optional but Recommended API Keys

### 3. LangWatch API Key (Monitoring)
```bash
LANGWATCH_API_KEY=lw-your-real-langwatch-key-here
```
- **Get it from**: https://langwatch.ai
- **Used for**: LLM monitoring and observability
- **Current placeholder**: `lw-dev-placeholder-langwatch-key`

### 4. GitHub Personal Access Token
```bash
GITHUB_TOKEN=ghp_your-real-github-token-here
```
- **Get it from**: GitHub Settings > Developer settings > Personal access tokens
- **Used for**: GitHub adapter, repository operations
- **Permissions needed**: `repo`, `read:user`, `read:org`
- **Current placeholder**: `ghp_dev-placeholder-github-token`

### 5. Notion Integration Token
```bash
NOTION_TOKEN=secret_your-real-notion-token-here
```
- **Get it from**: https://www.notion.so/my-integrations
- **Used for**: Notion adapter, database operations
- **Current placeholder**: `secret_dev-placeholder-notion-token`

### 6. Telegram Bot Token
```bash
TELEGRAM_BOT_TOKEN=your-real-telegram-bot-token
```
- **Get it from**: Create a bot with @BotFather on Telegram
- **Used for**: Telegram notifications and interactions
- **Current placeholder**: `dev-placeholder-bot-token`

### 7. Firecrawl API Key (Web Scraping)
```bash
FIRECRAWL_API_KEY=fc-your-real-firecrawl-key-here
```
- **Get it from**: https://firecrawl.dev
- **Used for**: Web scraping and content extraction
- **Current placeholder**: `fc-dev-placeholder-key`

## 🔧 How to Update API Keys

1. **Edit the main environment file**:
   ```bash
   nano /root/ultramcp/.env
   ```

2. **For voice system specifically**:
   ```bash
   nano /root/ultramcp/services/voice-system/.env
   ```

3. **Replace the placeholder values** with your real API keys

4. **Restart the services** after updating keys:
   ```bash
   docker-compose down && docker-compose up -d
   ```

## 🛡️ Security Best Practices

1. **Never commit real API keys** to version control
2. **Use different keys** for development and production
3. **Rotate keys regularly** for security
4. **Monitor API usage** to detect unauthorized access
5. **Set up billing alerts** to prevent unexpected charges

## 🚨 Priority Order for Setup

1. **OpenAI API Key** - Core functionality won't work without this
2. **Anthropic API Key** - Required for multi-LLM debates
3. **LangWatch API Key** - Critical for monitoring and debugging
4. **GitHub Token** - If you plan to use GitHub integrations
5. **Other keys** - Based on your specific use case

## 🔍 Testing API Keys

After setting up your keys, you can test them using:

```bash
# Test OpenAI connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Test Anthropic connection  
curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages

# Test GitHub connection
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

## ⚠️ Current Status

- ✅ Environment files created with secure generated secrets
- ⚠️  API keys are set to development placeholders
- 🔄 **Action Required**: Replace placeholders with real API keys

The system will start with placeholders but most functionality will be limited until real API keys are configured.
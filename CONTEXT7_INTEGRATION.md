# 📚 UltraMCP + Context7 Integration Guide

**Context7** is a revolutionary Model Context Protocol (MCP) server that provides **real-time, up-to-date documentation** directly to AI coding assistants, eliminating outdated or "hallucinated" code examples.

## 🚀 What is Context7?

Context7 solves a fundamental problem: **LLMs rely on outdated training data** when generating code. Context7 fetches current, version-specific documentation from libraries and injects it directly into AI prompts.

### Key Benefits:
- ✅ **Real-time Documentation** - Always current, never outdated
- ✅ **Version-Specific** - Get docs for exact library versions
- ✅ **AI-Native** - Designed for AI coding assistants
- ✅ **Multi-Platform** - Works with Claude, Cursor, VS Code, etc.
- ✅ **Zero Hallucination** - Accurate code examples from source

## 🏗️ UltraMCP Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UltraMCP Ecosystem                      │
├─────────────────────────────────────────────────────────────┤
│  Claude Code  ←→  Context7 Service  ←→  Upstash Context7   │
│      ↓                   ↓                      ↓          │
│  Enhanced        Real-time Docs         Library Sources    │
│  Prompts          & Caching              (GitHub, npm)     │
└─────────────────────────────────────────────────────────────┘
```

### Integration Components:

1. **Context7 MCP Service** (`services/context7-mcp/`)
   - Node.js service wrapping Upstash Context7
   - Caching and rate limiting
   - UltraMCP ecosystem integration

2. **Python Client** (`context7_client.py`)
   - High-level Python interface
   - Library detection and enhancement
   - CLI and programmatic access

3. **Makefile Commands**
   - Terminal-first approach integration
   - Quick documentation access
   - Enhanced AI chat commands

## 🛠️ Installation & Setup

### 1. Automatic Setup (Recommended)

```bash
# Start UltraMCP with Context7
make docker-hybrid

# Verify Context7 integration
make context7-test
```

### 2. Manual Setup

```bash
# Install Context7 MCP globally
npm install -g @upstash/context7-mcp@latest

# Build Context7 service
cd services/context7-mcp
npm install
npm start
```

### 3. Verification

```bash
# Check service health
make context7-health

# Test documentation retrieval
make context7-docs LIBRARY=react

# Run integration tests
make context7-test
```

## 📖 Usage Guide

### Quick Commands

```bash
# Get documentation for any library
make context7-docs LIBRARY=react
make context7-docs LIBRARY=express VERSION=4.18.0

# Search documentation
make context7-search LIBRARY=react QUERY="useState hook"

# AI chat with automatic documentation context
make context7-chat TEXT="Create a React component with useState"

# Enhance prompts with documentation
make context7-enhance PROMPT="Build a REST API with Express"

# Detect libraries in code
make context7-detect CODE="import React from 'react'; const app = express();"
```

### Python Client Usage

```python
import asyncio
from services.context7_mcp.context7_client import Context7Client

async def example():
    async with Context7Client() as client:
        # Get documentation
        docs = await client.get_documentation(
            DocumentationRequest(library="react", type="api")
        )
        
        # Enhance prompt with context
        enhanced = await client.enhance_prompt_with_context(
            "Create a todo app with React hooks"
        )
        print(enhanced['enhancedPrompt'])

asyncio.run(example())
```

### CLI Usage

```bash
# Python client CLI
python3 services/context7-mcp/context7_client.py get react --type=api
python3 services/context7-mcp/context7_client.py search react "hooks"
python3 services/context7-mcp/context7_client.py enhance "Build a React app"
```

## 🎯 Claude Code Integration

### 1. Standard Usage

In any Claude Code prompt, simply add `use context7`:

```
Create a Next.js 14 project with server components. use context7
```

Context7 will automatically:
- Detect mentioned libraries (Next.js)
- Fetch current documentation
- Enhance the prompt with real-time docs

### 2. UltraMCP Enhanced Usage

```bash
# Context7-enhanced chat
make context7-chat TEXT="Build a TypeScript Express API with authentication"

# Local LLM with Context7
make context7-local-chat TEXT="Create React components using modern patterns"

# Enhanced CoD debates with documentation
make cod-local TOPIC="React vs Vue architecture with Context7 documentation"
```

### 3. Automatic Enhancement

UltraMCP automatically enhances prompts when you use specific commands:

```bash
# These commands automatically include Context7 enhancement
make context7-chat TEXT="Your prompt here"
make claude-context7-chat TEXT="Your prompt here"
```

## 🔧 Advanced Configuration

### Service Configuration

Edit `services/context7-mcp/config/context7-config.json`:

```json
{
  "context7": {
    "cache": {
      "ttl": 3600,
      "maxSize": 1000
    },
    "documentation": {
      "maxLibraries": 50,
      "includeExamples": true,
      "preferredFormat": "markdown"
    },
    "integration": {
      "claudeCode": {
        "enabled": true,
        "autoEnhance": true,
        "maxLibrariesPerRequest": 10
      }
    }
  }
}
```

### Environment Variables

```bash
# Context7 service settings
CONTEXT7_CACHE_TTL=3600        # Cache timeout in seconds
CONTEXT7_MAX_DOCS=50           # Max docs per request
MCP_SERVER_PORT=8003           # Service port

# Integration settings
NODE_ENV=production            # Production mode
CONTEXT7_COMMAND=npx           # Command to run Context7
```

## 📊 Monitoring & Debugging

### Health Checks

```bash
# Service health
make context7-health

# Detailed statistics
make context7-stats

# Integration test suite
make context7-test
```

### Logs & Debugging

```bash
# Service logs
docker logs ultramcp-context7

# Direct service status
curl http://sam.chat:8003/health | jq

# Cache statistics
curl http://sam.chat:8003/api/stats | jq .data.cache
```

### Performance Monitoring

The Context7 service provides detailed metrics:

```bash
# Get service metrics
curl http://sam.chat:8003/api/stats | jq '{
  requests: .data.service.requestCount,
  errors: .data.service.errorCount,
  cache_hits: .data.cache.hits,
  cache_misses: .data.cache.misses
}'
```

## 🎨 Example Workflows

### 1. React Development Workflow

```bash
# Start with Context7 documentation
make context7-docs LIBRARY=react

# Enhanced development chat
make context7-chat TEXT="Create a React component with TypeScript, hooks, and modern patterns"

# Search specific functionality
make context7-search LIBRARY=react QUERY="useEffect cleanup"
```

### 2. Backend API Development

```bash
# Get Express.js documentation
make context7-docs LIBRARY=express

# Enhanced API development
make context7-chat TEXT="Build a REST API with Express, TypeScript, and JWT authentication"

# Database integration
make context7-docs LIBRARY=prisma
make context7-chat TEXT="Add Prisma ORM to Express API with PostgreSQL"
```

### 3. Full-Stack Development

```bash
# Multi-library enhancement
make context7-enhance PROMPT="Build a full-stack app with Next.js, Prisma, and TailwindCSS" LIBRARIES="next,prisma,tailwindcss"

# Enhanced debate with multiple technologies
make cod-local TOPIC="Architecture decision: Next.js vs Nuxt.js with current documentation"
```

## 🔍 Library Detection

Context7 automatically detects libraries in your prompts and code:

### Supported Patterns:
- `import React from 'react'`
- `require('express')`
- `from 'vue'`
- `@angular/core`
- `npm install lodash`
- `yarn add axios`

### Popular Libraries (Auto-detected):
- **Frontend**: React, Vue, Angular, Svelte, Next.js, Nuxt
- **Backend**: Express, Fastify, NestJS, Koa
- **Databases**: Prisma, Mongoose, Sequelize, TypeORM
- **Utilities**: Lodash, Moment, Axios, Zod
- **Styling**: TailwindCSS, Bootstrap, Material-UI, Chakra UI

## 🚀 Integration Examples

### Example 1: Enhanced React Development

**Input:**
```bash
make context7-chat TEXT="Create a React todo app with hooks and TypeScript"
```

**What happens:**
1. Context7 detects "React" and "TypeScript"
2. Fetches current React and TypeScript documentation
3. Enhances prompt with real-time docs
4. Sends enhanced prompt to AI model

**Result:** Accurate, current code using latest React patterns

### Example 2: API Development with Documentation

**Input:**
```bash
make context7-chat TEXT="Build Express API with authentication and validation"
```

**Enhanced Prompt:**
```
Build Express API with authentication and validation

--- Context7 Documentation ---

## Express (4.18.2)
Express is a minimal and flexible Node.js web application framework...
[Current Express.js documentation]

### Examples:
**Basic Express Server**
```js
const express = require('express');
const app = express();
// Current patterns and best practices
```
```

## 🔧 Troubleshooting

### Common Issues

**1. Context7 Service Not Running**
```bash
# Check service status
make context7-health

# Restart services
make docker-hybrid

# Check logs
docker logs ultramcp-context7
```

**2. Documentation Not Found**
```bash
# Test specific library
make context7-docs LIBRARY=react

# Check library name spelling
make context7-detect CODE="import React from 'react'"
```

**3. Empty or Invalid Responses**
```bash
# Clear cache
curl -X DELETE http://sam.chat:8003/api/cache

# Check service stats
make context7-stats
```

### Debug Mode

Enable debug logging:
```bash
# Set debug environment
export NODE_ENV=development

# Restart with debug logging
docker-compose -f docker-compose.hybrid.yml up -d ultramcp-context7
```

## 📚 API Reference

### REST API Endpoints

```bash
# Health check
GET /health

# Get documentation
POST /api/documentation
{
  "library": "react",
  "version": "18.0.0",
  "type": "api",
  "format": "markdown"
}

# Search documentation
GET /api/documentation/search?library=react&query=hooks

# Batch requests
POST /api/documentation/batch
{
  "requests": [
    {"library": "react", "type": "api"},
    {"library": "express", "type": "api"}
  ]
}

# Claude Code integration
POST /api/claude/context
{
  "prompt": "Create a React app",
  "libraries": ["react"],
  "autoDetect": true
}

# Cache management
DELETE /api/cache?pattern=react

# Service statistics
GET /api/stats
```

### Python Client API

```python
from context7_client import Context7Client, DocumentationRequest

async with Context7Client() as client:
    # Get documentation
    docs = await client.get_documentation(
        DocumentationRequest(library="react", type="api")
    )
    
    # Batch requests
    requests = [
        DocumentationRequest(library="react"),
        DocumentationRequest(library="vue")
    ]
    results = await client.get_batch_documentation(requests)
    
    # Search
    search_result = await client.search_documentation("react", "hooks")
    
    # Enhance prompts
    enhanced = await client.enhance_prompt_with_context(
        "Build a todo app", libraries=["react"]
    )
    
    # Detect libraries
    libraries = client.detect_libraries_in_text(
        "import React from 'react'; import axios from 'axios'"
    )
```

## 🎉 Success Stories

Context7 integration enables:

- **Faster Development**: Instant access to current documentation
- **Accurate Code**: No more outdated or hallucinated examples
- **Version Awareness**: Get docs for specific library versions
- **Multi-Library Support**: Handle complex projects with many dependencies
- **AI Enhancement**: Better AI responses with real documentation context

## 🔗 Resources

- **Context7 GitHub**: https://github.com/upstash/context7
- **Upstash Blog**: https://upstash.com/blog/context7-mcp
- **MCP Protocol**: https://modelcontextprotocol.io/
- **UltraMCP Docs**: `cat CLAUDE.md`

---

**🚀 Ready to enhance your AI coding with real-time documentation!**

Start with: `make context7-test` to verify your integration.
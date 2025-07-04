# =============================================================================
# UltraMCP Context7 Integration Service
# Provides real-time, up-to-date documentation for AI coding assistants
# =============================================================================

FROM node:20-alpine

LABEL maintainer="UltraMCP Team"
LABEL description="Context7 MCP Server for real-time documentation"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    curl \
    git \
    python3 \
    make \
    g++

# Create non-root user
RUN addgroup -g 1001 -S context7 && \
    adduser -S context7 -u 1001 -G context7

# Install global packages
RUN npm install -g @upstash/context7-mcp@latest

# Copy service files
COPY package.json package-lock.json* ./
COPY context7_service.js ./
COPY config/ ./config/
COPY scripts/ ./scripts/

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Set ownership
RUN chown -R context7:context7 /app

# Switch to non-root user
USER context7

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node scripts/health-check.js

# Expose port
EXPOSE 8003

# Environment variables
ENV NODE_ENV=production
ENV MCP_SERVER_PORT=8003
ENV CONTEXT7_CACHE_TTL=3600
ENV CONTEXT7_MAX_DOCS=50

# Start the service
CMD ["node", "context7_service.js"]
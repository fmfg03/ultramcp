FROM node:18-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache curl

# Copy package files first for better caching
COPY package*.json ./
RUN npm ci --only=production

# Copy service files
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Expose ports (HTTP API and WebSocket)
EXPOSE 8007 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

# Run the service
CMD ["node", "control_tower_service.js"]
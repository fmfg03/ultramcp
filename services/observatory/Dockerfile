# Observatory Service Dockerfile for sam.chat
# UltraMCP Supreme Stack
# Generated: 2025-07-08

FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 5177

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5177/health || exit 1

# Start the application
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5177"]
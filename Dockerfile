# UltraMCP Hybrid Implementation Dockerfile
# Base stage for Node.js services
FROM node:18-alpine AS base-alpine

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    postgresql-client \
    redis \
    curl \
    jq \
    bash \
    make \
    git \
    openssh-client

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install Node.js dependencies
RUN npm ci --only=production

# CoD Protocol Service Stage (Ubuntu-based for Playwright)
FROM node:18 AS cod-service

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    postgresql-client \
    redis-tools \
    curl \
    jq \
    make \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --only=production && \
    npx playwright install chromium && \
    npx playwright install-deps

# Install Python dependencies for CoD service
RUN pip3 install --break-system-packages fastapi uvicorn pydantic python-multipart aiofiles

# Copy CoD service files
COPY scripts/cod-service.py ./scripts/
COPY scripts/common.sh ./scripts/

# Create necessary directories
RUN mkdir -p logs data/debates data/scrapes data/research data/analysis

# Expose CoD service port
EXPOSE 8001

# Health check for CoD service
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start CoD Protocol service
CMD ["python3", "scripts/cod-service.py"]

# Terminal Interface Stage (Main hybrid interface)
FROM base-alpine AS terminal

# Install additional tools for terminal operations
RUN apk add --no-cache \
    vim \
    nano \
    htop \
    tree \
    ripgrep \
    docker-cli

# Install Python dependencies for all scripts
RUN pip3 install \
    fastapi \
    uvicorn \
    pydantic \
    requests \
    psycopg2-alpine \
    redis \
    python-dotenv

# Copy all application files
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Create necessary directories with proper permissions
RUN mkdir -p logs data/debates data/scrapes data/research data/analysis && \
    chown -R node:node /app

# Switch to non-root user
USER node

# Default command opens interactive shell with Makefile available
CMD ["/bin/bash", "-c", "echo '🚀 UltraMCP Terminal-First Interface Ready!' && echo 'Available commands: make help' && /bin/bash"]

# Web Dashboard Stage (Optional monitoring interface)
FROM base-alpine AS web-dashboard

WORKDIR /app

# Install dashboard dependencies
RUN npm init -y && \
    npm install express cors morgan helmet

# Create simple monitoring dashboard
RUN echo 'const express = require("express"); \
const cors = require("cors"); \
const morgan = require("morgan"); \
const helmet = require("helmet"); \
const app = express(); \
app.use(helmet()); \
app.use(cors()); \
app.use(morgan("combined")); \
app.use(express.static("public")); \
app.get("/", (req, res) => { \
  res.json({ \
    service: "UltraMCP Web Dashboard", \
    status: "operational", \
    timestamp: new Date().toISOString() \
  }); \
}); \
app.get("/health", (req, res) => { \
  res.json({ status: "healthy" }); \
}); \
const PORT = process.env.PORT || 3000; \
app.listen(PORT, () => { \
  console.log(`Dashboard running on port ${PORT}`); \
});' > server.js

# Create public directory with basic HTML
RUN mkdir -p public && \
    echo '<!DOCTYPE html> \
<html> \
<head><title>UltraMCP Dashboard</title></head> \
<body> \
  <h1>🚀 UltraMCP Hybrid System</h1> \
  <p>Terminal-first AI orchestration platform</p> \
  <p>Status: <span id="status">Loading...</span></p> \
  <script> \
    fetch("/health").then(r=>r.json()).then(d=>{ \
      document.getElementById("status").textContent = d.status; \
    }); \
  </script> \
</body> \
</html>' > public/index.html

EXPOSE 3000

CMD ["node", "server.js"]

# Development Stage
FROM terminal AS development

# Install development tools
RUN apk add --no-cache \
    fish \
    zsh \
    tmux \
    neovim

# Install additional Python development tools
RUN pip3 install \
    black \
    flake8 \
    pytest \
    ipython

# Create development configuration
RUN echo 'alias ll="ls -la"' >> /home/node/.bashrc && \
    echo 'alias logs="tail -f logs/combined.log"' >> /home/node/.bashrc && \
    echo 'export PS1="🧠 UltraMCP \\w \\$ "' >> /home/node/.bashrc

USER node

CMD ["/bin/bash", "-c", "echo '🔧 UltraMCP Development Mode' && echo 'Run: make help for available commands' && /bin/bash"]
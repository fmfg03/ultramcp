#!/bin/bash
# PostgreSQL initialization script for MCP system

set -e

# Create MCP database and user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create MCP user if not exists
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcp_user') THEN
            CREATE USER mcp_user WITH PASSWORD '${MCP_DB_PASSWORD:-mcp_password}';
        END IF;
    END
    \$\$;

    -- Create MCP database if not exists
    SELECT 'CREATE DATABASE mcp_system OWNER mcp_user'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mcp_system')\gexec

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE mcp_system TO mcp_user;
EOSQL

# Connect to MCP database and create tables
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "mcp_system" <<-EOSQL
    -- Enable extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    -- Create sessions table
    CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        session_id VARCHAR(255) UNIQUE NOT NULL,
        agent_type VARCHAR(100) NOT NULL,
        status VARCHAR(50) DEFAULT 'running',
        input_data JSONB,
        output_data JSONB,
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        completed_at TIMESTAMP WITH TIME ZONE
    );

    -- Create logs table
    CREATE TABLE IF NOT EXISTS logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        session_id VARCHAR(255),
        level VARCHAR(20) NOT NULL,
        message TEXT NOT NULL,
        agent VARCHAR(100),
        node VARCHAR(100),
        metadata JSONB,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    );

    -- Create errors table
    CREATE TABLE IF NOT EXISTS errors (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        session_id VARCHAR(255),
        error_type VARCHAR(100) NOT NULL,
        error_message TEXT NOT NULL,
        stack_trace TEXT,
        context JSONB,
        agent VARCHAR(100),
        node VARCHAR(100),
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    );

    -- Create cache table
    CREATE TABLE IF NOT EXISTS cache_entries (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        cache_key VARCHAR(255) UNIQUE NOT NULL,
        cache_value JSONB NOT NULL,
        node_type VARCHAR(100),
        expires_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        access_count INTEGER DEFAULT 1
    );

    -- Create agents table
    CREATE TABLE IF NOT EXISTS agents (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        agent_id VARCHAR(100) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        configuration JSONB,
        permissions JSONB,
        enabled BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_agent_type ON sessions(agent_type);
    CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
    CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

    CREATE INDEX IF NOT EXISTS idx_logs_session_id ON logs(session_id);
    CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
    CREATE INDEX IF NOT EXISTS idx_logs_agent ON logs(agent);
    CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);

    CREATE INDEX IF NOT EXISTS idx_errors_session_id ON errors(session_id);
    CREATE INDEX IF NOT EXISTS idx_errors_error_type ON errors(error_type);
    CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors(timestamp);

    CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key);
    CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache_entries(expires_at);
    CREATE INDEX IF NOT EXISTS idx_cache_node_type ON cache_entries(node_type);

    CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents(agent_id);
    CREATE INDEX IF NOT EXISTS idx_agents_enabled ON agents(enabled);

    -- Create updated_at trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS \$\$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    \$\$ language 'plpgsql';

    -- Create triggers
    DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
    CREATE TRIGGER update_sessions_updated_at
        BEFORE UPDATE ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
    CREATE TRIGGER update_agents_updated_at
        BEFORE UPDATE ON agents
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Insert default agents
    INSERT INTO agents (agent_id, name, description, configuration, permissions) VALUES
    ('complete_mcp', 'Complete MCP Agent', 'Full MCP agent with reasoning, building, and reward evaluation', 
     '{"max_iterations": 10, "timeout": 300}', 
     '["reasoning", "building", "reward", "research"]'),
    ('reasoning_agent', 'Reasoning Agent', 'Specialized agent for task analysis and reasoning',
     '{"max_depth": 5, "confidence_threshold": 0.8}',
     '["reasoning", "analysis"]'),
    ('builder_agent', 'Builder Agent', 'Specialized agent for building and construction tasks',
     '{"build_timeout": 600, "max_retries": 3}',
     '["building", "deployment"]'),
    ('research_agent', 'Research Agent', 'Specialized agent for research and information gathering',
     '{"max_sources": 10, "research_timeout": 180}',
     '["research", "analysis", "web_search"]')
    ON CONFLICT (agent_id) DO NOTHING;

    -- Grant permissions to mcp_user
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mcp_user;

    -- Set default privileges for future objects
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mcp_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mcp_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO mcp_user;
EOSQL

echo "MCP database initialization completed successfully!"


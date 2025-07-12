-- UltraMCP + Supabase Database Initialization
-- Combines Supabase backend with UltraMCP service requirements

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ================================================
-- Supabase Integration Tables
-- ================================================

-- Document embeddings for AI functionality
CREATE TABLE IF NOT EXISTS "public"."page" (
  id BIGSERIAL PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  checksum TEXT,
  meta JSONB
);

CREATE TABLE IF NOT EXISTS "public"."page_section" (
  id BIGSERIAL PRIMARY KEY,
  page_id BIGINT NOT NULL REFERENCES public.page ON DELETE CASCADE,
  content TEXT,
  token_count INT,
  embedding VECTOR(1536)
);

-- ================================================
-- UltraMCP Core System Tables
-- ================================================

-- System status and health tracking
CREATE TABLE IF NOT EXISTS system_status (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    last_health_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service metrics aggregation
CREATE TABLE IF NOT EXISTS service_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    metric_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Chain-of-Debate (CoD) Service Schema
-- ================================================

-- CoD debates and orchestrations
CREATE TABLE IF NOT EXISTS cod_debates (
    id SERIAL PRIMARY KEY,
    debate_id VARCHAR(255) UNIQUE NOT NULL,
    topic TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    debate_type VARCHAR(100) DEFAULT 'standard',
    participants JSONB DEFAULT '[]',
    results JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- CoD debate messages and rounds
CREATE TABLE IF NOT EXISTS cod_debate_messages (
    id SERIAL PRIMARY KEY,
    debate_id VARCHAR(255) REFERENCES cod_debates(debate_id),
    round_number INTEGER DEFAULT 1,
    participant VARCHAR(100) NOT NULL,
    message_type VARCHAR(50) DEFAULT 'argument',
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Asterisk Security Service Schema
-- ================================================

-- Security scans and assessments
CREATE TABLE IF NOT EXISTS security_scans (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(255) UNIQUE NOT NULL,
    target_path TEXT NOT NULL,
    scan_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    findings JSONB DEFAULT '[]',
    severity_counts JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Security findings and vulnerabilities
CREATE TABLE IF NOT EXISTS security_findings (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(255) REFERENCES security_scans(scan_id),
    finding_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    file_path TEXT,
    line_number INTEGER,
    remediation TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Blockoli Code Intelligence Schema
-- ================================================

-- Code projects and indexing
CREATE TABLE IF NOT EXISTS code_projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    project_path TEXT NOT NULL,
    language VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Code analysis results
CREATE TABLE IF NOT EXISTS code_analysis (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) REFERENCES code_projects(project_id),
    analysis_type VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    results JSONB NOT NULL,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Voice System Schema
-- ================================================

-- Voice sessions and processing
CREATE TABLE IF NOT EXISTS voice_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    session_type VARCHAR(100) DEFAULT 'conversation',
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- Voice transcriptions and audio data
CREATE TABLE IF NOT EXISTS voice_transcriptions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES voice_sessions(session_id),
    audio_file_path TEXT,
    transcription TEXT,
    confidence_score NUMERIC(5,2),
    language VARCHAR(10) DEFAULT 'en',
    processing_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- DeepClaude Metacognitive Schema
-- ================================================

-- Reasoning sessions and decisions
CREATE TABLE IF NOT EXISTS reasoning_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    reasoning_type VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    reasoning_chain JSONB DEFAULT '[]',
    final_decision JSONB,
    confidence_metrics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ================================================
-- Claude Code Memory Schema
-- ================================================

-- Memory projects and semantic indexing
CREATE TABLE IF NOT EXISTS memory_projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    project_path TEXT NOT NULL,
    indexing_status VARCHAR(50) DEFAULT 'pending',
    semantic_metadata JSONB DEFAULT '{}',
    embedding_model VARCHAR(100) DEFAULT 'voyage-code-2',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_indexed TIMESTAMP
);

-- Semantic code embeddings
CREATE TABLE IF NOT EXISTS code_embeddings (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(255) REFERENCES memory_projects(project_id),
    file_path TEXT NOT NULL,
    code_block_hash VARCHAR(64) NOT NULL,
    embedding VECTOR(1024), -- VoyageAI Code embeddings
    code_content TEXT NOT NULL,
    semantic_tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Control Tower Orchestration Schema
-- ================================================

-- Workflow orchestrations
CREATE TABLE IF NOT EXISTS orchestration_workflows (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB NOT NULL,
    service_calls JSONB DEFAULT '[]',
    results JSONB,
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Service orchestration logs
CREATE TABLE IF NOT EXISTS orchestration_logs (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) REFERENCES orchestration_workflows(workflow_id),
    service_name VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    request_data JSONB,
    response_data JSONB,
    status VARCHAR(50) NOT NULL,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- WebUI Integration Schema
-- ================================================

-- WebUI user sessions and preferences
CREATE TABLE IF NOT EXISTS webui_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    preferences JSONB DEFAULT '{}',
    active_services JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WebUI pipeline executions
CREATE TABLE IF NOT EXISTS webui_pipeline_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES webui_sessions(session_id),
    pipeline_name VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ================================================
-- Indexes for Performance
-- ================================================

-- System monitoring indexes
CREATE INDEX IF NOT EXISTS idx_system_status_service ON system_status(service_name);
CREATE INDEX IF NOT EXISTS idx_service_metrics_timestamp ON service_metrics(timestamp);

-- CoD service indexes
CREATE INDEX IF NOT EXISTS idx_cod_debates_status ON cod_debates(status);
CREATE INDEX IF NOT EXISTS idx_cod_debates_created ON cod_debates(created_at);

-- Security service indexes
CREATE INDEX IF NOT EXISTS idx_security_scans_status ON security_scans(status);
CREATE INDEX IF NOT EXISTS idx_security_findings_severity ON security_findings(severity);

-- Code intelligence indexes
CREATE INDEX IF NOT EXISTS idx_code_projects_status ON code_projects(status);
CREATE INDEX IF NOT EXISTS idx_code_analysis_project ON code_analysis(project_id);

-- Memory service indexes
CREATE INDEX IF NOT EXISTS idx_memory_projects_status ON memory_projects(indexing_status);
CREATE INDEX IF NOT EXISTS idx_code_embeddings_project ON code_embeddings(project_id);
CREATE INDEX IF NOT EXISTS idx_code_embeddings_vector ON code_embeddings USING hnsw (embedding vector_cosine_ops);

-- Voice service indexes
CREATE INDEX IF NOT EXISTS idx_voice_sessions_status ON voice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_voice_transcriptions_session ON voice_transcriptions(session_id);

-- Orchestration indexes
CREATE INDEX IF NOT EXISTS idx_orchestration_workflows_status ON orchestration_workflows(status);
CREATE INDEX IF NOT EXISTS idx_orchestration_logs_workflow ON orchestration_logs(workflow_id);

-- WebUI indexes
CREATE INDEX IF NOT EXISTS idx_webui_sessions_user ON webui_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_webui_pipeline_executions_session ON webui_pipeline_executions(session_id);

-- ================================================
-- Row Level Security (RLS) Policies
-- ================================================

-- Enable RLS on user-specific tables
ALTER TABLE webui_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE webui_pipeline_executions ENABLE ROW LEVEL SECURITY;

-- RLS policies for WebUI sessions
CREATE POLICY "Users can view own sessions" ON webui_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions" ON webui_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON webui_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- RLS policies for pipeline executions
CREATE POLICY "Users can view own pipeline executions" ON webui_pipeline_executions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM webui_sessions 
            WHERE webui_sessions.session_id = webui_pipeline_executions.session_id 
            AND webui_sessions.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own pipeline executions" ON webui_pipeline_executions
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM webui_sessions 
            WHERE webui_sessions.session_id = webui_pipeline_executions.session_id 
            AND webui_sessions.user_id = auth.uid()
        )
    );

-- ================================================
-- Functions and Triggers
-- ================================================

-- Function to update timestamp on row changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_system_status_updated_at BEFORE UPDATE ON system_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to maintain WebUI session activity
CREATE OR REPLACE FUNCTION update_last_active()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_active = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_webui_sessions_last_active BEFORE UPDATE ON webui_sessions
    FOR EACH ROW EXECUTE FUNCTION update_last_active();

-- ================================================
-- Initial Data and Configuration
-- ================================================

-- Insert initial system status entries
INSERT INTO system_status (service_name, status) VALUES
    ('supabase-db', 'healthy'),
    ('supabase-auth', 'healthy'),
    ('supabase-rest', 'healthy'),
    ('supabase-realtime', 'healthy'),
    ('supabase-storage', 'healthy'),
    ('supabase-kong', 'healthy'),
    ('ultramcp-webui', 'starting'),
    ('ultramcp-cod-service', 'starting'),
    ('ultramcp-asterisk-mcp', 'starting'),
    ('ultramcp-context7', 'starting'),
    ('ultramcp-blockoli', 'starting'),
    ('ultramcp-voice', 'starting'),
    ('ultramcp-deepclaude', 'starting'),
    ('ultramcp-claude-memory', 'starting'),
    ('ultramcp-control-tower', 'starting'),
    ('ultramcp-unified-docs', 'starting')
ON CONFLICT (service_name) DO NOTHING;

-- Create default storage bucket for UltraMCP files
INSERT INTO storage.buckets (id, name, public) VALUES 
    ('ultramcp-data', 'UltraMCP Data Files', false),
    ('ultramcp-voice', 'UltraMCP Voice Files', false),
    ('ultramcp-logs', 'UltraMCP Log Files', false)
ON CONFLICT (id) DO NOTHING;

-- Set up storage policies for UltraMCP buckets
CREATE POLICY "Authenticated users can access UltraMCP data" ON storage.objects
    FOR ALL USING (bucket_id = 'ultramcp-data' AND auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can access voice files" ON storage.objects
    FOR ALL USING (bucket_id = 'ultramcp-voice' AND auth.role() = 'authenticated');

CREATE POLICY "Service role can access log files" ON storage.objects
    FOR ALL USING (bucket_id = 'ultramcp-logs' AND auth.role() = 'service_role');

-- ================================================
-- Views for Dashboard and Monitoring
-- ================================================

-- System health overview
CREATE OR REPLACE VIEW system_health_overview AS
SELECT 
    service_name,
    status,
    last_health_check,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_health_check)) as seconds_since_check
FROM system_status
ORDER BY service_name;

-- Service metrics summary
CREATE OR REPLACE VIEW service_metrics_summary AS
SELECT 
    service_name,
    metric_type,
    COUNT(*) as metric_count,
    AVG(metric_value) as avg_value,
    MAX(metric_value) as max_value,
    MIN(metric_value) as min_value
FROM service_metrics
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY service_name, metric_type
ORDER BY service_name, metric_type;

-- Active workflows overview
CREATE OR REPLACE VIEW active_workflows_overview AS
SELECT 
    workflow_type,
    status,
    COUNT(*) as workflow_count,
    AVG(EXTRACT(EPOCH FROM (COALESCE(completed_at, CURRENT_TIMESTAMP) - started_at))) as avg_duration_seconds
FROM orchestration_workflows
WHERE started_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY workflow_type, status
ORDER BY workflow_type, status;

COMMENT ON DATABASE postgres IS 'UltraMCP + Supabase Integrated Backend - Enterprise AI Platform with Complete Service Integration';
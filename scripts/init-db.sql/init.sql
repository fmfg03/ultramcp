-- UltraMCP Supreme Stack - Database Schema
-- Complete schema for all integrated services

-- ================================================
-- Core System Tables
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
    round_number INTEGER NOT NULL,
    participant_role VARCHAR(100) NOT NULL,
    message_content TEXT NOT NULL,
    reasoning JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Asterisk Security Service Schema
-- ================================================

-- Security scans
CREATE TABLE IF NOT EXISTS security_scans (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(255) UNIQUE NOT NULL,
    scan_type VARCHAR(100) NOT NULL,
    target_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    vulnerability_count INTEGER DEFAULT 0,
    risk_score NUMERIC DEFAULT 0,
    results JSONB,
    scan_options JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Security vulnerabilities
CREATE TABLE IF NOT EXISTS security_vulnerabilities (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(255) REFERENCES security_scans(scan_id),
    vulnerability_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    description TEXT,
    recommendation TEXT,
    cve_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance checks
CREATE TABLE IF NOT EXISTS compliance_checks (
    id SERIAL PRIMARY KEY,
    check_id VARCHAR(255) UNIQUE NOT NULL,
    compliance_framework VARCHAR(100) NOT NULL,
    target_system TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    compliance_score NUMERIC DEFAULT 0,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ================================================
-- Blockoli Code Intelligence Schema
-- ================================================

-- Indexed projects
CREATE TABLE IF NOT EXISTS blockoli_projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) UNIQUE NOT NULL,
    project_path TEXT NOT NULL,
    index_status VARCHAR(50) DEFAULT 'pending',
    total_files INTEGER DEFAULT 0,
    indexed_files INTEGER DEFAULT 0,
    project_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_indexed TIMESTAMP
);

-- Code search queries and results
CREATE TABLE IF NOT EXISTS blockoli_searches (
    id SERIAL PRIMARY KEY,
    search_id VARCHAR(255) UNIQUE NOT NULL,
    project_name VARCHAR(255) REFERENCES blockoli_projects(project_name),
    query_text TEXT NOT NULL,
    search_type VARCHAR(100) DEFAULT 'semantic',
    results_count INTEGER DEFAULT 0,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Code intelligence debates
CREATE TABLE IF NOT EXISTS blockoli_code_debates (
    id SERIAL PRIMARY KEY,
    debate_id VARCHAR(255) UNIQUE NOT NULL,
    project_name VARCHAR(255) REFERENCES blockoli_projects(project_name),
    topic TEXT NOT NULL,
    intelligence_mode VARCHAR(100) DEFAULT 'basic',
    status VARCHAR(50) DEFAULT 'pending',
    code_context JSONB,
    debate_results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ================================================
-- Voice System Schema
-- ================================================

-- Voice sessions
CREATE TABLE IF NOT EXISTS voice_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    session_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    participant_count INTEGER DEFAULT 0,
    ai_enabled BOOLEAN DEFAULT false,
    real_time BOOLEAN DEFAULT false,
    websocket_url TEXT,
    session_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- Voice transcriptions
CREATE TABLE IF NOT EXISTS voice_transcriptions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES voice_sessions(session_id),
    transcription_id VARCHAR(255) UNIQUE NOT NULL,
    speaker_id VARCHAR(100),
    transcription_text TEXT NOT NULL,
    confidence_score NUMERIC,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    audio_duration NUMERIC
);

-- Voice AI interactions
CREATE TABLE IF NOT EXISTS voice_ai_interactions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES voice_sessions(session_id),
    interaction_id VARCHAR(255) UNIQUE NOT NULL,
    user_input TEXT,
    ai_response TEXT,
    processing_time NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- DeepClaude Metacognitive Service Schema
-- ================================================

-- Reasoning sessions
CREATE TABLE IF NOT EXISTS deepclaude_reasoning (
    id SERIAL PRIMARY KEY,
    reasoning_id VARCHAR(255) UNIQUE NOT NULL,
    topic TEXT NOT NULL,
    reasoning_mode VARCHAR(100) DEFAULT 'analytical',
    depth VARCHAR(50) DEFAULT 'standard',
    status VARCHAR(50) DEFAULT 'pending',
    context_data JSONB,
    reasoning_steps JSONB,
    final_conclusion TEXT,
    confidence_score NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Metacognitive insights
CREATE TABLE IF NOT EXISTS deepclaude_insights (
    id SERIAL PRIMARY KEY,
    reasoning_id VARCHAR(255) REFERENCES deepclaude_reasoning(reasoning_id),
    insight_type VARCHAR(100) NOT NULL,
    insight_content TEXT NOT NULL,
    relevance_score NUMERIC,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Control Tower Orchestration Schema
-- ================================================

-- Orchestration tasks
CREATE TABLE IF NOT EXISTS control_tower_orchestrations (
    id SERIAL PRIMARY KEY,
    orchestration_id VARCHAR(255) UNIQUE NOT NULL,
    orchestration_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    services_involved JSONB DEFAULT '[]',
    input_data JSONB,
    results JSONB,
    error_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Service coordination logs
CREATE TABLE IF NOT EXISTS control_tower_coordination_logs (
    id SERIAL PRIMARY KEY,
    orchestration_id VARCHAR(255) REFERENCES control_tower_orchestrations(orchestration_id),
    service_name VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    request_data JSONB,
    response_data JSONB,
    execution_time NUMERIC,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System monitoring events
CREATE TABLE IF NOT EXISTS control_tower_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source_service VARCHAR(100),
    event_data JSONB,
    severity VARCHAR(50) DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- Integration and Cross-Service Tables
-- ================================================

-- Service dependencies mapping
CREATE TABLE IF NOT EXISTS service_dependencies (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    depends_on VARCHAR(100) NOT NULL,
    dependency_type VARCHAR(100) DEFAULT 'required',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cross-service task tracking
CREATE TABLE IF NOT EXISTS cross_service_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    initiating_service VARCHAR(100) NOT NULL,
    involved_services JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'pending',
    task_data JSONB,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ================================================
-- Indexes for Performance
-- ================================================

-- System status indexes
CREATE INDEX IF NOT EXISTS idx_system_status_service ON system_status(service_name);
CREATE INDEX IF NOT EXISTS idx_system_status_timestamp ON system_status(last_health_check);

-- CoD debates indexes
CREATE INDEX IF NOT EXISTS idx_cod_debates_status ON cod_debates(status);
CREATE INDEX IF NOT EXISTS idx_cod_debates_created ON cod_debates(created_at);
CREATE INDEX IF NOT EXISTS idx_cod_debate_messages_debate_id ON cod_debate_messages(debate_id);

-- Security scans indexes
CREATE INDEX IF NOT EXISTS idx_security_scans_status ON security_scans(status);
CREATE INDEX IF NOT EXISTS idx_security_scans_created ON security_scans(created_at);
CREATE INDEX IF NOT EXISTS idx_security_vulnerabilities_scan_id ON security_vulnerabilities(scan_id);

-- Blockoli indexes
CREATE INDEX IF NOT EXISTS idx_blockoli_projects_status ON blockoli_projects(index_status);
CREATE INDEX IF NOT EXISTS idx_blockoli_searches_project ON blockoli_searches(project_name);
CREATE INDEX IF NOT EXISTS idx_blockoli_code_debates_project ON blockoli_code_debates(project_name);

-- Voice system indexes
CREATE INDEX IF NOT EXISTS idx_voice_sessions_status ON voice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_voice_transcriptions_session ON voice_transcriptions(session_id);

-- DeepClaude indexes
CREATE INDEX IF NOT EXISTS idx_deepclaude_reasoning_status ON deepclaude_reasoning(status);
CREATE INDEX IF NOT EXISTS idx_deepclaude_insights_reasoning_id ON deepclaude_insights(reasoning_id);

-- Control Tower indexes
CREATE INDEX IF NOT EXISTS idx_control_tower_orchestrations_status ON control_tower_orchestrations(status);
CREATE INDEX IF NOT EXISTS idx_control_tower_coordination_logs_orchestration ON control_tower_coordination_logs(orchestration_id);

-- Cross-service indexes
CREATE INDEX IF NOT EXISTS idx_cross_service_tasks_status ON cross_service_tasks(status);
CREATE INDEX IF NOT EXISTS idx_cross_service_tasks_initiating_service ON cross_service_tasks(initiating_service);

-- ================================================
-- Initial Data - Service Dependencies
-- ================================================

INSERT INTO service_dependencies (service_name, depends_on, dependency_type) VALUES
('cod-service', 'database', 'required'),
('asterisk-mcp', 'database', 'required'),
('blockoli', 'database', 'required'),
('voice-system', 'database', 'required'),
('deepclaude', 'database', 'required'),
('control-tower', 'database', 'required'),
('control-tower', 'cod-service', 'orchestration'),
('control-tower', 'asterisk-mcp', 'orchestration'),
('control-tower', 'blockoli', 'orchestration'),
('control-tower', 'voice-system', 'orchestration'),
('control-tower', 'deepclaude', 'orchestration'),
('blockoli', 'cod-service', 'integration'),
('voice-system', 'cod-service', 'integration'),
('deepclaude', 'cod-service', 'integration')
ON CONFLICT DO NOTHING;

-- ================================================
-- Views for System Monitoring
-- ================================================

-- Overall system health view
CREATE OR REPLACE VIEW system_health_overview AS
SELECT 
    COUNT(*) as total_services,
    COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy_services,
    COUNT(CASE WHEN status = 'unhealthy' THEN 1 END) as unhealthy_services,
    ROUND(
        (COUNT(CASE WHEN status = 'healthy' THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC) * 100, 
        2
    ) as health_percentage,
    MAX(last_health_check) as last_system_check
FROM system_status;

-- Active tasks summary
CREATE OR REPLACE VIEW active_tasks_summary AS
SELECT 
    'cod_debates' as task_type,
    COUNT(*) as active_count,
    'cod-service' as service_name
FROM cod_debates 
WHERE status IN ('pending', 'in_progress')
UNION ALL
SELECT 
    'security_scans' as task_type,
    COUNT(*) as active_count,
    'asterisk-mcp' as service_name
FROM security_scans 
WHERE status IN ('pending', 'running')
UNION ALL
SELECT 
    'code_debates' as task_type,
    COUNT(*) as active_count,
    'blockoli' as service_name
FROM blockoli_code_debates 
WHERE status IN ('pending', 'running')
UNION ALL
SELECT 
    'voice_sessions' as task_type,
    COUNT(*) as active_count,
    'voice-system' as service_name
FROM voice_sessions 
WHERE status = 'active'
UNION ALL
SELECT 
    'reasoning_tasks' as task_type,
    COUNT(*) as active_count,
    'deepclaude' as service_name
FROM deepclaude_reasoning 
WHERE status IN ('pending', 'processing')
UNION ALL
SELECT 
    'orchestrations' as task_type,
    COUNT(*) as active_count,
    'control-tower' as service_name
FROM control_tower_orchestrations 
WHERE status IN ('pending', 'running');

-- Service performance metrics
CREATE OR REPLACE VIEW service_performance_metrics AS
SELECT 
    service_name,
    COUNT(*) as total_requests,
    AVG(CASE WHEN metric_type = 'response_time' THEN metric_value END) as avg_response_time,
    MAX(timestamp) as last_metric_update
FROM service_metrics 
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY service_name;

COMMENT ON SCHEMA public IS 'UltraMCP Supreme Stack - Complete integrated database schema for all microservices';
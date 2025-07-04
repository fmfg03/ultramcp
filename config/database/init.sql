-- UltraMCP ContextBuilderAgent 2.0 - Complete Database Schema
-- PostgreSQL Database Initialization for Production

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS contextbuilder;

-- Connect to the database
\c contextbuilder;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- Core ContextBuilderAgent Tables
-- =============================================================================

-- Context validation and coherence tracking
CREATE TABLE IF NOT EXISTS context_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_id VARCHAR(255) NOT NULL,
    validation_type VARCHAR(50) NOT NULL,
    coherence_score DECIMAL(5,3) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    validation_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_context_validations_context_id (context_id),
    INDEX idx_context_validations_created_at (created_at),
    INDEX idx_context_validations_coherence_score (coherence_score)
);

-- Belief revision tracking
CREATE TABLE IF NOT EXISTS belief_revisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_id VARCHAR(255) NOT NULL,
    original_belief JSONB NOT NULL,
    revised_belief JSONB NOT NULL,
    revision_reason TEXT,
    confidence_score DECIMAL(5,3) NOT NULL,
    revision_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_belief_revisions_context_id (context_id),
    INDEX idx_belief_revisions_created_at (created_at),
    INDEX idx_belief_revisions_confidence_score (confidence_score)
);

-- Contradiction resolution history
CREATE TABLE IF NOT EXISTS contradiction_resolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_id VARCHAR(255) NOT NULL,
    contradiction_type VARCHAR(50) NOT NULL,
    contradictory_elements JSONB NOT NULL,
    resolution_strategy VARCHAR(100) NOT NULL,
    resolution_result JSONB NOT NULL,
    confidence_score DECIMAL(5,3) NOT NULL,
    processing_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_contradiction_resolutions_context_id (context_id),
    INDEX idx_contradiction_resolutions_created_at (created_at),
    INDEX idx_contradiction_resolutions_type (contradiction_type)
);

-- Utility predictions and learning
CREATE TABLE IF NOT EXISTS utility_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_id VARCHAR(255) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,
    predicted_utility DECIMAL(10,6) NOT NULL,
    actual_utility DECIMAL(10,6),
    prediction_accuracy DECIMAL(5,3),
    features JSONB NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluated_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_utility_predictions_context_id (context_id),
    INDEX idx_utility_predictions_created_at (created_at),
    INDEX idx_utility_predictions_accuracy (prediction_accuracy)
);

-- Context drift detection
CREATE TABLE IF NOT EXISTS context_drift_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_id VARCHAR(255) NOT NULL,
    drift_type VARCHAR(50) NOT NULL,
    drift_magnitude DECIMAL(10,6) NOT NULL,
    drift_direction VARCHAR(20) NOT NULL,
    baseline_metrics JSONB NOT NULL,
    current_metrics JSONB NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_context_drift_events_context_id (context_id),
    INDEX idx_context_drift_events_detected_at (detected_at),
    INDEX idx_context_drift_events_magnitude (drift_magnitude)
);

-- =============================================================================
-- PromptAssemblerAgent Tables
-- =============================================================================

-- Prompt templates and management
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    template_content TEXT NOT NULL,
    variables JSONB NOT NULL,
    complexity_level VARCHAR(20) NOT NULL,
    version VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_prompt_templates_name (name),
    INDEX idx_prompt_templates_complexity (complexity_level),
    INDEX idx_prompt_templates_active (is_active)
);

-- Prompt assembly history
CREATE TABLE IF NOT EXISTS prompt_assemblies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prompt_templates(id),
    assembled_prompt TEXT NOT NULL,
    context_variables JSONB NOT NULL,
    semantic_score DECIMAL(5,3) NOT NULL,
    optimization_level VARCHAR(20) NOT NULL,
    processing_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_prompt_assemblies_template_id (template_id),
    INDEX idx_prompt_assemblies_created_at (created_at),
    INDEX idx_prompt_assemblies_semantic_score (semantic_score)
);

-- ML optimization tracking
CREATE TABLE IF NOT EXISTS prompt_optimizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_assembly_id UUID REFERENCES prompt_assemblies(id),
    optimization_type VARCHAR(50) NOT NULL,
    original_features JSONB NOT NULL,
    optimized_features JSONB NOT NULL,
    performance_improvement DECIMAL(5,3) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_prompt_optimizations_assembly_id (prompt_assembly_id),
    INDEX idx_prompt_optimizations_created_at (created_at),
    INDEX idx_prompt_optimizations_improvement (performance_improvement)
);

-- =============================================================================
-- ContextObservatory Tables
-- =============================================================================

-- System metrics and monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20) NOT NULL,
    tags JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_system_metrics_service_name (service_name),
    INDEX idx_system_metrics_collected_at (collected_at),
    INDEX idx_system_metrics_type (metric_type)
);

-- Health checks and status
CREATE TABLE IF NOT EXISTS health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_message TEXT,
    details JSONB,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_health_checks_service_name (service_name),
    INDEX idx_health_checks_checked_at (checked_at),
    INDEX idx_health_checks_status (status)
);

-- Alerts and notifications
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_alerts_service_name (service_name),
    INDEX idx_alerts_created_at (created_at),
    INDEX idx_alerts_severity (severity),
    INDEX idx_alerts_resolved (is_resolved)
);

-- Performance trends
CREATE TABLE IF NOT EXISTS performance_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    time_window VARCHAR(20) NOT NULL,
    trend_direction VARCHAR(20) NOT NULL,
    trend_magnitude DECIMAL(10,6) NOT NULL,
    confidence_score DECIMAL(5,3) NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_performance_trends_service_name (service_name),
    INDEX idx_performance_trends_calculated_at (calculated_at),
    INDEX idx_performance_trends_confidence (confidence_score)
);

-- =============================================================================
-- DeterministicDebugMode Tables
-- =============================================================================

-- Debug sessions
CREATE TABLE IF NOT EXISTS debug_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255) NOT NULL,
    debug_level VARCHAR(20) NOT NULL,
    random_seed INTEGER NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    session_config JSONB NOT NULL,
    
    INDEX idx_debug_sessions_name (session_name),
    INDEX idx_debug_sessions_started_at (started_at),
    INDEX idx_debug_sessions_ended_at (ended_at)
);

-- System snapshots
CREATE TABLE IF NOT EXISTS system_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES debug_sessions(id),
    snapshot_type VARCHAR(50) NOT NULL,
    system_state JSONB NOT NULL,
    state_hash VARCHAR(64) NOT NULL,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_system_snapshots_session_id (session_id),
    INDEX idx_system_snapshots_captured_at (captured_at),
    INDEX idx_system_snapshots_hash (state_hash)
);

-- Operation tracing
CREATE TABLE IF NOT EXISTS operation_traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES debug_sessions(id),
    operation_type VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    traced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_operation_traces_session_id (session_id),
    INDEX idx_operation_traces_traced_at (traced_at),
    INDEX idx_operation_traces_operation_type (operation_type)
);

-- =============================================================================
-- ContextMemoryTuner Tables
-- =============================================================================

-- Memory optimization events
CREATE TABLE IF NOT EXISTS memory_optimizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    optimization_type VARCHAR(50) NOT NULL,
    context_id VARCHAR(255) NOT NULL,
    before_metrics JSONB NOT NULL,
    after_metrics JSONB NOT NULL,
    improvement_score DECIMAL(5,3) NOT NULL,
    tuning_parameters JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_memory_optimizations_context_id (context_id),
    INDEX idx_memory_optimizations_created_at (created_at),
    INDEX idx_memory_optimizations_improvement (improvement_score)
);

-- Learning adaptation history
CREATE TABLE IF NOT EXISTS learning_adaptations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    adaptation_type VARCHAR(50) NOT NULL,
    context_pattern VARCHAR(255) NOT NULL,
    learning_rate DECIMAL(8,6) NOT NULL,
    adaptation_impact JSONB NOT NULL,
    effectiveness_score DECIMAL(5,3) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_learning_adaptations_pattern (context_pattern),
    INDEX idx_learning_adaptations_created_at (created_at),
    INDEX idx_learning_adaptations_effectiveness (effectiveness_score)
);

-- =============================================================================
-- Semantic Coherence Bus Tables
-- =============================================================================

-- Coherence events and streaming
CREATE TABLE IF NOT EXISTS coherence_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    source_service VARCHAR(100) NOT NULL,
    target_service VARCHAR(100),
    event_data JSONB NOT NULL,
    coherence_score DECIMAL(5,3) NOT NULL,
    processing_priority INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_coherence_events_source_service (source_service),
    INDEX idx_coherence_events_created_at (created_at),
    INDEX idx_coherence_events_coherence_score (coherence_score)
);

-- Cross-service coordination
CREATE TABLE IF NOT EXISTS service_coordination (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    coordination_type VARCHAR(50) NOT NULL,
    participating_services JSONB NOT NULL,
    coordination_state VARCHAR(20) NOT NULL,
    coordination_result JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_service_coordination_type (coordination_type),
    INDEX idx_service_coordination_started_at (started_at),
    INDEX idx_service_coordination_state (coordination_state)
);

-- =============================================================================
-- Performance Indexes and Optimizations
-- =============================================================================

-- Time-series data partitioning for metrics
CREATE TABLE IF NOT EXISTS system_metrics_partitioned (
    LIKE system_metrics INCLUDING ALL
) PARTITION BY RANGE (collected_at);

-- Create monthly partitions for the next 12 months
DO $$
DECLARE
    start_date DATE := date_trunc('month', CURRENT_DATE);
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..11 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'system_metrics_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF system_metrics_partitioned 
                       FOR VALUES FROM (%L) TO (%L)', 
                       partition_name, start_date, end_date);
        
        start_date := end_date;
    END LOOP;
END $$;

-- =============================================================================
-- Views for Common Queries
-- =============================================================================

-- System health overview
CREATE OR REPLACE VIEW system_health_overview AS
SELECT 
    service_name,
    COUNT(*) as total_checks,
    COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy_checks,
    AVG(response_time_ms) as avg_response_time,
    MAX(checked_at) as last_check_time
FROM health_checks 
WHERE checked_at > NOW() - INTERVAL '1 hour'
GROUP BY service_name;

-- Context coherence summary
CREATE OR REPLACE VIEW context_coherence_summary AS
SELECT 
    context_id,
    COUNT(*) as total_validations,
    AVG(coherence_score) as avg_coherence_score,
    MAX(coherence_score) as max_coherence_score,
    MIN(coherence_score) as min_coherence_score,
    MAX(created_at) as last_validation_time
FROM context_validations
GROUP BY context_id;

-- Active alerts summary
CREATE OR REPLACE VIEW active_alerts_summary AS
SELECT 
    service_name,
    severity,
    COUNT(*) as alert_count,
    MIN(created_at) as oldest_alert,
    MAX(created_at) as newest_alert
FROM alerts
WHERE is_resolved = FALSE
GROUP BY service_name, severity;

-- =============================================================================
-- Stored Procedures for Common Operations
-- =============================================================================

-- Function to calculate coherence trend
CREATE OR REPLACE FUNCTION calculate_coherence_trend(
    p_context_id VARCHAR(255),
    p_time_window INTERVAL DEFAULT '1 hour'
) RETURNS DECIMAL(5,3) AS $$
DECLARE
    trend_score DECIMAL(5,3);
BEGIN
    WITH trend_data AS (
        SELECT 
            coherence_score,
            created_at,
            ROW_NUMBER() OVER (ORDER BY created_at) as rn,
            COUNT(*) OVER () as total_count
        FROM context_validations
        WHERE context_id = p_context_id
        AND created_at > NOW() - p_time_window
        ORDER BY created_at
    )
    SELECT 
        CASE 
            WHEN total_count < 2 THEN 0.0
            ELSE (
                SELECT corr(rn, coherence_score) 
                FROM trend_data
            )
        END
    INTO trend_score;
    
    RETURN COALESCE(trend_score, 0.0);
END;
$$ LANGUAGE plpgsql;

-- Function to get service health score
CREATE OR REPLACE FUNCTION get_service_health_score(
    p_service_name VARCHAR(100),
    p_time_window INTERVAL DEFAULT '15 minutes'
) RETURNS DECIMAL(5,3) AS $$
DECLARE
    health_score DECIMAL(5,3);
BEGIN
    WITH health_data AS (
        SELECT 
            COUNT(*) as total_checks,
            COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy_checks,
            AVG(response_time_ms) as avg_response_time
        FROM health_checks
        WHERE service_name = p_service_name
        AND checked_at > NOW() - p_time_window
    )
    SELECT 
        CASE 
            WHEN total_checks = 0 THEN 0.0
            ELSE (
                (healthy_checks::DECIMAL / total_checks::DECIMAL) * 0.7 +
                (CASE WHEN avg_response_time < 100 THEN 1.0 
                      WHEN avg_response_time < 500 THEN 0.8
                      WHEN avg_response_time < 1000 THEN 0.6
                      ELSE 0.4 END) * 0.3
            )
        END
    INTO health_score
    FROM health_data;
    
    RETURN COALESCE(health_score, 0.0);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Triggers for Automatic Updates
-- =============================================================================

-- Update timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to relevant tables
CREATE TRIGGER update_context_validations_updated_at
    BEFORE UPDATE ON context_validations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_templates_updated_at
    BEFORE UPDATE ON prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Cleanup and Maintenance
-- =============================================================================

-- Create cleanup function for old data
CREATE OR REPLACE FUNCTION cleanup_old_data() RETURNS VOID AS $$
BEGIN
    -- Delete old metrics (older than 30 days)
    DELETE FROM system_metrics 
    WHERE collected_at < NOW() - INTERVAL '30 days';
    
    -- Delete old health checks (older than 7 days)
    DELETE FROM health_checks 
    WHERE checked_at < NOW() - INTERVAL '7 days';
    
    -- Delete resolved alerts (older than 30 days)
    DELETE FROM alerts 
    WHERE is_resolved = TRUE AND resolved_at < NOW() - INTERVAL '30 days';
    
    -- Delete old debug sessions (older than 7 days)
    DELETE FROM debug_sessions 
    WHERE ended_at < NOW() - INTERVAL '7 days';
    
    -- Vacuum and analyze tables
    VACUUM ANALYZE;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contextbuilder;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contextbuilder;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO contextbuilder;

-- Create user for application if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'contextbuilder') THEN
        CREATE USER contextbuilder WITH PASSWORD 'contextbuilder_secure_2024';
        GRANT ALL PRIVILEGES ON DATABASE contextbuilder TO contextbuilder;
    END IF;
END $$;

-- Final message
SELECT 'UltraMCP ContextBuilderAgent 2.0 database initialized successfully!' AS status;
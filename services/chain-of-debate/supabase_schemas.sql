-- ============================================================================
-- Chain-of-Debate Dinámico - Supabase Database Schemas
-- Sistema de superinteligencia colectiva con debate multi-LLM
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Tabla principal de tareas de debate
CREATE TABLE debate_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 3,
    input_content TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE,
    
    -- Results
    consensus_result TEXT,
    consensus_score FLOAT,
    quality_score FLOAT,
    
    -- Cost and performance
    total_cost FLOAT DEFAULT 0.0,
    total_tokens INTEGER DEFAULT 0,
    total_duration FLOAT DEFAULT 0.0,
    
    -- Human intervention
    human_intervention_used BOOLEAN DEFAULT FALSE,
    human_review_required BOOLEAN DEFAULT FALSE,
    human_timeout_at TIMESTAMP WITH TIME ZONE,
    
    -- Routing information
    routed_destination VARCHAR(255),
    routing_confidence FLOAT,
    
    -- Indexing
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'consensus_reached', 'human_intervention', 'completed', 'failed', 'timeout')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 5),
    CONSTRAINT valid_scores CHECK (consensus_score >= 0 AND consensus_score <= 1 AND quality_score >= 0 AND quality_score <= 1)
);

-- Índices para optimización
CREATE INDEX idx_debate_tasks_status ON debate_tasks(status);
CREATE INDEX idx_debate_tasks_created_at ON debate_tasks(created_at);
CREATE INDEX idx_debate_tasks_client_id ON debate_tasks(client_id);
CREATE INDEX idx_debate_tasks_domain ON debate_tasks(domain);
CREATE INDEX idx_debate_tasks_priority ON debate_tasks(priority);

-- Tabla de rondas de debate
CREATE TABLE debate_rounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES debate_tasks(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    round_type VARCHAR(50) NOT NULL,
    topic VARCHAR(500),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration FLOAT,
    
    -- Results
    consensus_score FLOAT,
    synthesis TEXT,
    
    -- Metadata
    participants JSONB DEFAULT '[]',
    round_metadata JSONB DEFAULT '{}',
    
    UNIQUE(task_id, round_number),
    CONSTRAINT valid_consensus_score CHECK (consensus_score >= 0 AND consensus_score <= 1)
);

CREATE INDEX idx_debate_rounds_task_id ON debate_rounds(task_id);
CREATE INDEX idx_debate_rounds_round_number ON debate_rounds(round_number);

-- Tabla de respuestas de modelos individuales
CREATE TABLE model_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    round_id UUID NOT NULL REFERENCES debate_rounds(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES debate_tasks(id) ON DELETE CASCADE,
    
    -- Model information
    model_name VARCHAR(100) NOT NULL,
    model_provider VARCHAR(50) NOT NULL,
    role_assigned VARCHAR(100),
    
    -- Response content
    content TEXT NOT NULL,
    reasoning TEXT,
    confidence FLOAT,
    
    -- Performance metrics
    response_time FLOAT,
    tokens_used INTEGER DEFAULT 0,
    cost FLOAT DEFAULT 0.0,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Timing
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Embeddings for similarity analysis
    content_embedding VECTOR(1536),
    
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX idx_model_responses_round_id ON model_responses(round_id);
CREATE INDEX idx_model_responses_task_id ON model_responses(task_id);
CREATE INDEX idx_model_responses_model_name ON model_responses(model_name);
CREATE INDEX idx_model_responses_success ON model_responses(success);

-- ============================================================================
-- ROLE ASSIGNMENT TABLES
-- ============================================================================

-- Tabla de asignaciones de roles dinámicos
CREATE TABLE role_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES debate_tasks(id) ON DELETE CASCADE,
    
    -- Assignment details
    model_name VARCHAR(100) NOT NULL,
    role_type VARCHAR(100) NOT NULL,
    assignment_reason TEXT,
    confidence FLOAT,
    
    -- Context analysis that led to assignment
    context_factors JSONB DEFAULT '{}',
    analysis_metadata JSONB DEFAULT '{}',
    
    -- Timing
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(task_id, model_name),
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX idx_role_assignments_task_id ON role_assignments(task_id);
CREATE INDEX idx_role_assignments_role_type ON role_assignments(role_type);

-- ============================================================================
-- HUMAN INTERVENTION TABLES
-- ============================================================================

-- Tabla de intervenciones humanas
CREATE TABLE human_interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES debate_tasks(id) ON DELETE CASCADE,
    
    -- Intervention details
    intervention_type VARCHAR(50) NOT NULL,
    original_result TEXT,
    human_result TEXT,
    intervention_reason TEXT,
    
    -- User information
    user_id VARCHAR(255),
    user_role VARCHAR(100),
    
    -- Performance impact
    quality_improvement FLOAT,
    time_spent_seconds INTEGER,
    intervention_cost FLOAT DEFAULT 1.0,
    
    -- Timing
    intervention_requested_at TIMESTAMP WITH TIME ZONE,
    intervention_completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    timeout_at TIMESTAMP WITH TIME ZONE,
    
    -- Feedback
    user_satisfaction INTEGER, -- 1-5 scale
    outcome_success BOOLEAN,
    
    CONSTRAINT valid_intervention_type CHECK (intervention_type IN ('approval', 'modification', 'rejection', 'escalation')),
    CONSTRAINT valid_satisfaction CHECK (user_satisfaction >= 1 AND user_satisfaction <= 5)
);

CREATE INDEX idx_human_interventions_task_id ON human_interventions(task_id);
CREATE INDEX idx_human_interventions_type ON human_interventions(intervention_type);
CREATE INDEX idx_human_interventions_completed_at ON human_interventions(intervention_completed_at);

-- ============================================================================
-- SHADOW LEARNING TABLES
-- ============================================================================

-- Tabla de eventos de aprendizaje
CREATE TABLE shadow_learning_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    task_id UUID NOT NULL REFERENCES debate_tasks(id) ON DELETE CASCADE,
    
    -- Event details
    domain VARCHAR(50) NOT NULL,
    original_input TEXT NOT NULL,
    model_outputs JSONB NOT NULL,
    final_decision TEXT,
    
    -- Human intervention data
    human_intervention JSONB,
    client_feedback TEXT,
    
    -- Outcome metrics
    outcome_success BOOLEAN,
    outcome_metrics JSONB DEFAULT '{}',
    
    -- Context for learning
    context_factors JSONB DEFAULT '{}',
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Embeddings for pattern analysis
    input_embedding VECTOR(1536),
    decision_embedding VECTOR(1536)
);

CREATE INDEX idx_shadow_learning_task_id ON shadow_learning_events(task_id);
CREATE INDEX idx_shadow_learning_domain ON shadow_learning_events(domain);
CREATE INDEX idx_shadow_learning_timestamp ON shadow_learning_events(timestamp);
CREATE INDEX idx_shadow_learning_outcome ON shadow_learning_events(outcome_success);

-- Tabla de patrones de aprendizaje identificados
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Pattern details
    domain VARCHAR(50) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    confidence FLOAT,
    frequency INTEGER DEFAULT 1,
    
    -- Pattern data
    examples JSONB DEFAULT '[]',
    improvement_suggestions JSONB DEFAULT '[]',
    
    -- Discovery metadata
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Related events
    related_event_ids JSONB DEFAULT '[]',
    
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX idx_learning_patterns_domain ON learning_patterns(domain);
CREATE INDEX idx_learning_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX idx_learning_patterns_confidence ON learning_patterns(confidence);

-- Tabla de triggers de reentrenamiento
CREATE TABLE retraining_triggers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trigger_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Trigger details
    domain VARCHAR(50) NOT NULL,
    threshold_met BOOLEAN DEFAULT FALSE,
    data_points_available INTEGER,
    quality_improvement_potential FLOAT,
    
    -- Suggestions
    suggested_improvements JSONB DEFAULT '[]',
    
    -- Status
    executed BOOLEAN DEFAULT FALSE,
    execution_results JSONB,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_retraining_triggers_domain ON retraining_triggers(domain);
CREATE INDEX idx_retraining_triggers_executed ON retraining_triggers(executed);

-- ============================================================================
-- DECISION REPLAY TABLES
-- ============================================================================

-- Tabla de replays de decisiones para auditoría evolutiva
CREATE TABLE decision_replays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    replay_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Original decision reference
    original_task_id UUID REFERENCES debate_tasks(id),
    original_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Replay details
    replay_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Input/Output comparison
    original_input TEXT,
    original_output TEXT,
    original_cost FLOAT DEFAULT 0.0,
    original_duration FLOAT DEFAULT 0.0,
    
    replay_output TEXT,
    replay_cost FLOAT DEFAULT 0.0,
    replay_duration FLOAT DEFAULT 0.0,
    
    -- Improvement analysis
    improvement_score FLOAT DEFAULT 0.0,
    improvement_types JSONB DEFAULT '[]',
    differences_analysis JSONB DEFAULT '{}',
    
    -- System configuration comparison
    system_config_original JSONB DEFAULT '{}',
    system_config_current JSONB DEFAULT '{}',
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    CONSTRAINT valid_improvement_score CHECK (improvement_score >= 0 AND improvement_score <= 1)
);

CREATE INDEX idx_decision_replays_original_task ON decision_replays(original_task_id);
CREATE INDEX idx_decision_replays_timestamp ON decision_replays(replay_timestamp);
CREATE INDEX idx_decision_replays_improvement ON decision_replays(improvement_score);

-- ============================================================================
-- MODEL RESILIENCE TABLES
-- ============================================================================

-- Tabla de llamadas a modelos para circuit breaker tracking
CREATE TABLE model_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Model information
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    
    -- Call details
    success BOOLEAN NOT NULL,
    response_time FLOAT,
    tokens_used INTEGER DEFAULT 0,
    cost FLOAT DEFAULT 0.0,
    error_message TEXT,
    
    -- Context
    task_id UUID REFERENCES debate_tasks(id),
    call_context JSONB DEFAULT '{}',
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_model_calls_provider ON model_calls(provider);
CREATE INDEX idx_model_calls_success ON model_calls(success);
CREATE INDEX idx_model_calls_timestamp ON model_calls(timestamp);
CREATE INDEX idx_model_calls_task_id ON model_calls(task_id);

-- Tabla de estado de circuit breakers
CREATE TABLE circuit_breaker_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) UNIQUE NOT NULL,
    
    -- Circuit breaker state
    state VARCHAR(20) NOT NULL DEFAULT 'closed',
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    
    -- Health metrics
    success_rate FLOAT DEFAULT 1.0,
    avg_response_time FLOAT DEFAULT 0.0,
    
    -- Status tracking
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_state CHECK (state IN ('closed', 'open', 'half_open'))
);

CREATE INDEX idx_circuit_breaker_provider ON circuit_breaker_states(provider);
CREATE INDEX idx_circuit_breaker_state ON circuit_breaker_states(state);

-- ============================================================================
-- TASK ROUTING TABLES
-- ============================================================================

-- Tabla de decisiones de routing
CREATE TABLE routing_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES debate_tasks(id) ON DELETE CASCADE,
    
    -- Routing details
    destination_id VARCHAR(255) NOT NULL,
    destination_type VARCHAR(50) NOT NULL,
    routing_reason TEXT,
    confidence FLOAT,
    
    -- Routing performance
    routing_time FLOAT,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    actual_completion TIMESTAMP WITH TIME ZONE,
    
    -- Fallback information
    fallback_destinations JSONB DEFAULT '[]',
    fallback_used BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    routing_metadata JSONB DEFAULT '{}',
    
    -- Timing
    routed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX idx_routing_decisions_task_id ON routing_decisions(task_id);
CREATE INDEX idx_routing_decisions_destination ON routing_decisions(destination_id);
CREATE INDEX idx_routing_decisions_routed_at ON routing_decisions(routed_at);

-- Tabla de servidores MCP disponibles
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    server_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Server details
    server_uri TEXT NOT NULL,
    capabilities JSONB DEFAULT '[]',
    priority_domains JSONB DEFAULT '[]',
    
    -- Health status
    status VARCHAR(50) DEFAULT 'unknown',
    success_rate FLOAT DEFAULT 0.0,
    avg_response_time FLOAT DEFAULT 0.0,
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    -- Load metrics
    current_load FLOAT DEFAULT 0.0,
    total_requests INTEGER DEFAULT 0,
    
    -- Metadata
    server_metadata JSONB DEFAULT '{}',
    
    -- Timing
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'unknown'))
);

CREATE INDEX idx_mcp_servers_server_id ON mcp_servers(server_id);
CREATE INDEX idx_mcp_servers_status ON mcp_servers(status);

-- ============================================================================
-- ANALYTICS AND METRICS TABLES
-- ============================================================================

-- Tabla de métricas del sistema agregadas por día
CREATE TABLE daily_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    
    -- Task metrics
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    avg_consensus_score FLOAT DEFAULT 0.0,
    avg_quality_score FLOAT DEFAULT 0.0,
    
    -- Performance metrics
    avg_completion_time FLOAT DEFAULT 0.0,
    total_cost FLOAT DEFAULT 0.0,
    total_tokens INTEGER DEFAULT 0,
    
    -- Human intervention metrics
    human_interventions INTEGER DEFAULT 0,
    human_intervention_rate FLOAT DEFAULT 0.0,
    avg_human_satisfaction FLOAT DEFAULT 0.0,
    
    -- Learning metrics
    learning_events INTEGER DEFAULT 0,
    patterns_discovered INTEGER DEFAULT 0,
    improvement_rate FLOAT DEFAULT 0.0,
    
    -- System health metrics
    circuit_breaker_activations INTEGER DEFAULT 0,
    system_uptime_percentage FLOAT DEFAULT 100.0,
    
    UNIQUE(date)
);

CREATE INDEX idx_daily_metrics_date ON daily_metrics(date);

-- Tabla de métricas por cliente
CREATE TABLE client_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    
    -- Client-specific metrics
    tasks_submitted INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    avg_quality_score FLOAT DEFAULT 0.0,
    total_cost FLOAT DEFAULT 0.0,
    
    -- Satisfaction metrics
    interventions_requested INTEGER DEFAULT 0,
    avg_satisfaction FLOAT DEFAULT 0.0,
    
    UNIQUE(client_id, date)
);

CREATE INDEX idx_client_metrics_client_date ON client_metrics(client_id, date);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Vista de tareas activas con información de routing
CREATE VIEW active_tasks_with_routing AS
SELECT 
    dt.id,
    dt.task_id,
    dt.client_id,
    dt.domain,
    dt.status,
    dt.priority,
    dt.created_at,
    dt.deadline,
    rd.destination_id,
    rd.confidence as routing_confidence,
    rd.estimated_completion
FROM debate_tasks dt
LEFT JOIN routing_decisions rd ON dt.id = rd.task_id
WHERE dt.status IN ('pending', 'in_progress', 'human_intervention');

-- Vista de métricas de rendimiento por modelo
CREATE VIEW model_performance_metrics AS
SELECT 
    model_name,
    model_provider,
    COUNT(*) as total_responses,
    AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate,
    AVG(response_time) as avg_response_time,
    AVG(confidence) as avg_confidence,
    SUM(tokens_used) as total_tokens,
    SUM(cost) as total_cost
FROM model_responses
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY model_name, model_provider;

-- Vista de tendencias de calidad por dominio
CREATE VIEW quality_trends_by_domain AS
SELECT 
    domain,
    DATE_TRUNC('day', created_at) as day,
    COUNT(*) as tasks_count,
    AVG(consensus_score) as avg_consensus,
    AVG(quality_score) as avg_quality,
    AVG(total_duration) as avg_duration,
    SUM(CASE WHEN human_intervention_used THEN 1 ELSE 0 END) as interventions_count
FROM debate_tasks
WHERE completed_at IS NOT NULL
    AND created_at >= NOW() - INTERVAL '90 days'
GROUP BY domain, DATE_TRUNC('day', created_at)
ORDER BY day DESC;

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Función para actualizar métricas diarias automáticamente
CREATE OR REPLACE FUNCTION update_daily_metrics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO daily_metrics (date)
    VALUES (CURRENT_DATE)
    ON CONFLICT (date) DO NOTHING;
    
    -- Update task completion metrics
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE daily_metrics 
        SET 
            completed_tasks = completed_tasks + 1,
            total_cost = total_cost + COALESCE(NEW.total_cost, 0),
            total_tokens = total_tokens + COALESCE(NEW.total_tokens, 0)
        WHERE date = CURRENT_DATE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar métricas cuando se completa una tarea
CREATE TRIGGER trigger_update_daily_metrics
    AFTER UPDATE ON debate_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_metrics();

-- Función para generar embeddings automáticamente
CREATE OR REPLACE FUNCTION generate_embeddings()
RETURNS TRIGGER AS $$
BEGIN
    -- En producción, esto llamaría a un servicio de embeddings
    -- Por ahora, generamos embeddings dummy para demostración
    IF NEW.content IS NOT NULL AND NEW.content_embedding IS NULL THEN
        -- Simular embedding (en producción usar OpenAI embeddings API)
        NEW.content_embedding = array_fill(random(), ARRAY[1536])::vector;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para generar embeddings en model_responses
CREATE TRIGGER trigger_generate_embeddings
    BEFORE INSERT ON model_responses
    FOR EACH ROW
    EXECUTE FUNCTION generate_embeddings();

-- ============================================================================
-- INITIAL DATA AND CONFIGURATION
-- ============================================================================

-- Insertar configuración inicial del sistema
INSERT INTO circuit_breaker_states (provider, state, success_rate) VALUES
('gpt-4', 'closed', 0.95),
('claude-3-sonnet', 'closed', 0.92),
('gemini-pro', 'closed', 0.88),
('local-backup', 'closed', 0.85);

-- Insertar métricas diarias iniciales para la fecha actual
INSERT INTO daily_metrics (date) VALUES (CURRENT_DATE)
ON CONFLICT (date) DO NOTHING;

-- ============================================================================
-- SECURITY POLICIES (Row Level Security)
-- ============================================================================

-- Habilitar RLS en tablas sensibles
ALTER TABLE debate_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE human_interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE shadow_learning_events ENABLE ROW LEVEL SECURITY;

-- Política para que los clientes solo vean sus propias tareas
CREATE POLICY client_tasks_policy ON debate_tasks
    FOR ALL USING (client_id = current_setting('app.current_client_id', true));

-- Política para intervenciones humanas (solo usuarios autorizados)
CREATE POLICY human_intervention_policy ON human_interventions
    FOR ALL USING (
        current_setting('app.user_role', true) IN ('admin', 'operator', 'supervisor')
    );

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Índices compuestos para consultas comunes
CREATE INDEX idx_tasks_status_created ON debate_tasks(status, created_at);
CREATE INDEX idx_tasks_client_domain ON debate_tasks(client_id, domain);
CREATE INDEX idx_model_responses_performance ON model_responses(model_name, success, response_time);
CREATE INDEX idx_learning_events_domain_outcome ON shadow_learning_events(domain, outcome_success);

-- Índices para embeddings (usando vector extension)
CREATE INDEX idx_model_responses_embedding ON model_responses 
USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_learning_events_input_embedding ON shadow_learning_events 
USING ivfflat (input_embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- STORED PROCEDURES FOR COMMON OPERATIONS
-- ============================================================================

-- Procedimiento para obtener métricas de rendimiento del sistema
CREATE OR REPLACE FUNCTION get_system_performance_metrics(
    days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    metric_name TEXT,
    metric_value NUMERIC,
    metric_unit TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH recent_tasks AS (
        SELECT * FROM debate_tasks 
        WHERE created_at >= NOW() - (days_back || ' days')::INTERVAL
    )
    SELECT 'total_tasks'::TEXT, COUNT(*)::NUMERIC, 'count'::TEXT FROM recent_tasks
    UNION ALL
    SELECT 'completion_rate'::TEXT, 
           (COUNT(*) FILTER (WHERE status = 'completed')::NUMERIC / NULLIF(COUNT(*), 0) * 100), 
           'percentage'::TEXT 
    FROM recent_tasks
    UNION ALL
    SELECT 'avg_consensus_score'::TEXT, 
           AVG(consensus_score)::NUMERIC, 
           'score'::TEXT 
    FROM recent_tasks WHERE consensus_score IS NOT NULL
    UNION ALL
    SELECT 'total_cost'::TEXT, 
           SUM(total_cost)::NUMERIC, 
           'dollars'::TEXT 
    FROM recent_tasks;
END;
$$ LANGUAGE plpgsql;

-- Procedimiento para análisis de patrones de intervención humana
CREATE OR REPLACE FUNCTION analyze_human_intervention_patterns()
RETURNS TABLE (
    domain TEXT,
    intervention_rate NUMERIC,
    avg_quality_improvement NUMERIC,
    common_intervention_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dt.domain,
        (COUNT(hi.id)::NUMERIC / COUNT(dt.id) * 100) as intervention_rate,
        AVG(hi.quality_improvement) as avg_quality_improvement,
        MODE() WITHIN GROUP (ORDER BY hi.intervention_type) as common_intervention_type
    FROM debate_tasks dt
    LEFT JOIN human_interventions hi ON dt.id = hi.task_id
    WHERE dt.created_at >= NOW() - INTERVAL '30 days'
    GROUP BY dt.domain
    HAVING COUNT(dt.id) > 10;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE debate_tasks IS 'Main table storing all debate tasks with their status, results, and performance metrics';
COMMENT ON TABLE model_responses IS 'Individual model responses within debate rounds, including embeddings for similarity analysis';
COMMENT ON TABLE shadow_learning_events IS 'Events captured for continuous learning and system improvement';
COMMENT ON TABLE decision_replays IS 'Historical decision replays for evolutionary auditing and ROI demonstration';
COMMENT ON TABLE human_interventions IS 'Human interventions in the debate process for quality control and learning';

COMMENT ON COLUMN debate_tasks.consensus_score IS 'Score from 0-1 indicating level of consensus reached between models';
COMMENT ON COLUMN debate_tasks.quality_score IS 'Overall quality assessment of the final result';
COMMENT ON COLUMN model_responses.content_embedding IS 'Vector embedding of response content for similarity analysis';
COMMENT ON COLUMN shadow_learning_events.outcome_success IS 'Whether the final outcome was successful from business perspective';

-- ============================================================================
-- END OF SCHEMA DEFINITION
-- ============================================================================

-- Final verification query
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%debate%' 
   OR tablename LIKE '%learning%' 
   OR tablename LIKE '%routing%'
   OR tablename LIKE '%circuit%'
ORDER BY tablename;
-- Inicialización de base de datos MCP Enterprise con pgvector
-- Este script se ejecuta automáticamente al crear el contenedor

-- Crear extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Crear esquemas
CREATE SCHEMA IF NOT EXISTS mcp_core;
CREATE SCHEMA IF NOT EXISTS mcp_memory;
CREATE SCHEMA IF NOT EXISTS mcp_analytics;
CREATE SCHEMA IF NOT EXISTS mcp_security;

-- Tabla de usuarios y autenticación
CREATE TABLE IF NOT EXISTS mcp_security.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE,
    roles TEXT[] DEFAULT ARRAY['user'],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0
);

-- Tabla de sesiones
CREATE TABLE IF NOT EXISTS mcp_security.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES mcp_security.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Tabla de logs de auditoría
CREATE TABLE IF NOT EXISTS mcp_security.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES mcp_security.users(id),
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de tareas MCP
CREATE TABLE IF NOT EXISTS mcp_core.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES mcp_security.users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    tool_name VARCHAR(255),
    parameters JSONB,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_duration INTEGER, -- en segundos
    actual_duration INTEGER
);

-- Tabla de herramientas MCP
CREATE TABLE IF NOT EXISTS mcp_core.tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    capabilities TEXT[],
    configuration JSONB,
    is_enabled BOOLEAN DEFAULT true,
    version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de ejecuciones de herramientas
CREATE TABLE IF NOT EXISTS mcp_core.tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES mcp_core.tasks(id),
    tool_id UUID REFERENCES mcp_core.tools(id),
    input_parameters JSONB,
    output_result JSONB,
    execution_time INTEGER, -- en milisegundos
    status VARCHAR(50),
    error_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de memoria semántica con vectores
CREATE TABLE IF NOT EXISTS mcp_memory.semantic_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES mcp_security.users(id),
    content TEXT NOT NULL,
    content_type VARCHAR(100) DEFAULT 'text',
    embedding vector(1536), -- OpenAI embeddings dimension
    metadata JSONB,
    tags TEXT[],
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Tabla de contexto de conversaciones
CREATE TABLE IF NOT EXISTS mcp_memory.conversation_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES mcp_security.users(id),
    session_id VARCHAR(255),
    message_content TEXT,
    message_role VARCHAR(50), -- 'user', 'assistant', 'system'
    embedding vector(1536),
    tokens_used INTEGER,
    model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de conocimiento persistente
CREATE TABLE IF NOT EXISTS mcp_memory.knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE,
    embedding vector(1536),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    keywords TEXT[],
    confidence_score FLOAT DEFAULT 1.0,
    source_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de métricas y analytics
CREATE TABLE IF NOT EXISTS mcp_analytics.metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_type VARCHAR(100), -- 'counter', 'gauge', 'histogram'
    labels JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de eventos del sistema
CREATE TABLE IF NOT EXISTS mcp_analytics.system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(255) NOT NULL,
    event_data JSONB,
    severity VARCHAR(50) DEFAULT 'info', -- 'debug', 'info', 'warning', 'error', 'critical'
    source VARCHAR(255),
    user_id UUID REFERENCES mcp_security.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para optimización de consultas

-- Índices para búsqueda vectorial
CREATE INDEX IF NOT EXISTS idx_semantic_memory_embedding 
ON mcp_memory.semantic_memory USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_conversation_embedding 
ON mcp_memory.conversation_context USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_embedding 
ON mcp_memory.knowledge_base USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON mcp_core.tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON mcp_core.tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_semantic_memory_user_tags ON mcp_memory.semantic_memory(user_id, tags);
CREATE INDEX IF NOT EXISTS idx_conversation_user_session ON mcp_memory.conversation_context(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON mcp_analytics.metrics(metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_type_timestamp ON mcp_analytics.system_events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON mcp_security.audit_logs(user_id, action, created_at DESC);

-- Índices de texto completo
CREATE INDEX IF NOT EXISTS idx_semantic_memory_content_gin ON mcp_memory.semantic_memory USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_knowledge_content_gin ON mcp_memory.knowledge_base USING gin(to_tsvector('english', content));

-- Funciones útiles para búsqueda semántica

-- Función para búsqueda de similitud semántica
CREATE OR REPLACE FUNCTION search_semantic_memory(
    query_embedding vector(1536),
    user_id_param UUID DEFAULT NULL,
    limit_param INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sm.id,
        sm.content,
        1 - (sm.embedding <=> query_embedding) as similarity,
        sm.metadata,
        sm.created_at
    FROM mcp_memory.semantic_memory sm
    WHERE 
        (user_id_param IS NULL OR sm.user_id = user_id_param)
        AND (1 - (sm.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY sm.embedding <=> query_embedding
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql;

-- Función para búsqueda en base de conocimiento
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding vector(1536),
    category_param VARCHAR(100) DEFAULT NULL,
    limit_param INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(255),
    content TEXT,
    similarity FLOAT,
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.title,
        kb.content,
        1 - (kb.embedding <=> query_embedding) as similarity,
        kb.category,
        kb.created_at
    FROM mcp_memory.knowledge_base kb
    WHERE 
        (category_param IS NULL OR kb.category = category_param)
        AND (1 - (kb.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY kb.embedding <=> query_embedding
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar memoria antigua
CREATE OR REPLACE FUNCTION cleanup_old_memory()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Eliminar memoria expirada
    DELETE FROM mcp_memory.semantic_memory 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Eliminar conversaciones muy antiguas (más de 90 días)
    DELETE FROM mcp_memory.conversation_context 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    -- Eliminar métricas muy antiguas (más de 30 días)
    DELETE FROM mcp_analytics.metrics 
    WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- Eliminar eventos antiguos (más de 60 días)
    DELETE FROM mcp_analytics.system_events 
    WHERE created_at < NOW() - INTERVAL '60 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Triggers para actualizar timestamps

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON mcp_security.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tools_updated_at 
    BEFORE UPDATE ON mcp_core.tools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_updated_at 
    BEFORE UPDATE ON mcp_memory.knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar datos iniciales

-- Usuario administrador por defecto
INSERT INTO mcp_security.users (username, email, password_hash, api_key, roles) 
VALUES (
    'admin',
    'admin@mcp-enterprise.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RX.PZa2u.', -- password: admin123
    'mcp_admin_' || encode(gen_random_bytes(16), 'hex'),
    ARRAY['admin', 'user']
) ON CONFLICT (username) DO NOTHING;

-- Herramientas por defecto
INSERT INTO mcp_core.tools (name, type, description, capabilities, configuration) VALUES
('firecrawl', 'web_scraping', 'Web scraping and crawling service', ARRAY['scrape', 'crawl', 'extract'], '{"endpoint": "https://api.firecrawl.dev/v0/scrape", "timeout": 30}'),
('telegram', 'messaging', 'Telegram bot integration', ARRAY['send_message', 'send_photo', 'bot_commands'], '{"endpoint": "https://api.telegram.org", "timeout": 10}'),
('notion', 'productivity', 'Notion workspace integration', ARRAY['create_page', 'update_page', 'query_database'], '{"endpoint": "https://api.notion.com/v1", "timeout": 15}'),
('github', 'development', 'GitHub repository operations', ARRAY['create_repo', 'create_file', 'create_issue', 'create_pr'], '{"endpoint": "https://api.github.com", "timeout": 20}')
ON CONFLICT (name) DO NOTHING;

-- Configurar job de limpieza automática (ejecutar diariamente)
-- Nota: Esto requiere la extensión pg_cron en producción
-- SELECT cron.schedule('cleanup-old-memory', '0 2 * * *', 'SELECT cleanup_old_memory();');

COMMIT;


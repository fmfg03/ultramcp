-- Supabase Schema para Sam's Memory Analyzer
-- Tabla principal de memorias con soporte para búsqueda vectorial

-- Habilitar extensión para vectores
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de memorias
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    summary TEXT NOT NULL,
    embedding VECTOR(1536), -- Dimensión para text-embedding-3-large
    tags TEXT[] DEFAULT '{}',
    memory_type TEXT NOT NULL CHECK (memory_type IN ('success', 'failure', 'escalation', 'critical', 'learning')),
    success_score FLOAT DEFAULT 0.0 CHECK (success_score >= 0.0 AND success_score <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_json JSONB NOT NULL,
    concepts JSONB DEFAULT '[]'::jsonb
);

-- Índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON memories (memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_success_score ON memories (success_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN (tags);

-- Índice compuesto para búsquedas complejas
CREATE INDEX IF NOT EXISTS idx_memories_type_score_date ON memories (memory_type, success_score DESC, created_at DESC);

-- Función para búsqueda de similitud vectorial
CREATE OR REPLACE FUNCTION match_memories(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    summary TEXT,
    embedding VECTOR(1536),
    tags TEXT[],
    memory_type TEXT,
    success_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    raw_json JSONB,
    concepts JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        m.id,
        m.summary,
        m.embedding,
        m.tags,
        m.memory_type,
        m.success_score,
        m.created_at,
        m.raw_json,
        m.concepts,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM memories m
    WHERE 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Función para búsqueda híbrida (vectorial + filtros)
CREATE OR REPLACE FUNCTION hybrid_search_memories(
    query_embedding VECTOR(1536),
    memory_types TEXT[] DEFAULT NULL,
    min_success_score FLOAT DEFAULT 0.0,
    tag_filter TEXT[] DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    summary TEXT,
    embedding VECTOR(1536),
    tags TEXT[],
    memory_type TEXT,
    success_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    raw_json JSONB,
    concepts JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        m.id,
        m.summary,
        m.embedding,
        m.tags,
        m.memory_type,
        m.success_score,
        m.created_at,
        m.raw_json,
        m.concepts,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM memories m
    WHERE 
        (1 - (m.embedding <=> query_embedding)) > match_threshold
        AND (memory_types IS NULL OR m.memory_type = ANY(memory_types))
        AND m.success_score >= min_success_score
        AND (tag_filter IS NULL OR m.tags && tag_filter)
    ORDER BY 
        -- Boost por tipo de memoria y success score
        CASE 
            WHEN m.memory_type = 'success' THEN (1 - (m.embedding <=> query_embedding)) * 1.2
            WHEN m.memory_type = 'critical' THEN (1 - (m.embedding <=> query_embedding)) * 1.3
            ELSE (1 - (m.embedding <=> query_embedding))
        END * (0.8 + 0.4 * m.success_score) DESC
    LIMIT match_count;
$$;

-- Función para obtener estadísticas de memoria
CREATE OR REPLACE FUNCTION get_memory_stats()
RETURNS TABLE (
    total_memories BIGINT,
    success_memories BIGINT,
    failure_memories BIGINT,
    escalation_memories BIGINT,
    critical_memories BIGINT,
    avg_success_score FLOAT,
    latest_memory TIMESTAMP WITH TIME ZONE,
    oldest_memory TIMESTAMP WITH TIME ZONE
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        COUNT(*) as total_memories,
        COUNT(*) FILTER (WHERE memory_type = 'success') as success_memories,
        COUNT(*) FILTER (WHERE memory_type = 'failure') as failure_memories,
        COUNT(*) FILTER (WHERE memory_type = 'escalation') as escalation_memories,
        COUNT(*) FILTER (WHERE memory_type = 'critical') as critical_memories,
        AVG(success_score) as avg_success_score,
        MAX(created_at) as latest_memory,
        MIN(created_at) as oldest_memory
    FROM memories;
$$;

-- Función para limpiar memorias antiguas
CREATE OR REPLACE FUNCTION cleanup_old_memories(days_old INT DEFAULT 90)
RETURNS INT
LANGUAGE SQL
AS $$
    WITH deleted AS (
        DELETE FROM memories 
        WHERE created_at < NOW() - INTERVAL '1 day' * days_old
        RETURNING id
    )
    SELECT COUNT(*)::INT FROM deleted;
$$;

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_memories_updated_at 
    BEFORE UPDATE ON memories 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Política de seguridad (Row Level Security)
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas las operaciones con service role
CREATE POLICY "Service role can manage all memories" ON memories
    FOR ALL USING (auth.role() = 'service_role');

-- Política para lectura pública (opcional, ajustar según necesidades)
CREATE POLICY "Public can read memories" ON memories
    FOR SELECT USING (true);

-- Vista para análisis de conceptos
CREATE OR REPLACE VIEW memory_concepts AS
SELECT 
    m.id,
    m.memory_type,
    m.success_score,
    m.created_at,
    concept->>'type' as concept_type,
    concept->>'value' as concept_value,
    (concept->>'confidence')::float as concept_confidence
FROM memories m,
LATERAL jsonb_array_elements(m.concepts) as concept;

-- Vista para análisis de tags
CREATE OR REPLACE VIEW memory_tag_analysis AS
SELECT 
    tag,
    COUNT(*) as usage_count,
    AVG(success_score) as avg_success_score,
    COUNT(*) FILTER (WHERE memory_type = 'success') as success_count,
    COUNT(*) FILTER (WHERE memory_type = 'failure') as failure_count
FROM memories m,
UNNEST(m.tags) as tag
GROUP BY tag
ORDER BY usage_count DESC;

-- Función para obtener memorias similares a una memoria específica
CREATE OR REPLACE FUNCTION find_similar_memories(
    memory_id UUID,
    match_threshold FLOAT DEFAULT 0.8,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    summary TEXT,
    memory_type TEXT,
    success_score FLOAT,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    WITH target_memory AS (
        SELECT embedding FROM memories WHERE id = memory_id
    )
    SELECT 
        m.id,
        m.summary,
        m.memory_type,
        m.success_score,
        1 - (m.embedding <=> tm.embedding) AS similarity
    FROM memories m, target_memory tm
    WHERE 
        m.id != memory_id
        AND (1 - (m.embedding <=> tm.embedding)) > match_threshold
    ORDER BY m.embedding <=> tm.embedding
    LIMIT match_count;
$$;

-- Comentarios para documentación
COMMENT ON TABLE memories IS 'Tabla principal para almacenar memorias semánticas de Sam con embeddings vectoriales';
COMMENT ON COLUMN memories.embedding IS 'Vector embedding de 1536 dimensiones generado por text-embedding-3-large';
COMMENT ON COLUMN memories.success_score IS 'Puntuación de éxito de 0.0 a 1.0 basada en el resultado de la tarea';
COMMENT ON COLUMN memories.concepts IS 'Array JSON de conceptos extraídos con tipo, valor, confianza y contexto';
COMMENT ON FUNCTION match_memories IS 'Búsqueda de similitud vectorial usando cosine distance';
COMMENT ON FUNCTION hybrid_search_memories IS 'Búsqueda híbrida con filtros adicionales y boosting inteligente';


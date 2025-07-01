-- Esquemas SQL para las tablas del sistema MCP
-- Estas tablas deben crearse manualmente en Supabase

-- Tabla de sesiones
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    original_input TEXT NOT NULL,
    task_type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabla de pasos
CREATE TABLE IF NOT EXISTS steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    step_type TEXT NOT NULL,
    step_name TEXT NOT NULL,
    agent_used TEXT,
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB DEFAULT '{}'::jsonb,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabla de evaluaciones/rewards
CREATE TABLE IF NOT EXISTS rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    step_id UUID REFERENCES steps(id) ON DELETE CASCADE,
    score DECIMAL(3,2),
    quality_level TEXT,
    feedback JSONB DEFAULT '{}'::jsonb,
    retry_recommended BOOLEAN DEFAULT FALSE,
    evaluation_criteria JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Tabla de planes de ejecución
CREATE TABLE IF NOT EXISTS execution_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    plan_data JSONB NOT NULL,
    complexity_score INTEGER,
    estimated_duration TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_task_type ON sessions(task_type);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_steps_session_id ON steps(session_id);
CREATE INDEX IF NOT EXISTS idx_steps_step_type ON steps(step_type);
CREATE INDEX IF NOT EXISTS idx_steps_status ON steps(status);
CREATE INDEX IF NOT EXISTS idx_steps_started_at ON steps(started_at);

CREATE INDEX IF NOT EXISTS idx_rewards_session_id ON rewards(session_id);
CREATE INDEX IF NOT EXISTS idx_rewards_step_id ON rewards(step_id);
CREATE INDEX IF NOT EXISTS idx_rewards_score ON rewards(score);
CREATE INDEX IF NOT EXISTS idx_rewards_created_at ON rewards(created_at);

CREATE INDEX IF NOT EXISTS idx_execution_plans_session_id ON execution_plans(session_id);
CREATE INDEX IF NOT EXISTS idx_execution_plans_created_at ON execution_plans(created_at);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at en sessions
CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentar las tablas
COMMENT ON TABLE sessions IS 'Almacena información de sesiones de orquestación MCP';
COMMENT ON TABLE steps IS 'Almacena cada paso del proceso de orquestación';
COMMENT ON TABLE rewards IS 'Almacena evaluaciones y puntuaciones de los resultados';
COMMENT ON TABLE execution_plans IS 'Almacena planes de ejecución generados por el reasoning shell';

-- Comentarios para columnas importantes
COMMENT ON COLUMN sessions.status IS 'Estados: active, completed, failed, cancelled';
COMMENT ON COLUMN steps.step_type IS 'Tipos: reasoning, execution, evaluation, retry, finalization';
COMMENT ON COLUMN steps.status IS 'Estados: pending, running, success, error';
COMMENT ON COLUMN rewards.score IS 'Puntuación de 0.00 a 1.00';
COMMENT ON COLUMN rewards.quality_level IS 'Niveles: excellent, good, acceptable, poor, unacceptable';


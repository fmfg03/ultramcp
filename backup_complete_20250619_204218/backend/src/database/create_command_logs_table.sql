-- SQL script to create the command_logs table in Supabase

CREATE TABLE IF NOT EXISTS command_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ DEFAULT now() NOT NULL,
  command TEXT NOT NULL,
  response JSONB, -- Storing response as JSONB for flexibility
  user_id TEXT, -- Optional, can be linked to an auth.users table later
  llm_used TEXT,
  agent_used TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Optional: Add an index on timestamp for faster querying of history
CREATE INDEX IF NOT EXISTS idx_command_logs_timestamp ON command_logs (timestamp DESC);

-- Optional: Add an index on user_id if you plan to filter by user frequently
-- CREATE INDEX IF NOT EXISTS idx_command_logs_user_id ON command_logs (user_id);

-- Enable Row Level Security (RLS) on the table if you plan to expose it directly to clients
-- Ensure to define appropriate policies for SELECT, INSERT, UPDATE, DELETE.
-- For now, assuming backend service will handle access, RLS might not be immediately needed
-- but it's good practice for Supabase.

-- Example of enabling RLS (policies would need to be defined):
-- ALTER TABLE command_logs ENABLE ROW LEVEL SECURITY;

-- Grant usage on schema and all privileges on table to supabase_admin and postgres
-- These are typically default and might not be needed explicitly but good to be aware of.
-- GRANT USAGE ON SCHEMA public TO supabase_admin;
-- GRANT ALL PRIVILEGES ON TABLE command_logs TO supabase_admin;
-- GRANT USAGE ON SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON TABLE command_logs TO postgres;

-- For authenticated users (if using Supabase Auth and RLS)
-- GRANT SELECT, INSERT ON TABLE command_logs TO authenticated;

COMMENT ON COLUMN command_logs.id IS 'Unique identifier for the log entry.';
COMMENT ON COLUMN command_logs.timestamp IS 'Timestamp when the command was processed or logged.';
COMMENT ON COLUMN command_logs.command IS 'The natural language command issued by the user.';
COMMENT ON COLUMN command_logs.response IS 'The JSON response from the orchestration service.';
COMMENT ON COLUMN command_logs.user_id IS 'Identifier for the user who issued the command (optional).';
COMMENT ON COLUMN command_logs.llm_used IS 'The language model used for processing the command.';
COMMENT ON COLUMN command_logs.agent_used IS 'The agent used for processing the command.';
COMMENT ON COLUMN command_logs.created_at IS 'Timestamp of when the log record was created.';



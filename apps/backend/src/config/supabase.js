/**
 * Supabase Configuration for MCP System
 * Handles database connections, logging, and analytics
 */

const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

// Public client for frontend operations
const supabasePublic = createClient(supabaseUrl, supabaseAnonKey);

// Service client for backend operations (bypasses RLS)
const supabaseService = supabaseServiceKey 
  ? createClient(supabaseUrl, supabaseServiceKey)
  : null;

/**
 * Log MCP system events to Supabase
 */
async function logToSupabase(level, message, metadata = {}) {
    return;
  }

  try {
    const { error } = await supabaseService
      .from(process.env.SUPABASE_TABLE_LOGS || 'mcp_logs')
      .insert({
        level,
        message,
        metadata,
        timestamp: new Date().toISOString(),
        service: 'mcp-backend'
      });

    if (error) {
      console.error('Supabase logging error:', error);
    }
  } catch (err) {
    console.error('Supabase logging exception:', err);
  }
}

/**
 * Track session metrics
 */
async function trackSession(sessionId, userId, action, data = {}) {

  try {
    const { error } = await supabaseService
      .from(process.env.SUPABASE_TABLE_SESSIONS || 'mcp_sessions')
      .insert({
        session_id: sessionId,
        user_id: userId,
        action,
        data,
        timestamp: new Date().toISOString()
      });

    if (error) {
      console.error('Session tracking error:', error);
    }
  } catch (err) {
    console.error('Session tracking exception:', err);
  }
}

/**
 * Store system metrics
 */
async function storeMetrics(metrics) {

  try {
    const { error } = await supabaseService
      .from(process.env.SUPABASE_TABLE_METRICS || 'mcp_metrics')
      .insert({
        ...metrics,
        timestamp: new Date().toISOString()
      });

    if (error) {
      console.error('Metrics storage error:', error);
    }
  } catch (err) {
    console.error('Metrics storage exception:', err);
  }
}

module.exports = {
  supabasePublic,
  supabaseService,
  logToSupabase,
  trackSession,
  storeMetrics,
  isConfigured: cd /home/ubuntu && ssh root@65.109.54.94 cd supermcp

import { createClient } from "@supabase/supabase-js";
import dotenv from "dotenv";

dotenv.config();

let supabaseClientInstance = null;

/**
 * @function getSupabaseClient
 * @description Initializes and returns a Supabase client instance (singleton).
 * @returns {object} The Supabase client instance.
 * @throws {Error} If Supabase URL or Key is not provided in .env file.
 */
function getSupabaseClient() {
  if (supabaseClientInstance) {
    return supabaseClientInstance;
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.error("Supabase URL and Key must be provided in .env file. Make sure .env is loaded correctly.");
    throw new Error("Supabase URL and Key must be provided in .env file");
  }
  
  supabaseClientInstance = createClient(supabaseUrl, supabaseKey);
  return supabaseClientInstance;
}

/**
 * @async
 * @function setupTables
 * @description Creates the required tables (credentials, scheduled_jobs, command_logs) in Supabase if they don't already exist.
 * @returns {Promise<void>}
 */
async function setupTables() {
  const supabase = getSupabaseClient();
  try {
    // Create credentials table
    const { error: credentialsError } = await supabase.rpc('query', {
      sql: `
        CREATE TABLE IF NOT EXISTS credentials (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          service TEXT NOT NULL,
          key TEXT NOT NULL,
          value TEXT NOT NULL, -- Encrypted value
          created_at TIMESTAMPTZ DEFAULT NOW(),
          updated_at TIMESTAMPTZ DEFAULT NOW(),
          UNIQUE (service, key)
        );
      `
    });
    if (credentialsError) throw credentialsError;
    console.log("Table 'credentials' checked/created successfully.");

    // Create scheduled_jobs table
    const { error: jobsError } = await supabase.rpc('query', {
      sql: `
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          name TEXT NOT NULL,
          cron TEXT NOT NULL,
          workflow TEXT NOT NULL,
          params JSONB,
          status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused')),
          created_at TIMESTAMPTZ DEFAULT NOW(),
          updated_at TIMESTAMPTZ DEFAULT NOW()
        );
      `
    });
    if (jobsError) throw jobsError;
    console.log("Table 'scheduled_jobs' checked/created successfully.");

    // Add command_logs table creation
    const { error: logsError } = await supabase.rpc('query', {
      sql: `
        CREATE TABLE IF NOT EXISTS command_logs (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          timestamp TIMESTAMPTZ DEFAULT now() NOT NULL,
          command TEXT NOT NULL,
          response JSONB,
          user_id TEXT,
          llm_used TEXT,
          agent_used TEXT,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        
        -- Create index on timestamp for faster querying
        CREATE INDEX IF NOT EXISTS idx_command_logs_timestamp ON command_logs (timestamp DESC);
      `
    });
    if (logsError) throw logsError;
    console.log("Table 'command_logs' checked/created successfully.");

  } catch (error) {
    console.error("Error setting up tables:", error.message);
    // Optionally re-throw or handle more gracefully depending on application needs
    // For now, we log the error and let the application continue if other tables were setup
    // or if the error is specific to one table creation that might already exist with a different config.
    // However, the user's pasted_content.txt suggests exiting if table setup fails in the main server file.
    // This function itself doesn't exit, but the caller might.
  }
}

/**
 * @async
 * @function createRecord
 * @description Creates a new record in the specified Supabase table.
 * @param {string} tableName - The name of the table.
 * @param {object} recordData - The data for the new record.
 * @returns {Promise<object|null>} The created record or null if an error occurred.
 */
async function createRecord(tableName, recordData) {
  const supabase = getSupabaseClient();
  try {
    const { data, error } = await supabase
      .from(tableName)
      .insert([recordData])
      .select();
    if (error) throw error;
    return data ? data[0] : null;
  } catch (error) {
    console.error(`Error creating record in ${tableName}:`, error.message);
    return null;
  }
}

/**
 * @async
 * @function getRecord
 * @description Retrieves a record from the specified Supabase table by its ID.
 * @param {string} tableName - The name of the table.
 * @param {string} id - The ID of the record to retrieve.
 * @returns {Promise<object|null>} The retrieved record or null if not found or an error occurred.
 */
async function getRecord(tableName, id) {
  const supabase = getSupabaseClient();
  try {
    const { data, error } = await supabase
      .from(tableName)
      .select("*")
      .eq("id", id)
      .single();
    if (error && error.code !== 'PGRST116') { // PGRST116: Row not found, not an error for single()
        throw error;
    }
    return data;
  } catch (error) {
    console.error(`Error retrieving record ${id} from ${tableName}:`, error.message);
    return null;
  }
}

/**
 * @async
 * @function updateRecord
 * @description Updates an existing record in the specified Supabase table.
 * @param {string} tableName - The name of the table.
 * @param {string} id - The ID of the record to update.
 * @param {object} updatedData - The data to update the record with.
 * @returns {Promise<object|null>} The updated record or null if an error occurred.
 */
async function updateRecord(tableName, id, updatedData) {
  const supabase = getSupabaseClient();
  try {
    const { data, error } = await supabase
      .from(tableName)
      .update(updatedData)
      .eq("id", id)
      .select();
    if (error) throw error;
    return data ? data[0] : null;
  } catch (error) {
    console.error(`Error updating record ${id} in ${tableName}:`, error.message);
    return null;
  }
}

/**
 * @async
 * @function deleteRecord
 * @description Deletes a record from the specified Supabase table by its ID.
 * @param {string} tableName - The name of the table.
 * @param {string} id - The ID of the record to delete.
 * @returns {Promise<boolean>} True if deletion was successful, false otherwise.
 */
async function deleteRecord(tableName, id) {
  const supabase = getSupabaseClient();
  try {
    const { error } = await supabase
      .from(tableName)
      .delete()
      .eq("id", id);
    if (error) throw error;
    return true;
  } catch (error) {
    console.error(`Error deleting record ${id} from ${tableName}:`, error.message);
    return false;
  }
}

/**
 * @async
 * @function listRecords
 * @description Lists records from the specified Supabase table, with optional filtering and pagination.
 * @param {string} tableName - The name of the table.
 * @param {object} [options={}] - Optional parameters for filtering and pagination.
 * @returns {Promise<Array<object>|null>} An array of records or null if an error occurred.
 */
async function listRecords(tableName, options = {}) {
  const supabase = getSupabaseClient();
  try {
    let query = supabase.from(tableName).select("*");

    if (options.filters) {
      for (const key in options.filters) {
        query = query.eq(key, options.filters[key]);
      }
    }

    if (options.orderBy) {
      query = query.order(options.orderBy, { ascending: options.ascending !== false });
    }

    if (options.limit) {
      query = query.limit(options.limit);
    }

    if (options.offset) {
      query = query.range(options.offset, options.offset + (options.limit || 0) - 1);
    }

    const { data, error } = await query;
    if (error) throw error;
    return data;
  } catch (error) {
    console.error(`Error listing records from ${tableName}:`, error.message);
    return null;
  }
}

export {
  getSupabaseClient, // Exporting for potential direct use or testing mocks
  setupTables,
  createRecord,
  getRecord,
  updateRecord,
  deleteRecord,
  listRecords
};


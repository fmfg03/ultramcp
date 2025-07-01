const supabase = require("../lib/supabaseClient.cjs"); // Assuming supabase client is initialized here

class LogService {
  async saveLog(logData) {
    const { command, response, timestamp, user, llm_used, agent_used } = logData;

    // Ensure response is stringified if it's an object
    const responseString = typeof response === 'object' ? JSON.stringify(response) : response;

    const { data, error } = await supabase
      .from("command_logs")
      .insert([
        {
          command,
          response: responseString,
          timestamp: timestamp || new Date().toISOString(), // Ensure timestamp is present
          user: user || null, // Handle optional user
          llm_used,
          agent_used,
        },
      ])
      .select(); // Return the inserted row

    if (error) {
      console.error("Error saving log to Supabase:", error);
      throw new Error(`Supabase error: ${error.message}`);
    }
    return data ? data[0] : null;
  }

  async getLogs(limit = 100) { // Default to fetching last 100 logs
    const { data, error } = await supabase
      .from("command_logs")
      .select("*")
      .order("timestamp", { ascending: false })
      .limit(limit);

    if (error) {
      console.error("Error fetching logs from Supabase:", error);
      throw new Error(`Supabase error: ${error.message}`);
    }
    return data || [];
  }
}

module.exports = new LogService();


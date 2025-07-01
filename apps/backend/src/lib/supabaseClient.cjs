const { createClient } = require("@supabase/supabase-js");

// Ensure you have SUPABASE_URL and SUPABASE_KEY in your .env file
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("Supabase URL or Key is missing. Please check your .env file.");
  // Optionally throw an error to prevent the application from starting without proper config
  // throw new Error("Supabase URL or Key is missing.");
}

const supabase = supabaseUrl && supabaseKey ? createClient(supabaseUrl, supabaseKey) : null;

module.exports = supabase;


import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

// Determine the correct path to the .env file in the project root
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const envPath = path.join(projectRoot, ".env");

dotenv.config({ path: envPath });

// Now that .env is loaded, we can import credentialsService dynamically
async function saveToken() {
  // Dynamically import storeCredential after dotenv has loaded
  const { storeCredential } = await import("../src/services/credentialsService.js");

  const TELEGRAM_BOT_TOKEN = "7680854019:AAGYmUg10m6wT7cxnMyxJXJVQ9EnOdXM1PY";
  const SERVICE_NAME = "telegram";
  const KEY_NAME = "botToken";

  console.log(`Attempting to store token for service: ${SERVICE_NAME}, key: ${KEY_NAME}`);
  try {
    const result = await storeCredential(SERVICE_NAME, KEY_NAME, TELEGRAM_BOT_TOKEN);
    if (result) {
      console.log("Telegram Bot Token stored successfully:", result);
    } else {
      console.error("Failed to store Telegram Bot Token. Result was null or undefined. This might be due to CRED_ENCRYPTION_KEY still not being available in credentialsService or an issue with Supabase.");
    }
  } catch (error) {
    console.error("Error storing Telegram Bot Token:", error);
  }
}

saveToken();


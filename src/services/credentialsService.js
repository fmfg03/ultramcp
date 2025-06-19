import CryptoJS from "crypto-js";
import dotenv from "dotenv";
import { getSupabaseClient } from "../adapters/supabaseAdapter.js";

dotenv.config(); // Ensure .env variables are loaded

const CRED_ENCRYPTION_KEY_FROM_ENV = process.env.CRED_ENCRYPTION_KEY;

if (!CRED_ENCRYPTION_KEY_FROM_ENV) {
  console.error("CRITICAL: CRED_ENCRYPTION_KEY is not defined in the .env file. Credentials service cannot operate securely.");
  // Consider throwing an error in a real application to halt if the key is critical for startup
  // throw new Error("CRED_ENCRYPTION_KEY is not defined.");
}

/**
 * Encrypts a value using AES encryption.
 * @param {string} text The text to encrypt.
 * @returns {string} The encrypted string.
 * @private
 */
function _encrypt(text) {
  if (!CRED_ENCRYPTION_KEY_FROM_ENV) {
    // This case should ideally be prevented by the initial check, but good for robustness
    throw new Error("Encryption key is not available at time of encryption.");
  }
  return CryptoJS.AES.encrypt(text, CRED_ENCRYPTION_KEY_FROM_ENV).toString();
}

/**
 * Decrypts a value using AES encryption.
 * @param {string} ciphertext The ciphertext to decrypt.
 * @returns {string} The decrypted string.
 * @private
 */
function _decrypt(ciphertext) {
  if (!CRED_ENCRYPTION_KEY_FROM_ENV) {
    throw new Error("Decryption key is not available at time of decryption.");
  }
  const bytes = CryptoJS.AES.decrypt(ciphertext, CRED_ENCRYPTION_KEY_FROM_ENV);
  return bytes.toString(CryptoJS.enc.Utf8);
}

/**
 * Stores a credential securely after encrypting its value.
 * Uses Supabase upsert to create or update the credential based on service and key.
 * @async
 * @function storeCredential
 * @param {string} service The name of the service (e.g., "notion", "google_drive").
 * @param {string} key The name of the credential key (e.g., "api_token", "client_secret").
 * @param {string} value The value of the credential.
 * @returns {Promise<object|null>} The stored credential object (with encrypted value) or null on failure.
 */
export async function storeCredential(service, key, value) {
  if (!CRED_ENCRYPTION_KEY_FROM_ENV) {
    console.error("Cannot store credential: Encryption key is missing.");
    return null;
  }
  if (!service || !key || typeof value === "undefined") {
    console.error("Service, key, and value are required for storing a credential.");
    return null;
  }

  const supabase = getSupabaseClient();
  try {
    const encryptedValue = _encrypt(String(value)); // Ensure value is a string
    const { data, error } = await supabase
      .from("credentials")
      .upsert(
        {
          service,
          key,
          value: encryptedValue,
          updated_at: new Date().toISOString(),
        },
        {
          onConflict: "service,key", 
          ignoreDuplicates: false,
        }
      )
      .select(); 

    if (error) {
      console.error(`Error storing credential for ${service} - ${key}:`, error.message);
      return null;
    }
    return data ? data[0] : null;
  } catch (e) {
    console.error(`Exception during storeCredential for ${service} - ${key}:`, e.message);
    return null;
  }
}

/**
 * Retrieves and decrypts a credential.
 * @async
 * @function getCredential
 * @param {string} service The name of the service.
 * @param {string} key The name of the credential key.
 * @returns {Promise<string|null>} The decrypted credential value, or null if not found or on error.
 */
export async function getCredential(service, key) {
  if (!CRED_ENCRYPTION_KEY_FROM_ENV) {
    console.error("Cannot get credential: Encryption key is missing.");
    return null;
  }
  if (!service || !key) {
    console.error("Service and key are required for retrieving a credential.");
    return null;
  }

  const supabase = getSupabaseClient();
  try {
    const { data, error } = await supabase
      .from("credentials")
      .select("value")
      .eq("service", service)
      .eq("key", key)
      .single();

    if (error) {
      if (error.code === "PGRST116") { 
        // Credential not found, not necessarily an error to log loudly.
      } else {
        console.error(`Error retrieving credential for ${service} - ${key} from Supabase:`, error.message);
      }
      return null;
    }

    if (!data || typeof data.value !== "string") {
      return null;
    }

    return _decrypt(data.value);
  } catch (e) {
    console.error(`Exception during getCredential for ${service} - ${key}:`, e.message);
    return null;
  }
}


import { jest } from "@jest/globals";
import dotenv from "dotenv";
import CryptoJS from "crypto-js";

// Mock environment variables first
process.env.CRED_ENCRYPTION_KEY = "test_encryption_key_1234567890abcdef"; // Ensure it's a valid length for AES, e.g., 32 chars for AES-256
process.env.SUPABASE_URL = "http://localhost:54321";
process.env.SUPABASE_KEY = "your_dummy_anon_key";

// This is the API object our mocked getSupabaseClient will return
const mockSupabaseClientAPI = {
  from: jest.fn(),
  select: jest.fn(),
  upsert: jest.fn(), // Upsert is a top-level method on the client, not chained after from().select() typically
  eq: jest.fn(),
  single: jest.fn(),
  // Add any other Supabase client methods that your service might directly or indirectly use
};

// Mock the supabaseAdapter.js module
jest.mock("../src/adapters/supabaseAdapter.js", () => ({
  __esModule: true,
  // Mock getSupabaseClient to return our mock client API object
  getSupabaseClient: jest.fn(() => mockSupabaseClientAPI),
  // We also need to mock other functions from supabaseAdapter if credentialsService uses them directly.
  // Based on credentialsService.js, it ONLY uses getSupabaseClient.
}));

// Mock crypto-js for controlled encryption/decryption testing
const mockEncrypt = jest.fn();
const mockDecrypt = jest.fn();
jest.mock("crypto-js", () => ({
  ...jest.requireActual("crypto-js"),
  AES: {
    encrypt: mockEncrypt,
    decrypt: mockDecrypt,
  },
  enc: {
      Utf8: jest.requireActual("crypto-js").enc.Utf8 // ensure Utf8 is available
  }
}));


// Now import the service AFTER all mocks are set up
import { storeCredential, getCredential } from "../src/services/credentialsService.js";

dotenv.config(); // Load .env variables (though we mock CRED_ENCRYPTION_KEY above for tests)

describe("Credentials Service", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset process.env for each test if modified during a test, though it's set globally above for these tests
    process.env.CRED_ENCRYPTION_KEY = "test_encryption_key_1234567890abcdef";

    // Setup default mock implementations for crypto-js
    mockEncrypt.mockImplementation((text, key) => ({
      toString: () => `encrypted_${text}_with_${key}`,
    }));
    mockDecrypt.mockImplementation((ciphertext, key) => ({
      toString: (encoding) => {
        if (encoding === CryptoJS.enc.Utf8) {
          return String(ciphertext).replace(`encrypted_`, "").replace(`_with_${key}`, "");
        }
        return "";
      },
    }));

    // Reset and configure the Supabase client mock for each test
    // The getSupabaseClient mock itself is already set up by jest.mock
    // We need to configure what its returned object (mockSupabaseClientAPI) does.
    mockSupabaseClientAPI.from.mockReturnThis(); // for chaining: supabase.from().select()... 
    mockSupabaseClientAPI.select.mockReturnThis();
    mockSupabaseClientAPI.upsert.mockReturnThis(); // upsert().select() is a common pattern
    mockSupabaseClientAPI.eq.mockReturnThis();
    mockSupabaseClientAPI.single.mockReturnThis();
    // For terminal operations like .select() (if it's terminal in a chain) or .single(), mock their resolution
  });

  describe("storeCredential", () => {
    it("should encrypt and store a credential", async () => {
      const service = "testService";
      const key = "testKey";
      const value = "testValue";
      const encryptedValue = `encrypted_${value}_with_${process.env.CRED_ENCRYPTION_KEY}`;
      const expectedStoredRecord = { service, key, value: encryptedValue, id: "uuid-test" };

      // Mock the final select() call after upsert
      mockSupabaseClientAPI.select.mockResolvedValue({ data: [expectedStoredRecord], error: null });
      // Mock upsert itself if it doesn't chain to select directly for resolution in your actual code
      // but typically it does, or you check the error from upsert directly.
      // For this test, we assume `upsert(...).select()` pattern.
      mockSupabaseClientAPI.upsert.mockReturnValue({ select: mockSupabaseClientAPI.select }); // Ensure upsert can chain to select


      const result = await storeCredential(service, key, value);

      expect(mockEncrypt).toHaveBeenCalledWith(String(value), process.env.CRED_ENCRYPTION_KEY);
      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("credentials");
      expect(mockSupabaseClientAPI.upsert).toHaveBeenCalledWith(
        expect.objectContaining({
          service,
          key,
          value: encryptedValue,
        }),
        { onConflict: "service,key", ignoreDuplicates: false }
      );
      expect(mockSupabaseClientAPI.select).toHaveBeenCalled();
      expect(result).toEqual(expectedStoredRecord);
    });

    it("should return null and log error if encryption key is missing from env", async () => {
      const originalKey = process.env.CRED_ENCRYPTION_KEY;
      delete process.env.CRED_ENCRYPTION_KEY; // Simulate missing key
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});

      // Re-import or re-initialize the service if its key check is at module load time
      // For this structure, the check is within the function, so direct call is fine.
      const result = await storeCredential("service", "key", "value");

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Cannot store credential: Encryption key is missing.");
      
      consoleErrorSpy.mockRestore();
      process.env.CRED_ENCRYPTION_KEY = originalKey; // Restore for other tests
    });

    it("should return null and log error if service, key, or value is missing", async () => {
        const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  
        let result = await storeCredential(null, "key", "value");
        expect(result).toBeNull();
        expect(consoleErrorSpy).toHaveBeenCalledWith("Service, key, and value are required for storing a credential.");
  
        result = await storeCredential("service", null, "value");
        expect(result).toBeNull();
  
        result = await storeCredential("service", "key", undefined);
        expect(result).toBeNull();
        
        consoleErrorSpy.mockRestore();
      });

    it("should return null and log error if Supabase upsert itself returns an error", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      // Simulate error directly from upsert or the chained select
      mockSupabaseClientAPI.upsert.mockReturnValue({ 
        select: jest.fn().mockResolvedValue({ data: null, error: new Error("Supabase upsert failed") })
      });

      const result = await storeCredential("service", "key", "value");

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error storing credential for service - key:", "Supabase upsert failed");
      consoleErrorSpy.mockRestore();
    });
  });

  describe("getCredential", () => {
    it("should retrieve and decrypt a credential", async () => {
      const service = "testService";
      const key = "testKey";
      const rawValue = "decryptedValue";
      const encryptedValue = `encrypted_${rawValue}_with_${process.env.CRED_ENCRYPTION_KEY}`;
      
      mockSupabaseClientAPI.single.mockResolvedValue({ data: { value: encryptedValue }, error: null });
      // Ensure from -> select -> eq -> eq -> single chain is mockable
      mockSupabaseClientAPI.eq.mockReturnValue({ single: mockSupabaseClientAPI.single }); 

      const result = await getCredential(service, key);

      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("credentials");
      expect(mockSupabaseClientAPI.select).toHaveBeenCalledWith("value");
      expect(mockSupabaseClientAPI.eq).toHaveBeenCalledWith("service", service);
      expect(mockSupabaseClientAPI.eq).toHaveBeenCalledWith("key", key);
      expect(mockSupabaseClientAPI.single).toHaveBeenCalled();
      expect(mockDecrypt).toHaveBeenCalledWith(encryptedValue, process.env.CRED_ENCRYPTION_KEY);
      expect(result).toBe(rawValue);
    });

    it("should return null and log error if encryption key is missing from env for get", async () => {
      const originalKey = process.env.CRED_ENCRYPTION_KEY;
      delete process.env.CRED_ENCRYPTION_KEY; 
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});

      const result = await getCredential("service", "key");

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Cannot get credential: Encryption key is missing.");
      
      consoleErrorSpy.mockRestore();
      process.env.CRED_ENCRYPTION_KEY = originalKey; 
    });

    it("should return null if service or key is missing for get", async () => {
        const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
        let result = await getCredential(null, "key");
        expect(result).toBeNull();
        expect(consoleErrorSpy).toHaveBeenCalledWith("Service and key are required for retrieving a credential.");

        result = await getCredential("service", null);
        expect(result).toBeNull();
        consoleErrorSpy.mockRestore();
    });

    it("should return null and log error if Supabase select fails (not PGRST116)", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      mockSupabaseClientAPI.single.mockResolvedValue({ data: null, error: new Error("DB error") });
      mockSupabaseClientAPI.eq.mockReturnValue({ single: mockSupabaseClientAPI.single });

      const result = await getCredential("service", "key");

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error retrieving credential for service - key from Supabase:", "DB error");
      consoleErrorSpy.mockRestore();
    });

    it("should return null if credential not found (PGRST116 error)", async () => {
        const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
        mockSupabaseClientAPI.single.mockResolvedValue({ data: null, error: { code: "PGRST116", message: "Not found" } });
        mockSupabaseClientAPI.eq.mockReturnValue({ single: mockSupabaseClientAPI.single });

        const result = await getCredential("nonexistent_service", "nonexistent_key");
        expect(result).toBeNull();
        expect(consoleErrorSpy).not.toHaveBeenCalled(); //PGRST116 is handled gracefully
        consoleErrorSpy.mockRestore();
      });

    it("should return null if no data or data.value is not a string from Supabase", async () => {
      mockSupabaseClientAPI.single.mockResolvedValue({ data: null, error: null });
      mockSupabaseClientAPI.eq.mockReturnValue({ single: mockSupabaseClientAPI.single });
      let result = await getCredential("service", "key");
      expect(result).toBeNull();

      mockSupabaseClientAPI.single.mockResolvedValue({ data: { value: 123 }, error: null }); // Non-string value
      result = await getCredential("service", "key");
      expect(result).toBeNull();
    });

  });
});


import { jest } from "@jest/globals";

// Set up mock environment variables BEFORE any other imports that might use them
process.env.SUPABASE_URL = "http://sam.chat:54321"; // Dummy valid URL
process.env.SUPABASE_KEY = "your_dummy_anon_key";    // Dummy valid key

// This is the API object our mocked getSupabaseClient will return
const mockSupabaseClientAPI = {
  from: jest.fn(),
  select: jest.fn(),
  insert: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
  eq: jest.fn(),
  single: jest.fn(),
  rpc: jest.fn(),
  range: jest.fn(),
  order: jest.fn(),
  limit: jest.fn(),
};

// Mock the module. The getSupabaseClient export from this module will be a Jest mock function.
jest.mock("../src/adapters/supabaseAdapter.js", () => {
  const originalModule = jest.requireActual("../src/adapters/supabaseAdapter.js");
  return {
    __esModule: true, // Necessary for ES modules
    ...originalModule, // Spread original exports (like setupTables, createRecord, etc.)
    // Override getSupabaseClient with a Jest mock function.
    // This mock function, when called, will by default return our mockSupabaseClientAPI.
    getSupabaseClient: jest.fn(() => mockSupabaseClientAPI),
  };
});

// Now, import the functions to be tested from the (partially) mocked adapter.
// The `getSupabaseClient` imported here IS the Jest mock function defined in the factory above.
import {
  setupTables,
  createRecord,
  getRecord,
  updateRecord,
  deleteRecord,
  listRecords,
  getSupabaseClient, // This is the actual Jest mock function for getSupabaseClient
} from "../src/adapters/supabaseAdapter.js";

describe("Supabase Adapter", () => {
  beforeEach(() => {
    // Clear call history and reset any specific mock implementations for ALL mocks.
    jest.clearAllMocks();

    // Ensure our main mock `getSupabaseClient` is configured to return the API object for each test.
    // This is important if a test might have changed its implementation (e.g., with mockImplementationOnce).
    getSupabaseClient.mockReturnValue(mockSupabaseClientAPI);

    // Re-establish the default behavior for chained methods on mockSupabaseClientAPI for each test.
    mockSupabaseClientAPI.from.mockReturnValue(mockSupabaseClientAPI);
    mockSupabaseClientAPI.select.mockReturnValue(mockSupabaseClientAPI);
    mockSupabaseClientAPI.insert.mockReturnValue(mockSupabaseClientAPI);
    mockSupabaseClientAPI.update.mockReturnValue(mockSupabaseClientAPI);
    mockSupabaseClientAPI.delete.mockReturnValue(mockSupabaseClientAPI);
    mockSupabaseClientAPI.eq.mockReturnValue(mockSupabaseClientAPI);
    mockSupabaseClientAPI.order.mockReturnValue(mockSupabaseClientAPI);
    mockSupabaseClientAPI.limit.mockReturnValue(mockSupabaseClientAPI);
    // Terminal methods like rpc, single, range will have their specific mockResolvedValue/mockRejectedValue set in each test case.
  });

  describe("setupTables", () => {
    it("should attempt to create credentials and scheduled_jobs tables", async () => {
      mockSupabaseClientAPI.rpc
        .mockResolvedValueOnce({ error: null }) // Credentials table
        .mockResolvedValueOnce({ error: null }); // Scheduled_jobs table

      await setupTables();

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(mockSupabaseClientAPI.rpc).toHaveBeenCalledTimes(2);
      expect(mockSupabaseClientAPI.rpc).toHaveBeenCalledWith("query", {
        sql: expect.stringContaining("CREATE TABLE IF NOT EXISTS credentials")
      });
      expect(mockSupabaseClientAPI.rpc).toHaveBeenCalledWith("query", {
        sql: expect.stringContaining("CREATE TABLE IF NOT EXISTS scheduled_jobs")
      });
    });

    it("should log an error if table creation fails for credentials table", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      mockSupabaseClientAPI.rpc
        .mockResolvedValueOnce({ error: new Error("Credentials table creation failed") })
        .mockResolvedValueOnce({ error: null });

      await setupTables();
      
      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error setting up tables:", "Credentials table creation failed");
      consoleErrorSpy.mockRestore();
    });

    it("should log an error if table creation fails for scheduled_jobs table", async () => {
        const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
        mockSupabaseClientAPI.rpc
            .mockResolvedValueOnce({ error: null })
            .mockResolvedValueOnce({ error: new Error("Jobs table creation failed") });
  
        await setupTables();
        
        expect(getSupabaseClient).toHaveBeenCalledTimes(1);
        expect(consoleErrorSpy).toHaveBeenCalledWith("Error setting up tables:", "Jobs table creation failed");
        consoleErrorSpy.mockRestore();
      });
  });

  describe("createRecord", () => {
    it("should insert a record and return it", async () => {
      const recordData = { name: "Test Job", cron: "* * * * *" };
      const expectedRecord = { id: "uuid", ...recordData };
      mockSupabaseClientAPI.select.mockResolvedValue({ data: [expectedRecord], error: null });

      const result = await createRecord("scheduled_jobs", recordData);

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("scheduled_jobs");
      expect(mockSupabaseClientAPI.insert).toHaveBeenCalledWith([recordData]);
      expect(mockSupabaseClientAPI.select).toHaveBeenCalled(); 
      expect(result).toEqual(expectedRecord);
    });

    it("should return null and log error if insert fails", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      mockSupabaseClientAPI.select.mockResolvedValue({ data: null, error: new Error("Insert failed") });

      const result = await createRecord("scheduled_jobs", {});

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error creating record in scheduled_jobs:", "Insert failed");
      consoleErrorSpy.mockRestore();
    });
  });

  describe("getRecord", () => {
    it("should retrieve a record by ID", async () => {
      const recordId = "test-id";
      const expectedRecord = { id: recordId, name: "Test" };
      mockSupabaseClientAPI.single.mockResolvedValue({ data: expectedRecord, error: null });

      const result = await getRecord("some_table", recordId);

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("some_table");
      expect(mockSupabaseClientAPI.select).toHaveBeenCalledWith("*");
      expect(mockSupabaseClientAPI.eq).toHaveBeenCalledWith("id", recordId);
      expect(mockSupabaseClientAPI.single).toHaveBeenCalled();
      expect(result).toEqual(expectedRecord);
    });

    it("should return null if record not found (PGRST116 error)", async () => {
        mockSupabaseClientAPI.single.mockResolvedValue({ data: null, error: { code: 'PGRST116', message: 'Row not found' } });
        const result = await getRecord("some_table", "non-existent-id");
        expect(getSupabaseClient).toHaveBeenCalledTimes(1);
        expect(result).toBeNull();
      });

    it("should return null and log error if retrieval fails for other reasons", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      mockSupabaseClientAPI.single.mockResolvedValue({ data: null, error: new Error("DB error") });

      const result = await getRecord("some_table", "test-id");

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error retrieving record test-id from some_table:", "DB error");
      consoleErrorSpy.mockRestore();
    });
  });

  describe("updateRecord", () => {
    it("should update a record and return it", async () => {
      const recordId = "test-id";
      const updatedData = { name: "Updated Name" };
      const expectedRecord = { id: recordId, ...updatedData };
      mockSupabaseClientAPI.select.mockResolvedValue({ data: [expectedRecord], error: null });

      const result = await updateRecord("some_table", recordId, updatedData);

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("some_table");
      expect(mockSupabaseClientAPI.update).toHaveBeenCalledWith(updatedData);
      expect(mockSupabaseClientAPI.eq).toHaveBeenCalledWith("id", recordId);
      expect(mockSupabaseClientAPI.select).toHaveBeenCalled();
      expect(result).toEqual(expectedRecord);
    });

    it("should return null and log error if update fails", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      mockSupabaseClientAPI.select.mockResolvedValue({ data: null, error: new Error("Update failed") });

      const result = await updateRecord("some_table", "test-id", {});

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error updating record test-id in some_table:", "Update failed");
      consoleErrorSpy.mockRestore();
    });
  });

  describe("deleteRecord", () => {
    it("should delete a record and return true", async () => {
      mockSupabaseClientAPI.eq.mockResolvedValue({ error: null });

      const result = await deleteRecord("some_table", "test-id");

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("some_table");
      expect(mockSupabaseClientAPI.delete).toHaveBeenCalled();
      expect(mockSupabaseClientAPI.eq).toHaveBeenCalledWith("id", "test-id");
      expect(result).toBe(true);
    });

    it("should return false and log error if delete fails", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      mockSupabaseClientAPI.eq.mockResolvedValue({ error: new Error("Delete failed") });

      const result = await deleteRecord("some_table", "test-id");

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(result).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error deleting record test-id from some_table:", "Delete failed");
      consoleErrorSpy.mockRestore();
    });
  });

  describe("listRecords", () => {
    it("should list records with no options", async () => {
      const expectedRecords = [{ id: "1" }, { id: "2" }];
      mockSupabaseClientAPI.select.mockResolvedValue({ data: expectedRecords, error: null });

      const result = await listRecords("some_table");

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("some_table");
      expect(mockSupabaseClientAPI.select).toHaveBeenCalledWith("*");
      expect(result).toEqual(expectedRecords);
    });

    it("should list records with filters, order, limit, and offset", async () => {
      const options = {
        filters: { status: "active", type: "important" },
        orderBy: "created_at",
        ascending: false,
        limit: 10,
        offset: 5,
      };
      const expectedRecords = [{ id: "1" }];
      mockSupabaseClientAPI.range.mockResolvedValue({ data: expectedRecords, error: null });

      const result = await listRecords("some_table", options);

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(mockSupabaseClientAPI.from).toHaveBeenCalledWith("some_table");
      expect(mockSupabaseClientAPI.select).toHaveBeenCalledWith("*");
      expect(mockSupabaseClientAPI.eq).toHaveBeenCalledWith("status", "active");
      expect(mockSupabaseClientAPI.eq).toHaveBeenCalledWith("type", "important");
      expect(mockSupabaseClientAPI.order).toHaveBeenCalledWith("created_at", { ascending: false });
      expect(mockSupabaseClientAPI.limit).toHaveBeenCalledWith(10);
      expect(mockSupabaseClientAPI.range).toHaveBeenCalledWith(5, 14); 
      expect(result).toEqual(expectedRecords);
    });

    it("should return null and log error if listing fails", async () => {
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      mockSupabaseClientAPI.select.mockResolvedValue({ data: null, error: new Error("List failed") });

      const result = await listRecords("some_table");

      expect(getSupabaseClient).toHaveBeenCalledTimes(1);
      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith("Error listing records from some_table:", "List failed");
      consoleErrorSpy.mockRestore();
    });
  });
});


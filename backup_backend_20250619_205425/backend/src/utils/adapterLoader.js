const path = require("path");
const fs = require("fs");
const { getSupabaseClient } = require("../../../src/adapters/supabaseAdapter.js"); 
const mcpBrokerService = require("../services/mcpBrokerService.js"); 

const adapterConstructors = {};

const loadAdapterClasses = () => {
  const adapterDir = path.join(__dirname, "../adapters");
  try {
    const adapterFiles = fs.readdirSync(adapterDir)
      .filter(file => 
        file.endsWith("Adapter.js") && 
        file !== "baseMCPAdapter.js" &&
        file !== "supabaseAdapter.js"
      );
    
    for (const file of adapterFiles) {
      try {
        const AdapterClass = require(path.join(adapterDir, file));
        if (typeof AdapterClass === 'function' && AdapterClass.prototype && AdapterClass.prototype.constructor) {
            let className = AdapterClass.name;
            if (!className) { 
                const instance = new AdapterClass();
                className = instance.constructor.name;
            }

            if (className && className !== "Object") { 
                adapterConstructors[className] = AdapterClass;
                console.log(`[AdapterLoader] Loaded adapter class: ${className} from ${file}`);
            } else {
                console.warn(`[AdapterLoader] Could not determine class name for adapter in ${file}`);
            }
        } else {
            console.warn(`[AdapterLoader] ${file} does not export a valid class constructor.`);
        }
      } catch (error) {
        console.error(`[AdapterLoader] Error loading adapter from ${file}:`, error);
      }
    }
  } catch (err) {
    console.error(`[AdapterLoader] Error reading adapters directory ${adapterDir}:`, err);
  }
  return adapterConstructors;
};

const setupAdapterRegistrationsTable = async () => {
  const supabase = getSupabaseClient();
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS adapter_registrations (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      adapter_id TEXT NOT NULL UNIQUE,
      adapter_name TEXT NOT NULL,
      adapter_class TEXT NOT NULL,
      config JSONB DEFAULT '{}'::jsonb,
      enabled BOOLEAN DEFAULT true,
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now()
    );
  `;
  const createIndexAdapterIdSQL = `CREATE INDEX IF NOT EXISTS idx_adapter_registrations_adapter_id ON adapter_registrations (adapter_id);`;
  const createIndexEnabledSQL = `CREATE INDEX IF NOT EXISTS idx_adapter_registrations_enabled ON adapter_registrations (enabled);`;

  try {
    const { error: tableError } = await supabase.rpc('query', { sql: createTableSQL });
    if (tableError) {
      console.error("[AdapterLoader] Error creating adapter_registrations table:", tableError);
      throw tableError; 
    }
    console.log("[AdapterLoader] Table 'adapter_registrations' checked/created successfully.");

    const { error: index1Error } = await supabase.rpc('query', { sql: createIndexAdapterIdSQL });
    if (index1Error) console.warn("[AdapterLoader] Warning creating index idx_adapter_registrations_adapter_id:", index1Error.message); 
    else console.log("[AdapterLoader] Index 'idx_adapter_registrations_adapter_id' checked/created.");

    const { error: index2Error } = await supabase.rpc('query', { sql: createIndexEnabledSQL });
    if (index2Error) console.warn("[AdapterLoader] Warning creating index idx_adapter_registrations_enabled:", index2Error.message); 
    else console.log("[AdapterLoader] Index 'idx_adapter_registrations_enabled' checked/created.");

    console.log("[AdapterLoader] Adapter registrations table setup complete.");
    return true;
  } catch (error) {
    console.error("[AdapterLoader] Critical error setting up adapter registrations table:", error.message);
    return false;
  }
};

const loadPersistedAdapters = async () => {
  try {
    loadAdapterClasses(); 
    const supabase = getSupabaseClient();
    let registrations = [];

    try {
        const { data, error } = await supabase
            .from("adapter_registrations")
            .select("*")
            .eq("enabled", true);

        if (error) {
            console.error("[AdapterLoader] Error fetching adapter registrations from Supabase:", error);
        } else {
            registrations = data || [];
            console.log(`[AdapterLoader] Found ${registrations.length} enabled adapter registrations in Supabase.`);
        }
    } catch (supaError) {
        console.error("[AdapterLoader] Exception fetching from Supabase:", supaError);
    }

    for (const reg of registrations) {
      try {
        const AdapterClass = adapterConstructors[reg.adapter_class];
        if (!AdapterClass) {
          console.error(`[AdapterLoader] Adapter class ${reg.adapter_class} not found for adapter_id ${reg.adapter_id}`);
          continue;
        }
        
        const adapter = new AdapterClass(reg.config || {});
        
        if (typeof adapter.initialize === "function") {
          await adapter.initialize();
        }
        
        await mcpBrokerService.registerAdapter(adapter, false); 
        console.log(`[AdapterLoader] Successfully loaded and registered adapter from Supabase: ${reg.adapter_id}`);
      } catch (error) {
        console.error(`[AdapterLoader] Error initializing adapter ${reg.adapter_id} from Supabase:`, error);
      }
    }

    const jsonConfigPath = path.join(__dirname, "../../config/adapter_config.json"); 
    if (fs.existsSync(jsonConfigPath)) {
        console.log(`[AdapterLoader] Attempting to load adapters from JSON config: ${jsonConfigPath}`);
        try {
            const jsonData = fs.readFileSync(jsonConfigPath, "utf-8");
            const jsonAdapters = JSON.parse(jsonData);

            for (const reg of jsonAdapters) {
                if (reg.enabled === false) continue; 

                if (mcpBrokerService.getAdapter(reg.adapter_id)) {
                    console.log(`[AdapterLoader] Adapter ${reg.adapter_id} from JSON already loaded (likely from Supabase). Skipping.`);
                    continue;
                }

                try {
                    const AdapterClass = adapterConstructors[reg.adapter_class];
                    if (!AdapterClass) {
                        console.error(`[AdapterLoader] Adapter class ${reg.adapter_class} not found for adapter_id ${reg.adapter_id} from JSON.`);
                        continue;
                    }
                    const adapter = new AdapterClass(reg.config || {});
                    if (typeof adapter.initialize === "function") {
                        await adapter.initialize();
                    }
                    await mcpBrokerService.registerAdapter(adapter, true); 
                    console.log(`[AdapterLoader] Successfully loaded, registered, and persisted adapter from JSON: ${reg.adapter_id}`);
                } catch (jsonError) {
                    console.error(`[AdapterLoader] Error initializing adapter ${reg.adapter_id} from JSON:`, jsonError);
                }
            }
        } catch (fileError) {
            console.error(`[AdapterLoader] Error reading or parsing ${jsonConfigPath}:`, fileError);
        }
    } else {
        console.log("[AdapterLoader] JSON adapter config file not found, skipping JSON load.");
    }
    
    return true;
  } catch (e) {
    console.error("[AdapterLoader] Critical error in loadPersistedAdapters:", e);
    return false;
  }
};

module.exports = {
  loadAdapterClasses,
  loadPersistedAdapters,
  setupAdapterRegistrationsTable
};

